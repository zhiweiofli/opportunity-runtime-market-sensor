#!/usr/bin/env python3
"""Check the business entity scope of a PR after path and data validation."""
import argparse
import subprocess
import sys
from pathlib import Path
from check_paths import EVIDENCE
from validate import LAYOUT, load_json


def check_scope(kind, changes, root):
    root = Path(root)
    opportunities, tasks, decisions, results, reports, evidence = set(), [], [], [], [], []
    for status, path in changes:
        for name, pattern in LAYOUT.items():
            match = pattern.fullmatch(path)
            if not match: continue
            record = load_json((root / path).read_bytes())
            if name == 'opportunity': opportunities.add(record['opportunity_id'])
            elif name == 'task': tasks.append((status, record)); opportunities.add(record['opportunity_id'])
            elif name == 'decision': decisions.append(record)
            elif name == 'result': results.append((match.group(1), match.group(2)))
        if EVIDENCE.fullmatch(path):
            parts = path.split('/')
            evidence.append((parts[2], parts[3]))
        elif path.startswith('practice/results/') and path.endswith('/report.md'):
            parts = path.split('/')
            reports.append((parts[2], parts[3]))
    if kind == 'review':
        if len(opportunities) != 1: raise ValueError('review must address exactly one opportunity')
        oid = next(iter(opportunities))
        opportunity = load_json((root / 'opportunities' / oid / 'opportunity.json').read_bytes())
        if tasks and opportunity['judge_recommendation'] in ('WATCH', 'DROP'):
            raise ValueError('WATCH/DROP cannot create or change a practice task')
    elif kind == 'practice-result':
        if len(results) != 1 or reports != results or any(item != results[0] for item in evidence): raise ValueError('result PR must add exactly one result and its report and evidence')
    elif kind == 'decision':
        if len(decisions) != 1: raise ValueError('decision PR must add exactly one decision')
        d = decisions[0]
        if d['action'] == 'continue':
            if len(tasks) != 1 or tasks[0][0] != 'A' or tasks[0][1]['task_id'] != d['new_task_id'] or tasks[0][1]['opportunity_id'] != d['opportunity_id']:
                raise ValueError('continue must add exactly its own new task')
        elif tasks:
            raise ValueError('only continue may add a task')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--type', required=True, choices=['review','practice-result','decision','archive'])
    p.add_argument('--root', default='.')
    p.add_argument('--base', required=True)
    p.add_argument('--head', required=True)
    args = p.parse_args()
    diff = subprocess.run(['git','-C',args.root,'diff','--no-renames','--name-status','-z',args.base,args.head,'--'], check=True, stdout=subprocess.PIPE).stdout.split(b'\0')
    if not diff or diff[-1] != b'' or len(diff[:-1]) % 2: raise ValueError('malformed diff')
    changes = [(s.decode('ascii'), p.decode('utf-8', errors='surrogateescape')) for s,p in zip(diff[:-1:2],diff[1:-1:2])]
    check_scope(args.type, changes, args.root)
    print('Business PR scope passed.')


if __name__ == '__main__':
    try: main()
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        print(f'Scope check failed: {exc}', file=sys.stderr)
        sys.exit(1)
