import json
import unittest
from unittest.mock import patch
from decision_proposals import build_record, propose


class API:
    repo = 'example/repo'
    def __init__(self, existing=None): self.existing = existing or []; self.created = []
    def get(self, path, paginate=False):
        if path.startswith('pulls?'): return self.existing
        raise AssertionError(path)
    def post(self, path, body):
        self.created.append((path, body)); return {'number': 4}


class DecisionProposalTests(unittest.TestCase):
    def comment(self, updated='2026-01-01T00:00:00Z'):
        data = {'opportunity_id':'o1', 'action':'pause', 'run_id':'r1', 'reason':'test', 'recovery_condition':'later', 'new_task_id':None, 'project_url':None, 'new_task':None}
        return {'id': 17, 'updated_at': updated, 'html_url':'https://github.com/example/repo/issues/1#issuecomment-17', 'body':'<!-- or-decision -->\n```json\n'+json.dumps(data)+'\n```'}

    def test_edit_produces_distinct_version_even_if_body_repeated(self):
        a, _ = build_record(self.comment(), 'human')
        b, _ = build_record(self.comment('2026-01-02T00:00:00Z'), 'human')
        self.assertEqual(a['source_comment_sha256'], b['source_comment_sha256'])
        self.assertNotEqual(a['decision_id'], b['decision_id'])

    def test_continue_requires_matching_new_task(self):
        comment = self.comment()
        data = json.loads(comment['body'].split('```json\n')[1].split('\n```')[0])
        data.update(action='continue', new_task_id='t2', new_task={'task_id':'wrong'})
        comment['body'] = '<!-- or-decision -->\n```json\n'+json.dumps(data)+'\n```'
        with self.assertRaises(ValueError): build_record(comment, 'human')
        data['new_task']['task_id'] = 't2'
        comment['body'] = '<!-- or-decision -->\n```json\n'+json.dumps(data)+'\n```'
        self.assertEqual(build_record(comment, 'human')[1]['task_id'], 't2')

    def test_existing_closed_or_merged_proposal_is_not_recreated(self):
        api = API(existing=[{'number': 3, 'state':'closed'}])
        with patch('decision_proposals.preflight') as preflight:
            self.assertEqual(propose(api, None, 'base', 'main', 'human', self.comment())['number'], 3)
            preflight.assert_not_called()
        self.assertEqual(api.created, [])

    def test_new_proposal_preflights_before_creating(self):
        api = API()
        with patch('decision_proposals.preflight', return_value={'file':b'content'}) as preflight, patch('decision_proposals.ensure_branch') as branch:
            self.assertEqual(propose(api, None, 'base', 'main', 'human', self.comment())['number'], 4)
            preflight.assert_called_once(); branch.assert_called_once()
        self.assertIn('<!-- workflow-type: decision -->', api.created[0][1]['body'])


if __name__ == '__main__': unittest.main()
