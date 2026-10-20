"""V1-01..09/12 offline evidence. All histories and credentials here are synthetic."""

import argparse
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import date, timedelta
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import actions_entry
import market_history as history
import market_sensor as sensor


ROOT = Path(__file__).resolve().parents[2]
TARGET = '20261016'
CONFIG, DIGEST = history.load_config(history.CONFIG)
CODES = CONFIG['universe']


def rows(code=CODES[0], count=259):
    dates, d = [], date(2026, 10, 16)
    while len(dates) < count:
        if d.weekday() < 5:
            dates.append(d.strftime('%Y%m%d'))
        d -= timedelta(days=1)
    return [dict(ts_code=code, trade_date=d, close=10, pct_chg=0, vol=10000, amount=100000)
            for d in reversed(dates)]


def matching(code=CODES[0]):
    data = rows(code)
    for row in data[-2:]:
        row.update(pct_chg=5, amount=300000)
    return data


def args(**changes):
    values = dict(mode='history', source='fixture', as_of_date=TARGET, trade_date='', ts_code='',
                  demo_abs_pct=None, config=history.CONFIG,
                  history_fixture=ROOT / 'scripts/market/history-fixture.json')
    values.update(changes)
    return argparse.Namespace(**values)


def batch(data, config=None, **changes):
    config = deepcopy(config or CONFIG)
    with patch.object(history, 'load_config', return_value=(config, DIGEST)), \
            patch.object(history.DailyClient, 'fetch', side_effect=lambda start, end, code: data[code]), \
            patch.object(history, 'taipei_today', return_value='20261020'):
        return history.run_history(args(source='tushare', **changes))


