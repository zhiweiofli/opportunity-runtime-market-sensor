#!/usr/bin/env python3
"""Build decision PRs from authenticated, versioned issue comments."""
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
from pathlib import Path
from urllib.parse import quote, urlencode

from github_evidence import DECISION, GitHub, GitHubError, TASK_MARKER, check_comment, merged_addition, set_status, status_description
from issue_handoff import BOT, ROOT, bot
from validate import Validator, load_json, parse_time

KEYS = {'opportunity_id', 'action', 'run_id', 'reason', 'recovery_condition', 'new_task_id', 'project_url', 'new_task'}
ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$')


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def build_record(comment, human):
    body = comment.get('body')
    match = DECISION.fullmatch(body or '')
    if not match: raise ValueError('invalid decision block')
    data = load_json(match[1])
    if not isinstance(data, dict) or set(data) != KEYS: raise ValueError('invalid decision fields')
    if not isinstance(data['opportunity_id'], str) or not ID.fullmatch(data['opportunity_id']): raise ValueError('invalid opportunity ID')
    if data['action'] not in ('launch', 'continue', 'pause', 'close'): raise ValueError('invalid action')
    if data['run_id'] is not None and (not isinstance(data['run_id'], str) or not ID.fullmatch(data['run_id'])): raise ValueError('invalid run ID')
    if data['action'] == 'continue':
        if not isinstance(data['new_task'], dict) or not isinstance(data['new_task_id'], str) or not ID.fullmatch(data['new_task_id']) or data['new_task'].get('task_id') != data['new_task_id']:
            raise ValueError('continue requires a matching new task')
    elif data['new_task'] is not None or data['new_task_id'] is not None:
        raise ValueError('only continue may provide a new task')
    body_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
    version = hashlib.sha256((body_hash + '\0' + comment['updated_at']).encode('utf-8')).hexdigest()[:16]
    decision_id = f'd-{comment["id"]}-{version}'
    record = {'schema_version': 1, 'decision_id': decision_id, 'opportunity_id': data['opportunity_id'], 'action': data['action'], 'reason': data['reason'], 'actor': human, 'decided_at': comment['updated_at'], 'source_issue_comment_url': comment['html_url'], 'source_comment_sha256': body_hash, 'run_id': data['run_id'], 'recovery_condition': data['recovery_condition'], 'new_task_id': data['new_task_id'], 'project_url': data['project_url']}
    return record, data['new_task']


