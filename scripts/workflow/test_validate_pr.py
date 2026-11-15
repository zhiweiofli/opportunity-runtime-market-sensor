import base64
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from validate_pr import validate

T='2026-01-01T00:00:00Z'


class API:
    repo='example/repo'
    def __init__(self, responses): self.responses=responses; self.calls=[]
    def get(self, path, paginate=False):
        self.calls.append(path)
        return self.responses[path]


class UntrustedProposalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        def git(*args): return subprocess.run(['git',*args],cwd=self.root,check=True,capture_output=True,text=True).stdout.strip()
        git('init','-q');git('config','user.name','Test');git('config','user.email','test@example.invalid')
        (self.root/'README').write_text('base');git('add','.');git('commit','-qm','base')
        self.base=git('rev-parse','HEAD'); self.head='b'*40; self.merge='c'*40
        self.path='opportunities/o1/opportunity.json'
        record={'schema_version':1,'opportunity_id':'o1','title':'test','business_problem':'test','target_customer':'test','value_hypothesis':'test','economic_anchor':{'value':None,'currency':None,'unit':'month','basis':'unknown','evidence_ref':None},'gates':dict.fromkeys(['money','mechanism','persistence','capture'],'unknown'),'source_refs':[{'drive_doc_id':None,'source_updated_at':None,'mirror_path':None,'commit':None,'missing_reason':'unavailable'}],'research_status':'unknown','judge_recommendation':'WATCH','critical_unknown':'test','created_at':T,'updated_at':T}
        raw=json.dumps(record).encode()
        pr={'number':7,'state':'open','base':{'ref':'main','sha':'old-base-sha'},'head':{'sha':self.head},'body':'<!-- workflow-type: review -->','mergeable':True,'merge_commit_sha':self.merge,'changed_files':1}
        self.api=API({'pulls/7':pr,'branches/main':{'commit':{'sha':self.base}},f'git/commits/{self.merge}':{'tree':{'sha':'tree'},'parents':[{'sha':self.base},{'sha':self.head}]},'pulls/7/files':[{'status':'added','filename':self.path}], 'git/trees/tree?recursive=1':{'truncated':False,'tree':[{'path':self.path,'type':'blob','mode':'100644','sha':'blob'}]},'git/blobs/blob':{'encoding':'base64','size':len(raw),'content':base64.b64encode(raw).decode()}})

    def test_valid_data_is_read_from_merge_preview_without_checkout(self):
        self.assertEqual(validate(self.api,self.root,self.base,'main',7,'human'),(self.head,'<!-- workflow-type: review -->'))
        self.assertFalse((self.root/self.path).exists())
        self.assertIn('git/blobs/blob',self.api.calls)

    def test_business_pr_cannot_smuggle_code(self):
        pr=self.api.responses['pulls/7']; pr['changed_files']=2
        self.api.responses['pulls/7/files'].append({'status':'modified','filename':'.github/workflows/market-ci.yml'})
        with self.assertRaises(ValueError): validate(self.api,self.root,self.base,'main',7,'human')
        self.assertNotIn('git/blobs/blob',self.api.calls)

    def test_rejects_symlink_and_stale_preview(self):
        self.api.responses['git/trees/tree?recursive=1']['tree'][0]['mode']='120000'
        with self.assertRaises(ValueError): validate(self.api,self.root,self.base,'main',7,'human')
        self.api.responses['git/trees/tree?recursive=1']['tree'][0]['mode']='100644'
        self.api.responses[f'git/commits/{self.merge}']['parents'][0]['sha']='d'*40
        with self.assertRaises(ValueError): validate(self.api,self.root,self.base,'main',7,'human')


if __name__ == '__main__': unittest.main()