class HistoricalRuleTests(unittest.TestCase):
    def test_v1_02_compound_returns_units_and_baselines(self):
        result = history.evaluate(matching(), TARGET, CONFIG)
        self.assertEqual(result['status'], 'MATCH')
        first, previous, current = result['evaluations']
        self.assertEqual([first['r5'], previous['r5'], current['r5']], [0, 0.05, 0.1025])
        self.assertEqual(current['amount_ratio'], 3)
        self.assertEqual(current['amount_median_cny'], 100000000)
        self.assertEqual(result['avg_amount_20_cny'], 110000000)
        self.assertEqual(current['historical_samples'], 252)
        self.assertEqual(current['historical_le_count'], 252)
        self.assertEqual(current['baseline_range'], [matching()[6]['trade_date'], '20261015'])
        self.assertEqual(result['same_direction_hit_dates'], ['20261015', '20261016'])
        # An unadjusted close jump must not change pct_chg-based returns.
        adjusted = matching()
        adjusted[-1]['close'] = 100000
        self.assertEqual(history.evaluate(adjusted, TARGET, CONFIG), result)

    def test_v1_03_reject_single_current_miss_opposite_and_zero(self):
        cases = []
        single = rows()
        single[-1].update(pct_chg=6, amount=300000)
        cases.append(single)
        current_miss = matching()
        current_miss[-1]['amount'] = 100000
        cases.append(current_miss)
        opposite = matching()
        opposite[-2]['pct_chg'] = 10
        opposite[-1]['pct_chg'] = -20
        cases.append(opposite)
        cases.append(rows())
        for data in cases:
            with self.subTest(last=data[-1]):
                result = history.evaluate(data, TARGET, CONFIG)
                self.assertEqual(result['status'], 'NO_MATCH')
                self.assertTrue(result['reason'])

    def test_v1_04_return_amount_and_liquidity_boundaries(self):
        for change, hit in [(5, True), (4.999999, False), (-5, True), (-4.999999, False)]:
            data = rows()
            data[-1].update(pct_chg=change, amount=200000)
            self.assertEqual(history.evaluate_day(data, 258, CONFIG)['hit'], hit)
        data = rows()
        data[-1].update(pct_chg=5, amount=199999.999)
        self.assertFalse(history.evaluate_day(data, 258, CONFIG)['hit'])
        for amount, status in [(100000, 'NO_MATCH'), (99999.999, 'LOW_LIQUIDITY')]:
            data = rows()
            for row in data:
                row['amount'] = amount
            result = history.evaluate(data, TARGET, CONFIG)
            self.assertEqual(result['status'], status)
            self.assertEqual(result['avg_amount_20_cny'], amount * 1000)
        data = matching()
        data[-1]['amount'] = 0
        self.assertEqual(history.evaluate(data, TARGET, CONFIG)['status'], 'LOW_LIQUIDITY')

    def test_v1_04_even_median_and_percentile_counts(self):
        data = rows()
        for i, row in enumerate(data[198:258]):
            row['amount'] = 100000 if i % 2 else 200000
        data[-1].update(pct_chg=5, amount=300000)
        metric = history.evaluate_day(data, 258, CONFIG)
        self.assertEqual(metric['amount_median_cny'], 150000000)
        self.assertEqual(metric['amount_ratio'], 2)
        for spike, count, hit in [(3, 250, True), (4, 249, False)]:
            data = rows()
            data[spike]['pct_chg'] = 10
            data[-1].update(pct_chg=5, amount=200000)
            metric = history.evaluate_day(data, 258, CONFIG)
            self.assertEqual(metric['historical_le_count'], count)
            self.assertAlmostEqual(metric['historical_percentile'], count/252)
            self.assertEqual(metric['hit'], hit)
        # With 100 samples an exact 99% boundary can be represented as a count.
        cfg = {**CONFIG, 'baseline_observations': 100}
        data = rows()
        data[154]['pct_chg'] = 10  # Only historical evaluation 158 exceeds current.
        data[-1].update(pct_chg=5, amount=200000)
        self.assertEqual(history.evaluate_day(data, 258, cfg)['historical_percentile'], 0.99)
        self.assertTrue(history.evaluate_day(data, 258, cfg)['hit'])

    def test_v1_05_future_excluded_and_current_not_in_baseline(self):
        data = matching()
        before = history.evaluate_day(data, 258, CONFIG)
        future = {**data[-1], 'trade_date': '20261019', 'pct_chg': 9000}
        self.assertEqual(history.evaluate_day(data+[future], 258, CONFIG), before)
        future['pct_chg'] = -99
        self.assertEqual(history.evaluate_day(data+[future], 258, CONFIG), before)
        with self.assertRaises(sensor.SensorError):
            history.validate_history(data+[future], '20250414', TARGET, CODES[0])
        # The earlier evaluation has all-zero history: a later spike must not enter it.
        data[-1]['pct_chg'] = 9000
        earlier = history.evaluate_day(data, 257, CONFIG)
        self.assertEqual(earlier['historical_le_count'], 252)
        self.assertLess(earlier['baseline_range'][1], earlier['trade_date'])

    def test_v1_06_history_target_and_freshness_boundaries(self):
        self.assertEqual(history.evaluate(matching()[1:], TARGET, CONFIG)['status'], 'INSUFFICIENT_HISTORY')
        self.assertEqual(history.evaluate(matching(), TARGET, CONFIG)['status'], 'MATCH')
        self.assertEqual(history.evaluate(matching()[:-1], TARGET, CONFIG)['status'], 'NO_DATA')
        for span, expected in [(7, 'MATCH'), (8, 'STALE_HISTORY')]:
            data = matching()
            shift = (history.day(TARGET)-history.day(data[-3]['trade_date'])).days
            for row in data[:-2]:
                row['trade_date'] = (history.day(row['trade_date'])-timedelta(days=span-shift)).strftime('%Y%m%d')
            self.assertEqual(history.evaluate(data, TARGET, CONFIG)['status'], expected)
        for span, expected in [(120, 'MATCH'), (121, 'STALE_HISTORY')]:
            data = matching()
            shift = span - (history.day(TARGET)-history.day(data[-60]['trade_date'])).days
            for row in data[:-59]:
                row['trade_date'] = (history.day(row['trade_date'])-timedelta(days=shift)).strftime('%Y%m%d')
            self.assertEqual(history.evaluate(data, TARGET, CONFIG)['status'], expected)
        report = batch({code: matching(code) for code in CODES}, as_of_date='20990101')
        self.assertEqual(report['status'], 'ERROR')

    def test_zero_median_is_insufficient_instead_of_dividing(self):
        data = matching()
        for row in data[198:238]:
            row['amount'] = 0
        self.assertEqual(history.evaluate(data, TARGET, CONFIG)['status'], 'INSUFFICIENT_HISTORY')

    def test_v1_07_sort_and_reject_contract_errors(self):
        data = matching()
        normalized = history.validate_history(list(reversed(data)), '20250414', TARGET, CODES[0])
        self.assertEqual(normalized, data)
        cases = [data+[data[-1]], data+[dict(data[-1], trade_date='20261019')],
                 data+[dict(data[-1], trade_date='20200101')]]
        for key, value in [('pct_chg', float('nan')), ('pct_chg', float('inf')), ('pct_chg', -100),
                           ('pct_chg', True), ('close', 0), ('amount', -1), ('vol', False),
                           ('ts_code', CODES[1]), ('trade_date', '20260230')]:
            cases.append(data[:-1]+[{**data[-1], key: value}])
        cases += [data[:-1]+[{'trade_date': TARGET}], None]
        for invalid in cases:
            with self.subTest(last=invalid[-1] if invalid else None):
                with self.assertRaises(sensor.SensorError):
                    history.validate_history(invalid, '20250414', TARGET, CODES[0])

    def test_v1_08_fixture_coverage_and_reproducibility(self):
        one = history.run_history(args())
        two = history.run_history(args())
        self.assertEqual(one['status'], 'SIGNALS')
        self.assertEqual([i['status'] for i in one['instruments']],
                         ['MATCH', 'NO_MATCH', 'LOW_LIQUIDITY', 'NO_DATA', 'INSUFFICIENT_HISTORY', 'STALE_HISTORY'])
        self.assertFalse(one['coverage_complete'])
        self.assertEqual(one['coverage']['expected'], sorted(CODES))
        self.assertTrue(one['demo_only'])
        self.assertFalse(one['research_eligible'])
        self.assertEqual(one['config_sha256'], DIGEST)
        for field in ['signal_id', 'magnitude', 'same_direction_hit_dates', 'evaluations']:
            self.assertEqual(one['signals'][0][field], two['signals'][0][field])
        for item in one['instruments']:
            subset = one['observations'][item['observations_start']:item['observations_start']+item['valid_rows']]
            self.assertTrue(all(row['ts_code'] == item['ts_code'] for row in subset))

    def test_legacy_sort_truncate_dedupe_always_demo_flags(self):
        data = {code: matching(code) for code in CODES}
        data[CODES[1]][-1]['pct_chg'] = 6
        data[CODES[2]][-1].update(pct_chg=6, amount=400000)
        config = {**CONFIG, 'universe': [*reversed(CODES), CODES[0]]}
        report = batch(data, config)
        self.assertEqual(report['status'], 'SIGNALS')
        self.assertEqual(report['total_matches'], 6)
        self.assertEqual(report['truncated_matches'], 1)
        self.assertEqual([s['instrument'] for s in report['signals']],
                         [CODES[2], CODES[1], CODES[0], CODES[3], CODES[4]])
        self.assertEqual(len(report['instruments']), 6)
        self.assertTrue(report['coverage_complete'])
        self.assertTrue(report['demo_only'])
        self.assertEqual(report['rule']['status'], 'legacy_demo')
        self.assertTrue(all(s['demo_only'] and not s['research_eligible'] for s in report['signals']))
        # Percentile outranks a larger R5: this code has two larger historical windows.
        data[CODES[0]][3]['pct_chg'] = 30
        data[CODES[0]][-1]['pct_chg'] = 20
        report = batch(data, config)
        self.assertEqual(report['instruments'][0]['evaluations'][-1]['historical_le_count'], 250)
        self.assertEqual([s['instrument'] for s in report['signals']],
                         [CODES[2], CODES[1], CODES[3], CODES[4], CODES[5]])

    def test_twenty_code_offline_batch(self):
        codes = [f'{i:06d}.SZ' for i in range(1, 21)]
        cfg = {**CONFIG, 'universe': codes}
        report = batch({c: matching(c) for c in codes}, cfg)
        self.assertEqual(report['total_matches'], 20)
        self.assertEqual(report['truncated_matches'], 15)
        self.assertEqual(len(report['instruments']), 20)
        self.assertTrue(report['coverage_complete'])
        self.assertEqual(len(report['signals']), 5)

    def test_run_status_aggregation_and_global_error_suppression(self):
        data = {code: [] for code in CODES}
        self.assertEqual(batch(data)['status'], 'NO_DATA')
        data[CODES[0]] = matching()[1:]
        self.assertEqual(batch(data)['status'], 'INSUFFICIENT_DATA')
        data[CODES[1]] = rows(CODES[1])
        self.assertEqual(batch(data)['status'], 'NO_MATCH')
        data[CODES[0]] = matching()
        data[CODES[2]] = matching(CODES[2])+matching(CODES[2])[-1:]
        report = batch(data)
        self.assertEqual(report['status'], 'ERROR')
        self.assertEqual(report['signals'], [])
        self.assertEqual(report['coverage']['failed'], [CODES[2]])
        self.assertEqual(report['coverage']['matched'], [CODES[0]])
        self.assertFalse(report['coverage_complete'])

    def test_v1_12_markdown_traceability_and_error_snapshot(self):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            output = Path(directory)/'report.json'
            cli = ['--mode', 'history', '--source', 'fixture', '--as-of-date', TARGET, '--output', str(output)]
            self.assertEqual(sensor.main(cli), 0)
            r = json.loads(output.read_text())
            md = output.with_suffix('.md').read_text()
            for text in [r['signals'][0]['signal_id'], DIGEST, '#/observations', '待验证推测', '人工下一步',
                         'NO_DATA', 'STALE_HISTORY', 'research_eligible=false', '合成数据']:
                self.assertIn(text, md)
            self.assertEqual(sensor.main(cli+['--as-of-date', '20990101']), 1)
            self.assertEqual(json.loads(output.read_text())['status'], 'ERROR')
            self.assertNotIn(r['signals'][0]['signal_id'], output.with_suffix('.md').read_text())

    def test_markdown_distinguishes_real_demo_data_from_synthetic(self):
        report = sensor.run(argparse.Namespace(source='fixture', trade_date='', ts_code='', demo_abs_pct='5'))
        report.update(source='tushare')
        text = sensor.render_markdown(report)
        self.assertIn('真实数据、单日演示规则', text)
        self.assertNotIn('合成数据不是真实行情', text)

    def test_v1_07_write_failure_cleans_both_snapshots(self):
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            output = Path(directory)/'report.json'
            output.write_text('old success')
            output.with_suffix('.md').write_text('old success')
            real_write = Path.write_text
            def fail_markdown(path, *a, **kw):
                if path.suffix == '.md':
                    raise OSError('synthetic private diagnostic')
                return real_write(path, *a, **kw)
            with patch.object(Path, 'write_text', fail_markdown):
                self.assertEqual(sensor.main(['--demo-abs-pct', '5', '--output', str(output)]), 1)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix('.md').exists())


