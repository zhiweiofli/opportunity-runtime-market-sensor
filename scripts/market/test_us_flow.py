"""US-01..11 offline contracts. Simulated transport never proves native source access."""

import argparse
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import actions_entry
import market_sensor as sensor
import tushare_us_preflight as probe
import us_flow as flow
from us_sources import Blocked, amount, parse_ici, parse_spy


CONFIG, _ = flow.load_config(flow.CONFIG)
FIXTURE_DIR = flow.FIXTURE.parent
ICI = (FIXTURE_DIR/'ici-synthetic.html').read_bytes()
SPY = (FIXTURE_DIR/'spy-synthetic.html').read_bytes()
CLOCK = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)


def rule(values):
    dates = ['2026-09-16', '2026-09-23', '2026-09-30', '2026-10-07']
    return flow.reversal([{'period_end': d, 'value_usd_million': str(v)} for d, v in zip(dates, values)], CONFIG)


class FlowTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)

    def inputs(self, ici=ICI, spy=SPY, synthetic=True, retrieved='2026-10-15T12:00:00+00:00', **changes):
        sources = {}
        for name, raw, url in [('ici', ici, CONFIG['ici_url']), ('instrument', spy, CONFIG['instrument_url'])]:
            file = name+'.html'
            (self.path/file).write_bytes(raw)
            sources[name] = {'file': file, 'source_url': url, 'retrieved_at': retrieved,
                             'sha256': hashlib.sha256(raw).hexdigest()}
        manifest = self.path/'manifest.json'
        manifest.write_text(json.dumps({'schema_version': 1, 'synthetic': synthetic, 'sources': sources}))
        values = dict(mode='flow', input_mode='supplied_snapshot', snapshot_manifest=manifest,
                      config=flow.CONFIG, as_of='2026-10-20', output=self.path/'report.json',
                      demo_abs_pct=None, trade_date='', ts_code='', as_of_date='', previous_report_data=None)
        values.update(changes)
        return argparse.Namespace(**values)

    def run_input(self, **kw):
        args = self.inputs(**kw)
        with patch.object(flow, 'now', return_value=CLOCK):
            return flow.run_flow(args)

    def test_us_02_reversal_positive_negative_and_no_signal_cases(self):
        out = rule([3000, 3000, -4000, -4000])
        self.assertTrue(out['rule_hit'])
        self.assertEqual(out['direction'], 'outflow_reversal')
        self.assertEqual((out['before_net_usd_million'], out['after_net_usd_million'], out['change_usd_million']), ('6000', '-8000', '-14000'))
        self.assertEqual(rule([-3000, -3000, 4000, 4000])['direction'], 'inflow_reversal')
        for values in [[3000, 3000, 4000, -4000], [3000]*4, [-3000]*4,
                       [0, 6000, -4000, -4000], [2499, 2500, -4000, -4000]]:
            self.assertFalse(rule(values)['rule_hit'])

    def test_us_03_exact_amount_boundaries_and_formats(self):
        self.assertTrue(rule([2500, 2500, -2500, -2500])['rule_hit'])
        self.assertFalse(rule(['2499.999', 2500, -2500, -2500])['rule_hit'])
        self.assertFalse(rule([2500, 2500, '-2499.999', -2500])['rule_hit'])
        self.assertEqual(amount('−3,000.25'), -amount('3,000.25'))
        self.assertEqual(amount('(3,000)'), -3000)
        self.assertEqual(amount('0'), 0)
        for value in ['—', '', 'NaN', 'Inf', '1,00', '3000 million']:
            with self.assertRaises(Blocked):
                amount(value)

    def test_us_04_structured_html_and_fail_closed_drift(self):
        actual = parse_ici(ICI)
        self.assertEqual(actual['published_date'], '2026-10-14')
        self.assertEqual(actual['category'], 'Domestic equity')
        self.assertEqual(actual['unit'], 'USD million')
        self.assertEqual(actual['selected_rows'][0]['value_usd_million'], '3000')
        # Head/title text must not be mistaken for the release's body date.
        html = ICI.replace(b'<title>SYNTHETIC FIXTURE</title>', b'<title>Release: Combined Estimated Long-Term Flows and ETF Net Issuance</title>')
        self.assertEqual(parse_ici(html)['published_date'], '2026-10-14')
        for raw in [b'<h1>Log in</h1>', ICI.replace(b'Millions of dollars', b'Thousands of dollars'),
                    ICI.replace(b'>Domestic<', b'>World<'), ICI.replace(b'Combined', b'Mutual Fund Only'),
                    ICI.replace(b'October 14, 2026', b'unknown date')]:
            self.assertEqual(self.run_input(ici=raw)['status'], 'BLOCKED')
        with self.assertRaises(Blocked):
            parse_ici(ICI.replace(b'Millions of dollars', b'Thousands of dollars')+b'<p>Millions of dollars</p>')

    def test_us_05_duplicate_missing_weeks_sort_and_freshness(self):
        for raw in [ICI.replace(b'9/23/2026', b'9/16/2026'), ICI.replace(b'9/23/2026', b'9/2/2026')]:
            self.assertEqual(self.run_input(ici=raw)['status'], 'BLOCKED')
        result = self.run_input()
        self.assertEqual([r['period_end'] for r in result['rule_evaluation']['rows']],
                         ['2026-09-16', '2026-09-23', '2026-09-30', '2026-10-07'])
        self.assertEqual(self.run_input(as_of='2026-10-28')['status'], 'SIGNALS')
        self.assertEqual(self.run_input(as_of='2026-10-29')['status'], 'BLOCKED')
        self.assertEqual(self.run_input(ici=ICI.replace(b'October 14, 2026', b'October 30, 2026'))['status'], 'BLOCKED')
        # Fresh publication but its latest period is too old.
        self.assertEqual(self.run_input(ici=ICI.replace(b'October 14, 2026', b'October 25, 2026'), as_of='2026-10-26')['status'], 'BLOCKED')

    def test_us_05_date_precision_and_new_york_dst(self):
        self.assertEqual(flow.availability('2026-03-07').isoformat(), '2026-03-08T05:00:00+00:00')
        self.assertEqual(flow.availability('2026-03-08').isoformat(), '2026-03-09T04:00:00+00:00')
        self.assertEqual(flow.availability('2026-10-31').isoformat(), '2026-11-01T04:00:00+00:00')
        self.assertEqual(flow.availability('2026-11-01').isoformat(), '2026-11-02T05:00:00+00:00')
        # Retrieved during publication day is still conservatively unavailable before NY midnight.
        self.assertEqual(self.run_input(retrieved='2026-10-14T12:00:00Z', as_of='2026-10-15T03:59:59Z')['status'], 'BLOCKED')
        self.assertEqual(self.run_input(retrieved='2026-10-14T12:00:00Z', as_of='2026-10-15T04:00:00Z')['status'], 'SIGNALS')
        self.assertEqual(self.run_input(as_of='2026-10-20T12:00:00')['status'], 'ERROR')

    def test_us_06_pit_replay_requires_saved_vintage(self):
        self.assertEqual(self.run_input(retrieved='2026-10-20T10:00:00Z', as_of='2026-10-18')['status'], 'BLOCKED')
        self.assertEqual(self.run_input(retrieved='2026-10-15T12:00:00Z', as_of='2026-10-18')['status'], 'SIGNALS')
        args = self.inputs()
        manifest = json.loads(args.snapshot_manifest.read_text())
        del manifest['sources']['ici']['retrieved_at']
        args.snapshot_manifest.write_text(json.dumps(manifest))
        self.assertEqual(flow.run_flow(args)['status'], 'BLOCKED')

    def test_us_06_dedup_reuses_signal_and_marks_revision(self):
        previous = self.run_input()
        args = self.inputs(previous_report_data=previous)
        with patch.object(flow, 'now', return_value=CLOCK.replace(hour=13)):
            report = flow.run_flow(args)
        self.assertEqual(report['signals'], previous['signals'])
        self.assertNotEqual(report['generated_at'], previous['generated_at'])
        self.assertEqual(report['dedup']['status'], 'same_observation_reused')
        # A changed earlier week is a new observation with the same stable Signal ID.
        changed = self.run_input(ici=ICI.replace(b'3,000', b'3,001'), previous_report_data=previous)
        self.assertEqual(changed['signals'][0]['signal_id'], previous['signals'][0]['signal_id'])
        self.assertNotEqual(changed['signals'][0]['observation_id'], previous['signals'][0]['observation_id'])
        self.assertEqual(changed['signals'][0]['revision_of'], previous['signals'][0]['observation_id'])
        self.assertEqual(changed['dedup']['status'], 'revised_observation')
        archived = json.loads((self.path/'source-manifest.json').read_text())
        for source in archived['sources'].values():
            raw = (self.path/source['file']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])
        # Original and revised content-addressed bytes both remain on disk.
        self.assertGreaterEqual(len(list((self.path/'sources').glob('ici-*.html'))), 2)

    def test_us_07_identity_and_liquidity_do_not_use_nav_or_aum(self):
        for raw in [SPY.replace(b'>USD<', b'>CNY<'), SPY.replace(b'>SPY<', b'>OTHER<'),
                    SPY.replace(b'Closing Price', b'NAV'), SPY.replace(b'Exchange Volume (Shares)', b'Assets Under Management'),
                    SPY.replace(b'Exchange Volume (Shares)', b'Exchange Volume (Lots)'),
                    SPY.replace(b'$500.00', b'$0.00'), SPY.replace(b'Oct 14 2026', b'Oct 1 2026'),
                    SPY.replace(b'Oct 14 2026', b'Oct 22 2026'),
                    SPY.replace(b'<tr><th>Exchange Volume', b'</table><h2>Fund Market Price as of Oct 15 2026</h2><table><tr><th>Exchange Volume')]:
            self.assertEqual(self.run_input(spy=raw)['status'], 'BLOCKED')
        self.assertEqual(self.run_input(spy=SPY.replace(b'$500.00', b'$100.00'))['status'], 'SIGNALS')
        self.assertEqual(self.run_input(spy=SPY.replace(b'$500.00', b'$99.999999'))['status'], 'BLOCKED')
        self.assertEqual(parse_spy(SPY)['notional_proxy_usd'], '500000000')

    def test_us_08_synthetic_never_promoted_by_input_mode(self):
        result = self.run_input(input_mode='supplied_snapshot')
        self.assertEqual(result['status'], 'SIGNALS')
        self.assertTrue(result['demo_only'])
        self.assertFalse(result['research_eligible'])
        self.assertFalse(result['signals'][0]['research_eligible'])
        self.assertEqual(self.run_input(synthetic=False)['status'], 'BLOCKED')

    def test_us_08_simulated_genuine_source_contract_can_enter_r1(self):
        # Simulates the provenance contract in memory, not a real acquisition claim.
        args = self.inputs(synthetic=False)
        def acquired(name, config, args, manifest, synthetic):
            raw = ICI if name == 'ici' else SPY
            return raw, {'name': name, 'source_url': config['ici_url' if name == 'ici' else 'instrument_url'],
                         'retrieved_at': '2026-10-15T12:00:00Z', 'sha256': hashlib.sha256(raw).hexdigest(),
                         'raw_file': 'simulated-transport-only', 'synthetic': False}
        with patch.object(flow, 'acquire_source', side_effect=acquired), patch.object(flow, 'now', return_value=CLOCK):
            result = flow.run_flow(args)
        self.assertEqual(result['status'], 'SIGNALS')
        self.assertTrue(result['research_eligible'])
        self.assertTrue(result['signals'][0]['research_eligible'])
        self.assertFalse(result['demo_only'])
        self.assertEqual(result['rule']['status'], 'trial')
        packet = flow.render_packet(result)
        for text in ['可交R1核验', '3000', '-4000', '2026-09-16', '2026-10-07', CONFIG['ici_url'],
                     CONFIG['instrument_url'], '配置', 'KILL', '现金缓冲', '不是已证实的价格因果', 'Generated At', 'Observation ID']:
            self.assertIn(text, packet)

    def test_us_09_live_failure_blocked_never_falls_back_or_leaks(self):
        args = self.inputs(input_mode='live_http')
        for error in [URLError('FAKE_PRIVATE'), HTTPError(CONFIG['ici_url'], 403, 'FAKE_PRIVATE', {}, None)]:
            with patch.object(flow, 'urlopen', side_effect=error):
                result = flow.run_flow(args)
            self.assertEqual(result['status'], 'BLOCKED')
            self.assertEqual(result['signals'], [])
            self.assertNotIn('FAKE_PRIVATE', json.dumps(result))
            self.assertEqual(json.loads((self.path/'source-manifest.json').read_text())['sources'], {})

    def test_us_09_three_files_stale_cleanup_packet_write_failure(self):
        output = self.path/'report.json'
        cli = ['--mode', 'flow', '--input-mode', 'synthetic_fixture', '--as-of', '2026-10-20', '--output', str(output)]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(sensor.main(cli), 0)
            self.assertIn('SYNTHETIC', (self.path/'researcher-packet.md').read_text())
            real_write = Path.write_text
            def fail_packet(path, *a, **kw):
                if path.name == 'researcher-packet.md':
                    raise OSError('FAKE_PRIVATE')
                return real_write(path, *a, **kw)
            with patch.object(Path, 'write_text', fail_packet):
                self.assertEqual(sensor.main(cli), 1)
            self.assertTrue(all(not (self.path/name).exists() for name in ['report.json', 'report.md', 'researcher-packet.md']))
            self.assertEqual(sensor.main(cli+['--as-of', 'bad']), 1)
            self.assertEqual(json.loads(output.read_text())['status'], 'ERROR')
            self.assertNotIn('MKT-', (self.path/'researcher-packet.md').read_text())

    def test_supplied_manifest_missing_metadata_wrong_source_or_hash(self):
        for key, value in [('source_url', 'https://example.com/copied-flow.json'), ('retrieved_at', '2026-10-15'), ('sha256', 'bad')]:
            args = self.inputs()
            manifest = json.loads(args.snapshot_manifest.read_text())
            manifest['sources']['ici'][key] = value
            args.snapshot_manifest.write_text(json.dumps(manifest))
            result = flow.run_flow(args)
            self.assertEqual(result['status'], 'BLOCKED')
            self.assertEqual(result['signals'], [])

    def test_us_11_public_reference_is_no_reversal_not_native_html_claim(self):
        # Published ICI 2026-10-14 values checked via original public reference;
        # no reconstructed HTML is labelled as an original response.
        result = rule([-11490, 5696, -7282, -18355])
        self.assertFalse(result['rule_hit'])
        self.assertEqual(result['before_net_usd_million'], '-5794')
        self.assertEqual(result['after_net_usd_million'], '-25637')
        self.assertEqual(result['change_usd_million'], '-19843')

    def test_valid_complete_no_match_is_no_signal_missing_instrument_is_blocked(self):
        no_match = ICI.replace(b'3,000', b'-3,000')
        self.assertEqual(self.run_input(ici=no_match)['status'], 'NO_SIGNAL')
        self.assertEqual(self.run_input(ici=no_match, spy=b'<h1>unavailable</h1>')['status'], 'BLOCKED')

    def test_us_10_schedule_and_replay_inputs_and_permissions(self):
        self.assertEqual(actions_entry.arguments('schedule', {'INPUT_MODE': 'history', 'INPUT_INPUT_MODE': 'synthetic_fixture'}),
                         ['--mode', 'flow', '--input-mode', 'live_http'])
        options = actions_entry.arguments('workflow_dispatch', {'INPUT_MODE': 'flow', 'INPUT_INPUT_MODE': 'supplied_snapshot',
                    'INPUT_AS_OF': '2026-10-20', 'INPUT_SNAPSHOT_RUN_ID': '123', 'INPUT_PREVIOUS_RUN_ID': '122'})
        self.assertIn('inputs/snapshot/source-manifest.json', options)
        self.assertIn('inputs/previous/report.json', options)
        active = (flow.ROOT/'.github/workflows/market-sensor.yml').read_text()
        self.assertEqual(active, (flow.ROOT/'tasks/github-actions/market-sensor.yml').read_text())
        self.assertIn("cron: '17 8 * * 5'", active)
        self.assertIn('timezone: Asia/Taipei', active)
        self.assertIn('actions: read', active)
        self.assertIn('if: ${{ always() }}', active)
        self.assertNotIn('17 20 * * 1-5', active)
        self.assertNotIn('contents: write', active)


