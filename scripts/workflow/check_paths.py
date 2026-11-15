#!/usr/bin/env python3
"""Check business PR path boundaries; content and GitHub evidence need separate checks."""
import argparse
import re
import subprocess
import sys

ID = r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}'
OPPORTUNITY = re.compile(rf'opportunities/{ID}/opportunity\.json\Z')
DECISION = re.compile(rf'opportunities/{ID}/decisions/{ID}\.json\Z')
TASK = re.compile(rf'practice/inbox/{ID}/task\.json\Z')
RESULT = re.compile(rf'practice/results/{ID}/{ID}/(?:result\.json|report\.md)\Z')


def archive(path):
    return path.startswith('or-archive/') and all(part not in ('', '.', '..') for part in path.split('/'))


def allowed(kind, status, path):
    if kind == 'implementation':
        if path in ('opportunities/README.md', 'practice/inbox/README.md', 'practice/results/README.md'):
            return status in ('A', 'M')
        return not any(path == root or path.startswith(root + '/') for root in ('opportunities', 'practice', 'or-archive'))
    if status not in ('A', 'M'):
        return False
    if kind == 'archive':
        return archive(path)
    if kind == 'review':
        return bool(OPPORTUNITY.fullmatch(path) or TASK.fullmatch(path) or archive(path))
    if kind == 'practice-result':
        return status == 'A' and bool(RESULT.fullmatch(path))
    if kind == 'decision':
        return status == 'A' and bool(DECISION.fullmatch(path) or TASK.fullmatch(path))
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--type', required=True, choices=['review', 'practice-result', 'decision', 'archive', 'implementation'])
    parser.add_argument('--base', required=True)
    parser.add_argument('--head', required=True)
    args = parser.parse_args()
    result = subprocess.run(['git', 'diff', '--no-renames', '--name-status', '-z', args.base, args.head, '--'], check=True, stdout=subprocess.PIPE)
    entries = result.stdout.split(b'\0')
    if entries[-1] != b'':
        raise ValueError('Malformed git diff')
    entries.pop()
    if len(entries) % 2 or not entries:
        raise ValueError('Empty or malformed diff')
    errors = []
    for status, path in zip(entries[::2], entries[1::2]):
        status = status.decode('ascii')
        path = path.decode('utf-8', errors='surrogateescape')
        if not allowed(args.type, status, path):
            errors.append(f'{status} {path!r}')
    if errors:
        print('Disallowed changes:\n' + '\n'.join(errors), file=sys.stderr)
        return 1
    print('Path boundary passed; content and merge evidence still require validation.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