class HistoricalTransportTests(unittest.TestCase):
    @patch.dict(os.environ, {'TUSHARE_TOKEN': 'SYNTHETIC_ONLY'}, clear=True)
    def test_history_request_and_response_contract(self):
        row = matching()[0]
        response = {'code': 0, 'data': {'fields': list(reversed(sensor.FIELDS)),
                    'items': [[row[f] for f in reversed(sensor.FIELDS)]]}}
        with patch.object(sensor, 'urlopen', return_value=io.StringIO(json.dumps(response))) as connect:
            result = history.DailyClient(CONFIG).fetch('20250414', TARGET, CODES[0])
        request = connect.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.tushare.pro')
        self.assertEqual(connect.call_args.kwargs['timeout'], 30)
        payload = json.loads(request.data)
        self.assertEqual(payload['params'], {'start_date': '20250414', 'end_date': TARGET, 'ts_code': CODES[0]})
        self.assertEqual(payload['fields'], ','.join(sensor.FIELDS))
        self.assertEqual(result, [row])

    def test_retry_backoff_pacing_and_no_api_error_retry(self):
        clock, sleeps = [0.0], []
        def sleep(seconds):
            sleeps.append(seconds)
            clock[0] += seconds
        with patch.object(history.time, 'monotonic', side_effect=lambda: clock[0]), \
                patch.object(history.time, 'sleep', side_effect=sleep), \
                patch.object(sensor, 'request_daily', side_effect=[sensor.TemporaryFetchError('safe'),
                    sensor.TemporaryFetchError('safe'), [], []]) as fetch:
            client = history.DailyClient(CONFIG)
            client.fetch('20250414', TARGET, CODES[0])
            client.fetch('20250414', TARGET, CODES[1])
        self.assertEqual(fetch.call_count, 4)
        self.assertEqual(sleeps, [2, 5, 2])
        with patch.object(sensor, 'request_daily', side_effect=sensor.SensorError('safe API rejection')) as fetch:
            with self.assertRaises(sensor.SensorError):
                history.DailyClient(CONFIG).fetch('20250414', TARGET, CODES[0])
        self.assertEqual(fetch.call_count, 1)
        with patch.object(history.time, 'sleep'), patch.object(sensor, 'request_daily', side_effect=sensor.TemporaryFetchError('safe')) as fetch:
            with self.assertRaises(sensor.TemporaryFetchError):
                history.DailyClient(CONFIG).fetch('20250414', TARGET, CODES[0])
        self.assertEqual(fetch.call_count, 3)

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_secret_never_connects_or_falls_back(self):
        with patch.object(sensor, 'urlopen') as fetch, patch.object(history.time, 'sleep'):
            report = history.run_history(args(source='tushare'))
        fetch.assert_not_called()
        self.assertEqual(report['status'], 'ERROR')
        self.assertEqual(report['signals'], [])
        self.assertEqual(report['coverage']['failed'], sorted(CODES))
        self.assertTrue(report['demo_only'])

    @patch.dict(os.environ, {'TUSHARE_TOKEN': 'SYNTHETIC_ONLY'}, clear=True)
    def test_network_failure_sanitized_and_http_retry_classified(self):
        for exc, retryable in [(URLError('SYNTHETIC_ONLY'), True),
                               (HTTPError(sensor.ENDPOINT, 503, 'SYNTHETIC_ONLY', {}, None), True),
                               (HTTPError(sensor.ENDPOINT, 403, 'SYNTHETIC_ONLY', {}, None), False)]:
            with self.subTest(retryable=retryable), patch.object(sensor, 'urlopen', side_effect=exc):
                expected = sensor.TemporaryFetchError if retryable else sensor.SensorError
                with self.assertRaises(expected) as raised:
                    sensor.request_daily({})
                self.assertNotIn('SYNTHETIC_ONLY', str(raised.exception))

    def test_config_validation_and_history_argument_separation(self):
        for key, value in [('max_signals', 6), ('min_history', 258), ('percentile_min', float('nan')),
                           ('return_window', True), ('request_interval_seconds', 1),
                           ('retry_delays_seconds', [1, 1]), ('universe', ['bad']),
                           ('universe', [f'{i:06d}.SZ' for i in range(1, 22)])]:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'config.json'
                path.write_text(json.dumps({**CONFIG, key: value}))
                with self.assertRaises(sensor.SensorError):
                    history.load_config(path)
        for option in ['demo_abs_pct', 'trade_date', 'ts_code']:
            report = history.run_history(args(**{option: '5'}))
            self.assertEqual(report['status'], 'ERROR')


