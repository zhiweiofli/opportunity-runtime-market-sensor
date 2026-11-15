#!/usr/bin/env python3
"""Create an isolated, cost-free synthetic review package; no network actions."""
import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = 'examples/synthetic/research.md'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True, help='unique test suffix: letters, digits, underscore or hyphen')
    parser.add_argument('--input-commit', required=True, help='full current main SHA containing the synthetic fixture')
    parser.add_argument('--output', required=True, help='new directory for the proposed files')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,90}', args.id): parser.error('invalid test suffix')
    if not re.fullmatch(r'[0-9a-f]{40}', args.input_commit): parser.error('input commit must be a full SHA')
    source = subprocess.run(['git','-C',str(ROOT),'show',f'{args.input_commit}:{FIXTURE}'],check=True,capture_output=True).stdout
    if b'execution_mode: synthetic' not in source: parser.error('commit does not contain the marked synthetic fixture')
    now = datetime.now(timezone.utc).isoformat()
    oid, tid = 'synthetic-o-' + args.id, 'synthetic-t-' + args.id
    ref = {'path': FIXTURE, 'commit': args.input_commit}
    opportunity = {'schema_version':1,'execution_mode':'synthetic','opportunity_id':oid,'title':'Synthetic protocol exercise','business_problem':'Exercise the workflow with invented data.','target_customer':'Synthetic only','value_hypothesis':'The handoff can be traced end to end.','economic_anchor':{'value':None,'currency':None,'unit':'month','basis':'unknown','evidence_ref':None},'gates':{'money':'Synthetic only','mechanism':'Synthetic only','persistence':'Synthetic only','capture':'Synthetic only'},'source_refs':[{'drive_doc_id':None,'source_updated_at':None,'mirror_path':FIXTURE,'commit':args.input_commit,'missing_reason':'local synthetic fixture, not a Drive document'}],'research_status':'unknown','judge_recommendation':'NEXT','critical_unknown':'Whether the synthetic handshake works.','created_at':now,'updated_at':now}
    task = {'schema_version':1,'execution_mode':'synthetic','task_id':tid,'opportunity_id':oid,'question':'Can the synthetic handoff complete?','hypothesis':'The approved test task can be claimed and returned.','success_criteria':[{'id':'success','description':'Record the synthetic handshake.'}],'falsification_criteria':[{'id':'failure','description':'Record a failed or blocked handshake.'}],'deliverables':['Synthetic result and report'],'context_refs':[ref],'budget':{'max_duration':1,'duration_unit':'hours','max_cost':0,'currency':'USD'},'allowed_actions':['synthetic-only'],'stop_conditions':['Stop on any need for a real external action or expense.'],'created_at':now}
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    for path, record in [(f'opportunities/{oid}/opportunity.json',opportunity),(f'practice/inbox/{tid}/task.json',task)]:
        dest=output/path; dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
        print(dest)
    print('SYNTHETIC ONLY: no real customer, expense, or external action.')


if __name__ == '__main__': main()
