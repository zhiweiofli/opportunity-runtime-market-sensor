#!/usr/bin/env python3
"""Build a browsable index from the repository's mirrored documents."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def clean(value):
    return re.sub(r'\s+', ' ', re.sub(r'^[\s#*\-]+', '', value)).strip()


def readable_filename(value):
    value = value.removesuffix('.md')
    value = re.sub(r'^Research-(?:IBF|UW|Business|Friction)-\d{4}-?\d{2}-?\d{2}-?', '', value, flags=re.I)
    value = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', value)
    return value.replace('-', ' ').strip()


def extract(text, fallback, kind):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    title_patterns = [r'(?im)^\s*(?:\*\s*)?Opportunity Hypothesis\s*[:：]\s*(\S[^\n]*)',
                      r'(?im)^\s*(?:\*\s*)?Opportunity Hypothesis\s*\n+\s*(?:Title\s*[:：]\s*)?(\S[^\n]*)',
                      r'(?im)^\s*(?:\*\s*)?Title\s*[:：]\s*(\S[^\n]*)',
                      r'(?im)^\s*Primary Domain\s*\n+\s*(\S[^\n]*)',
                      r'(?m)^#\s+(.+)']
    if kind == 'judge':
        title_patterns.insert(0, r'(?m)^\s*(Opportunity Runtime\s*[—–-]\s*Weekly Judge[^\n]*)')
    title = readable_filename(fallback)
    for pattern in title_patterns:
        match = re.search(pattern, text)
        if match:
            candidate = clean(match.group(1))
            if candidate.lower() not in ('opportunity runtime research record', 'opportunity hypothesis'):
                title = candidate
                break
    summary_patterns = ([r'(?m)^\s*[AＡ][.、．]\s*本周结论\s*\n+\s*(\S[^\n]*)'] if kind == 'judge' else []) + [
        r'(?im)^\s*(?:[-*]\s*)?Known\s*[:：]\s*(\S[^\n]*)',
        r'(?im)^\s*Known\s*\n+\s*(\S[^\n]*)',
        r'(?im)^\s*\d+[.、]\s*(?:Problem & Friction Analysis|Signal Context & Overview)\s*\n+\s*(\S[^\n]*)',
        r'(?im)^\s*(?:\*\s*)?Decision.Critical Unknown\s*[:：]\s*(\S[^\n]*)']
    summary = ''
    for pattern in summary_patterns:
        match = re.search(pattern, text)
        if match:
            summary = clean(match.group(1))
            break
    if not summary:
        paragraphs = [clean(line) for line in text.splitlines()]
        summary = next((line for line in paragraphs if len(line) >= 70 and (re.search(r'[\u4e00-\u9fff]', line) or re.search(r'\b(the|this|these|because|would)\b', line, re.I))), '')
    if len(summary) > 180:
        summary = summary[:180].rstrip() + '…'
    return title, summary


def build(root):
    manifest = json.loads((root / 'or-archive/manifest.json').read_text(encoding='utf-8'))
    entries = []
    for entry in manifest['entries']:
        path = entry.get('path', '')
        match = re.fullmatch(r'or-archive/(research|judge)/[^/]+\.md', path)
        if not match or entry.get('sync_status') != 'mirrored':
            continue
        file = root / path
        if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(root.resolve()):
            raise ValueError('archive file is missing or unsafe: ' + path)
        text = file.read_text(encoding='utf-8')
        title, summary = extract(text, entry.get('title', path), match.group(1))
        status = re.search(r'(?im)^[ \t]*(?:[-*][ \t]*)*(?:Stage\s*&\s*)?Final (?:Status|Verdict)[*]*[ \t]*[:：]?[ \t\r\n]*(HYPOTHESIS_READY|KILL|WATCH|BLOCKED)\b', text)
        source = re.match(r'(?i)^Research-(IBF|UW|Business|Friction)-', entry.get('title', ''))
        tags = [source.group(1).upper() if source.group(1).lower() in ('ibf', 'uw') else source.group(1).title()] if source else []
        entries.append({'title': title, 'summary': summary, 'status': status.group(1).upper() if status else None, 'tags': tags, 'path': path, 'kind': match.group(1), 'modified': entry.get('modified_at')})
    return {'inventory_at': manifest.get('inventory_at'), 'entries': entries}


if __name__ == '__main__':
    output = ROOT / 'site/data/archive.json'
    output.write_text(json.dumps(build(ROOT), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
