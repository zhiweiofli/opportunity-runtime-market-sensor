#!/usr/bin/env python3
"""Check merged input and human comment facts through the GitHub API."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

from validate import load_json, parse_time

MARKER = re.compile(r'(?m)^<!-- workflow-type: (review|practice-result|decision|archive|implementation) -->$')
DECISION = re.compile(r'\A<!-- or-decision -->\s*```json\s*\n(.*?)\n```\s*\Z', re.DOTALL)
TASK_MARKER = re.compile(r'(?m)^<!-- workflow-task: ([A-Za-z0-9][A-Za-z0-9_-]{0,127}) -->$')
EVENT_BLOCK = re.compile(r'\A<!-- or-(request|receipt|recover) -->\s*```json\s*\n(.*?)\n```\s*\Z', re.DOTALL)


def pr_type(body):
    matches = MARKER.findall(body or '')
    if len(matches) != 1:
        raise ValueError('PR body requires exactly one workflow-type marker')
    return matches[0]


class GitHubError(ValueError):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class GitHub:
    def __init__(self, repo, token):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo) or not token:
            raise ValueError('repository and GitHub token are required')
        self.repo, self.token = repo, token

    def get(self, endpoint, paginate=False):
        output = []
        page = 1
        while True:
            suffix = ('&' if '?' in endpoint else '?') + f'per_page=100&page={page}' if paginate else ''
            data = self.request('GET', endpoint + suffix)
            if not paginate: return data
            if not isinstance(data, list): raise ValueError('unexpected GitHub response')
            output.extend(data)
            if len(data) < 100: return output
            page += 1

    def post(self, endpoint, body):
        return self.request('POST', endpoint, body)

    def request(self, method, endpoint, body=None):
        args = ['gh', 'api', '--method', method, '-H', 'Accept: application/vnd.github+json', '-H', 'X-GitHub-Api-Version: 2022-11-28', f'repos/{self.repo}/{endpoint}']
        if body is not None: args.extend(['--input', '-'])
        result = subprocess.run(args, input=json.dumps(body) if body is not None else None, text=True, capture_output=True, timeout=60, env={**os.environ, 'GH_TOKEN': self.token})
        if result.returncode:
            match = re.search(r'HTTP (\d{3})', result.stderr)
            raise GitHubError(result.stderr.strip() or 'GitHub API request failed', int(match[1]) if match else None)
        return json.loads(result.stdout) if result.stdout.strip() else None


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def status_description(base, body):
    return 'b:' + base + ';p:' + hashlib.sha256((body or '').encode('utf-8')).hexdigest()


def protocol_passed_at_merge(api, pr, root):
    head = (pr.get('head') or {}).get('sha')
    merge = pr.get('merge_commit_sha')
    if not head or not merge or not pr.get('merged_at'): return False
    parent = git(root, 'rev-parse', '--verify', f'{merge}^1')
    if parent.returncode: return False
    second_parent = git(root, 'rev-parse', '--verify', f'{merge}^2')
    if second_parent.returncode == 0:
        head = second_parent.stdout.strip()
    validated_base = parent.stdout.strip()
    merged = parse_time(pr['merged_at'])
    statuses = api.get(f'commits/{head}/statuses', paginate=True)
    relevant = [s for s in statuses if s.get('context') == f'opportunity/protocol/{pr["number"]}'
                and (s.get('creator') or {}).get('login', '').lower() == 'github-actions[bot]'
                and s.get('created_at') and parse_time(s['created_at']) < merged]
    if not relevant: return False
    status = max(relevant, key=lambda s: (parse_time(s['created_at']), s.get('id', 0)))
    return status.get('state') == 'success' and status.get('description') == status_description(validated_base, pr.get('body'))


def set_status(api, sha, number, state, description):
    context = f'opportunity/protocol/{number}'
    existing = api.get(f'commits/{sha}/status').get('statuses', [])
    current = next((s for s in existing if s.get('context') == context), None)
    if current and (current.get('creator') or {}).get('login', '').lower() == 'github-actions[bot]' and current.get('state') == state and current.get('description') == description:
        return
    status = {'state': state, 'context': context, 'description': description}
    server, repo, run = (os.environ.get(k) for k in ('GITHUB_SERVER_URL', 'GITHUB_REPOSITORY', 'GITHUB_RUN_ID'))
    if server and repo and run: status['target_url'] = f'{server}/{repo}/actions/runs/{run}'
    api.post(f'statuses/{sha}', status)


def merged_addition(root, base, path, types, api, human=None):
    human = human or os.environ.get('WORKFLOW_HUMAN_LOGIN', '')
    if not human or human.lower() == 'github-actions[bot]':
        raise ValueError('WORKFLOW_HUMAN_LOGIN must identify the configured human')
    log = git(root, 'log', '--first-parent', '-m', '--diff-filter=A', '--format=%H', base, '--', path)
    if log.returncode: raise ValueError('could not inspect input history')
    for commit in dict.fromkeys(log.stdout.splitlines()):
        for summary in api.get(f'commits/{commit}/pulls', paginate=True):
            pr = api.get(f'pulls/{summary["number"]}')
            if not pr.get('merged_at') or not pr.get('merged_by') or not pr.get('merge_commit_sha'):
                continue
            if pr['merged_by'].get('login', '').lower() != human.lower():
                continue
            if (pr.get('base') or {}).get('ref') != os.environ.get('DEFAULT_BRANCH', 'main') or not on_first_parent(root, pr['merge_commit_sha'], base):
                continue
            try:
                if pr_type(pr.get('body')) not in types: continue
            except ValueError:
                continue
            if not protocol_passed_at_merge(api, pr, root):
                continue
            files = api.get(f'pulls/{pr["number"]}/files', paginate=True)
            if any(x.get('filename') == path and x.get('status') == 'added' for x in files):
                return pr
    raise ValueError(f'no merged authorized PR adding {path} in base history')


def on_first_parent(root, ancestor, head):
    history = git(root, 'rev-list', '--first-parent', head)
    return history.returncode == 0 and ancestor in set(history.stdout.splitlines())


def merged_current_version(root, base, path, api, human, accepted):
    """Find the validated PR for the latest main-branch change of a record."""
    human = human or os.environ.get('WORKFLOW_HUMAN_LOGIN', '')
    if not human or human.lower() == 'github-actions[bot]':
        raise ValueError('WORKFLOW_HUMAN_LOGIN must identify the configured human')
    history = git(root, '--literal-pathspecs', 'log', '--first-parent', '-m', '--format=%H', base, '--', path)
    if history.returncode: raise ValueError('could not inspect task history')
    for commit in dict.fromkeys(history.stdout.splitlines()):
        for summary in api.get(f'commits/{commit}/pulls', paginate=True):
            pr = api.get(f'pulls/{summary["number"]}')
            merge = pr.get('merge_commit_sha')
            if not pr.get('merged_at') or (pr.get('merged_by') or {}).get('login', '').lower() != human.lower() or (pr.get('base') or {}).get('ref') != os.environ.get('DEFAULT_BRANCH', 'main') or not merge or not on_first_parent(root, merge, base):
                continue
            try: kind = pr_type(pr.get('body'))
            except ValueError: continue
            if kind not in accepted or not protocol_passed_at_merge(api, pr, root): continue
            later = git(root, '--literal-pathspecs', 'log', '--first-parent', '-m', '--format=%H', f'{merge}..{base}', '--', path)
            if later.returncode or later.stdout.strip(): continue
            files = api.get(f'pulls/{pr["number"]}/files', paginate=True)
            if any(f.get('filename') == path and f.get('status') in accepted[kind] for f in files):
                return pr
    raise ValueError(f'latest record version lacks a validated human-merged PR: {path}')


def merged_task_version(root, base, path, api, human=None):
    return merged_current_version(root, base, path, api, human, {'review': {'added', 'modified'}, 'decision': {'added'}})


def merged_opportunity_version(root, base, path, api, human=None):
    return merged_current_version(root, base, path, api, human, {'review': {'added', 'modified'}})


def check_comment(record, api, human, root):
    if not human:
        raise ValueError('WORKFLOW_HUMAN_LOGIN is not configured')
    url = urlsplit(record['source_issue_comment_url'])
    match = re.fullmatch(r'/([^/]+)/([^/]+)/issues/(\d+)', url.path)
    fragment = re.fullmatch(r'issuecomment-(\d+)', url.fragment)
    if url.scheme != 'https' or url.netloc != 'github.com' or not match or not fragment or f'{match[1]}/{match[2]}'.lower() != api.repo.lower() or url.query:
        raise ValueError('decision comment URL must identify an issue comment in this repository')
    comment = api.get(f'issues/comments/{fragment[1]}')
    if (comment.get('user') or {}).get('login', '').lower() != human.lower() or record['actor'].lower() != human.lower():
        raise ValueError('comment actor is not the configured human')
    if not comment.get('issue_url', '').endswith(f'/issues/{match[3]}'):
        raise ValueError('comment belongs to another issue')
    body = comment.get('body')
    if not isinstance(body, str) or hashlib.sha256(body.encode('utf-8')).hexdigest() != record['source_comment_sha256']:
        raise ValueError('comment content has changed or hash is wrong')
    if parse_time(record['decided_at']) != parse_time(comment['updated_at']):
        raise ValueError('decision time does not match latest comment version')
    match_body = DECISION.fullmatch(body)
    if not match_body: raise ValueError('invalid structured decision comment')
    data = load_json(match_body[1])
    keys = ('opportunity_id', 'action', 'run_id', 'reason', 'recovery_condition', 'new_task_id', 'project_url')
    if set(data) != set(keys) | {'new_task'} or any(data[k] != record[k] for k in keys):
        raise ValueError('decision differs from structured comment')
    if record['action'] == 'continue':
        proposed = root / 'practice' / 'inbox' / record['new_task_id'] / 'task.json'
        if proposed.is_symlink() or not proposed.is_file() or load_json(proposed.read_bytes()) != data['new_task']:
            raise ValueError('new task differs from structured comment')
    elif data['new_task'] is not None:
        raise ValueError('new_task is only allowed for continue')
    issue = api.get(f'issues/{match[3]}')
    owner = issue.get('user') or {}
    if owner.get('login', '').lower() != 'github-actions[bot]' or owner.get('type') != 'Bot':
        raise ValueError('issue is not a center-created task issue')
    markers = TASK_MARKER.findall(issue.get('body') or '')
    if len(markers) != 1: raise ValueError('issue does not identify one task')
    matches = []
    for candidate in api.get('issues?state=all', paginate=True):
        creator = candidate.get('user') or {}
        if candidate.get('pull_request') or creator.get('login', '').lower() != 'github-actions[bot]' or creator.get('type') != 'Bot':
            continue
        if TASK_MARKER.findall(candidate.get('body') or '') == markers:
            matches.append(candidate.get('number'))
    if matches != [int(match[3])]: raise ValueError('task issue mapping is missing or ambiguous')
    task_path = root / 'practice' / 'inbox' / markers[0] / 'task.json'
    if task_path.is_symlink() or not task_path.is_file(): raise ValueError('issue task not found')
    task = load_json(task_path.read_bytes())
    if task['opportunity_id'] != record['opportunity_id']: raise ValueError('issue task belongs to another opportunity')


def decision_comment_at_merge(record, pr, api, human, root):
    """Keep merged decisions immutable while rejecting comments changed before merge."""
    if parse_time(record['decided_at']) > parse_time(pr['merged_at']):
        raise ValueError('decision comment was created after PR merge')
    url = urlsplit(record['source_issue_comment_url'])
    match = re.fullmatch(r'/([^/]+)/([^/]+)/issues/(\d+)', url.path)
    fragment = re.fullmatch(r'issuecomment-(\d+)', url.fragment)
    if url.scheme != 'https' or url.netloc != 'github.com' or not match or not fragment or f'{match[1]}/{match[2]}'.lower() != api.repo.lower() or url.query:
        raise ValueError('decision comment URL must identify an issue comment in this repository')
    comment = api.get(f'issues/comments/{fragment[1]}')
    if (comment.get('user') or {}).get('login', '').lower() != human.lower() or record['actor'].lower() != human.lower():
        raise ValueError('decision comment actor is not the configured human')
    if not comment.get('issue_url', '').endswith(f'/issues/{match[3]}'):
        raise ValueError('decision comment belongs to another issue')
    if parse_time(comment['updated_at']) <= parse_time(pr['merged_at']):
        check_comment(record, api, human, root)


def verify_run_receipts(api, result, task, human):
    """Require each declared execution interval to be covered by authenticated leases."""
    task_id, run_id = result['task_id'], result['run_id']
    issues = []
    for issue in api.get('issues?state=all', paginate=True):
        owner = issue.get('user') or {}
        if issue.get('pull_request') or owner.get('login', '').lower() != 'github-actions[bot]' or owner.get('type') != 'Bot': continue
        if TASK_MARKER.findall(issue.get('body') or '') == [task_id]: issues.append(issue)
    if len(issues) != 1: raise ValueError('result task issue mapping is missing or ambiguous')
    comments = api.get(f'issues/{issues[0]["number"]}/comments', paginate=True)
    by_id = {c['id']: c for c in comments}
    events, seen = [], set()
    request_types = {'accepted':'claim', 'heartbeat':'heartbeat', 'blocked':'blocked', 'resumed':'resume', 'released':'released'}
    for comment in comments:
        author = comment.get('user') or {}
        match = EVENT_BLOCK.fullmatch(comment.get('body') or '')
        if not match or match[1] != 'receipt' or author.get('login', '').lower() != 'github-actions[bot]' or author.get('type') != 'Bot': continue
        receipt = load_json(match[2])
        if not isinstance(receipt, dict) or receipt.get('task_id') != task_id or receipt.get('run_id') != run_id or receipt.get('event_type') == 'rejected': continue
        kind = receipt.get('event_type')
        if kind not in request_types or receipt.get('execution_mode') != task['execution_mode'] or receipt.get('task_hash') != result['task_hash']:
            raise ValueError('run receipt type, mode or task hash is invalid')
        rid = receipt.get('request_comment_id')
        if rid in seen or rid not in by_id: raise ValueError('run receipt request is missing or duplicated')
        seen.add(rid)
        request_comment = by_id[rid]
        body = request_comment.get('body') or ''
        request = EVENT_BLOCK.fullmatch(body)
        actor = (request_comment.get('user') or {}).get('login', '').lower()
        if not request or request[1] not in ('request', 'recover') or not actor or actor != (receipt.get('request_actor') or '').lower() or hashlib.sha256(body.encode('utf-8')).hexdigest() != receipt.get('request_sha256'):
            raise ValueError('run receipt does not match its immutable request and actor')
        payload = load_json(request[2])
        if not isinstance(payload, dict) or payload.get('task_id') != task_id or payload.get('run_id') != run_id:
            raise ValueError('run request does not match the result')
        if request[1] == 'recover':
            if kind != 'released' or actor != human.lower(): raise ValueError('recovery receipt actor is invalid')
        elif payload.get('event_type') != request_types[kind] or payload.get('task_hash') != result['task_hash'] or payload.get('agent_id') != receipt.get('agent_id') or payload.get('event_id') != receipt.get('event_id'):
            raise ValueError('run receipt differs from its request')
        recorded = parse_time(receipt['timestamp'])
        posted = parse_time(comment['created_at'])
        if parse_time(request_comment['created_at']) > posted: raise ValueError('receipt predates its request')
        if recorded < parse_time(request_comment['created_at']) - timedelta(seconds=60) or recorded > posted + timedelta(seconds=60):
            raise ValueError('receipt timestamp does not match GitHub comment chronology')
        events.append((max(recorded, posted), kind, receipt, actor, request[1]))
    if not events: raise ValueError('result has no authenticated claim receipt')
    segments, state, start, expiry, agent, run_agent = [], None, None, None, None, None
    previous, run_actor = None, None
    for timestamp, kind, receipt, actor, request_kind in events:
        if previous and timestamp < previous: raise ValueError('run receipt times are not ordered')
        previous = timestamp
        if kind == 'accepted':
            if state is not None or parse_time(receipt['started_at']) != parse_time(receipt['timestamp']): raise ValueError('invalid claim receipt sequence')
            state, start, expiry, agent = 'active', timestamp, parse_time(receipt['lease_until']), receipt['agent_id']
            if run_agent is not None and agent != run_agent: raise ValueError('run agent changed across recoveries')
            if run_actor is not None and actor != run_actor: raise ValueError('run consumer changed across recoveries')
            run_agent = agent
            run_actor = actor
            if expiry <= start: raise ValueError('invalid lease expiry')
            continue
        if state is None or receipt.get('agent_id') != agent: raise ValueError('run receipt has no matching lease')
        if request_kind == 'request' and actor != run_actor: raise ValueError('run receipt actor changed')
        if kind != 'released' and timestamp > expiry: raise ValueError('lease event occurred after expiry')
        segments.append((start, min(timestamp, expiry), state))
        if kind == 'released':
            state, start, expiry = None, None, None
            continue
        if kind == 'blocked':
            if state != 'active': raise ValueError('duplicate block receipt')
            state = 'blocked'
        elif kind == 'resumed':
            if state != 'blocked': raise ValueError('resume without block')
            state = 'active'
        start, expiry = timestamp, parse_time(receipt['lease_until'])
        if expiry <= start: raise ValueError('invalid lease renewal')
    if state is not None: segments.append((start, expiry, state))
    for interval in result['execution_intervals']:
        begin, end = parse_time(interval['started_at']), parse_time(interval['finished_at'])
        cursor = begin
        covered = False
        for left, right, status in segments:
            if status == 'blocked' and result['outcome'] != 'blocked': continue
            if left <= cursor <= right:
                cursor = max(cursor, right)
                if cursor >= end:
                    covered = True
                    break
        if not covered: raise ValueError('execution interval is not covered by an authorized lease')


def verify_main_facts(root, base, api, human, records):
    """Refuse to consume results or decisions lacking verified main-branch provenance."""
    for path, _ in records['opportunity'].values():
        merged_opportunity_version(root, base, path, api, human)
    for path, _ in records['task'].values():
        merged_task_version(root, base, path, api, human)
    for path, result in records['result'].values():
        result_pr = merged_addition(root, base, path, {'practice-result'}, api, human)
        task_pr = merged_task_version(root, base, f'practice/inbox/{result["task_id"]}/task.json', api, human)
        if not on_first_parent(root, result['input_commit'], base) or not on_first_parent(root, task_pr['merge_commit_sha'], result['input_commit']):
            raise ValueError(f'{path}: result input does not follow task approval on main')
        if parse_time(result['started_at']) < parse_time(task_pr['merged_at']) or parse_time(result_pr['merged_at']) < parse_time(result['finished_at']):
            raise ValueError(f'{path}: result chronology does not match merged PRs')
        task = records['task'][result['task_id']][1]
        verify_run_receipts(api, result, task, human)
    for path, decision in records['decision'].values():
        pr = merged_addition(root, base, path, {'decision'}, api, human)
        decision_comment_at_merge(decision, pr, api, human, root)
        if decision['run_id']:
            entry = records['result'].get(decision['run_id'])
            if not entry: raise ValueError(f'{path}: referenced result missing')
            result_pr = merged_addition(root, base, entry[0], {'practice-result'}, api, human)
            if parse_time(decision['decided_at']) < parse_time(result_pr['merged_at']):
                raise ValueError(f'{path}: decision comment predates result acceptance')


def check_changes(root, base, changes, api, human):
    root = Path(root).resolve()
    new_result_tasks = set()
    for status, path in changes:
        record_match = re.fullmatch(r'(?:practice/inbox/[A-Za-z0-9_-]+/task\.json|opportunities/[A-Za-z0-9_-]+/opportunity\.json)', path)
        if status == 'M' and record_match:
            original = git(root, 'show', f'{base}:{path}')
            if original.returncode or load_json(original.stdout).get('execution_mode') != load_json((root / path).read_bytes()).get('execution_mode'):
                raise ValueError('execution mode is immutable; create a separate record')
        task_match = re.fullmatch(r'practice/inbox/([A-Za-z0-9_-]+)/task\.json', path)
        if status == 'M' and task_match:
            prior = git(root, '--literal-pathspecs', 'ls-tree', '-r', '--name-only', base, '--', f'practice/results/{task_match[1]}/')
            if prior.returncode or any(x.endswith('/result.json') for x in prior.stdout.splitlines()):
                raise ValueError('completed tasks cannot be changed; create a new task')
        if status != 'A': continue
        if re.fullmatch(r'practice/results/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+/result\.json', path):
            record = load_json((root / path).read_bytes())
            task_id = record['task_id']
            if task_id in new_result_tasks:
                raise ValueError('a task cannot accept multiple result runs in one PR')
            new_result_tasks.add(task_id)
            prior = git(root, '--literal-pathspecs', 'ls-tree', '-r', '--name-only', base, '--', f'practice/results/{task_id}/')
            if prior.returncode or any(x.endswith('/result.json') for x in prior.stdout.splitlines()):
                raise ValueError('task already has an accepted result or its history cannot be read')
            pr = merged_task_version(root, base, f'practice/inbox/{record["task_id"]}/task.json', api, human)
            if not on_first_parent(root, record['input_commit'], base) or not on_first_parent(root, pr['merge_commit_sha'], record['input_commit']):
                raise ValueError('input commit must be on main after task approval')
            if parse_time(record['started_at']) < parse_time(pr['merged_at']):
                raise ValueError('run started before latest task approval')
            task = load_json((root / 'practice' / 'inbox' / task_id / 'task.json').read_bytes())
            verify_run_receipts(api, record, task, human)
        elif re.fullmatch(r'opportunities/[A-Za-z0-9_-]+/decisions/[A-Za-z0-9_-]+\.json', path):
            record = load_json((root / path).read_bytes())
            check_comment(record, api, human, root)
            if record['run_id']:
                result_path = next(iter((root / 'practice/results').glob(f'*/{record["run_id"]}/result.json')), None)
                if result_path is None: raise ValueError('decision result not found')
                result_pr = merged_addition(root, base, result_path.relative_to(root).as_posix(), {'practice-result'}, api, human)
                if parse_time(record['decided_at']) < parse_time(result_pr['merged_at']):
                    raise ValueError('decision comment predates result acceptance')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', default='.')
    p.add_argument('--base', required=True)
    p.add_argument('--head', required=True)
    p.add_argument('--repo', required=True)
    p.add_argument('--human', default=os.environ.get('WORKFLOW_HUMAN_LOGIN', ''))
    a = p.parse_args()
    root = Path(a.root).resolve()
    api = GitHub(a.repo, os.environ.get('GH_TOKEN', ''))
    diff = git(root, 'diff', '--no-renames', '--name-status', '-z', a.base, a.head, '--')
    if diff.returncode: raise ValueError('cannot read PR diff')
    entries = diff.stdout.split('\0')
    if entries[-1] != '' or len(entries[:-1]) % 2: raise ValueError('malformed diff')
    check_changes(root, a.base, list(zip(entries[:-1:2], entries[1:-1:2])), api, a.human)
    print('GitHub evidence checks passed for new results and decisions.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f'GitHub evidence check failed: {exc}', file=sys.stderr)
        sys.exit(1)
