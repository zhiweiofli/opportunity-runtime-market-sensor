#!/usr/bin/env python3
"""Build a top-level brief snapshot (site/data/brief.json) from drive-mirror."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re

from build_archive_index import card, extract, mirror_kind
from drive_mirror import safe_existing

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = 'or-brief@1'

# Judge spec calls for every 3 days, but observed cadence is weekly;
# 8 days (192h) catches a missed weekly run without triggering constant alerts.
JUDGE_STALE_HOURS = 192
SIGNAL_STALE_HOURS = 72
RESEARCH_STALE_HOURS = 72
BUSINESS_WINDOW_DAYS = 7
# A Judge reviews Research modified within the preceding 7 days.
JUDGE_LOOKBACK_DAYS = 7
SOURCE_KEYS = ('Business', 'Friction', 'IBF', 'UW', 'unknown')

CONCLUSION_MAX_CHARS = 600
MAX_ITEM_DETAILS = 8
MAX_REPEAT_HITS = 3

SLUG_STOPWORDS = frozenset({
    'manual', 'small', 'business', 'audit', 'packet', 'legacy', 'migration',
    'failure', 'recovery', 'saas', 'commercial', 'enterprise', 'sunset',
    'forced', 'status', 'account', 'client', 'customer', 'demand', 'claim',
    'dispute', 'appeal', 'auto', 'tool', 'service', 'system', 'data',
})

_VERDICT_RE = re.compile(r'(?<![A-Za-z])(?:NOW|NEXT|WATCH|DROP|KILL)(?![A-Za-z])|暂缓')
_NO_SIGNAL_RE = re.compile(r'\bno[- ]signal\b', re.I)


def parse_iso(value):
    """Parse an ISO-8601 timestamp string into a UTC-aware datetime, or None."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text[-1] in ('Z', 'z'):
        text = text[:-1] + '+00:00'
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _normalize_text(text):
    if text.startswith('\ufeff'):
        text = text[1:]
    return text.replace('\r\n', '\n').replace('\r', '\n')


def read_mirror_text(root, item):
    """Safely read mirrored UTF-8 text content from drive-mirror."""
    path = item.get('path', '')
    file = safe_existing(root, path)
    if not file:
        raise ValueError('missing or unsafe Drive mirror file: ' + str(path))
    mime = item.get('export_mime_type') or item.get('mime_type', '')
    if not mime.startswith('text/'):
        return ''
    return _normalize_text(file.read_text(encoding='utf-8', errors='replace'))


def extract_source_signal_ids(text):
    """Extract comma-separated Source Signal IDs from research document text."""
    match = re.search(
        r'(?im)^[ \t]*(?:[-*][ \t]*)?(?:\*\*)?Source\s+Signal\s+IDs?(?:\*\*)?[ \t]*[:：][ \t]*([^\n]*)',
        text,
    )
    if not match:
        return []
    raw = match.group(1)
    ids = []
    for part in re.split(r'[,，]', raw):
        cleaned = part.strip().strip('`*').strip()
        if cleaned:
            ids.append(cleaned)
    return ids


def slug_tokens(filename):
    """Extract normalized topic tokens from a Research filename or slug."""
    s = (filename or '').strip()
    if s.lower().endswith('.md'):
        s = s[:-3]
    s = re.sub(r'^Research-(?:IBF|UW|Business|Friction)-', '', s, flags=re.I)
    s = re.sub(r'\d{4}-?\d{2}-?\d{2}', ' ', s)
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', s)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', s)
    parts = re.split(r'[-_\s]+', s.lower())
    return {tok for tok in parts if len(tok) >= 4 and tok not in SLUG_STOPWORDS}


def _is_strictly_earlier(earlier_val, later_val):
    dt1 = parse_iso(earlier_val)
    dt2 = parse_iso(later_val)
    if dt1 is not None and dt2 is not None:
        return dt1 < dt2
    if earlier_val and later_val:
        return earlier_val < later_val
    return False


