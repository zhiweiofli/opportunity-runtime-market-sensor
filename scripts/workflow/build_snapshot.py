#!/usr/bin/env python3
"""Fetch GitHub facts and generate a sanitized static dashboard artifact."""
import argparse
import base64
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit

from github_evidence import GitHub, merged_addition, merged_task_version, pr_type, status_description, verify_main_facts
from issue_handoff import TASK_MARKER, bot, parsed
from projection import project
from validate import LAYOUT, Validator, load_json, parse_time, safe_path

ROOT = Path(__file__).resolve().parents[2]


def github_url(value, repo, kind):
    u = urlsplit(value or '')
    if u.scheme != 'https' or u.netloc != 'github.com' or u.query or u.fragment or not re.fullmatch('/' + re.escape(repo) + f'/{kind}/[0-9]+', u.path, re.IGNORECASE):
        raise ValueError('unexpected GitHub URL')
    return value


def latest_protocol_status(api, sha, number, base, body):
    statuses = api.get(f'commits/{sha}/statuses', paginate=True)
    trusted = [x for x in statuses if x.get('context') == f'opportunity/protocol/{number}' and (x.get('creator') or {}).get('login', '').lower() == 'github-actions[bot]' and x.get('created_at')]
    if not trusted: return False
    status = max(trusted, key=lambda x: (parse_time(x['created_at']), x.get('id', 0)))
    return status.get('state') == 'success' and status.get('description') == status_description(base, body)


def fetch_candidate(api, path, tree, schema):
    entry = tree.get(path)
    if not entry or entry.get('type') != 'blob' or entry.get('mode') not in ('100644', '100755'):
        raise ValueError('PR candidate is not a regular file')
    if not isinstance(entry.get('size'), int) or entry['size'] > 1000000:
        raise ValueError('PR candidate is too large or has unknown size')
    obj = api.get('git/blobs/' + entry['sha'])
    if obj.get('encoding') != 'base64' or obj.get('size', 0) > 1000000: raise ValueError('unsupported PR data file')
    raw = base64.b64decode(''.join(obj['content'].split()), validate=True)
    if len(raw) != obj['size']: raise ValueError('PR data size mismatch')
    record = load_json(raw)
    schema.validate(record)
    return record


def last_judge_at(root, now):
    manifest = root / 'or-archive/manifest.json'
    if not manifest.is_file() or manifest.is_symlink(): return None
    inventory = load_json(manifest.read_bytes()).get('entries', [])
    if any(x.get('sync_status') != 'mirrored' for x in inventory): return None
    entries = [x for x in inventory if (x.get('path') or '').startswith('or-archive/judge/')]
    if not entries: return None
    times = []
    for entry in entries:
        path = entry['path']
        if entry.get('sync_status') != 'mirrored' or not safe_path(path): return None
        file = root / path
        if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(root.resolve()): return None
        matches = re.findall(r'(?m)^Generated At:\s*([^\s]+)\s*$', file.read_text(encoding='utf-8'))
        if len(matches) != 1: return None
        try: value = parse_time(matches[0])
        except ValueError: return None
        if value > now: return None
        times.append(value)
    return max(times).isoformat()


