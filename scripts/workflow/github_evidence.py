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
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from validate import load_json, parse_time

MARKER = re.compile(r'(?m)^<!-- workflow-type: (review|practice-result|decision|archive|implementation) -->$')
DECISION = re.compile(r'\A<!-- or-decision -->\s*```json\s*\n(.*?)\n```\s*\Z', re.DOTALL)
TASK_MARKER = re.compile(r'(?m)^<!-- workflow-task: ([A-Za-z0-9][A-Za-z0-9_-]{0,127}) -->$')


def pr_type(body):
    matches = MARKER.findall(body or '')
    if len(matches) != 1:
        raise ValueError('PR body requires exactly one workflow-type marker')
    return matches[0]


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
            url = f'https://api.github.com/repos/{self.repo}/{endpoint}{suffix}'
            request = urllib.request.Request(url, headers={'Authorization': f'Bearer {self.token}', 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'opportunity-workflow'})
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.load(response)
            if not paginate: return data
            if not isinstance(data, list): raise ValueError('unexpected GitHub response')
            output.extend(data)
            if len(data) < 100: return output
            page += 1

    def post(self, endpoint, body):
        url = f'https://api.github.com/repos/{self.repo}/{endpoint}'
        request = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), method='POST', headers={'Authorization': f'Bearer {self.token}', 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'opportunity-workflow'})
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def merged_addition(root, base, path, types, api):
    log = git(root, 'log', '--first-parent', '-m', '--diff-filter=A', '--format=%H', base, '--', path)
    if log.returncode: raise ValueError('could not inspect input history')
    for commit in dict.fromkeys(log.stdout.splitlines()):
        for summary in api.get(f'commits/{commit}/pulls', paginate=True):
            pr = api.get(f'pulls/{summary["number"]}')
            if not pr.get('merged_at') or not pr.get('merged_by') or not pr.get('merge_commit_sha'):
                continue
            if git(root, 'merge-base', '--is-ancestor', pr['merge_commit_sha'], base).returncode:
                continue
            try:
                if pr_type(pr.get('body')) not in types: continue
            except ValueError:
                continue
            files = api.get(f'pulls/{pr["number"]}/files', paginate=True)
            if any(x.get('filename') == path and x.get('status') == 'added' for x in files):
                return pr
    raise ValueError(f'no merged authorized PR adding {path} in base history')


def on_first_parent(root, ancestor, head):
    history = git(root, 'rev-list', '--first-parent', head)
    return history.returncode == 0 and ancestor in set(history.stdout.splitlines())


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
    task_path = root / 'practice' / 'inbox' / markers[0] / 'task.json'
    if task_path.is_symlink() or not task_path.is_file(): raise ValueError('issue task not found')
    task = load_json(task_path.read_bytes())
    if task['opportunity_id'] != record['opportunity_id']: raise ValueError('issue task belongs to another opportunity')


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
    for status, path in zip(entries[:-1:2], entries[1:-1:2]):
        if status != 'A': continue
        if re.fullmatch(r'practice/results/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+/result\.json', path):
            record = load_json((root / path).read_bytes())
            pr = merged_addition(root, a.base, f'practice/inbox/{record["task_id"]}/task.json', {'review', 'decision'}, api)
            if not on_first_parent(root, record['input_commit'], a.base) or not on_first_parent(root, pr['merge_commit_sha'], record['input_commit']):
                raise ValueError('input commit must be on main after task approval')
        elif re.fullmatch(r'opportunities/[A-Za-z0-9_-]+/decisions/[A-Za-z0-9_-]+\.json', path):
            record = load_json((root / path).read_bytes())
            check_comment(record, api, a.human, root)
            if record['run_id']:
                result_path = next(iter((root / 'practice/results').glob(f'*/{record["run_id"]}/result.json')), None)
                if result_path is None: raise ValueError('decision result not found')
                merged_addition(root, a.base, result_path.relative_to(root).as_posix(), {'practice-result'}, api)
    print('GitHub evidence checks passed for new results and decisions.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f'GitHub evidence check failed: {exc}', file=sys.stderr)
        sys.exit(1)
