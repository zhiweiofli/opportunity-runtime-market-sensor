#!/usr/bin/env python3
"""Build a browsable index from the repository's mirrored documents."""
import json
import re
from pathlib import Path
from drive_mirror import safe_existing

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


def receipt_summary(text):
    batch = re.search(r'(?im)^\W*Batch (?:Processing )?Status\W*[:：]\s*([A-Z_]+)', text)
    queue = re.search(r'(?im)^\W*Queue Status\W*[:：]\s*([A-Z_]+)', text)
    records = len(set(re.findall(r'Research-(?:IBF|UW|Business|Friction)-[\w.-]+?\.md', text)))
    parts = ['Researcher 批次回执']
    if batch: parts.append('批次 ' + batch.group(1))
    if queue: parts.append('队列 ' + queue.group(1))
    parts.append('本批产出研究 %d 份' % records)
    return ' · '.join(parts)


def card(text, title, path, kind, modified, doc_id=None, source_status='present'):
    heading, summary = extract(text, title, kind)
    if kind == 'receipt':
        summary = receipt_summary(text)
    status = re.search(r'(?im)^[ \t]*(?:[-*][ \t]*)*(?:Stage\s*&\s*)?(?:Final (?:Status|Verdict)|Underwriting Verdict)[*]*[ \t]*[:：]?[ \t\r\n]*(HYPOTHESIS_READY|KILL|WATCH|BLOCKED)\b', text)
    source = re.match(r'(?i)^Research-(IBF|UW|Business|Friction)-', title)
    tags = [source.group(1).upper() if source.group(1).lower() in ('ibf', 'uw') else source.group(1).title()] if source else []
    return {'id': doc_id, 'title': heading, 'summary': summary, 'status': status.group(1).upper() if status else None,
            'tags': tags, 'path': path, 'kind': kind, 'modified': modified, 'source_status': source_status}


def mirror_kind(entry):
    parts = entry.get('folder_path') or []
    first = parts[0].lower() if parts else ''
    title = entry.get('title', '')
    if first == 'research':
        return 'receipt' if re.match(r'(?i)^execution[-_ ]receipt', title) else 'research'
    return {'judge': 'judge', 'signals': 'signals', 'archive': 'archive'}.get(first, 'other')


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
        entries.append(card(file.read_text(encoding='utf-8'), entry.get('title', path), path, match.group(1), entry.get('modified_at'), entry.get('doc_id')))
    mirror_file = root / 'drive-mirror/manifest.json'
    mirror = json.loads(mirror_file.read_text(encoding='utf-8')) if mirror_file.is_file() else None
    if mirror:
        if mirror.get('schema_version') != 'drive-mirror@1' or not isinstance(mirror.get('entries'), list):
            raise ValueError('invalid Drive mirror manifest')
        mirrored_ids = set()
        mirror_cards = []
        for item in mirror['entries']:
            path = item['path']
            file = safe_existing(root, path)
            if not file:
                raise ValueError('missing or unsafe Drive mirror file: ' + path)
            if item['id'] in mirrored_ids:
                raise ValueError('duplicate Drive mirror ID')
            mirrored_ids.add(item['id'])
            mime = item.get('export_mime_type') or item.get('mime_type', '')
            text = file.read_text(encoding='utf-8', errors='replace') if mime.startswith('text/') else ''
            mirror_cards.append(card(text, item['title'], path, mirror_kind(item), item.get('modified_at'), item['id'], item.get('source_status', 'present')))
        entries = [entry for entry in entries if entry.get('id') not in mirrored_ids] + mirror_cards
    return {'inventory_at': manifest.get('inventory_at'), 'mirror_last_changed_at': mirror.get('last_changed_at') if mirror else None, 'entries': entries}


if __name__ == '__main__':
    output = ROOT / 'site/data/archive.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build(ROOT), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
