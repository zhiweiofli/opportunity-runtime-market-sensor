import json
import tempfile
import unittest
from pathlib import Path
from check_scope import check_scope


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
    def put(self, path, value):
        p=self.root/path; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(value))
    def test_review_one_opportunity_and_watch_cannot_enqueue(self):
        self.put('opportunities/o1/opportunity.json',{'opportunity_id':'o1','judge_recommendation':'NEXT'})
        self.put('opportunities/o2/opportunity.json',{'opportunity_id':'o2','judge_recommendation':'NEXT'})
        self.put('practice/inbox/t1/task.json',{'task_id':'t1','opportunity_id':'o1'})
        changes=[('A','opportunities/o1/opportunity.json'),('A','practice/inbox/t1/task.json')]
        check_scope('review',changes,self.root)
        with self.assertRaises(ValueError): check_scope('review',changes+[('A','opportunities/o2/opportunity.json')],self.root)
        self.put('opportunities/o1/opportunity.json',{'opportunity_id':'o1','judge_recommendation':'WATCH'})
        with self.assertRaises(ValueError): check_scope('review',changes,self.root)
    def test_result_requires_matching_report(self):
        self.put('practice/results/t1/r1/result.json',{})
        changes=[('A','practice/results/t1/r1/result.json'),('A','practice/results/t1/r1/report.md')]
        check_scope('practice-result',changes,self.root)
        with self.assertRaises(ValueError): check_scope('practice-result',changes[:1],self.root)
    def test_continue_requires_new_task(self):
        self.put('opportunities/o1/decisions/d1.json',{'opportunity_id':'o1','action':'continue','new_task_id':'t2'})
        self.put('practice/inbox/t2/task.json',{'task_id':'t2','opportunity_id':'o1'})
        changes=[('A','opportunities/o1/decisions/d1.json'),('A','practice/inbox/t2/task.json')]
        check_scope('decision',changes,self.root)
        with self.assertRaises(ValueError): check_scope('decision',changes[:1],self.root)


if __name__ == '__main__': unittest.main()
