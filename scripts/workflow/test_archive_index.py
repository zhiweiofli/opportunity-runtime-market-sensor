import unittest

from build_archive_index import extract


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


if __name__ == '__main__':
    unittest.main()