def find_possible_repeats(candidate, kill_records, limit=MAX_REPEAT_HITS):
    """Find up to `limit` earlier KILL records that may overlap with `candidate`."""
    if candidate.get('status') == 'KILL':
        return []
    cand_mod = candidate.get('modified')
    cand_ssids = set(candidate.get('source_signal_ids') or [])
    cand_slug_src = candidate.get('filename') or candidate.get('title') or ''
    cand_tokens = slug_tokens(cand_slug_src)

    hits = []
    for kill_rec in kill_records:
        kill_mod = kill_rec.get('modified')
        if not _is_strictly_earlier(kill_mod, cand_mod):
            continue
        ssid_hit = bool(cand_ssids and (cand_ssids & set(kill_rec.get('source_signal_ids') or [])))
        kill_slug_src = kill_rec.get('filename') or kill_rec.get('title') or ''
        k_tokens = slug_tokens(kill_slug_src)
        inter = cand_tokens & k_tokens
        union = cand_tokens | k_tokens
        jacc = (len(inter) / len(union)) if union else 0.0
        slug_hit = bool(inter) and (len(inter) >= 2 or jacc >= 0.5)
        if not (ssid_hit or slug_hit):
            continue
        rule = 'source_signal_id' if ssid_hit else 'slug_tokens'
        k_dt = parse_iso(kill_mod)
        sort_key = (0 if ssid_hit else 1, -len(inter), -jacc, -(k_dt.timestamp() if k_dt else 0.0))
        hits.append((
            sort_key,
            {
                'title': kill_rec['title'],
                'path': kill_rec['path'],
                'modified': kill_mod,
                'rule': rule,
                'matched': sorted(inter) if not ssid_hit else [],
            },
        ))
    hits.sort(key=lambda item: item[0])
    return [item[1] for item in hits[:limit]]


def _extract_section(lines, start_re, stop_re):
    started = False
    collected = []
    for line in lines:
        if not started:
            if start_re.match(line):
                started = True
            continue
        if stop_re.match(line):
            break
        collected.append(line)
    return collected


def _parse_judge_items(section_lines):
    items = []
    current = None
    for raw_line in section_lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if re.fullmatch(r'[\s|:-]+', stripped):
            continue
        num_match = re.match(r'^\s*\|?\s*(\d+)\s*\|(.*)$', raw_line)
        if num_match:
            rank = int(num_match.group(1))
            row = stripped.strip('|')
            parts = [re.sub(r'\s+', ' ', p).strip() for p in row.split('|')]
            item_title = parts[1] if len(parts) >= 2 else ''
            last_cell = parts[-1] if len(parts) >= 3 else ''
            cells = parts[2:-1] if len(parts) > 3 else []
            vm = _VERDICT_RE.search(last_cell)
            verdict = vm.group(0) if vm else None
            current = {
                'rank': rank,
                'title': item_title,
                'verdict': verdict,
                'verdict_note': last_cell,
                'cells': cells,
                'details': [],
            }
            items.append(current)
        elif current is not None:
            # Skip table header rows before item 1; attach follow-up lines to current item.
            cleaned = re.sub(r'\s+', ' ', stripped).strip()
            if cleaned and len(current['details']) < MAX_ITEM_DETAILS:
                current['details'].append(cleaned)
    return items


def parse_judge(text, fallback_title):
    """Parse Judge document text into structured summary fields."""
    text = _normalize_text(text)
    title_match = re.search(
        r'(?m)^\s*(Opportunity Runtime\s*[—–-]\s*(?:Weekly\s+)?Judge[^\n]*)',
        text,
    )
    title = re.sub(r'\s+', ' ', title_match.group(1)).strip() if title_match else extract(text, fallback_title, 'judge')[0]

    gen_match = re.search(
        r'(?im)^\s*(?:[-*]\s*)?(?:\*\*)?Generated\s+At(?:\*\*)?\s*[:：]\s*(\S[^\n]*)',
        text,
    )
    generated_at = gen_match.group(1).strip() if gen_match else None

    lines = text.splitlines()
    conclusion_lines = _extract_section(
        lines,
        re.compile(r'^\s*[AＡ][.、．]\s*本(?:周|轮)结论'),
        re.compile(r'^\s*[B-HＢ-Ｈ][.、．]\s'),
    )
    conclusion = re.sub(r'\s+', ' ', ' '.join(conclusion_lines)).strip()
    if len(conclusion) > CONCLUSION_MAX_CHARS:
        conclusion = conclusion[:CONCLUSION_MAX_CHARS].rstrip() + '…'

    board_lines = _extract_section(
        lines,
        re.compile(r'^\s*[BＢ][.、．]\s*本(?:周|轮)决策看板'),
        re.compile(r'^\s*[C-HＣ-Ｈ][.、．]\s'),
    )
    items = _parse_judge_items(board_lines)

    decision_lines = _extract_section(
        lines,
        re.compile(r'^\s*[GＧ][.、．]\s*Human Decision Needed', re.I),
        re.compile(r'^\s*[HＨ][.、．]\s'),
    )
    decisions = []
    for line in decision_lines:
        cleaned = re.sub(r'\s+', ' ', line).strip()
        if not cleaned:
            continue
        if re.match(r'^\d+[.、．]', cleaned):
            decisions.append(cleaned)
        elif decisions:
            decisions[-1] += ' ' + cleaned

    return {
        'title': title,
        'generated_at': generated_at,
        'conclusion': conclusion,
        'items': items,
        'decisions': decisions,
        'parse_ok': bool(conclusion) or bool(items) or bool(decisions),
    }


