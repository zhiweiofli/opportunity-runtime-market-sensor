#!/usr/bin/env python3
"""Explicit test consumer: request one synthetic claim or prepare a synthetic result."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from github_evidence import GitHub, TASK_MARKER, merged_task_version, verify_main_facts
from issue_handoff import ROOT, block, bot, open_result_tasks, parsed, runnable
from leases import latest
from validate import Validator, parse_time

ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', required=True)
    p.add_argument('--task-id', required=True)
    p.add_argument('--run-id', required=True)
    p.add_argument('--agent-id', required=True)
    p.add_argument('--issue', type=int, required=True)
    p.add_argument('--output', required=True, help='new directory for the result package')
    p.add_argument('--human', required=True, help='configured human GitHub login')
    a=p.parse_args()
    if any(not ID.fullmatch(x) for x in (a.task_id,a.run_id,a.agent_id)) or a.issue <= 0: p.error('invalid identifier')
    token=os.environ.get('GH_TOKEN')
    if not token:
        token=subprocess.run(['gh','auth','token'],check=True,capture_output=True,text=True).stdout.strip()
    api=GitHub(a.repo,token)
    env={**os.environ,'GH_TOKEN':token}
    actor=subprocess.run(['gh','api','user','--jq','.login'],check=True,capture_output=True,text=True,env=env).stdout.strip()
    base=subprocess.run(['git','-C',str(ROOT),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
    if api.get('branches/main')['commit']['sha'] != base: raise ValueError('checkout is not at current main')
    dirty=subprocess.run(['git','-C',str(ROOT),'status','--porcelain','--','practice','opportunities'],check=True,capture_output=True,text=True).stdout
    if dirty: raise ValueError('workflow data has local changes')
    validator=Validator(ROOT,base); errors=validator.run()
    if errors: raise ValueError('invalid workflow data: '+'; '.join(errors))
    verify_main_facts(ROOT,base,api,a.human,validator.records)
    item=validator.records['task'].get(a.task_id)
    if not item or item[1]['execution_mode'] != 'synthetic': raise ValueError('task is not an approved synthetic task')
    path, task=item
    merged_task_version(ROOT,base,path,api,a.human)
    if any(a.run_id in records for records in validator.records.values()): raise ValueError('run ID is already used')
    if not runnable(ROOT,task) or a.task_id in open_result_tasks(api): raise ValueError('task is stopped, complete or has an open result PR')
    issue=api.get(f'issues/{a.issue}')
    if not bot(issue) or issue.get('state') != 'open' or TASK_MARKER.findall(issue.get('body') or '') != [a.task_id]:
        raise ValueError('issue is not the open center task issue')
    matches = [i for i in api.get('issues?state=all',paginate=True) if not i.get('pull_request') and bot(i) and TASK_MARKER.findall(i.get('body') or '') == [a.task_id]]
    if len(matches) != 1 or matches[0]['number'] != a.issue:
        raise ValueError('task issue mapping is missing or ambiguous')
    comments=api.get(f'issues/{a.issue}/comments',paginate=True)
    task_hash=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    event_id='synthetic-claim-'+hashlib.sha256((a.task_id+'\0'+a.run_id+'\0'+a.agent_id).encode()).hexdigest()[:24]
    existing=[]
    for comment in comments:
        kind, data=parsed(comment)
        if kind == 'request' and isinstance(data,dict) and data.get('event_id') == event_id:
            existing.append((comment,data))
    if len(existing)>1: raise ValueError('duplicate claim event; manual reconciliation required')
    if not existing:
        now=datetime.now(timezone.utc).isoformat()
        request={'event_id':event_id,'task_id':a.task_id,'run_id':a.run_id,'agent_id':a.agent_id,'task_hash':task_hash,'event_type':'claim','timestamp':now,'reason':None}
        api.post(f'issues/{a.issue}/comments',{'body':block('request',request)})
        print('SYNTHETIC: claim requested; rerun after the center posts a receipt.')
        return
    request_comment, request=existing[0]
    if (request_comment.get('user') or {}).get('login','').lower()!=actor.lower() or any(request.get(k)!=v for k,v in {'task_id':a.task_id,'run_id':a.run_id,'agent_id':a.agent_id,'task_hash':task_hash,'event_type':'claim'}.items()):
        raise ValueError('existing claim differs from requested run or identity')
    digest=hashlib.sha256(request_comment['body'].encode('utf-8')).hexdigest()
    receipts=[]
    receipt_comments={}
    for comment in comments:
        kind, data=parsed(comment)
        if bot(comment) and kind == 'receipt' and isinstance(data,dict) and data.get('task_id') == a.task_id:
            receipts.append(data)
            receipt_comments[data.get('request_comment_id')]=comment
    responses=[r for r in receipts if r.get('request_comment_id') == request_comment['id']]
    if not responses:
        print('SYNTHETIC: awaiting center receipt; no result prepared.')
        return
    if len(responses)!=1: raise ValueError('ambiguous claim receipts')
    response=responses[0]
    if response.get('event_type')!='accepted': raise ValueError('claim was not accepted: '+str(response.get('reason','unknown')))
    if response.get('request_sha256')!=digest or response.get('request_actor','').lower()!=actor.lower() or response.get('execution_mode')!='synthetic': raise ValueError('claim receipt does not match request')
    state=latest(receipts); now=datetime.now(timezone.utc)
    if not state or state['status']!='active' or state['run_id']!=a.run_id or state['agent_id']!=a.agent_id or state['task_hash']!=task_hash or parse_time(state['lease_until']) <= now:
        raise ValueError('synthetic lease is no longer active')
    if now < max(parse_time(response['timestamp']), parse_time(receipt_comments[request_comment['id']]['created_at'])):
        raise ValueError('synthetic claim receipt is not yet effective')
    if api.get('branches/main')['commit']['sha']!=base or not runnable(ROOT,task) or a.task_id in open_result_tasks(api):
        raise ValueError('main or task status changed; stop and rescan')
    context=task['context_refs'][0]
    started=datetime.now(timezone.utc)
    source=validator.read_ref(context['path'],context['commit'],path)
    if source is None: raise ValueError('synthetic context is unavailable')
    finished=datetime.now(timezone.utc)
    if finished >= parse_time(state['lease_until']): raise ValueError('synthetic lease expired before completion')
    start_text, finish_text = started.isoformat(), finished.isoformat()
    result={'schema_version':1,'task_id':a.task_id,'opportunity_id':task['opportunity_id'],'run_id':a.run_id,'task_hash':task_hash,'input_commit':base,'started_at':start_text,'finished_at':finish_text,'execution_intervals':[{'started_at':start_text,'finished_at':finish_text}],'outcome':'inconclusive','criteria_results':[{'criterion_id':c['id'],'result':'Synthetic handshake only; no real-world claim.'} for c in task['success_criteria']+task['falsification_criteria']],'evidence_refs':[{'source':'synthetic','collected_at':finish_text,'summary':'Synthetic fixture read during the test.','ref':context,'sha256':hashlib.sha256(source).hexdigest()}],'actual_cost':{'duration':(finished-started).total_seconds()/3600,'duration_unit':'hours','cost':0,'currency':task['budget']['currency']},'remaining_unknown':['This test does not validate a real business opportunity.'],'recommendation':'Review the synthetic handshake only.'}
    output=Path(a.output); output.mkdir(parents=True,exist_ok=False)
    directory=output/'practice'/'results'/a.task_id/a.run_id; directory.mkdir(parents=True)
    (directory/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (directory/'report.md').write_text('execution_mode: synthetic\n\n# Synthetic handshake\n\nThis report records a test claim and fixture read. No fees, external contacts or real-world actions were performed.\n')
    print(f'SYNTHETIC: accepted claim; result package prepared in {output}. No PR created.')


if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(f'SYNTHETIC consumer stopped: {exc}',file=sys.stderr)
        sys.exit(1)
