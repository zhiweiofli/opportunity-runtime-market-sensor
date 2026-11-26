import json
import tempfile
import unittest
from pathlib import Path

from build_archive_index import build, card, extract, judge_title


class ArchiveIndexTest(unittest.TestCase):
    def test_research_title_and_known_are_extracted_from_original(self):
        text = '<!-- hidden metadata -->\nKnown\n实际业务问题与成本。\nOpportunity Hypothesis\n面向客户的验证工具\n'
        title, summary = extract(text, 'fallback.md', 'research')
        self.assertEqual(title, '面向客户的验证工具')
        self.assertEqual(summary, '实际业务问题与成本。')

    def test_english_research_section_is_searchable(self):
        text = 'Primary Domain\nSmall Business Lending\n1. Problem & Friction Analysis\nSmall businesses face long delays when old liens are not released.\n'
        title, summary = extract(text, 'fallback.md', 'research')
        self.assertEqual(title, 'Small Business Lending')
        self.assertIn('old liens', summary)

    def test_judge_summary_uses_conclusion(self):
        text = 'Opportunity Runtime — Weekly Judge | 2026-11-08\nA. 本周结论\n本周不建议启动新项目。\n'
        title, summary = extract(text, 'fallback.md', 'judge')
        self.assertIn('Weekly Judge', title)
        self.assertEqual(summary, '本周不建议启动新项目。')

    def test_source_tags_and_final_status_from_varied_formats(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'or-archive/research').mkdir(parents=True)
            entries = []
            for index, status in enumerate(('- **Final Status**: KILL', 'Stage & Final Status\nHYPOTHESIS_READY')):
                path = 'or-archive/research/%d.md' % index
                (root / path).write_text(status, encoding='utf-8')
                entries.append({'path': path, 'title': 'Research-IBF-test.md', 'sync_status': 'mirrored'})
            (root / 'or-archive/manifest.json').write_text(json.dumps({'entries': entries}), encoding='utf-8')
            result = build(root)['entries']
            self.assertEqual([x['status'] for x in result], ['KILL', 'HYPOTHESIS_READY'])
            self.assertEqual([x['tags'] for x in result], [['IBF'], ['IBF']])


class ReceiptSummaryTest(unittest.TestCase):
    def test_receipt_summary_reports_batch_not_research_text(self):
        text = ('Execution Receipt: Researcher Batch 20261125\n* Batch Processing Status: COMPLETED\n* Queue Status: NO_PENDING_SIGNALS\n'
                '\tHYPOTHESIS_READY\n\t四 Gate 全数通过：这是一段研究结论，不应成为回执摘要，需要足够长才能被兜底规则选中的那种句子。\n'
                '\tResearch-IBF-20261124-A.md\n\tResearch-UW-20261125-B.md\n\tResearch-IBF-20261124-A.md\n')
        c = card(text, 'Execution-Receipt-20261125.md', 'x', 'receipt', None)
        self.assertEqual(c['summary'], 'Researcher 批次回执 · 批次 COMPLETED · 队列 NO_PENDING_SIGNALS · 本批产出研究 2 份')
        self.assertIsNone(c['status'])


class JudgeTitleTest(unittest.TestCase):
    def test_judge_titles_are_chinese_and_dated(self):
        self.assertEqual(judge_title('2026-11-26-1633-judge'), '2026-11-26 评审 16:33')
        self.assertEqual(judge_title('2026-10-22-judge'), '2026-10-22 评审')
        self.assertIsNone(judge_title('weekly-judge'))


if __name__ == '__main__':
    unittest.main()