def _health_bucket(entry):
    fp = entry.get('folder_path') or []
    first = fp[0] if fp else ''
    if first == 'Judge':
        return 'judge'
    if first == 'Research' and mirror_kind(entry) == 'research':
        return 'research'
    if first == 'Signals':
        second = fp[1] if len(fp) >= 2 else ''
        if second == 'Business':
            return 'signals_business'
        if second == 'Friction':
            return 'signals_friction'
        upper_title = (entry.get('title') or '').upper()
        if upper_title.startswith('IBF-'):
            return 'signals_ibf'
        if upper_title.startswith('UW-'):
            return 'signals_uw'
    return None


def compute_health(entries, now_dt, manifest_missing=False):
    """Compute pipeline freshness health items relative to `now_dt`."""
    specs = (
        ('judge', 'Judge 评审', JUDGE_STALE_HOURS),
        ('signals_business', 'Business 信号', SIGNAL_STALE_HOURS),
        ('signals_friction', 'Friction 信号', SIGNAL_STALE_HOURS),
        ('signals_ibf', 'IBF 信号', SIGNAL_STALE_HOURS),
        ('signals_uw', 'UW 信号', SIGNAL_STALE_HOURS),
        ('research', 'Research 研究', RESEARCH_STALE_HOURS),
    )
    buckets = {cid: [] for cid, _, _ in specs}
    for entry in entries:
        bucket = _health_bucket(entry)
        if bucket is None:
            continue
        dt = parse_iso(entry.get('modified_at'))
        if dt is not None:
            buckets[bucket].append((dt, entry))

    results = []
    for cid, label, threshold_hours in specs:
        items = buckets[cid]
        if manifest_missing or not items:
            results.append({
                'id': cid,
                'label': label,
                'status': 'unknown',
                'last_at': None,
                'age_hours': None,
                'threshold_hours': threshold_hours,
                'detail': '镜像清单缺失' if manifest_missing else '暂无记录',
            })
            continue
        last_dt, latest_entry = max(items, key=lambda pair: (pair[0], pair[1].get('path', '')))
        raw_age_hours = (now_dt - last_dt).total_seconds() / 3600.0
        age_hours = round(raw_age_hours, 1)
        status = 'warn' if raw_age_hours > threshold_hours else 'ok'
        if status == 'warn':
            if age_hours >= 24 and threshold_hours % 24 == 0:
                detail = f'已 {round(age_hours / 24)} 天未更新（阈值 {threshold_hours // 24} 天）'
            else:
                detail = f'已 {age_hours:.1f} 小时未更新（阈值 {threshold_hours} 小时）'
        else:
            detail = f'最近更新于 {max(0.0, age_hours):.1f} 小时前'

        if cid == 'signals_business':
            cutoff = BUSINESS_WINDOW_DAYS * 86400
            recent = [e for dt, e in items if 0 <= (now_dt - dt).total_seconds() <= cutoff]
            no_sig = sum(1 for e in recent if _NO_SIGNAL_RE.search(e.get('title') or ''))
            detail += f'；近 7 天 no-signal {no_sig}/{len(recent)}'

        results.append({
            'id': cid,
            'label': label,
            'status': status,
            'last_at': latest_entry.get('modified_at'),
            'age_hours': age_hours,
            'threshold_hours': threshold_hours,
            'detail': detail,
        })
    return results


def _week_start(dt):
    day = dt.date()
    return day - timedelta(days=day.weekday())


