#!/usr/bin/env python3
"""Reconcile main-branch tasks and process authenticated task-issue requests."""
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from github_evidence import GitHub, TASK_MARKER, merged_addition
from leases import latest, recover, transition
from validate import Validator, load_json, parse_time

ROOT = Path(__file__).resolve().parents[2]
ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$')
HASH = re.compile(r'^[0-9a-f]{64}$')
BLOCK = re.compile(r'\A<!-- or-(request|receipt|recover) -->\s*```json\s*\n(.*?)\n```\s*\Z', re.DOTALL)
REQUEST_KEYS = {'event_id', 'task_id', 'run_id', 'agent_id', 'task_hash', 'event_type', 'timestamp', 'reason'}
RECOVER_KEYS = {'task_id', 'run_id', 'reason'}
BOT = 'github-actions[bot]'


def block(kind, value):
    return '<!-- or-' + kind + ' -->\n```json\n' + json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n```'


def parsed(comment):
    body = comment.get('body') or ''
    m = BLOCK.fullmatch(body)
    if not m: return None, None
    try: return m[1], load_json(m[2])
    except (ValueError, TypeError): return None, None


def bot(comment):
    user = comment.get('user') or {}
    return user.get('login', '').lower() == BOT and user.get('type') == 'Bot'


def valid_request(e, task_id):
    if not isinstance(e, dict) or set(e) != REQUEST_KEYS: raise ValueError('invalid request fields')
    if any(not isinstance(e.get(k), str) or not ID.fullmatch(e[k]) for k in ('event_id', 'task_id', 'run_id', 'agent_id')): raise ValueError('invalid request identifier')
    if e['task_id'] != task_id or not isinstance(e['task_hash'], str) or not HASH.fullmatch(e['task_hash']): raise ValueError('task ID or hash is invalid')
    if e['event_type'] not in ('claim', 'heartbeat', 'blocked', 'resume', 'released'): raise ValueError('invalid event type')
    if e['reason'] is not None and (not isinstance(e['reason'], str) or not e['reason'].strip()): raise ValueError('invalid reason')
    parse_time(e['timestamp'])


def runnable(root, task):
    if any((root / 'practice/results' / task['task_id']).glob('*/result.json')): return False
    directory = root / 'opportunities' / task['opportunity_id'] / 'decisions'
    decisions = [load_json(p.read_bytes()) for p in directory.glob('*.json')]
    if not decisions: return True
    latest_time = max(parse_time(x['decided_at']) for x in decisions)
    recent = [x for x in decisions if parse_time(x['decided_at']) == latest_time]
    if len(recent) != 1: return False
    d = recent[0]
    return d['action'] == 'continue' and d['new_task_id'] == task['task_id']


def reconcile(api, root, base, consumer, human, now):
    tasks = {}
    for path in sorted((root / 'practice/inbox').glob('*/task.json')):
        task = load_json(path.read_bytes())
        tasks[task['task_id']] = (path, task)
    all_issues = api.get('issues?state=all', paginate=True)
    matches = {}
    for issue in all_issues:
        if issue.get('pull_request') or not bot(issue): continue
        markers = TASK_MARKER.findall(issue.get('body') or '')
        if len(markers) == 1 and markers[0] in tasks:
            matches.setdefault(markers[0], []).append(issue)
    for task_id, (path, task) in tasks.items():
        if len(matches.get(task_id, [])) > 1:
            raise ValueError(f'duplicate task issues for {task_id}; manual reconciliation required')
        if not matches.get(task_id) and runnable(root, task):
            merged_addition(root, base, path.relative_to(root).as_posix(), {'review', 'decision'}, api)
            body = f'<!-- workflow-task: {task_id} -->\n\n任务 `{task_id}`。此 Issue 保存领取与运行回执；以 main 的任务文件为准。'
            issue = api.post('issues', {'title': f'Practice task: {task_id}', 'body': body})
            matches[task_id] = [issue]
    comments = {}
    used_event_ids = set()
    for task_id, issues in matches.items():
        comments[task_id] = api.get(f'issues/{issues[0]["number"]}/comments', paginate=True)
        for c in comments[task_id]:
            kind, data = parsed(c)
            if bot(c) and kind == 'receipt' and isinstance(data, dict) and data.get('event_id'):
                used_event_ids.add(data['event_id'])
    for task_id, issues in matches.items():
        issue = issues[0]
        if issue.get('state') != 'open':
            print(f'{task_id}: task issue closed; not processing')
            continue
        path, task = tasks[task_id]
        cs = comments[task_id]
        receipts = []
        processed = set()
        for c in cs:
            kind, data = parsed(c)
            if bot(c) and kind == 'receipt' and isinstance(data, dict) and data.get('task_id') == task_id:
                if isinstance(data.get('request_comment_id'), int):
                    processed.add(data['request_comment_id'])
                    receipts.append(data)
        for c in cs:
            kind, event = parsed(c)
            author = (c.get('user') or {}).get('login', '').lower()
            if c['id'] in processed or kind not in ('request', 'recover'): continue
            if kind == 'request' and (not consumer or author != consumer.lower() or author == BOT): continue
            if kind == 'recover' and (not human or author != human.lower() or author == BOT): continue
            now_at = datetime.now(timezone.utc) if now is None else now
            state = latest(receipts)
            event_id = event.get('event_id') if isinstance(event, dict) else None
            if not isinstance(event_id, str) or not ID.fullmatch(event_id): event_id = None
            base_receipt = {'request_comment_id': c['id'], 'request_sha256': hashlib.sha256((c.get('body') or '').encode('utf-8')).hexdigest(), 'task_id': task_id, 'event_id': event_id, 'run_id': event.get('run_id') if isinstance(event, dict) else None, 'agent_id': event.get('agent_id') if isinstance(event, dict) else None, 'task_hash': event.get('task_hash') if isinstance(event, dict) else None, 'timestamp': now_at.isoformat()}
            try:
                if kind == 'request':
                    valid_request(event, task_id)
                    if event_id in used_event_ids: raise ValueError('event_id already processed')
                    if parse_time(event['timestamp']) > now_at: raise ValueError('request timestamp is in the future')
                    if event['event_type'] == 'claim' and now_at - parse_time(c['created_at']) > timedelta(hours=2): raise ValueError('claim request expired')
                    merged_addition(root, base, path.relative_to(root).as_posix(), {'review', 'decision'}, api)
                    budget = task['budget']
                    permitted = runnable(root, task) and budget['max_cost'] is not None and budget['currency'] is not None
                    fragment = transition(state, event, now_at, hashlib.sha256(path.read_bytes()).hexdigest(), budget['max_duration'], permitted)
                else:
                    if not isinstance(event, dict) or set(event) != RECOVER_KEYS or event['task_id'] != task_id or not isinstance(event['run_id'], str) or not ID.fullmatch(event['run_id']): raise ValueError('invalid recovery fields')
                    if not isinstance(event['reason'], str) or not event['reason'].strip(): raise ValueError('recovery reason required')
                    fragment = recover(state, event['run_id'], event['reason'], now_at)
                    base_receipt.update({'run_id': state['run_id'], 'agent_id': state['agent_id'], 'task_hash': state['task_hash']})
                receipt = {**base_receipt, **fragment}
            except (ValueError, KeyError, TypeError) as exc:
                receipt = {**base_receipt, 'event_type': 'rejected', 'started_at': None, 'lease_until': None, 'reason': str(exc)}
            api.post(f'issues/{issue["number"]}/comments', {'body': block('receipt', receipt)})
            receipts.append(receipt)
            processed.add(c['id'])
            if event_id: used_event_ids.add(event_id)


def main():
    token = os.environ.get('GH_TOKEN', '')
    repo = os.environ.get('GITHUB_REPOSITORY', '')
    consumer = os.environ.get('WORKFLOW_CONSUMER_LOGIN', '')
    human = os.environ.get('WORKFLOW_HUMAN_LOGIN', '')
    api = GitHub(repo, token)
    import subprocess
    base = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()
    errors = Validator(ROOT, base).run()
    if errors: raise ValueError('main workflow data invalid: ' + '; '.join(errors))
    reconcile(api, ROOT, base, consumer, human, None)


if __name__ == '__main__':
    try: main()
    except Exception as exc:
        print(f'task reconciliation failed: {exc}', file=sys.stderr)
        sys.exit(1)
