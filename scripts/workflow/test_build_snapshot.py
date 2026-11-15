import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from build_snapshot import collect, github_url, last_judge_at, latest_protocol_status
from github_evidence import status_description

NOW = datetime(2026,2,1,tzinfo=timezone.utc)


class FakeAPI:
    repo='example/repo'
    def __init__(self, responses): self.responses=responses
    def get(self, endpoint, paginate=False):
        response=self.responses[endpoint]
        if isinstance(response, Exception): raise response
        return response


class SnapshotCollectionTests(unittest.TestCase):
    def test_empty_snapshot_and_api_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def git(*args): return subprocess.run(['git',*args],cwd=root,check=True,capture_output=True,text=True).stdout.strip()
            git('init','-q'); git('config','user.name','Test'); git('config','user.email','test@example.invalid')
            (root/'README').write_text('test'); git('add','.'); git('commit','-qm','base'); base=git('rev-parse','HEAD')
            api=FakeAPI({'pulls?state=open':[],'issues?state=all':[],'deployments?environment=github-pages':[],'branches/main':{'commit':{'sha':base}}})
            data=collect(api,root,base,'human',NOW)
            self.assertEqual(data['tasks'],[])
            self.assertIsNone(data['last_pages_deploy_at'])
            api.responses['issues?state=all']=OSError('API unavailable')
            with self.assertRaises(OSError): collect(api,root,base,'human',NOW)

    def test_only_bot_success_is_trusted(self):
        statuses=[{'context':'opportunity/protocol/7','creator':{'login':'human'},'created_at':'2026-01-01T00:00:00Z','state':'success','description':status_description('base','body'),'id':1}]
        api=FakeAPI({'commits/abc/statuses':statuses})
        self.assertFalse(latest_protocol_status(api,'abc',7,'base','body'))
        statuses.append({'context':'opportunity/protocol/7','creator':{'login':'github-actions[bot]'},'created_at':'2026-01-01T00:00:00Z','state':'success','description':status_description('base','body'),'id':2})
        self.assertTrue(latest_protocol_status(api,'abc',7,'base','body'))
        self.assertFalse(latest_protocol_status(api,'abc',8,'base','body'))
        self.assertFalse(latest_protocol_status(api,'abc',7,'other-base','body'))
        self.assertFalse(latest_protocol_status(api,'abc',7,'base','changed body'))
        statuses.append({'context':'opportunity/protocol/7','creator':{'login':'github-actions[bot]'},'created_at':'2026-01-01T00:00:00Z','state':'failure','description':status_description('base','body'),'id':3})
        self.assertFalse(latest_protocol_status(api,'abc',7,'base','body'))

    def test_public_links_stay_in_target_repository(self):
        self.assertEqual(github_url('https://github.com/example/repo/issues/12','example/repo','issues'),'https://github.com/example/repo/issues/12')
        for url in ['https://evil.example/example/repo/issues/12','https://github.com/example/other/issues/12','https://github.com/example/repo/issues/12?token=secret']:
            with self.assertRaises(ValueError): github_url(url,'example/repo','issues')

    def test_judge_freshness_uses_explicit_timestamp_and_reports_unknown(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); folder=root/'or-archive/judge'; folder.mkdir(parents=True)
            file=folder/'j.md'; file.write_text('Generated At: 2026-01-01T00:00:00Z\n')
            manifest=root/'or-archive/manifest.json'
            manifest.write_text(json.dumps({'entries':[{'path':'or-archive/judge/j.md','sync_status':'mirrored'}]}))
            self.assertEqual(last_judge_at(root,NOW),'2026-01-01T00:00:00+00:00')
            file.write_text('Generated At: 2030-01-01T00:00:00Z\n')
            self.assertIsNone(last_judge_at(root,NOW))
            file.write_text('no explicit timestamp')
            self.assertIsNone(last_judge_at(root,NOW))


if __name__ == '__main__': unittest.main()
