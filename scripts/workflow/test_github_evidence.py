import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from github_evidence import check_comment, merged_addition, merged_task_version, on_first_parent, pr_type, status_description


class FakeGitHub:
    repo = 'example/repo'
    def __init__(self, data): self.data = data
    def get(self, path, paginate=False): return self.data[path]


class GitHubEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.write('README', 'base')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        self.write('practice/inbox/t1/task.json', json.dumps({'opportunity_id': 'o1'}))
        self.git('add', '.')
        self.git('commit', '-qm', 'add task')
        self.sha = self.git('rev-parse', 'HEAD')
        self.parent = self.git('rev-parse', 'HEAD^')

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True, text=True).stdout.strip()

    def write(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def test_type_must_be_unambiguous(self):
        self.assertEqual(pr_type('x\n<!-- workflow-type: review -->'), 'review')
        for body in ['', '<!-- workflow-type: review -->\n<!-- workflow-type: implementation -->']:
            with self.assertRaises(ValueError): pr_type(body)

    def test_merge_evidence_requires_added_file_and_merged_pr(self):
        path = 'practice/inbox/t1/task.json'
        pr = {'number': 1, 'merged_at': '2026-01-01T00:00:00Z', 'merged_by': {'login': 'human'}, 'merge_commit_sha': self.sha, 'head': {'sha': self.sha}, 'base': {'ref':'main'}, 'body': '<!-- workflow-type: review -->'}
        api = FakeGitHub({f'commits/{self.sha}/pulls': [{'number': 1}], 'pulls/1': pr, f'commits/{self.sha}/statuses': [{'context':'opportunity/protocol/1','creator':{'login':'github-actions[bot]'},'created_at':'2025-12-31T00:00:00Z','state':'success','description':status_description(self.parent, '<!-- workflow-type: review -->')}], 'pulls/1/files': [{'filename': path, 'status': 'added'}]})
        self.assertEqual(merged_addition(self.root, self.sha, path, {'review'}, api, 'human')['number'], 1)
        status = api.data[f'commits/{self.sha}/statuses'][0]
        original_description = status['description']
        status['description'] = status_description('0'*40, pr['body'])
        with self.assertRaises(ValueError): merged_addition(self.root, self.sha, path, {'review'}, api, 'human')
        status['description'] = original_description
        pr['body'] += '\nchanged'
        with self.assertRaises(ValueError): merged_addition(self.root, self.sha, path, {'review'}, api, 'human')
        pr['body'] = '<!-- workflow-type: review -->'
        status['state'] = 'failure'
        with self.assertRaises(ValueError): merged_addition(self.root, self.sha, path, {'review'}, api, 'human')
        status['state'] = 'success'
        status['creator']['login'] = 'human'
        with self.assertRaises(ValueError): merged_addition(self.root, self.sha, path, {'review'}, api, 'human')
        status['creator']['login'] = 'github-actions[bot]'
        api.data['pulls/1/files'][0]['status'] = 'modified'
        with self.assertRaises(ValueError): merged_addition(self.root, self.sha, path, {'review'}, api, 'human')
        api.data['pulls/1/files'][0]['status'] = 'added'
        pr['merged_at'] = None
        with self.assertRaises(ValueError): merged_addition(self.root, self.sha, path, {'review'}, api, 'human')

    def test_decision_comment_checks_actor_issue_and_version(self):
        data = {'opportunity_id': 'o1', 'action': 'pause', 'run_id': None, 'reason': 'test', 'recovery_condition': 'later', 'new_task_id': None, 'project_url': None, 'new_task': None}
        body = '<!-- or-decision -->\n```json\n' + json.dumps(data) + '\n```'
        record = {**data, 'actor': 'human', 'decided_at': '2026-01-01T00:00:00Z', 'source_issue_comment_url': 'https://github.com/example/repo/issues/1#issuecomment-5', 'source_comment_sha256': hashlib.sha256(body.encode()).hexdigest()}
        comment = {'body': body, 'user': {'login': 'human'}, 'updated_at': record['decided_at'], 'issue_url': 'https://api.github.com/repos/example/repo/issues/1'}
        issue = {'number': 1, 'body': '<!-- workflow-task: t1 -->', 'user': {'login': 'github-actions[bot]', 'type': 'Bot'}}
        api = FakeGitHub({'issues/comments/5': comment, 'issues/1': issue, 'issues?state=all': [issue]})
        check_comment(record, api, 'human', self.root)
        comment['body'] += ' changed'
        with self.assertRaises(ValueError): check_comment(record, api, 'human', self.root)
        comment['body'] = body
        with self.assertRaises(ValueError): check_comment(record, api, 'other', self.root)
        api.data['issues/1']['body'] = '<!-- workflow-task: missing -->'
        with self.assertRaises(ValueError): check_comment(record, api, 'human', self.root)

    def test_first_parent_merge_commit_is_discovered(self):
        base = self.git('rev-parse', 'HEAD')
        self.git('switch', '-qc', 'proposal')
        self.write('practice/inbox/t2/task.json', '{}')
        self.git('add', '.')
        self.git('commit', '-qm', 'new task')
        proposal = self.git('rev-parse', 'HEAD')
        self.git('switch', '-q', '--detach', base)
        self.git('merge', '--no-ff', '-qm', 'merge proposal', 'proposal')
        merge = self.git('rev-parse', 'HEAD')
        path = 'practice/inbox/t2/task.json'
        pr = {'number': 2, 'merged_at': '2026-01-01T00:00:00Z', 'merged_by': {'login': 'human'}, 'merge_commit_sha': merge, 'head': {'sha': merge}, 'base': {'ref':'main'}, 'body': '<!-- workflow-type: review -->'}
        api = FakeGitHub({f'commits/{merge}/pulls': [{'number': 2}], 'pulls/2': pr, f'commits/{merge}/statuses': [{'context':'opportunity/protocol/2','creator':{'login':'github-actions[bot]'},'created_at':'2025-12-31T00:00:00Z','state':'success','description':status_description(base, '<!-- workflow-type: review -->')}], 'pulls/2/files': [{'filename': path, 'status': 'added'}]})
        self.assertEqual(merged_addition(self.root, merge, path, {'review'}, api, 'human')['number'], 2)
        self.assertTrue(on_first_parent(self.root, merge, merge))
        self.assertFalse(on_first_parent(self.root, proposal, merge))

    def test_latest_task_change_needs_its_own_validated_merge(self):
        path = 'practice/inbox/t1/task.json'
        self.write(path, '{"opportunity_id":"o1","question":"changed"}')
        self.git('add', '.')
        self.git('commit', '-qm', 'modify task')
        changed = self.git('rev-parse', 'HEAD')
        status = {'context':'opportunity/protocol/1','creator':{'login':'github-actions[bot]'},'created_at':'2025-12-31T00:00:00Z','state':'success','description':status_description(self.parent, '<!-- workflow-type: review -->')}
        old = {'number':1,'merged_at':'2026-01-01T00:00:00Z','merged_by':{'login':'human'},'merge_commit_sha':self.sha,'head':{'sha':self.sha},'base':{'ref':'main'},'body':'<!-- workflow-type: review -->'}
        api = FakeGitHub({f'commits/{changed}/pulls':[], f'commits/{self.sha}/pulls':[{'number':1}], 'pulls/1':old, f'commits/{self.sha}/statuses':[status], 'pulls/1/files':[{'filename':path,'status':'added'}]})
        with self.assertRaises(ValueError): merged_task_version(self.root, changed, path, api, 'human')
        new = {**old, 'number':2, 'merge_commit_sha':changed, 'head':{'sha':changed}}
        api.data.update({f'commits/{changed}/pulls':[{'number':2}], 'pulls/2':new, f'commits/{changed}/statuses':[{**status,'context':'opportunity/protocol/2','description':status_description(self.sha, '<!-- workflow-type: review -->')}], 'pulls/2/files':[{'filename':path,'status':'modified'}]})
        self.assertEqual(merged_task_version(self.root, changed, path, api, 'human')['number'], 2)


if __name__ == '__main__': unittest.main()
