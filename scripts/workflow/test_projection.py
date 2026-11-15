import json
import unittest
from datetime import datetime, timezone
from projection import project

NOW = datetime(2026, 2, 1, tzinfo=timezone.utc)
T = '2026-01-01T00:00:00Z'
URL = 'https://github.com/example/repo/pull/1'


def entry(data, time=T): return {'data': data, 'merged_at': time, 'url': URL}


def sample():
    opportunity = {'opportunity_id':'o1', 'execution_mode':'real', 'title':'PRIVATE TITLE', 'target_customer':'PRIVATE CUSTOMER', 'research_status':'HYPOTHESIS_READY', 'judge_recommendation':'NEXT', 'created_at':T, 'public': {'title':'Safe title','summary':'Safe summary'}}
    task = {'task_id':'t1', 'execution_mode':'real', 'opportunity_id':'o1', 'question':'PRIVATE QUESTION', 'created_at':T, 'public': {'question_summary':'Safe question'}}
    result = {'task_id':'t1','opportunity_id':'o1','run_id':'r1','recommendation':'PRIVATE RESULT','public':{'summary':'Safe result'}}
    decision = {'opportunity_id':'o1','run_id':'r1','action':'pause','reason':'PRIVATE REASON','new_task_id':None}
    return {'opportunities':[entry(opportunity)], 'tasks':[entry(task)], 'results':[entry(result)], 'decisions':[entry(decision)], 'pull_requests':[], 'issues':{}, 'last_judge_at':T,'last_pages_deploy_at':None,'github_synced_at':T}


class ProjectionTests(unittest.TestCase):
    def test_counts_and_allowlist(self):
        s=sample()
        s['opportunities'][0]['data']['public']['economic_anchor']={'value':1,'currency':'USD','unit':'month','basis':'estimated','evidence_ref':'PRIVATE LINK'}
        d=project(s, NOW)
        self.assertEqual(d['completion'], {'numerator':1,'denominator':1})
        self.assertEqual(d['conversion'], {'numerator':0,'denominator':1})
        self.assertEqual(d['counts']['opportunities_awaiting_decision'],0)
        self.assertEqual(d['opportunities'][0]['stage'],'暂缓')
        self.assertNotIn('PRIVATE', json.dumps(d))

    def test_each_result_requires_its_own_decision(self):
        s=sample()
        s['tasks'].append(entry({'task_id':'t2','execution_mode':'real','opportunity_id':'o1','question':'private','created_at':T}))
        s['results'].append(entry({'task_id':'t2','execution_mode':'real','opportunity_id':'o1','run_id':'r2'}))
        d=project(s,NOW)
        self.assertEqual(d['counts']['opportunities_awaiting_decision'],1)
        self.assertEqual(d['opportunities'][0]['stage'],'待立项决定')
        self.assertEqual([x['stage'] for x in d['opportunities'][0]['tasks']],['暂缓','待立项决定'])

    def test_unverified_pr_unknown_time_and_empty_cohort(self):
        s=sample(); s['tasks']=[]; s['results']=[]; s['decisions']=[]
        s['pull_requests']=[{'kind':'review','verified':False,'task_ids':[],'opportunity_ids':[],'url':URL,'created_at':T}]
        s['opportunities'][0]['merged_at']='2030-01-01T00:00:00Z'
        d=project(s,NOW)
        self.assertEqual(d['counts']['unverified_prs'],1)
        self.assertEqual(d['counts']['open_review_prs'],0)
        self.assertEqual(d['completion']['denominator'],0)
        self.assertIsNone(d['opportunities'][0]['history'][0]['at'])

    def test_pause_does_not_show_old_task_as_available(self):
        s=sample(); s['results']=[]; s['decisions'][0]['data']['run_id']=None
        d=project(s,NOW)
        self.assertEqual(d['opportunities'][0]['tasks'][0]['stage'],'暂缓')
        self.assertEqual(d['opportunities'][0]['stage'],'暂缓')

    def test_synthetic_records_are_not_business_metrics(self):
        s=sample()
        s['opportunities'][0]['data']['execution_mode']='synthetic'
        s['tasks'][0]['data']['execution_mode']='synthetic'
        s['pull_requests']=[{'kind':'review','verified':True,'execution_mode':'synthetic','task_ids':[],'opportunity_ids':['o1'],'url':URL,'created_at':T}]
        d=project(s,NOW)
        self.assertEqual(d['counts']['open_review_prs'],0)
        self.assertEqual(d['completion']['denominator'],0)
        self.assertEqual(d['opportunities'],[])


if __name__ == '__main__': unittest.main()