class ActionsEntryTests(unittest.TestCase):
    def test_v1_09_schedule_ignores_dispatch_inputs(self):
        options = actions_entry.arguments('schedule', {'INPUT_MODE': 'demo', 'INPUT_SOURCE': 'fixture', 'INPUT_AS_OF_DATE': '19000101'})
        self.assertEqual(options, ['--mode', 'flow', '--input-mode', 'live_http'])
        with patch.object(history, 'taipei_today', return_value='20261020'), \
                patch.object(history.DailyClient, 'fetch', return_value=[]) as fetch:
            report = history.run_history(args(source='tushare', as_of_date=''))
        self.assertEqual(report['as_of_date'], '20261020')
        self.assertEqual(fetch.call_args.args[:2], ('20250418', '20261020'))

    def test_v1_09_manual_demo_and_replay(self):
        self.assertEqual(actions_entry.arguments('workflow_dispatch', {}),
                         ['--mode', 'flow', '--source', 'fixture', '--input-mode', 'live_http', '--as-of', ''])
        self.assertEqual(actions_entry.arguments('workflow_dispatch', {'INPUT_MODE': 'history', 'INPUT_SOURCE': 'tushare', 'INPUT_AS_OF_DATE': TARGET}),
                         ['--mode', 'history', '--source', 'tushare', '--as-of-date', TARGET])
        with self.assertRaises(sensor.SensorError):
            actions_entry.arguments('push', {})

    def test_v1_09_workflow_copies_schedule_permissions_and_artifact(self):
        active = (ROOT/'.github/workflows/market-sensor.yml').read_text()
        self.assertEqual(active, (ROOT/'tasks/github-actions/market-sensor.yml').read_text())
        for fragment in ["cron: '17 8 * * 5'", 'timezone: Asia/Taipei', 'contents: read', 'actions: read',
                         'timeout-minutes: 15', 'if: ${{ always() }}', 'path: outputs/market/',
                         'if-no-files-found: error', 'retention-days: 14',
                         'TUSHARE_TOKEN: ${{ secrets.TUSHARE_TOKEN }}']:
            self.assertIn(fragment, active)
        self.assertEqual(active.count('permissions:'), 1)
        self.assertNotIn('contents: write', active)


if __name__ == '__main__':
    unittest.main()
