#!/usr/bin/env python3
"""Validate workflow files as data; GitHub merge and actor evidence is checked separately."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from jsonschema import Draft202012Validator, FormatChecker

SCHEMAS = Path(__file__).resolve().parents[2] / 'schemas/workflow'
ID = r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}'
LAYOUT = {
    'opportunity': re.compile(rf'opportunities/({ID})/opportunity\.json\Z'),
    'decision': re.compile(rf'opportunities/({ID})/decisions/({ID})\.json\Z'),
    'task': re.compile(rf'practice/inbox/({ID})/task\.json\Z'),
    'result': re.compile(rf'practice/results/({ID})/({ID})/result\.json\Z'),
}
DEMO = re.compile(r'(?im)(?:\bdemo_only\b["\'`*]*\s*[:=]\s*["\']?true\b|\bresearch_eligible\b["\'`*]*\s*[:=]\s*["\']?false\b|\bTEST_ONLY\b|\bPILOT\b)')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def load_json(data):
    return json.loads(data, object_pairs_hook=unique_object,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f'invalid number: {x}')))


def safe_path(value):
    p = PurePosixPath(value)
    return bool(value and not value.startswith('/') and '\\' not in value and
                all(x not in ('', '.', '..') for x in value.split('/')) and str(p) == value)


def parse_time(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError('timezone required')
    return result.astimezone(timezone.utc)


class Validator:
    def __init__(self, root, base, now=None):
        self.root = Path(root).resolve()
        self.base = base
        self.now = now or datetime.now(timezone.utc)
        self.errors = []
        self.records = {kind: {} for kind in LAYOUT}
        self.raw = {}
        self.schemas = {kind: Draft202012Validator(load_json((SCHEMAS / f'{kind}.schema.json').read_text()), format_checker=FormatChecker()) for kind in LAYOUT}
        self.commit_cache = {}

    def error(self, path, message):
        self.errors.append(f'{path}: {message}')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def read_ref(self, path, commit, owner):
        if not safe_path(path):
            self.error(owner, f'unsafe reference path: {path!r}')
            return None
        if commit not in self.commit_cache:
            self.commit_cache[commit] = self.git('merge-base', '--is-ancestor', commit, self.base).returncode == 0
        if not self.commit_cache[commit]:
            self.error(owner, f'reference commit {commit} is not in trusted base history')
            return None
        spec = f'{commit}:{path}'
        tree = self.git('--literal-pathspecs', 'ls-tree', '-z', commit, '--', path)
        entries = tree.stdout.split(b'\0')
        parts = entries[0].split(b'\t', 1) if len(entries) == 2 and entries[1] == b'' else []
        if tree.returncode or len(parts) != 2 or not parts[0].startswith((b'100644 blob ', b'100755 blob ')) or parts[1] != path.encode('utf-8'):
            self.error(owner, f'reference is not a regular file: {spec}')
            return None
        kind = self.git('cat-file', '-t', spec)
        if kind.returncode or kind.stdout.strip() != b'blob':
            self.error(owner, f'reference does not name a file: {spec}')
            return None
        data = self.git('show', spec)
        if data.returncode:
            self.error(owner, f'cannot read {spec}')
            return None
        return data.stdout

    def times(self, obj, owner):
        for k, v in obj.items():
            if isinstance(v, dict):
                self.times(v, owner)
            elif isinstance(v, list):
                for x in v:
                    if isinstance(x, dict): self.times(x, owner)
            elif k in ('created_at', 'updated_at', 'source_updated_at', 'started_at', 'finished_at', 'decided_at', 'collected_at') and v is not None:
                try:
                    if parse_time(v) > self.now:
                        self.error(owner, f'{k} is in the future')
                except (TypeError, ValueError):
                    self.error(owner, f'{k} is not a timezone-aware timestamp')

    def amount(self, value, owner):
        if (value['basis'] == 'unknown') != (value['value'] is None):
            self.error(owner, 'unknown economic basis requires null value, and known basis requires a value')
        if value['value'] is not None and value['currency'] is None:
            self.error(owner, 'known amount requires currency')

    def files(self):
        for dirname in ('opportunities', 'practice/inbox', 'practice/results'):
            directory = self.root / dirname
            if not directory.exists():
                continue
            if directory.is_symlink():
                self.error(dirname, 'symlink is forbidden')
                continue
            for p in directory.rglob('*'):
                path = p.relative_to(self.root).as_posix()
                if p.is_symlink():
                    self.error(path, 'symlink is forbidden')
                    continue
                if not p.is_file():
                    continue
                if re.fullmatch(rf'practice/results/{ID}/{ID}/report\.md', path):
                    continue
                kinds = [(kind, pattern.fullmatch(path)) for kind, pattern in LAYOUT.items()]
                match = next(((kind, m) for kind, m in kinds if m), None)
                if not match:
                    if p.name != 'README.md': self.error(path, 'unrecognized workflow file')
                    continue
                kind, m = match
                try:
                    raw = p.read_bytes()
                    record = load_json(raw)
                except (OSError, ValueError, UnicodeDecodeError) as exc:
                    self.error(path, f'invalid JSON: {exc}')
                    continue
                errors = sorted(self.schemas[kind].iter_errors(record), key=lambda e: list(map(str, e.path)))
                if errors:
                    for err in errors: self.error(path, f'schema {"/".join(map(str, err.path))}: {err.message}')
                    continue
                key = m.group(1) if kind in ('task', 'opportunity') else m.group(2)
                expected = ({'opportunity': 'opportunity_id', 'task': 'task_id', 'decision': 'decision_id', 'result': 'run_id'}[kind], key)
                if record[expected[0]] != expected[1]: self.error(path, f'{expected[0]} does not match path')
                if kind in ('decision', 'result') and record['opportunity_id' if kind == 'decision' else 'task_id'] != m.group(1):
                    self.error(path, 'parent ID does not match path')
                if key in self.records[kind]: self.error(path, f'duplicate {kind} ID {key}')
                self.records[kind][key] = (path, record)
                self.raw[path] = raw
                self.times(record, path)

    def run(self):
        self.files()
        for path, o in self.records['opportunity'].values():
            if parse_time(o['updated_at']) < parse_time(o['created_at']): self.error(path, 'updated_at precedes created_at')
            a = o['economic_anchor']
            self.amount(a, path)
            if o.get('public', {}).get('economic_anchor'): self.amount(o['public']['economic_anchor'], path)
            if a['basis'] != 'unknown' and a['evidence_ref'] is None: self.error(path, 'known economic value requires evidence')
            if a['evidence_ref']: self.read_ref(**a['evidence_ref'], owner=path)
            for source in o['source_refs']:
                values = [source['drive_doc_id'], source['source_updated_at'], source['mirror_path'], source['commit']]
                if any(v is None for v in values) and not source['missing_reason']: self.error(path, 'incomplete source requires missing_reason')
                if bool(source['mirror_path']) != bool(source['commit']): self.error(path, 'mirror path and commit must be provided together')
                if source['mirror_path'] and source['commit']:
                    data = self.read_ref(source['mirror_path'], source['commit'], path)
                    if data is not None and DEMO.search(data.decode('utf-8', errors='replace')): self.error(path, 'source is marked demo/PILOT or ineligible')
                    if source['mirror_path'].startswith(('or-archive/research/', 'or-archive/judge/')):
                        manifest_data = self.read_ref('or-archive/manifest.json', source['commit'], path)
                        try:
                            entries = load_json(manifest_data)['entries'] if manifest_data is not None else []
                            matches = [x for x in entries if x.get('path') == source['mirror_path']]
                            if len(matches) != 1 or (source['drive_doc_id'] is not None and matches[0].get('doc_id') != source['drive_doc_id']) or (source['source_updated_at'] is not None and parse_time(matches[0]['modified_at']) != parse_time(source['source_updated_at'])):
                                self.error(path, 'source metadata does not match mirror manifest')
                        except (ValueError, KeyError, TypeError):
                            self.error(path, 'invalid source mirror manifest')
        for path, t in self.records['task'].values():
            if t['opportunity_id'] not in self.records['opportunity']: self.error(path, 'missing opportunity')
            else:
                opportunity = self.records['opportunity'][t['opportunity_id']][1]
                if not any(s['mirror_path'] and s['commit'] for s in opportunity['source_refs']):
                    self.error(path, 'task requires at least one fixed source mirror')
            ids = [x['id'] for x in t['success_criteria'] + t['falsification_criteria']]
            if len(ids) != len(set(ids)): self.error(path, 'duplicate criterion ID')
            if t['budget']['max_cost'] is not None and t['budget']['currency'] is None: self.error(path, 'known budget cost requires currency')
            if t.get('public', {}).get('budget'): self.amount(t['public']['budget'], path)
            for ref in t['context_refs']:
                data = self.read_ref(**ref, owner=path)
                if data is not None and DEMO.search(data.decode('utf-8', errors='replace')):
                    self.error(path, 'context is marked demo/PILOT or ineligible')
        for path, result in self.records['result'].values():
            item = self.records['task'].get(result['task_id'])
            if not item:
                self.error(path, 'missing input task')
                continue
            task_path, task = item
            if task['opportunity_id'] != result['opportunity_id']: self.error(path, 'opportunity does not match task')
            if parse_time(result['started_at']) < parse_time(task['created_at']): self.error(path, 'run starts before task creation')
            expected = hashlib.sha256(self.raw[task_path]).hexdigest()
            if result['task_hash'] != expected: self.error(path, 'task_hash does not match current task bytes')
            previous = self.read_ref(task_path, result['input_commit'], path)
            if previous is not None and hashlib.sha256(previous).hexdigest() != expected: self.error(path, 'task differs from input commit')
            criteria = [x['id'] for x in task['success_criteria'] + task['falsification_criteria']]
            got = [x['criterion_id'] for x in result['criteria_results']]
            if len(got) != len(set(got)) or set(got) != set(criteria): self.error(path, 'criteria_results must cover every task criterion exactly once')
            if parse_time(result['finished_at']) < parse_time(result['started_at']): self.error(path, 'finish precedes start')
            cost = result['actual_cost']
            if result.get('public', {}).get('actual_cost'): self.amount(result['public']['actual_cost'], path)
            if cost['cost'] is not None and cost['currency'] is None: self.error(path, 'known actual cost requires currency')
            for evidence in result['evidence_refs']:
                if parse_time(evidence['collected_at']) > parse_time(result['finished_at']): self.error(path, 'evidence collected after run finished')
                if evidence['ref']:
                    data = self.read_ref(**evidence['ref'], owner=path)
                    if not evidence['sha256']: self.error(path, 'referenced evidence file requires sha256')
                    elif data is not None and hashlib.sha256(data).hexdigest() != evidence['sha256']: self.error(path, 'evidence hash mismatch')
            report = self.root / Path(path).parent / 'report.md'
            if report.is_symlink() or not report.is_file() or not report.read_text(encoding='utf-8').strip(): self.error(path, 'missing nonempty report.md')
        for path, d in self.records['decision'].values():
            if d['opportunity_id'] not in self.records['opportunity']: self.error(path, 'missing opportunity')
            if d['action'] == 'launch' and not d['run_id']: self.error(path, 'launch requires an accepted result')
            if d['run_id']:
                found = self.records['result'].get(d['run_id'])
                if not found or found[1]['opportunity_id'] != d['opportunity_id']: self.error(path, 'decision references missing result for opportunity')
            if d['action'] == 'continue':
                task = self.records['task'].get(d['new_task_id'])
                if not task or task[1]['opportunity_id'] != d['opportunity_id']: self.error(path, 'continue references missing new task for opportunity')
        return self.errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--base', required=True, help='trusted default-branch commit')
    args = parser.parse_args()
    v = Validator(args.root, args.base)
    if v.git('rev-parse', '--verify', f'{args.base}^{{commit}}').returncode:
        parser.error('base must be a commit in the repository')
    errors = v.run()
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print('Workflow data valid; GitHub merge and actor evidence still require separate checks.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
