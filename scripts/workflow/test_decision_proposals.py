import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from decision_proposals import build_record, invalidate_missing_comments, invalidate_old_versions, propose


class API:
    repo = 'example/repo'
    def __init__(self, existing=None): self.existing = existing or []; self.created = []
    def get(self, path, paginate=False):
        if path.startswith('pulls?'): return self.existing
        if path.startswith('git/ref/heads/'): return {'object': {'sha': 'a'*40}}
        if path.startswith('commits/') and path.endswith('/status'): return {'statuses': []}
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
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/'opportunities/o1/opportunity.json'; file.parent.mkdir(parents=True)
            file.write_text(json.dumps({'execution_mode':'real'}))
            with patch('decision_proposals.preflight', return_value={'file':b'content'}) as preflight, patch('decision_proposals.ensure_branch') as branch:
                self.assertEqual(propose(api, tmp, 'base', 'main', 'human', self.comment())['number'], 4)
                preflight.assert_called_once(); branch.assert_called_once()
        pull = next(body for path, body in api.created if path == 'pulls')
        self.assertIn('<!-- workflow-type: decision -->', pull['body'])

    def test_edited_or_removed_comment_invalidates_old_head(self):
        api = API()
        old = {'number': 9, 'head': {'ref': 'codex/decision-d-17-' + 'a'*16, 'sha': 'b'*40}}
        invalidate_old_versions(api, [old], self.comment())
        self.assertEqual(api.created[-1][1]['state'], 'failure')
        api.created.clear()
        invalidate_missing_comments(api, [old], set())
        self.assertEqual(api.created[-1][1]['description'], 'Source decision comment is unavailable')


if __name__ == '__main__': unittest.main()