def compute_trends(research, signals, judges, now_dt):
    """Bucket Research, Signals and Judge runs into Monday-start UTC weeks."""
    starts = [dt for dt in (parse_iso(r.get('modified')) for r in research) if dt is not None]
    starts += [dt for dt in (parse_iso(s.get('modified_at')) for s in signals) if dt is not None]
    if not starts:
        return {'weeks': []}
    first = _week_start(min(starts))
    last = _week_start(now_dt)
    weeks = {}
    cursor = first
    while cursor <= last:
        weeks[cursor] = {
            'week_start': cursor.isoformat(),
            'research_ready': 0,
            'research_kill': 0,
            'research_other': 0,
            'by_source': {key: 0 for key in SOURCE_KEYS},
            'signals_total': 0,
            'signals_no_signal': 0,
            'judge_runs': 0,
        }
        cursor += timedelta(days=7)

    def bucket(value):
        dt = parse_iso(value)
        return weeks.get(_week_start(dt)) if dt is not None else None

    for rec in research:
        week = bucket(rec.get('modified'))
        if week is None:
            continue
        if rec.get('status') == 'HYPOTHESIS_READY':
            week['research_ready'] += 1
        elif rec.get('status') == 'KILL':
            week['research_kill'] += 1
        else:
            week['research_other'] += 1
        tags = rec.get('tags') or []
        source = tags[0] if tags and tags[0] in SOURCE_KEYS else 'unknown'
        week['by_source'][source] += 1
    for entry in signals:
        week = bucket(entry.get('modified_at'))
        if week is None:
            continue
        week['signals_total'] += 1
        if _NO_SIGNAL_RE.search(entry.get('title') or ''):
            week['signals_no_signal'] += 1
    for entry in judges:
        week = bucket(entry.get('modified_at'))
        if week is not None:
            week['judge_runs'] += 1
    return {'weeks': [weeks[key] for key in sorted(weeks)]}


def compute_source_yield(research, kill_records):
    """Per-source Research totals, READY/KILL counts and possible repeats of earlier KILLs."""
    rows = {}
    for rec in research:
        tags = rec.get('tags') or []
        source = tags[0] if tags else 'unknown'
        row = rows.setdefault(source, {'source': source, 'total': 0, 'ready': 0, 'kill': 0, 'possible_repeat': 0})
        row['total'] += 1
        if rec.get('status') == 'HYPOTHESIS_READY':
            row['ready'] += 1
        elif rec.get('status') == 'KILL':
            row['kill'] += 1
        if rec.get('status') != 'KILL' and find_possible_repeats(rec, kill_records):
            row['possible_repeat'] += 1
    order = {key: idx for idx, key in enumerate(SOURCE_KEYS)}
    return sorted(rows.values(), key=lambda row: (order.get(row['source'], len(order)), row['source']))


def compute_coverage_gaps(research, judge_times):
    """Research older than the latest Judge that falls outside every Judge lookback window."""
    if not judge_times:
        return []
    latest = max(judge_times)
    lookback = timedelta(days=JUDGE_LOOKBACK_DAYS)
    gaps = []
    for rec in research:
        dt = parse_iso(rec.get('modified'))
        if dt is None or dt >= latest:
            continue
        if any(jt - lookback < dt <= jt for jt in judge_times):
            continue
        gaps.append({
            'title': rec['title'],
            'path': rec['path'],
            'modified': rec['modified'],
            'status': rec['status'],
            'tags': rec['tags'],
        })
    gaps.sort(key=lambda g: (g.get('modified') or '', g['path']))
    return gaps


def coverage_health(gaps):
    return {
        'id': 'judge_coverage',
        'label': 'Judge 覆盖',
        'status': 'warn' if gaps else 'ok',
        'last_at': None,
        'age_hours': None,
        'threshold_hours': None,
        'detail': f'{len(gaps)} 份 Research 未进入任何 Judge 回看窗口',
    }


def _research_sort_key(item):
    status = item.get('status')
    group = 0 if status == 'HYPOTHESIS_READY' else (2 if status == 'KILL' else 1)
    mod = item.get('modified') or ''
    dt = parse_iso(mod)
    ts = dt.timestamp() if dt is not None else float('-inf')
    return (group, -ts, mod)