def collect(api, root, base, human, now):
    validator = Validator(root, base, now)
    errors = validator.run()
    if errors: raise ValueError('main workflow data invalid: ' + '; '.join(errors))
    verify_main_facts(root, base, api, human, validator.records)
    data = {'opportunities': [], 'tasks': [], 'results': [], 'decisions': [], 'pull_requests': [], 'issues': {}, 'last_judge_at': None, 'last_pages_deploy_at': None, 'github_synced_at': None}
    for kind, types, target in [('opportunity', {'review'}, 'opportunities'), ('task', {'review', 'decision'}, 'tasks'), ('result', {'practice-result'}, 'results'), ('decision', {'decision'}, 'decisions')]:
        for path, record in validator.records[kind].values():
            pr = merged_task_version(root, base, path, api, human) if kind == 'task' else merged_addition(root, base, path, types, api, human)
            entry = {'data': record, 'merged_at': pr['merged_at'], 'url': github_url(pr['html_url'], api.repo, 'pull')}
            if kind == 'task':
                import hashlib
                entry['task_hash'] = hashlib.sha256(validator.raw[path]).hexdigest()
            data[target].append(entry)
    for pr in api.get('pulls?state=open', paginate=True):
        try: kind = pr_type(pr.get('body'))
        except ValueError: continue
        if kind not in ('review', 'practice-result', 'decision'): continue
        sha = pr['head']['sha']
        verified = latest_protocol_status(api, sha, pr['number'], base, pr.get('body'))
        item = {'kind': kind, 'verified': verified, 'execution_mode': None, 'url': github_url(pr['html_url'], api.repo, 'pull'), 'created_at': pr['created_at'], 'task_ids': [], 'opportunity_ids': [], 'public_opportunities': [], '_number': pr['number'], '_head': sha, '_body': pr.get('body')}
        if verified:
            modes = set()
            details = api.get(f'pulls/{pr["number"]}')
            if details.get('state') != 'open' or details['head']['sha'] != sha or details.get('body') != pr.get('body'):
                raise ValueError('PR changed during snapshot generation')
            if details.get('changed_files', 0) > 3000: raise ValueError('PR file list exceeds GitHub API limit')
            files = api.get(f'pulls/{pr["number"]}/files', paginate=True)
            if len(files) != details.get('changed_files'): raise ValueError('PR file list is incomplete')
            tree = None
            if kind == 'review':
                merge = details.get('merge_commit_sha')
                if details.get('mergeable') is not True or not merge: raise ValueError('PR merge preview unavailable')
                commit = api.get('git/commits/' + merge)
                if [p['sha'] for p in commit.get('parents', [])] != [base, sha]: raise ValueError('PR merge preview is stale')
                tree_data = api.get('git/trees/' + commit['tree']['sha'] + '?recursive=1')
                if tree_data.get('truncated'): raise ValueError('PR merge tree is truncated')
                tree = {x['path']: x for x in tree_data['tree']}
            for f in files:
                path = f['filename']
                m = LAYOUT['result'].fullmatch(path)
                if kind == 'practice-result' and m and f['status'] == 'added':
                    item['task_ids'].append(m.group(1))
                    task = validator.records['task'].get(m.group(1))
                    if not task: raise ValueError('result PR refers to an unknown task')
                    modes.add(task[1]['execution_mode'])
                m = LAYOUT['decision'].fullmatch(path)
                if kind == 'decision' and m and f['status'] == 'added':
                    item['opportunity_ids'].append(m.group(1))
                    opportunity = validator.records['opportunity'].get(m.group(1))
                    if not opportunity: raise ValueError('decision PR refers to an unknown opportunity')
                    modes.add(opportunity[1]['execution_mode'])
                m = LAYOUT['opportunity'].fullmatch(path)
                if kind == 'review' and m and f['status'] in ('added', 'modified'):
                    record = fetch_candidate(api, path, tree, validator.schemas['opportunity'])
                    if record['opportunity_id'] != m.group(1): raise ValueError('PR opportunity ID mismatch')
                    item['opportunity_ids'].append(m.group(1))
                    item['public_opportunities'].append(record)
                    modes.add(record['execution_mode'])
                m = LAYOUT['task'].fullmatch(path)
                if kind == 'review' and m and f['status'] in ('added', 'modified'):
                    record = fetch_candidate(api, path, tree, validator.schemas['task'])
                    if record['task_id'] != m.group(1): raise ValueError('PR task ID mismatch')
                    item['opportunity_ids'].append(record['opportunity_id'])
                    modes.add(record['execution_mode'])
            if len(modes) != 1: raise ValueError('validated PR has unknown or mixed execution mode')
            item['execution_mode'] = modes.pop()
        data['pull_requests'].append(item)
    for issue in api.get('issues?state=all', paginate=True):
        if issue.get('pull_request') or not bot(issue): continue
        markers = TASK_MARKER.findall(issue.get('body') or '')
        if len(markers) != 1: continue
        comments = api.get(f'issues/{issue["number"]}/comments', paginate=True)
        receipts = []
        for c in comments:
            kind, record = parsed(c)
            if bot(c) and kind == 'receipt' and isinstance(record, dict) and record.get('task_id') == markers[0]:
                receipts.append(record)
        data['issues'].setdefault(markers[0], []).append({'url': github_url(issue['html_url'], api.repo, 'issues'), 'state': issue['state'], 'receipts': receipts})
    data['last_judge_at'] = last_judge_at(root, now)
    deployments = api.get('deployments?environment=github-pages', paginate=True)
    successful_deployments = []
    for deploy in deployments:
        statuses = api.get(f'deployments/{deploy["id"]}/statuses', paginate=True)
        successful_deployments.extend(x['created_at'] for x in statuses if x.get('state') == 'success' and x.get('created_at'))
    if successful_deployments:
        data['last_pages_deploy_at'] = max(successful_deployments, key=parse_time)
    for item in data['pull_requests']:
        fresh = api.get(f'pulls/{item["_number"]}')
        if fresh.get('state') != 'open' or fresh['head']['sha'] != item['_head'] or fresh.get('body') != item['_body']:
            raise ValueError('PR changed during snapshot generation')
        if item['verified'] and not latest_protocol_status(api, item['_head'], item['_number'], base, item['_body']):
            raise ValueError('PR validation changed during snapshot generation')
    default_branch = os.environ.get('DEFAULT_BRANCH', 'main')
    if api.get('branches/' + quote(default_branch, safe=''))['commit']['sha'] != base:
        raise ValueError('default branch changed during snapshot generation')
    data['github_synced_at'] = now.isoformat()
    return data


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    human = os.environ.get('WORKFLOW_HUMAN_LOGIN', '')
    if not human: raise ValueError('WORKFLOW_HUMAN_LOGIN is required')
    api = GitHub(os.environ.get('GITHUB_REPOSITORY', ''), os.environ.get('GH_TOKEN', ''))
    base = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()
    now = datetime.now(timezone.utc)
    snapshot = project(collect(api, ROOT, base, human, now), now)
    target = Path(a.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + '.tmp')
    temporary.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(target)


if __name__ == '__main__':
    try: main()
    except Exception as exc:
        print(f'workflow snapshot failed: {exc}', file=sys.stderr)
        sys.exit(1)
