from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from build_brief import (
    JUDGE_STALE_HOURS,
    RESEARCH_STALE_HOURS,
    SIGNAL_STALE_HOURS,
    build,
    compute_health,
    extract_source_signal_ids,
    find_possible_repeats,
    parse_judge,
    slug_tokens,
)


def _write_mirror_file(root, rel_path, content, entry_id, title, folder_path, modified_at, mime='text/plain'):
    target = root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')
    return {
        'id': entry_id,
        'title': title,
        'folder_path': folder_path,
        'mime_type': 'application/vnd.google-apps.document',
        'export_mime_type': mime,
        'modified_at': modified_at,
        'path': rel_path,
        'source_status': 'present',
    }


def _write_manifest(root, entries):
    manifest = {
        'schema_version': 'drive-mirror@1',
        'root_id': 'root-test',
        'folders': [],
        'entries': entries,
    }
    manifest_path = root / 'drive-mirror/manifest.json'
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')


class BuildBriefTest(unittest.TestCase):
    def test_missing_manifest_returns_null_judge_and_unknown_health(self):
        now = datetime(2026, 11, 26, 12, 0, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as d:
            result = build(Path(d), now=now)
        self.assertEqual(result['schema_version'], 'or-brief@1')
        self.assertEqual(result['generated_at'], now.isoformat())
        self.assertIsNone(result['judge'])
        self.assertEqual(result['new_research'], [])
        self.assertEqual(result['counts'], {'total': 0, 'ready': 0, 'kill': 0, 'unknown': 0})
        self.assertEqual(len(result['health']), 6)
        self.assertTrue(all(item['status'] == 'unknown' for item in result['health']))

    def test_parse_judge_2026_11_15_table_format(self):
        text = (
            'Opportunity Runtime — Judge | 2026-11-15 19:01 Asia/Taipei\n\n'
            'A. 本轮结论\n'
            '本轮不启动新产品。\n'
            '保持观察。\n\n'
            'B. 本轮决策看板\n'
            '优先级 | 机会 | 变化与受影响者 | 钱与轻捕获 | 最大未知 | 结论\n'
            '1 | QuickBooks Desktop 归档 | 停售迁移 | 先做核对 | 记账师付费 | NEXT\n'
            '2 | Dynamics GP 归档 | ERP 迁云 | 迁前审计 | 顾问采购 | NEXT\n'
            '3 | Stripe 权限漏开 | 异步不同步 | Cron 已覆盖 | 差异化 | DROP（重复历史 KILL）\n'
            '4 | Windows 11 扫描失败 | SMB 安全升级 | 只读诊断 | 能否复现 | WATCH\n'
            '5 | Cloudflare AI Search | 按量计费 | 成本分析 | 账单规模 | WATCH（本周人类暂缓）\n\n'
            'G. Human Decision Needed\n'
            '1. 是否同意本周 NOW 留空？\n'
            '2. 上周验证是否可确认？\n'
            '3. 是否先找迁出记账师？\n\n'
            'H. 审计\n'
            'Generated At: 2026-11-15T19:01:46+08:00\n'
        )
        parsed = parse_judge(text, '2026-11-15-1901-judge')
        self.assertTrue(parsed['parse_ok'])
        self.assertEqual(parsed['generated_at'], '2026-11-15T19:01:46+08:00')
        self.assertEqual(parsed['conclusion'], '本轮不启动新产品。 保持观察。')
        self.assertEqual(len(parsed['items']), 5)
        self.assertEqual([(i['rank'], i['verdict']) for i in parsed['items']], [
            (1, 'NEXT'), (2, 'NEXT'), (3, 'DROP'), (4, 'WATCH'), (5, 'WATCH'),
        ])
        self.assertEqual(parsed['items'][2]['verdict_note'], 'DROP（重复历史 KILL）')
        self.assertEqual(parsed['items'][0]['cells'], ['停售迁移', '先做核对', '记账师付费'])
        self.assertEqual(parsed['items'][0]['details'], [])
        self.assertEqual(len(parsed['decisions']), 3)

    def test_parse_judge_2026_11_08_multiline_and_detail_cap(self):
        extra_lines = '\n'.join(f'补充行 {idx}：详情   内容' for idx in range(1, 11))
        text = (
            'Opportunity Runtime — Weekly Judge | 2026-11-08 18:57 Asia/Taipei\n\n'
            'A. 本周结论\n' + ('结论文本' * 200) + '\n\n'
            'B. 本周决策看板（决策者视角）\n'
            '1 | Cloudflare AI Search 成本审计 | NOW（延续建议，尚未确认执行）\n'
            + extra_lines + '\n'
            '2 | 老版本 AWS MySQL 扩展支持费 | NEXT\n'
            '变化：进入附加费阶段\n\n'
            'G. Human Decision Needed\n'
            '1. 是否继续 Cloudflare 槽位？\n'
            'Generated At: 2026-11-08T18:57:00+08:00\n'
        )
        parsed = parse_judge(text, '2026-11-08-1857-judge')
        self.assertTrue(parsed['parse_ok'])
        self.assertTrue(parsed['conclusion'].endswith('…'))
        self.assertEqual(len(parsed['conclusion']), 601)
        self.assertEqual(len(parsed['items']), 2)
        first = parsed['items'][0]
        self.assertEqual(first['rank'], 1)
        self.assertEqual(first['verdict'], 'NOW')
        self.assertEqual(first['verdict_note'], 'NOW（延续建议，尚未确认执行）')
        self.assertEqual(first['cells'], [])
        self.assertEqual(len(first['details']), 8)
        self.assertEqual(first['details'][0], '补充行 1：详情 内容')

    def test_parse_judge_missing_sections_sets_parse_ok_false(self):
        parsed = parse_judge('仅有一行无结构的文本\nGenerated At: 2026-11-10T00:00:00Z\n', 'bad-judge')
        self.assertFalse(parsed['parse_ok'])
        self.assertEqual(parsed['conclusion'], '')
        self.assertEqual(parsed['items'], [])
        self.assertEqual(parsed['generated_at'], '2026-11-10T00:00:00Z')

    def test_no_judge_returns_all_non_receipt_research_and_sorts(self):
        now = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            entries = [
                _write_mirror_file(
                    root, 'drive-mirror/files/Research/r1.txt',
                    'Opportunity Hypothesis: Kill Old\nFinal Status: KILL\n',
                    'id1', 'Research-Friction-20261119-alpha.md', ['Research'], '2026-11-19T10:00:00Z',
                ),
                _write_mirror_file(
                    root, 'drive-mirror/files/Research/r2.txt',
                    'Opportunity Hypothesis: Unknown New\n',
                    'id2', 'Research-UW-20261119-beta.md', ['Research'], '2026-11-19T11:00:00Z',
                ),
                _write_mirror_file(
                    root, 'drive-mirror/files/Research/r3.txt',
                    'Opportunity Hypothesis: Ready Early\nFinal Status: HYPOTHESIS_READY\n',
                    'id3', 'Research-IBF-20261118-gamma.md', ['Research'], '2026-11-18T10:00:00Z',
                ),
                _write_mirror_file(
                    root, 'drive-mirror/files/Research/r4.txt',
                    'Opportunity Hypothesis: Ready Late\nFinal Status: HYPOTHESIS_READY\n* Source Signal IDs: Sig-1, Sig-2\n',
                    'id4', 'Research-Business-20261120-delta.md', ['Research'], '2026-11-20T10:00:00Z',
                ),
                _write_mirror_file(
                    root, 'drive-mirror/files/Research/receipt.txt',
                    'Execution Receipt\nFinal Status: HYPOTHESIS_READY\n',
                    'id5', 'Execution-Receipt-20261120.md', ['Research'], '2026-11-20T11:00:00Z',
                ),
            ]
            _write_manifest(root, entries)
            result = build(root, now=now)

        self.assertIsNone(result['judge'])
        self.assertEqual(result['counts'], {'total': 4, 'ready': 2, 'kill': 1, 'unknown': 1})
        self.assertEqual(
            [(r['title'], r['status']) for r in result['new_research']],
            [
                ('Ready Late', 'HYPOTHESIS_READY'),
                ('Ready Early', 'HYPOTHESIS_READY'),
                ('Unknown New', None),
                ('Kill Old', 'KILL'),
            ],
        )
        self.assertEqual(result['new_research'][0]['source_signal_ids'], ['Sig-1', 'Sig-2'])
        research_health = next(h for h in result['health'] if h['id'] == 'research')
        # Receipt at 11:00Z must be ignored; latest real research is 10:00Z (2.0h old).
        self.assertEqual(research_health['age_hours'], 2.0)

    def test_new_research_strictly_after_judge_modified(self):
        now = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            entries = [
                _write_mirror_file(
                    root, 'drive-mirror/files/Judge/j1.txt',
                    'Opportunity Runtime — Judge | 2026-11-15\nA. 本轮结论\n正常。\n',
                    'j1', '2026-11-15-judge', ['Judge'], '2026-11-15T11:00:00Z',
                ),
                _write_mirror_file(
                    root, 'drive-mirror/files/Research/eq.txt',
                    'Opportunity Hypothesis: Equal Ts\nFinal Status: HYPOTHESIS_READY\n',
                    'r_eq', 'Research-IBF-20261115-equal.md', ['Research'], '2026-11-15T11:00:00Z',
                ),
                _write_mirror_file(
                    root, 'drive-mirror/files/Research/after.txt',
                    'Opportunity Hypothesis: After Judge\nFinal Status: HYPOTHESIS_READY\n',
                    'r_after', 'Research-IBF-20261116-after.md', ['Research'], '2026-11-16T11:00:00Z',
                ),
            ]
            _write_manifest(root, entries)
            result = build(root, now=now)

        self.assertEqual([r['title'] for r in result['new_research']], ['After Judge'])
        self.assertEqual(result['counts'], {'total': 1, 'ready': 1, 'kill': 0, 'unknown': 0})

    def test_health_ok_warn_unknown_boundaries_and_business_no_signal(self):
        now = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)
        entries_ok = [
            {'folder_path': ['Judge'], 'title': 'j1', 'path': 'drive-mirror/files/j',
             'modified_at': (now - timedelta(hours=JUDGE_STALE_HOURS)).isoformat()},
            {'folder_path': ['Signals', 'Business'], 'title': 'Business-20261120-NO-SIGNAL.md', 'path': 'drive-mirror/files/b1',
             'modified_at': (now - timedelta(hours=SIGNAL_STALE_HOURS)).isoformat()},
            {'folder_path': ['Signals', 'Business'], 'title': 'Business-20261118-real-signal.md', 'path': 'drive-mirror/files/b2',
             'modified_at': (now - timedelta(days=2)).isoformat()},
            {'folder_path': ['Signals', 'Business'], 'title': 'Business-20261101-no-signal.md', 'path': 'drive-mirror/files/b3',
             'modified_at': (now - timedelta(days=10)).isoformat()},
            {'folder_path': ['Signals', 'Friction'], 'title': 'Friction-20261120.md', 'path': 'drive-mirror/files/f1',
             'modified_at': (now - timedelta(hours=10)).isoformat()},
            {'folder_path': ['Signals'], 'title': 'IBF-20261120-test.md', 'path': 'drive-mirror/files/i1',
             'modified_at': (now - timedelta(hours=10)).isoformat()},
            {'folder_path': ['Signals'], 'title': 'UW-20261120-test.md', 'path': 'drive-mirror/files/u1',
             'modified_at': (now - timedelta(hours=10)).isoformat()},
            {'folder_path': ['Research'], 'title': 'Research-UW-20261120-test.md', 'path': 'drive-mirror/files/r1',
             'modified_at': (now - timedelta(hours=RESEARCH_STALE_HOURS)).isoformat()},
        ]
        health_ok = {h['id']: h for h in compute_health(entries_ok, now)}
        self.assertEqual(health_ok['judge']['status'], 'ok')
        self.assertEqual(health_ok['signals_business']['status'], 'ok')
        self.assertIn('近 7 天 no-signal 1/2', health_ok['signals_business']['detail'])
        self.assertEqual(health_ok['research']['status'], 'ok')

        entries_warn = [
            {'folder_path': ['Judge'], 'title': 'j1', 'path': 'drive-mirror/files/j',
             'modified_at': (now - timedelta(hours=JUDGE_STALE_HOURS + 0.2)).isoformat()},
            {'folder_path': ['Signals', 'Friction'], 'title': 'Friction-old.md', 'path': 'drive-mirror/files/f1',
             'modified_at': (now - timedelta(hours=SIGNAL_STALE_HOURS + 0.2)).isoformat()},
            {'folder_path': ['Research'], 'title': 'Research-IBF-old.md', 'path': 'drive-mirror/files/r1',
             'modified_at': (now - timedelta(hours=RESEARCH_STALE_HOURS + 0.2)).isoformat()},
        ]
        health_warn = {h['id']: h for h in compute_health(entries_warn, now)}
        self.assertEqual(health_warn['judge']['status'], 'warn')
        self.assertEqual(health_warn['signals_friction']['status'], 'warn')
        self.assertEqual(health_warn['research']['status'], 'warn')
        self.assertEqual(health_warn['signals_business']['status'], 'unknown')
        self.assertEqual(health_warn['signals_ibf']['status'], 'unknown')
        self.assertEqual(health_warn['signals_uw']['status'], 'unknown')

    def test_duplicate_detection_positive_and_negative_cases(self):
        kill_records = [
            {
                'filename': 'Research-Friction-2026-11-09-Stripe-Fulfillment-Webhook-Mismatch.md',
                'title': 'Stripe Fulfillment Webhook Mismatch',
                'path': 'drive-mirror/files/Research/stripe-kill.txt',
                'modified': '2026-11-09T09:24:41.125Z',
                'source_signal_ids': ['Friction-2026-11-09-Stripe-Fulfillment-Webhook-Mismatch'],
                'status': 'KILL',
            },
            {
                'filename': 'Research-UW-20261101-SmallBusiness-ManualAuditFailure.md',
                'title': 'Small Business Manual Audit Failure',
                'path': 'drive-mirror/files/Research/sb-kill.txt',
                'modified': '2026-11-01T10:00:00Z',
                'source_signal_ids': ['UW-20261101-SmallBusiness-ManualAuditFailure'],
                'status': 'KILL',
            },
            {
                'filename': 'Research-IBF-20261102-Shopify-LegacyMigrationRecovery.md',
                'title': 'Shopify Legacy Migration Recovery',
                'path': 'drive-mirror/files/Research/shopify-kill.txt',
                'modified': '2026-11-02T10:00:00Z',
                'source_signal_ids': ['IBF-20261102-Shopify-LegacyMigrationRecovery'],
                'status': 'KILL',
            },
        ]

        # Positive 1: Stripe webhook provisioning leak matches Stripe fulfillment webhook mismatch
        stripe_cand = {
            'filename': 'Research-Friction-2026-11-15-stripe-webhook-provisioning-leak.md',
            'title': 'Stripe Webhook Provisioning Leak',
            'modified': '2026-11-15T09:24:35.280Z',
            'source_signal_ids': ['Friction-2026-11-15-stripe-webhook-provisioning-leak'],
            'status': 'HYPOTHESIS_READY',
        }
        stripe_hits = find_possible_repeats(stripe_cand, kill_records)
        self.assertEqual(len(stripe_hits), 1)
        self.assertEqual(stripe_hits[0]['rule'], 'slug_tokens')
        self.assertEqual(stripe_hits[0]['path'], 'drive-mirror/files/Research/stripe-kill.txt')

        # Positive 2: Source Signal ID overlap
        ssid_cand = {
            'filename': 'Research-Friction-2026-11-18-CompletelyDifferentName.md',
            'title': 'Completely Different Name',
            'modified': '2026-11-18T10:00:00Z',
            'source_signal_ids': ['UW-20261101-SmallBusiness-ManualAuditFailure'],
            'status': 'HYPOTHESIS_READY',
        }
        ssid_hits = find_possible_repeats(ssid_cand, kill_records)
        self.assertEqual(len(ssid_hits), 1)
        self.assertEqual(ssid_hits[0]['rule'], 'source_signal_id')

        # Negative 1: unrelated SmallBusiness audit topics must not match via stopwords
        neg1 = {
            'filename': 'Research-UW-20261125-SmallBusiness-UtilityBillTariffAudit.md',
            'title': 'Utility Bill Tariff Audit',
            'modified': '2026-11-25T09:56:41Z',
            'source_signal_ids': ['UW-20261125-SmallBusiness-UtilityBillTariffAudit'],
            'status': 'HYPOTHESIS_READY',
        }
        self.assertEqual(find_possible_repeats(neg1, kill_records), [])

        # Negative 2: unrelated migration topics must not match via stopwords
        neg2 = {
            'filename': 'Research-IBF-20261124-VMware-BroadcomSubscriptionShock-ProxmoxMigrationAudit.md',
            'title': 'VMware Proxmox Migration Audit',
            'modified': '2026-11-25T09:54:39Z',
            'source_signal_ids': ['IBF-20261124-VMware-Proxmox'],
            'status': 'HYPOTHESIS_READY',
        }
        self.assertEqual(find_possible_repeats(neg2, kill_records), [])

        # Negative 3: single shared token with low Jaccard must not match
        neg3 = {
            'filename': 'Research-Friction-2026-11-20-Stripe-Invoice-Export.md',
            'title': 'Stripe Invoice Export',
            'modified': '2026-11-20T09:00:00Z',
            'source_signal_ids': ['Friction-2026-11-20-Stripe-Invoice-Export'],
            'status': 'HYPOTHESIS_READY',
        }
        self.assertEqual(find_possible_repeats(neg3, kill_records), [])

        # Negative 4: candidate itself is KILL or KILL is newer than candidate
        self.assertEqual(find_possible_repeats({**stripe_cand, 'status': 'KILL'}, kill_records), [])
        self.assertEqual(find_possible_repeats({**stripe_cand, 'modified': '2026-11-08T00:00:00Z'}, kill_records), [])
        self.assertEqual(extract_source_signal_ids('No signal IDs here'), [])
        self.assertEqual(slug_tokens('Research-UW-20261125-SmallBusiness-UtilityBillTariffAudit.md'), {'utility', 'bill', 'tariff'})


