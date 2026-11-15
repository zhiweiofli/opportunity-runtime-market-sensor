import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from issue_handoff import block, parsed, reconcile

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class FakeGitHub:
    def __init__(self):
        self.issues = []
        self.comments = {}
        self.next_id = 10
    def get(self, path, paginate=False):
        if path == 'issues?state=all': return list(self.issues)
        parts = path.split('/')
        if len(parts) == 3 and parts[0] == 'issues' and parts[2] == 'comments': return list(self.comments[int(parts[1])])
        raise AssertionError(path)
    def post(self, path, data):
        if path == 'issues':
            issue = {'number': len(self.issues)+1, 'state': 'open', 'body': data['body'], 'user': {'login': 'github-actions[bot]', 'type': 'Bot'}}
            self.issues.append(issue); self.comments[issue['number']] = []
            return issue
        num = int(path.split('/')[1])
        self.next_id += 1
        comment = {'id': self.next_id, 'body': data['body'], 'user': {'login': 'github-actions[bot]', 'type': 'Bot'}, 'created_at': NOW.isoformat()}
        self.comments[num].append(comment)
        return comment
    def request(self, event, actor='consumer', issue=1):
        self.next_id += 1
        self.comments[issue].append({'id': self.next_id, 'body': block('request', event), 'user': {'login': actor, 'type': 'User'}, 'created_at': NOW.isoformat()})
    def receipts(self):
        return [data for comment in self.comments[1] for kind, data in [parsed(comment)] if kind == 'receipt']


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'practice/inbox/t1/task.json'; self.path.parent.mkdir(parents=True)
        self.task = {'task_id': 't1', 'opportunity_id': 'o1', 'budget': {'max_duration': 3, 'max_cost': 0, 'currency': 'USD'}}
        self.path.write_text(json.dumps(self.task))
        self.api = FakeGitHub()
        self.patcher = patch('issue_handoff.merged_task_version', return_value={'number': 1}); self.patcher.start(); self.addCleanup(self.patcher.stop)
        self.run_scan()

    def run_scan(self, now=NOW): reconcile(self.api, self.root, 'base', 'consumer', 'human', now)
    def event(self, event_id, run):
        return {'event_id': event_id, 'task_id': 't1', 'run_id': run, 'agent_id': 'agent', 'task_hash': hashlib.sha256(self.path.read_bytes()).hexdigest(), 'event_type': 'claim', 'timestamp': NOW.isoformat(), 'reason': None}

    def test_issue_creation_and_claims_are_idempotent(self):
        self.run_scan(); self.assertEqual(len(self.api.issues), 1)
        self.api.request(self.event('e1', 'r1'))
        self.api.request(self.event('e2', 'r2'))
        self.run_scan()
        self.assertEqual([r['event_type'] for r in self.api.receipts()], ['accepted', 'rejected'])
        self.run_scan()
        self.assertEqual(len(self.api.receipts()), 2)

    def test_unauthorized_and_expired_claim_are_not_accepted(self):
        self.api.request(self.event('e1', 'r1'), actor='stranger')
        self.api.request(self.event('e2', 'r2'))
        self.run_scan(NOW + timedelta(hours=3))
        self.assertEqual([r['event_type'] for r in self.api.receipts()], ['rejected'])
        self.assertIn('expired', self.api.receipts()[0]['reason'])

    def test_stale_hash_and_unknown_budget_rejected(self):
        self.api.request({**self.event('e1', 'r1'), 'task_hash': 'a'*64})
        self.run_scan(); self.assertIn('stale', self.api.receipts()[0]['reason'])
        self.task['budget']['max_cost'] = None
        self.path.write_text(json.dumps(self.task))
        self.api.request(self.event('e2', 'r2'))
        self.run_scan(); self.assertEqual(self.api.receipts()[-1]['event_type'], 'rejected')


if __name__ == '__main__': unittest.main()