class RunnerProbeTests(unittest.TestCase):
    def test_cloud_never_reads_tushare_token(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(probe, 'urlopen') as connect:
            report = probe.probe('20261016')
        connect.assert_not_called()
        self.assertEqual(report['status'], 'BLOCKED')

    @patch.dict(os.environ, {'GITHUB_ACTIONS': 'true', 'TUSHARE_TOKEN': 'SYNTHETIC_TOKEN'}, clear=True)
    def test_runner_probe_only_hits_tushare_and_does_not_infer_volume_units(self):
        response = {'code': 0, 'data': {'fields': ['ts_code', 'trade_date', 'close', 'vol', 'amount'],
                    'items': [['SPY', '20261016', 500, 1000000, 500000000]]}}
        with patch.object(probe, 'urlopen', return_value=io.StringIO(json.dumps(response))) as connect:
            report = probe.probe('20261016')
        self.assertEqual(connect.call_args.args[0].full_url, 'https://api.tushare.pro')
        self.assertEqual(json.loads(connect.call_args.args[0].data)['api_name'], 'us_daily')
        self.assertEqual(report['status'], 'RESPONSE_RECEIVED_UNITS_UNVERIFIED')
        self.assertFalse(report['volume_unit_verified'])
        self.assertFalse(report['coverage_verified'])
        self.assertNotIn('SYNTHETIC_TOKEN', json.dumps(report))

    @patch.dict(os.environ, {'GITHUB_ACTIONS': 'true', 'TUSHARE_TOKEN': 'SYNTHETIC_TOKEN'}, clear=True)
    def test_bad_us_fields_and_api_errors_are_not_exposed(self):
        for response in [{'code': -1, 'msg': 'SYNTHETIC_TOKEN'},
                         {'code': 0, 'data': {'fields': ['ts_code','trade_date','close','vol','amount'],
                          'items': [['SPY', '20261016', 'SYNTHETIC_TOKEN', 1, 1]]}}]:
            with patch.object(probe, 'urlopen', return_value=io.StringIO(json.dumps(response))):
                report = probe.probe('20261016')
            self.assertEqual(report['status'], 'BLOCKED')
            self.assertNotIn('SYNTHETIC_TOKEN', json.dumps(report))


if __name__ == '__main__':
    unittest.main()