class ReviewRegressionTest(unittest.TestCase):
    def test_outer_pipes_are_optional(self):
        import build_brief as bb
        text = 'B. 本轮决策看板\n| 1 | 产品甲 | 变化 | NOW |\n2 | 产品乙 | NEXT |\nC. 重点机会\n'
        items = bb.parse_judge(text, 'x')['items']
        self.assertEqual([(i['rank'], i['title'], i['verdict']) for i in items], [(1, '产品甲', 'NOW'), (2, '产品乙', 'NEXT')])

    def test_decision_continuation_lines_kept_and_g_alone_is_parse_ok(self):
        import build_brief as bb
        text = 'G. Human Decision Needed\n1. 是否同意执行？\n预算上限 100 元；仅允许只读验证\n2. 是否暂缓？\nH. 审计\n'
        parsed = bb.parse_judge(text, 'x')
        self.assertEqual(parsed['decisions'], ['1. 是否同意执行？ 预算上限 100 元；仅允许只读验证', '2. 是否暂缓？'])
        self.assertTrue(parsed['parse_ok'])

    def test_health_threshold_uses_unrounded_age(self):
        import build_brief as bb
        now = datetime(2026, 11, 26, tzinfo=timezone.utc)
        last = now - timedelta(hours=bb.JUDGE_STALE_HOURS, seconds=60)
        entries = [{'folder_path': ['Judge'], 'title': 'j', 'modified_at': last.isoformat().replace('+00:00', 'Z'), 'path': 'drive-mirror/files/j'}]
        judge = [h for h in bb.compute_health(entries, now) if h['id'] == 'judge'][0]
        self.assertEqual(judge['status'], 'warn')


