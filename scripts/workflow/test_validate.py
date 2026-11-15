import hashlib
import json
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from validate import DEMO, Validator

T = '2026-01-01T00:00:00Z'
NOW = datetime(2026, 2, 1, tzinfo=timezone.utc)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.write('or-archive/research/a.md', 'Synthetic research evidence')
        self.write_json('or-archive/manifest.json', {'entries': [{'path': 'or-archive/research/a.md', 'doc_id': 'synthetic', 'modified_at': T}]})
        self.git('add', '.')
        self.git('commit', '-qm', 'source')
        self.source = self.git('rev-parse', 'HEAD')
        ref = {'path': 'or-archive/research/a.md', 'commit': self.source}
        self.opp = {'schema_version': 1, 'opportunity_id': 'o1', 'title': 'Synthetic', 'business_problem': 'test', 'target_customer': 'test', 'value_hypothesis': 'test', 'economic_anchor': {'value': None, 'unit': 'month', 'currency': None, 'basis': 'unknown', 'evidence_ref': None}, 'gates': dict.fromkeys(['money', 'mechanism', 'persistence', 'capture'], 'unknown'), 'source_refs': [{'drive_doc_id': 'synthetic', 'source_updated_at': T, 'mirror_path': ref['path'], 'commit': self.source, 'missing_reason': None}], 'research_status': 'unknown', 'judge_recommendation': 'NEXT', 'critical_unknown': 'test', 'created_at': T, 'updated_at': T}
        self.task = {'schema_version': 1, 'task_id': 't1', 'opportunity_id': 'o1', 'question': 'test?', 'hypothesis': 'test', 'success_criteria': [{'id': 'c1', 'description': 'test'}], 'falsification_criteria': [{'id': 'c2', 'description': 'test'}], 'deliverables': ['report'], 'context_refs': [ref], 'budget': {'max_duration': 1, 'duration_unit': 'hours', 'max_cost': 0, 'currency': 'USD'}, 'allowed_actions': ['read'], 'stop_conditions': ['stop'], 'created_at': T}
        self.write_json('opportunities/o1/opportunity.json', self.opp)
        self.write_json('practice/inbox/t1/task.json', self.task)
        self.git('add', '.')
        self.git('commit', '-qm', 'task')
        self.base = self.git('rev-parse', 'HEAD')
        task_hash = hashlib.sha256((self.root / 'practice/inbox/t1/task.json').read_bytes()).hexdigest()
        self.result = {'schema_version': 1, 'task_id': 't1', 'opportunity_id': 'o1', 'run_id': 'r1', 'task_hash': task_hash, 'input_commit': self.base, 'started_at': T, 'finished_at': T, 'outcome': 'inconclusive', 'criteria_results': [{'criterion_id': 'c1', 'result': 'unknown'}, {'criterion_id': 'c2', 'result': 'unknown'}], 'evidence_refs': [{'source': 'synthetic', 'collected_at': T, 'summary': 'test evidence', 'ref': ref, 'sha256': hashlib.sha256(b'Synthetic research evidence').hexdigest()}], 'actual_cost': {'duration': None, 'duration_unit': 'hours', 'cost': None, 'currency': None}, 'remaining_unknown': ['test'], 'recommendation': 'more evidence'}
        self.write_json('practice/results/t1/r1/result.json', self.result)
        self.write('practice/results/t1/r1/report.md', 'Synthetic report')
        self.decision = {'schema_version': 1, 'decision_id': 'd1', 'opportunity_id': 'o1', 'action': 'pause', 'reason': 'test', 'actor': 'human', 'decided_at': T, 'source_issue_comment_url': 'https://github.com/example/repo/issues/1#issuecomment-1', 'source_comment_sha256': '0' * 64, 'run_id': 'r1', 'recovery_condition': 'new evidence', 'new_task_id': None, 'project_url': None}
        self.write_json('opportunities/o1/decisions/d1.json', self.decision)

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True, text=True).stdout.strip()

    def write(self, path, data):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data, encoding='utf-8')

    def write_json(self, path, data):
        self.write(path, json.dumps(data, ensure_ascii=False) + '\n')

    def errors(self):
        return Validator(self.root, self.base, NOW).run()

    def test_valid_review_result_and_decision(self):
        self.assertEqual(self.errors(), [])

    def test_missing_task_and_stale_hash(self):
        (self.root / 'practice/inbox/t1/task.json').unlink()
        self.assertTrue(any('missing input task' in e for e in self.errors()))
        self.task['question'] = 'changed?'
        self.write_json('practice/inbox/t1/task.json', self.task)
        errors = self.errors()
        self.assertTrue(any('task_hash' in e for e in errors))
        self.assertTrue(any('differs from input commit' in e for e in errors))

    def test_duplicate_ids_and_incomplete_criteria(self):
        self.write_json('opportunities/o1/decisions/d1.json', self.decision)
        self.write_json('opportunities/o2/decisions/d1.json', {**self.decision, 'opportunity_id': 'o2'})
        self.result['criteria_results'].pop()
        self.write_json('practice/results/t1/r1/result.json', self.result)
        errors = self.errors()
        self.assertTrue(any('duplicate decision ID' in e for e in errors))
        self.assertTrue(any('cover every task criterion' in e for e in errors))

    def test_unsafe_missing_and_untrusted_references(self):
        for ref in [{'path': '../secrets', 'commit': self.source}, {'path': 'missing', 'commit': self.source}, {'path': 'or-archive/research/a.md', 'commit': '0'*40}]:
            self.task['context_refs'] = [ref]
            self.write_json('practice/inbox/t1/task.json', self.task)
            self.assertTrue(self.errors(), ref)

    def test_ineligible_source_future_time_and_unknown_money(self):
        self.write('or-archive/research/a.md', 'demo_only: true')
        self.git('add', '.')
        self.git('commit', '-qm', 'demo')
        demo_commit = self.git('rev-parse', 'HEAD')
        self.base = demo_commit
        self.opp['source_refs'][0]['commit'] = demo_commit
        self.opp['created_at'] = '2030-01-01T00:00:00Z'
        self.opp['economic_anchor']['value'] = 10
        self.write_json('opportunities/o1/opportunity.json', self.opp)
        errors = self.errors()
        self.assertTrue(any('demo/PILOT' in e for e in errors))
        self.assertTrue(any('future' in e for e in errors))
        self.assertTrue(any('unknown economic basis' in e for e in errors))

    def test_demo_markers_in_json_and_markdown(self):
        for text in ['{"demo_only": true}', '{"research_eligible": false}', '**demo_only**: true', '`research_eligible`: false', 'PILOT']:
            with self.subTest(text=text): self.assertIsNotNone(DEMO.search(text))
        self.assertIsNone(DEMO.search('{"demo_only": false, "research_eligible": true}'))

    def test_duplicate_json_keys_and_symlink(self):
        self.write('practice/inbox/t1/task.json', '{"schema_version":1,"schema_version":1}')
        self.assertTrue(any('duplicate JSON key' in e for e in self.errors()))
        link = self.root / 'practice/inbox/link'
        link.symlink_to(self.root / 'practice/inbox/t1', target_is_directory=True)
        self.assertTrue(any('symlink' in e for e in self.errors()))


if __name__ == '__main__':
    unittest.main()