def build(root, now=None):
    """Build the or-brief@1 JSON payload from drive-mirror/manifest.json."""
    root = Path(root)
    now_dt = now or datetime.now(timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=timezone.utc)
    else:
        now_dt = now_dt.astimezone(timezone.utc)
    generated_at = now_dt.isoformat()

    mirror_file = root / 'drive-mirror/manifest.json'
    if not mirror_file.is_file():
        return {
            'schema_version': SCHEMA_VERSION,
            'generated_at': generated_at,
            'judge': None,
            'new_research': [],
            'counts': {'total': 0, 'ready': 0, 'kill': 0, 'unknown': 0},
            'health': compute_health([], now_dt, manifest_missing=True),
            'trends': {'weeks': []},
            'judge_history': [],
            'source_yield': [],
            'coverage_gaps': [],
        }

    mirror = json.loads(mirror_file.read_text(encoding='utf-8'))
    if mirror.get('schema_version') != 'drive-mirror@1' or not isinstance(mirror.get('entries'), list):
        raise ValueError('invalid Drive mirror manifest')
    entries = mirror['entries']

    judge_entries = [e for e in entries if (e.get('folder_path') or [''])[0] == 'Judge']
    judge_entries.sort(key=lambda e: (parse_iso(e.get('modified_at')) or datetime.min.replace(tzinfo=timezone.utc), e.get('path', '')))
    judge_history = []
    for entry in judge_entries:
        parsed_entry = parse_judge(read_mirror_text(root, entry), entry.get('title', entry['path']))
        judge_history.append({
            'date': (entry.get('modified_at') or '')[:10],
            'title': parsed_entry['title'],
            'path': entry['path'],
            'parse_ok': parsed_entry['parse_ok'],
            'items': [{'rank': i['rank'], 'title': i['title'], 'verdict': i['verdict']} for i in parsed_entry['items']],
        })
    judge = None
    judge_dt = None
    judge_mod_raw = None
    if judge_entries:
        latest_judge = max(
            judge_entries,
            key=lambda e: (parse_iso(e.get('modified_at')) or datetime.min.replace(tzinfo=timezone.utc), e.get('path', '')),
        )
        judge_text = read_mirror_text(root, latest_judge)
        parsed = parse_judge(judge_text, latest_judge.get('title', latest_judge['path']))
        judge_mod_raw = latest_judge.get('modified_at')
        judge_dt = parse_iso(judge_mod_raw)
        judge = {
            'title': parsed['title'],
            'path': latest_judge['path'],
            'modified_at': judge_mod_raw,
            'generated_at': parsed['generated_at'],
            'conclusion': parsed['conclusion'],
            'items': parsed['items'],
            'decisions': parsed['decisions'],
            'parse_ok': parsed['parse_ok'],
        }

    all_research = []
    for entry in entries:
        fp = entry.get('folder_path') or []
        if not fp or fp[0] != 'Research' or mirror_kind(entry) != 'research':
            continue
        text = read_mirror_text(root, entry)
        c = card(text, entry['title'], entry['path'], 'research', entry.get('modified_at'), entry.get('id'), entry.get('source_status', 'present'))
        all_research.append({
            'filename': entry['title'],
            'title': c['title'],
            'summary': c['summary'],
            'status': c['status'],
            'tags': c['tags'],
            'path': c['path'],
            'modified': c['modified'],
            'source_signal_ids': extract_source_signal_ids(text),
        })

    kill_records = [r for r in all_research if r['status'] == 'KILL']

    if judge is None:
        new_records = all_research
    else:
        new_records = []
        for rec in all_research:
            rec_mod = rec.get('modified')
            rec_dt = parse_iso(rec_mod)
            if judge_dt is not None and rec_dt is not None:
                is_after = rec_dt > judge_dt
            elif judge_mod_raw and rec_mod:
                is_after = rec_mod > judge_mod_raw
            else:
                is_after = False
            if is_after:
                new_records.append(rec)

    new_research = []
    for rec in new_records:
        new_research.append({
            'title': rec['title'],
            'summary': rec['summary'],
            'status': rec['status'],
            'tags': rec['tags'],
            'path': rec['path'],
            'modified': rec['modified'],
            'source_signal_ids': rec['source_signal_ids'],
            'possible_repeat_of': find_possible_repeats(rec, kill_records),
        })

    new_research.sort(key=_research_sort_key)

    ready_count = sum(1 for x in new_research if x['status'] == 'HYPOTHESIS_READY')
    kill_count = sum(1 for x in new_research if x['status'] == 'KILL')
    total_count = len(new_research)
    counts = {
        'total': total_count,
        'ready': ready_count,
        'kill': kill_count,
        'unknown': total_count - ready_count - kill_count,
    }

    signal_entries = [e for e in entries if (e.get('folder_path') or [''])[0] == 'Signals']
    judge_times = [dt for dt in (parse_iso(e.get('modified_at')) for e in judge_entries) if dt is not None]
    coverage_gaps = compute_coverage_gaps(all_research, judge_times)
    health = compute_health(entries, now_dt)
    health.append(coverage_health(coverage_gaps))

    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at': generated_at,
        'judge': judge,
        'new_research': new_research,
        'counts': counts,
        'health': health,
        'trends': compute_trends(all_research, signal_entries, judge_entries, now_dt),
        'judge_history': judge_history,
        'source_yield': compute_source_yield(all_research, kill_records),
        'coverage_gaps': coverage_gaps,
    }


if __name__ == '__main__':
    output = ROOT / 'site/data/brief.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build(ROOT), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