def _judge_text(rows):
    lines = ['Opportunity Runtime — Judge | test', 'B. 本轮决策看板'] + rows + ['C. 其他']
    return '\n'.join(lines) + '\n'


class TrendsAndCoverageTest(unittest.TestCase):
    def _build(self, now):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            entries = [
                # Judges written out of order to check judge_history sorting.
                _write_mirror_file(
                    root, 'drive-mirror/files/Judge/j2.txt',
                    _judge_text(['1 | 甲 | NOW', '2 | 乙 | WATCH']),
                    'j2', '2026-11-20-judge', ['Judge'], '2026-11-20T10:00:00Z',
                ),
                _write_mirror_file(
                    root, 'drive-mirror/files/Judge/j1.txt', '无法解析的旧格式\n',
                    'j1', '2026-11-10-judge', ['Judge'], '2026-11-10T10:00:00Z',
                ),
                # Sunday 2026-11-08 23:59Z belongs to week 2026-11-02.
                _write_mirror_file(
                    root, 'drive-mirror/files/Research/k1.txt',
                    'Opportunity Hypothesis: Stripe Kill\nFinal Status: KILL\n',
                    'k1', 'Research-Friction-20261108-Stripe-Webhook-Fulfillment.md', ['Research'], '2026-11-08T23:59:00Z',
                ),
                # Exactly j1 - 7d: on the open lower bound of j1's window, so it is a coverage gap.
                _write_mirror_file(
                    root, 'drive-mirror/files/Research/r1.txt',
                    'Opportunity Hypothesis: Stripe Again\nFinal Status: HYPOTHESIS_READY\n',
                    'r1', 'Research-Friction-20261109-Stripe-Webhook-Retry.md', ['Research'], '2026-11-03T10:00:00Z',
                ),
                # Exactly at j1 time: inside (j1-7d, j1].
                _write_mirror_file(
                    root, 'drive-mirror/files/Research/r2.txt',
                    'Opportunity Hypothesis: At Judge\nFinal Status: HYPOTHESIS_READY\n',
                    'r2', 'Research-IBF-20261110-at-judge.md', ['Research'], '2026-11-10T10:00:00Z',
                ),
                # Inside j2 window.
                _write_mirror_file(
                    root, 'drive-mirror/files/Research/r3.txt',
                    'Opportunity Hypothesis: In Window\n',
                    'r3', 'Other-20261115.md', ['Research'], '2026-11-15T10:00:00Z',
                ),
                # After latest Judge: not a gap.
                _write_mirror_file(
                    root, 'drive-mirror/files/Research/r4.txt',
                    'Opportunity Hypothesis: After Latest\nFinal Status: HYPOTHESIS_READY\n',
                    'r4', 'Research-UW-20261121-after.md', ['Research'], '2026-11-21T10:00:00Z',
                ),
                _write_mirror_file(
                    root, 'drive-mirror/files/Research/rcpt.txt', 'receipt\n',
                    'rc', 'Execution-Receipt-20261112.md', ['Research'], '2026-11-12T10:00:00Z',
                ),
                # Monday 2026-11-09 00:00Z starts week 2026-11-09.
                _write_mirror_file(
                    root, 'drive-mirror/files/Signals/b1.txt', 'x\n',
                    's1', 'Business-20261109-no-signal.md', ['Signals', 'Business'], '2026-11-09T00:00:00Z',
                ),
                _write_mirror_file(
                    root, 'drive-mirror/files/Signals/b2.txt', 'x\n',
                    's2', 'Business-20261111-No Signal.md', ['Signals', 'Business'], '2026-11-11T00:00:00Z',
                ),
                _write_mirror_file(
                    root, 'drive-mirror/files/Signals/b3.txt', 'x\n',
                    's3', 'IBF-20261112-real.md', ['Signals'], '2026-11-12T00:00:00Z',
                ),
            ]
            _write_manifest(root, entries)
            return build(root, now=now)

    def test_weeks_monday_start_and_counts(self):
        result = self._build(datetime(2026, 11, 26, 12, 0, tzinfo=timezone.utc))
        weeks = result['trends']['weeks']
        self.assertEqual([w['week_start'] for w in weeks], ['2026-11-02', '2026-11-09', '2026-11-16', '2026-11-23'])
        w1, w2, w3, w4 = weeks
        self.assertEqual((w1['research_ready'], w1['research_kill'], w1['research_other']), (1, 1, 0))
        self.assertEqual(w1['by_source']['Friction'], 2)
        self.assertEqual((w2['research_ready'], w2['research_other']), (1, 1))
        self.assertEqual(w2['by_source'], {'Business': 0, 'Friction': 0, 'IBF': 1, 'UW': 0, 'unknown': 1})
        self.assertEqual((w2['signals_total'], w2['signals_no_signal'], w2['judge_runs']), (3, 2, 1))
        self.assertEqual((w3['research_ready'], w3['by_source']['UW'], w3['judge_runs']), (1, 1, 1))
        self.assertEqual((w4['research_ready'], w4['signals_total'], w4['judge_runs']), (0, 0, 0))

    def test_judge_history_sorted_with_parse_ok(self):
        result = self._build(datetime(2026, 11, 26, tzinfo=timezone.utc))
        history = result['judge_history']
        self.assertEqual([(h['date'], h['parse_ok']) for h in history], [('2026-11-10', False), ('2026-11-20', True)])
        self.assertEqual(history[0]['items'], [])
        self.assertEqual(history[1]['items'], [
            {'rank': 1, 'title': '甲', 'verdict': 'NOW'},
            {'rank': 2, 'title': '乙', 'verdict': 'WATCH'},
        ])

    def test_source_yield_counts_possible_repeat(self):
        result = self._build(datetime(2026, 11, 26, tzinfo=timezone.utc))
        rows = {r['source']: r for r in result['source_yield']}
        self.assertEqual(list(rows), ['Friction', 'IBF', 'UW', 'unknown'])
        self.assertEqual(rows['Friction'], {'source': 'Friction', 'total': 2, 'ready': 1, 'kill': 1, 'possible_repeat': 0})
        self.assertEqual(rows['IBF']['possible_repeat'], 0)

    def test_source_yield_possible_repeat_requires_earlier_kill(self):
        import build_brief as bb
        kill = {'filename': 'Research-Friction-20261101-Stripe-Webhook-Fulfillment.md', 'title': 'K', 'path': 'p/k',
                'modified': '2026-11-01T00:00:00Z', 'source_signal_ids': [], 'status': 'KILL', 'tags': ['Friction']}
        later = {'filename': 'Research-Friction-20261105-Stripe-Webhook-Retry.md', 'title': 'L', 'path': 'p/l',
                 'modified': '2026-11-05T00:00:00Z', 'source_signal_ids': [], 'status': 'HYPOTHESIS_READY', 'tags': ['Friction']}
        earlier = {**later, 'path': 'p/e', 'modified': '2026-10-30T00:00:00Z'}
        rows = bb.compute_source_yield([kill, later, earlier], [kill])
        self.assertEqual(rows, [{'source': 'Friction', 'total': 3, 'ready': 2, 'kill': 1, 'possible_repeat': 1}])

    def test_coverage_gaps_window_boundaries(self):
        result = self._build(datetime(2026, 11, 26, tzinfo=timezone.utc))
        # k1 (11-08 23:59) is inside j1 window; r1 (11-03 10:00) is exactly j1-7d, so excluded;
        # r2 exactly at j1 is covered; r3 inside j2; r4 after latest Judge.
        self.assertEqual([g['path'] for g in result['coverage_gaps']], ['drive-mirror/files/Research/r1.txt'])
        gap = result['coverage_gaps'][0]
        self.assertEqual(set(gap), {'title', 'path', 'modified', 'status', 'tags'})
        self.assertEqual(gap['tags'], ['Friction'])
        coverage = next(h for h in result['health'] if h['id'] == 'judge_coverage')
        self.assertEqual(coverage, {
            'id': 'judge_coverage', 'label': 'Judge 覆盖', 'status': 'warn',
            'last_at': None, 'age_hours': None, 'threshold_hours': None,
            'detail': '1 份 Research 未进入任何 Judge 回看窗口',
        })

    def test_judge_coverage_ok_without_gaps(self):
        import build_brief as bb
        jt = datetime(2026, 11, 20, tzinfo=timezone.utc)
        rec = {'title': 't', 'path': 'p', 'modified': (jt - timedelta(days=7) + timedelta(seconds=1)).isoformat(),
               'status': None, 'tags': []}
        self.assertEqual(bb.JUDGE_LOOKBACK_DAYS, 7)
        gaps = bb.compute_coverage_gaps([rec], [jt])
        self.assertEqual(gaps, [])
        self.assertEqual(bb.coverage_health(gaps)['status'], 'ok')
        self.assertEqual(bb.compute_coverage_gaps([rec], []), [])


if __name__ == '__main__':
    unittest.main()
