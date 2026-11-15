import hashlib
import json
import os
import sys
import tempfile
import unittest
from jsonschema import Draft202012Validator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import synthetic_consumer
from issue_handoff import block, parsed


class API:
    def __init__(self): self.comments=[]; self.posts=0
    def get(self,path,paginate=False):
        if path=='branches/main': return {'commit':{'sha':'a'*40}}
        if path=='issues/1': return {'number':1,'state':'open','body':'<!-- workflow-task: t1 -->','user':{'login':'github-actions[bot]','type':'Bot'}}
        if path=='issues?state=all': return [self.get('issues/1')]
        if path=='issues/1/comments': return self.comments
        raise AssertionError(path)
    def post(self,path,body):
        self.posts+=1
        self.comments.append({'id':5,'body':body['body'],'user':{'login':'test-user','type':'User'},'created_at':datetime.now(timezone.utc).isoformat()})
        return self.comments[-1]


class ConsumerTests(unittest.TestCase):
    def test_claim_is_idempotent_and_result_is_synthetic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'repo'; path=root/'practice/inbox/t1/task.json'; path.parent.mkdir(parents=True)
            task={'task_id':'t1','opportunity_id':'o1','execution_mode':'synthetic','context_refs':[{'path':'examples/synthetic/research.md','commit':'a'*40}],'budget':{'currency':'USD'},'success_criteria':[{'id':'yes'}],'falsification_criteria':[{'id':'no'}]}
            path.write_text(json.dumps(task)); api=API(); output=Path(tmp)/'result'
            class FakeValidator:
                def __init__(self,*args): self.records={'task':{'t1':('practice/inbox/t1/task.json',task)},'result':{},'opportunity':{},'decision':{}}
                def run(self): return []
                def read_ref(self,*args): return b'execution_mode: synthetic\n'
            def run(args,**kwargs):
                return SimpleNamespace(stdout='test-user\n' if args[:2]==['gh','api'] else ('a'*40+'\n' if 'rev-parse' in args else ''))
            argv=['synthetic_consumer.py','--repo','example/repo','--task-id','t1','--run-id','r1','--agent-id','test-agent','--issue','1','--output',str(output),'--human','human']
            with patch.object(synthetic_consumer,'ROOT',root), patch.object(synthetic_consumer,'GitHub',return_value=api), patch.object(synthetic_consumer,'Validator',FakeValidator), patch.object(synthetic_consumer,'verify_main_facts'), patch.object(synthetic_consumer,'merged_task_version'), patch.object(synthetic_consumer,'runnable',return_value=True), patch.object(synthetic_consumer,'open_result_tasks',return_value=set()), patch.object(synthetic_consumer.subprocess,'run',side_effect=run), patch.dict(os.environ,{'GH_TOKEN':'fake'}), patch.object(sys,'argv',argv):
                synthetic_consumer.main(); self.assertEqual(api.posts,1)
                synthetic_consumer.main(); self.assertEqual(api.posts,1)
                claim=api.comments[0]; _, request=parsed(claim); now=datetime.now(timezone.utc)
                receipt={'request_comment_id':5,'request_sha256':hashlib.sha256(claim['body'].encode()).hexdigest(),'request_actor':'test-user','task_id':'t1','execution_mode':'synthetic','event_id':request['event_id'],'run_id':'r1','agent_id':'test-agent','task_hash':request['task_hash'],'event_type':'accepted','timestamp':now.isoformat(),'started_at':now.isoformat(),'lease_until':(now+timedelta(hours=1)).isoformat(),'reason':None}
                api.comments.append({'id':6,'body':block('receipt',receipt),'user':{'login':'github-actions[bot]','type':'Bot'},'created_at':now.isoformat()})
                synthetic_consumer.main()
                result=json.loads((output/'practice/results/t1/r1/result.json').read_text())
                schema=Path(__file__).resolve().parents[2]/'schemas/workflow/result.schema.json'
                Draft202012Validator(json.loads(schema.read_text())).validate(result)
                self.assertEqual(result['actual_cost']['cost'],0)
                self.assertEqual(result['evidence_refs'][0]['source'],'synthetic')
                self.assertEqual(api.posts,1)


if __name__=='__main__': unittest.main()
