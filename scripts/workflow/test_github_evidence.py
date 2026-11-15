import hashlib
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from github_evidence import check_comment, decision_comment_at_merge, merged_addition, merged_task_version, on_first_parent, pr_type, status_description, verify_main_facts, verify_run_receipts


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
        merged = {'merged_at': '2026-01-02T00:00:00Z'}
        decision_comment_at_merge(record, merged, api, 'human', self.root)
        comment['body'] += ' changed'
        with self.assertRaises(ValueError): check_comment(record, api, 'human', self.root)
        with self.assertRaises(ValueError): decision_comment_at_merge(record, merged, api, 'human', self.root)
        comment['updated_at'] = '2026-01-03T00:00:00Z'
        decision_comment_at_merge(record, merged, api, 'human', self.root)
        comment['updated_at'] = record['decided_at']
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

    def test_main_fact_verification_rejects_unapproved_opportunity(self):
        records={'opportunity':{'o1':('opportunities/o1/opportunity.json',{})},'task':{},'result':{},'decision':{}}
        with patch('github_evidence.merged_opportunity_version', side_effect=ValueError('missing merge')):
            with self.assertRaises(ValueError): verify_main_facts(self.root, self.sha, FakeGitHub({}), 'human', records)

    def test_result_requires_matching_unedited_claim_and_lease(self):
        from issue_handoff import block
        task={'task_id':'t1','execution_mode':'real'}
        result={'task_id':'t1','run_id':'r1','task_hash':'a'*64,'outcome':'supported','execution_intervals':[{'started_at':'2026-01-01T00:01:00Z','finished_at':'2026-01-01T00:30:00Z'}]}
        request={'event_id':'e1','task_id':'t1','run_id':'r1','agent_id':'agent','task_hash':'a'*64,'event_type':'claim','timestamp':'2026-01-01T00:00:00Z','reason':None}
        body=block('request',request)
        original={'id':5,'body':body,'user':{'login':'consumer','type':'User'},'created_at':'2026-01-01T00:00:00Z'}
        receipt={'request_comment_id':5,'request_sha256':hashlib.sha256(body.encode()).hexdigest(),'request_actor':'consumer','task_id':'t1','execution_mode':'real','event_id':'e1','run_id':'r1','agent_id':'agent','task_hash':'a'*64,'timestamp':'2026-01-01T00:00:00Z','started_at':'2026-01-01T00:00:00Z','lease_until':'2026-01-01T01:00:00Z','event_type':'accepted','reason':None}
        bot={'id':6,'body':block('receipt',receipt),'user':{'login':'github-actions[bot]','type':'Bot'},'created_at':'2026-01-01T00:00:01Z'}
        issue={'number':1,'body':'<!-- workflow-task: t1 -->','user':{'login':'github-actions[bot]','type':'Bot'}}
        api=FakeGitHub({'issues?state=all':[issue],'issues/1/comments':[original,bot]})
        verify_run_receipts(api,result,task,'human')
        original['body']+=' edited'
        with self.assertRaises(ValueError): verify_run_receipts(api,result,task,'human')
        original['body']=body
        result['execution_intervals'][0]['finished_at']='2026-01-01T02:00:00Z'
        with self.assertRaises(ValueError): verify_run_receipts(api,result,task,'human')
        def event(request_id, event_id, request_kind, receipt_kind, timestamp, expiry):
            req={**request,'event_id':event_id,'event_type':request_kind,'timestamp':timestamp,'reason':'synthetic test'}
            text=block('request',req)
            caller={'id':request_id,'body':text,'user':{'login':'consumer','type':'User'},'created_at':timestamp}
            response={**receipt,'request_comment_id':request_id,'request_sha256':hashlib.sha256(text.encode()).hexdigest(),'event_id':event_id,'event_type':receipt_kind,'timestamp':timestamp,'lease_until':expiry}
            confirmation={'id':request_id+1,'body':block('receipt',response),'user':{'login':'github-actions[bot]','type':'Bot'},'created_at':timestamp}
            return [caller,confirmation]
        comments=[original,bot]
        comments+=event(7,'e2','blocked','blocked','2026-01-01T00:20:00Z','2026-01-01T01:20:00Z')
        comments+=event(9,'e3','resume','resumed','2026-01-01T00:40:00Z','2026-01-01T01:40:00Z')
        api.data['issues/1/comments']=comments
        result['execution_intervals']=[{'started_at':'2026-01-01T00:01:00Z','finished_at':'2026-01-01T00:20:00Z'},{'started_at':'2026-01-01T00:40:00Z','finished_at':'2026-01-01T01:00:00Z'}]
        verify_run_receipts(api,result,task,'human')
        result['execution_intervals']=[{'started_at':'2026-01-01T00:01:00Z','finished_at':'2026-01-01T01:00:00Z'}]
        with self.assertRaises(ValueError): verify_run_receipts(api,result,task,'human')
        result['outcome']='blocked'
        verify_run_receipts(api,result,task,'human')
        api.data['issues/1/comments']=[]
        with self.assertRaises(ValueError): verify_run_receipts(api,result,task,'human')


if __name__ == '__main__': unittest.main()
