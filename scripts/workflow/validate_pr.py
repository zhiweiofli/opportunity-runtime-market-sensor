#!/usr/bin/env python3
"""Validate PR data through GitHub APIs without checking out or executing PR code."""
import base64
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

from check_paths import allowed
from check_scope import check_scope
from github_evidence import GitHub, check_changes, pr_type, set_status, status_description
from validate import LAYOUT, Validator

ROOT = Path(__file__).resolve().parents[2]
MAX_BLOB = 4 * 1024 * 1024


def materialize(api, root, merge_commit, changes, target):
    """Copy trusted data and overlay only changed business data blobs as non-executable files."""
    for name in ('opportunities', 'practice'):
        source = root / name
        if source.exists(): shutil.copytree(source, target / name, symlinks=True)
    (target / '.git').symlink_to(root / '.git', target_is_directory=True)
    changed_data = [(status, path) for status, path in changes if path.startswith(('opportunities/', 'practice/'))]
    if not changed_data: return
    commit = api.get(f'git/commits/{merge_commit}')
    tree = api.get(f'git/trees/{commit["tree"]["sha"]}?recursive=1')
    if tree.get('truncated'): raise ValueError('proposal tree is truncated')
    entries = {entry['path']: entry for entry in tree.get('tree', [])}
    total = 0
    for status, path in changed_data:
        if not any(pattern.fullmatch(path) for pattern in LAYOUT.values()) and not (path.startswith('practice/results/') and path.endswith('/report.md')):
            raise ValueError('unrecognized business data file')
        entry = entries.get(path)
        if status not in ('A', 'M') or not entry or entry.get('type') != 'blob' or entry.get('mode') not in ('100644', '100755'):
            raise ValueError('business data must be a regular file')
        parent = target
        for part in Path(path).parts[:-1]:
            parent = parent / part
            if parent.is_symlink(): raise ValueError('symlink in business data path')
            parent.mkdir(exist_ok=True)
        destination = target / path
        if destination.is_symlink(): raise ValueError('symlink in business data path')
        if (status == 'A' and destination.exists()) or (status == 'M' and not destination.is_file()):
            raise ValueError('proposal file status does not match current main')
        blob = api.get('git/blobs/' + entry['sha'])
        if blob.get('encoding') != 'base64' or blob.get('size', MAX_BLOB + 1) > MAX_BLOB:
            raise ValueError('business data blob is too large or unsupported')
        total += blob['size']
        if total > 20 * 1024 * 1024: raise ValueError('proposal business data exceeds size limit')
        encoded = ''.join(blob['content'].split())
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) != blob['size']: raise ValueError('business data blob size mismatch')
        destination.write_bytes(raw)


def validate(api, root, base, default_branch, number, human):
    pr = api.get(f'pulls/{number}')
    for _ in range(3):
        if pr.get('mergeable') is not None: break
        time.sleep(2)
        pr = api.get(f'pulls/{number}')
    if pr.get('state') != 'open' or pr['base']['ref'] != default_branch:
        raise ValueError('PR must target the checked default-branch commit')
    if api.get('branches/' + quote(default_branch, safe=''))['commit']['sha'] != base:
        raise ValueError('default branch changed before validation')
    kind = pr_type(pr.get('body'))
    head = pr['head']['sha']
    merge = pr.get('merge_commit_sha')
    if pr.get('mergeable') is not True or not merge:
        raise ValueError('GitHub merge preview is unavailable or conflicts')
    merge_object = api.get(f'git/commits/{merge}')
    if [p['sha'] for p in merge_object.get('parents', [])] != [base, head]:
        raise ValueError('GitHub merge preview does not match current base and head')
    files = api.get(f'pulls/{number}/files', paginate=True)
    if not files or pr.get('changed_files') != len(files) or len(files) > 3000:
        raise ValueError('PR file list is empty or incomplete')
    status_map = {'added':'A', 'modified':'M', 'removed':'D'}
    changes = [(status_map.get(f['status'], '?'), f['filename']) for f in files]
    if any(status == '?' for status, _ in changes): raise ValueError('renames or unsupported change types require a separate PR')
    invalid = [f'{status} {path!r}' for status, path in changes if not allowed(kind, status, path)]
    if invalid: raise ValueError('disallowed paths: ' + ', '.join(invalid))
    if kind != 'implementation':
        with tempfile.TemporaryDirectory(prefix='or-pr-data-') as tmp:
            target = Path(tmp)
            materialize(api, root, merge, changes, target)
            errors = Validator(target, base).run()
            if errors: raise ValueError('workflow data invalid: ' + '; '.join(errors))
            check_scope(kind, changes, target)
            check_changes(target, base, changes, api, human)
    fresh = api.get(f'pulls/{number}')
    current_branch = api.get('branches/' + quote(default_branch, safe=''))
    if fresh.get('state') != 'open' or fresh['head']['sha'] != head or fresh['base']['ref'] != default_branch or fresh.get('body') != pr.get('body') or current_branch['commit']['sha'] != base:
        raise ValueError('PR or default branch changed during validation; retry')
    return head, pr.get('body')


def main():
    repo = os.environ.get('GITHUB_REPOSITORY', '')
    api = GitHub(repo, os.environ.get('GH_TOKEN', ''))
    default_branch = os.environ.get('DEFAULT_BRANCH', 'main')
    human = os.environ.get('WORKFLOW_HUMAN_LOGIN', '')
    base = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    event_name = os.environ.get('GITHUB_EVENT_NAME', '')
    target_number = None
    if event_name == 'pull_request_target':
        from validate import load_json
        event = load_json(Path(event_path).read_bytes())
        if event['pull_request']['base']['ref'] != default_branch: return
        target_number = int(event['pull_request']['number'])
    candidates = []
    for item in api.get('pulls?state=open', paginate=True):
        if item['base']['ref'] != default_branch: continue
        if item['number'] != target_number:
            try: pr_type(item.get('body'))
            except ValueError: continue
            statuses = api.get(f'commits/{item["head"]["sha"]}/status').get('statuses', [])
            prior = next((s for s in statuses if s.get('context') == f'opportunity/protocol/{item["number"]}'), None)
            if prior and (prior.get('creator') or {}).get('login', '').lower() == 'github-actions[bot]' and prior.get('state') == 'success' and prior.get('description') == status_description(base, item.get('body')):
                continue
        candidates.append(item)
    failures = []
    for pr in candidates:
        set_status(api, pr['head']['sha'], pr['number'], 'pending', 'Trusted-base validation is running')
    for pr in candidates:
        try:
            sha, body = validate(api, ROOT, base, default_branch, pr['number'], human)
            set_status(api, sha, pr['number'], 'success', status_description(base, body))
            print(f'PR #{pr["number"]}: validated against {base}')
        except Exception as exc:
            set_status(api, pr['head']['sha'], pr['number'], 'failure', 'Trusted-base protocol validation failed')
            failures.append(f'PR #{pr["number"]}: {exc}')
    if failures: raise ValueError('; '.join(failures))


if __name__ == '__main__':
    try: main()
    except Exception as exc:
        print(f'PR validation failed: {exc}', file=sys.stderr)
        sys.exit(1)