def preflight(api, root, base, human, record, new_task):
    with tempfile.TemporaryDirectory(prefix='or-decision-') as tmp:
        subprocess.run(['git', 'clone', '--quiet', '--no-hardlinks', '--no-checkout', str(root), tmp], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        subprocess.run(['git', '-C', tmp, 'checkout', '--quiet', '--detach', base], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        sandbox = Path(tmp)
        path = f'opportunities/{record["opportunity_id"]}/decisions/{record["decision_id"]}.json'
        files = {path: encoded(record)}
        if new_task is not None:
            task_path = f'practice/inbox/{record["new_task_id"]}/task.json'
            if (sandbox / task_path).exists(): raise ValueError('new task ID already exists on main')
            files[task_path] = encoded(new_task)
        for name, content in files.items():
            p = sandbox / name
            if p.exists() or p.is_symlink(): raise ValueError('decision version already exists on main')
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(content)
        errors = Validator(sandbox, base).run()
        if errors: raise ValueError('decision proposal invalid: ' + '; '.join(errors))
        check_comment(record, api, human, sandbox)
        if record['run_id']:
            result = next(iter((sandbox / 'practice/results').glob(f'*/{record["run_id"]}/result.json')), None)
            if result is None: raise ValueError('result missing')
            result_pr = merged_addition(sandbox, base, result.relative_to(sandbox).as_posix(), {'practice-result'}, api)
            if parse_time(record['decided_at']) < parse_time(result_pr['merged_at']):
                raise ValueError('decision comment predates result acceptance')
        return files


def ensure_branch(api, root, base, branch, files):
    try:
        ref = api.get('git/ref/heads/' + branch)
    except GitHubError as exc:
        if exc.status != 404: raise
        commit = api.get(f'git/commits/{base}')
        tree = api.post('git/trees', {'base_tree': commit['tree']['sha'], 'tree': [{'path': path, 'mode': '100644', 'type': 'blob', 'content': content.decode('utf-8')} for path, content in files.items()]})
        created = api.post('git/commits', {'message': 'Propose human decision', 'tree': tree['sha'], 'parents': [base]})
        api.post('git/refs', {'ref': 'refs/heads/' + branch, 'sha': created['sha']})
        return
    sha = ref['object']['sha']
    commit = api.get(f'git/commits/{sha}')
    parents = commit.get('parents', [])
    if len(parents) != 1: raise ValueError('existing proposal branch is not a single decision commit')
    parent = parents[0]['sha']
    result = subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', parent, base], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode: raise ValueError('existing proposal branch is not based on main history')
    comparison = api.get(f'compare/{parent}...{sha}')
    changed = comparison.get('files', [])
    if len(changed) != len(files) or {(f['filename'], f['status']) for f in changed} != {(name, 'added') for name in files}:
        raise ValueError('existing proposal branch contains unexpected changes')
    for name, expected in files.items():
        obj = api.get('contents/' + quote(name, safe='/') + '?' + urlencode({'ref': branch}))
        if obj.get('encoding') != 'base64' or base64.b64decode(obj['content']) != expected:
            raise ValueError('existing proposal branch content differs')


def propose(api, root, base, branch_base, human, comment):
    record, new_task = build_record(comment, human)
    branch = 'codex/decision-' + record['decision_id']
    owner = api.repo.split('/')[0]
    params = urlencode({'state': 'all', 'head': owner + ':' + branch, 'base': branch_base})
    existing = api.get('pulls?' + params, paginate=True)
    if existing and existing[0].get('state') != 'open':
        return existing[0]
    files = preflight(api, root, base, human, record, new_task)
    ensure_branch(api, root, base, branch, files)
    ref = api.get('git/ref/heads/' + branch)
    if existing:
        pr = existing[0]
    else:
        summary = f"<!-- workflow-type: decision -->\n\n由 {record['source_issue_comment_url']} 提出的 `{record['action']}` 决定。机会 `{record['opportunity_id']}`；结果 `{record['run_id'] or '无'}`。请核对评论版本、理由和所有文件后合并；创建 PR 不代表决定已生效。"
        pr = api.post('pulls', {'title': f"Decision: {record['action']} {record['opportunity_id']}", 'head': branch, 'base': branch_base, 'body': summary})
    set_status(api, ref['object']['sha'], pr['number'], 'success', status_description(base, pr.get('body', summary if not existing else '')))
    return pr


def invalidate_old_versions(api, pull_requests, comment):
    try:
        record, _ = build_record(comment, '')
        current = 'codex/decision-' + record['decision_id']
    except (ValueError, KeyError, TypeError):
        current = None
    prefix = f'codex/decision-d-{comment["id"]}-'
    for pr in pull_requests:
        head = pr.get('head') or {}
        name = head.get('ref', '')
        if name.startswith(prefix) and name != current and head.get('sha'):
            set_status(api, head['sha'], pr['number'], 'failure', 'Source decision comment has changed')


def invalidate_missing_comments(api, pull_requests, seen):
    for pr in pull_requests:
        head = pr.get('head') or {}
        match = re.fullmatch(r'codex/decision-d-([0-9]+)-[0-9a-f]{16}', head.get('ref', ''))
        if match and int(match[1]) not in seen and head.get('sha'):
            set_status(api, head['sha'], pr['number'], 'failure', 'Source decision comment is unavailable')


def main():
    human = os.environ.get('WORKFLOW_HUMAN_LOGIN', '')
    if not human or human.lower() == BOT:
        raise ValueError('WORKFLOW_HUMAN_LOGIN must identify a human account')
    repo = os.environ.get('GITHUB_REPOSITORY', '')
    api = GitHub(repo, os.environ.get('GH_TOKEN', ''))
    branch_base = os.environ.get('DEFAULT_BRANCH', 'main')
    base = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()
    errors = Validator(ROOT, base).run()
    if errors: raise ValueError('main workflow data invalid: ' + '; '.join(errors))
    failures = []
    open_prs = api.get('pulls?state=open', paginate=True)
    seen = set()
    for issue in api.get('issues?state=all', paginate=True):
        if issue.get('pull_request') or not bot(issue) or len(TASK_MARKER.findall(issue.get('body') or '')) != 1: continue
        for comment in api.get(f'issues/{issue["number"]}/comments', paginate=True):
            author = (comment.get('user') or {}).get('login', '').lower()
            if author != human.lower(): continue
            seen.add(comment['id'])
            try:
                invalidate_old_versions(api, open_prs, comment)
                if not (comment.get('body') or '').startswith('<!-- or-decision -->'): continue
                pr = propose(api, ROOT, base, branch_base, human, comment)
                print(f'decision comment {comment["id"]}: PR #{pr["number"]}')
            except (ValueError, KeyError, OSError, urllib.error.URLError, subprocess.CalledProcessError) as exc:
                for pr in open_prs:
                    head = pr.get('head') or {}
                    if head.get('ref', '').startswith(f'codex/decision-d-{comment["id"]}-') and head.get('sha'):
                        set_status(api, head['sha'], pr['number'], 'failure', 'Decision validation failed')
                failures.append(f'comment {comment["id"]}: {exc}')
    invalidate_missing_comments(api, open_prs, seen)
    if failures: raise ValueError('; '.join(failures))


if __name__ == '__main__':
    try: main()
    except Exception as exc:
        print(f'decision reconciliation failed: {exc}', file=sys.stderr)
        sys.exit(1)
