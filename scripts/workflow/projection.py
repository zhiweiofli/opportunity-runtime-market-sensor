"""Pure, allowlisted public workflow projection. Input has already been verified."""
from datetime import datetime, timedelta, timezone
from leases import latest
from validate import parse_time

OPP_PUBLIC = ('title', 'summary', 'customer_summary', 'economic_anchor', 'gate_summary', 'unknown_summary', 'next_step_summary')
TASK_PUBLIC = ('question_summary', 'criteria_summary', 'budget')
RESULT_PUBLIC = ('summary', 'actual_cost')
RESEARCH_STATUS = {'Discussion', 'Behavior', 'Workaround', 'Price/Contract', 'Payment', 'Repeatable Profit', 'KILL', 'HYPOTHESIS_READY', 'BLOCKED', 'WATCH', 'R1', 'R2', 'R3', 'unknown'}


def stamp(value, now):
    if not value: return None
    try:
        v = parse_time(value)
        return v.isoformat() if v <= now else None
    except (ValueError, TypeError): return None


def elapsed(value, now):
    t = stamp(value, now)
    return max(0, int((now - parse_time(t)).total_seconds())) if t else None


def public_fields(obj, allowed):
    value = obj.get('public') or {}
    output = {}
    for key in allowed:
        if key not in value: continue
        field = value[key]
        if key in ('economic_anchor', 'budget', 'actual_cost'):
            field = {k: field[k] for k in ('value', 'currency', 'unit', 'basis') if k in field}
        elif key == 'gate_summary':
            field = {k: field[k] for k in ('money', 'mechanism', 'persistence', 'capture') if k in field}
        output[key] = field
    return output


def project(data, now):
    now = now.astimezone(timezone.utc)
    window = now - timedelta(days=90)
    cutoff = now.isoformat()
    opps = {x['data']['opportunity_id']: x for x in data['opportunities'] if x['data']['execution_mode'] == 'real'}
    tasks = {x['data']['task_id']: x for x in data['tasks'] if x['data']['execution_mode'] == 'real' and x['data']['opportunity_id'] in opps}
    results = [x for x in data['results'] if x['data']['task_id'] in tasks]
    decisions = [x for x in data['decisions'] if x['data']['opportunity_id'] in opps]
    prs = data['pull_requests']
    issues = data['issues']
    verified_prs = [p for p in prs if p['verified'] and p['execution_mode'] == 'real']
    result_prs = [p for p in verified_prs if p['kind'] == 'practice-result']
    review_prs = [p for p in verified_prs if p['kind'] == 'review']
    decision_prs = [p for p in verified_prs if p['kind'] == 'decision']
    by_task = {}
    covered = {(d['data']['opportunity_id'], d['data']['run_id']) for d in decisions if d['data']['run_id']}
    waiting = {r['data']['opportunity_id'] for r in results if (r['data']['opportunity_id'], r['data']['run_id']) not in covered}
    heartbeat_times = []
    for task_id, entry in tasks.items():
        task = entry['data']
        task_results = [r for r in results if r['data']['task_id'] == task_id]
        task_results.sort(key=lambda r: r['merged_at'])
        current_result = task_results[-1] if task_results else None
        open_result = next((p for p in result_prs if task_id in p['task_ids']), None)
        matching_issues = issues.get(task_id, [])
        issue = matching_issues[0] if len(matching_issues) == 1 else None
        receipts = issue['receipts'] if issue else []
        state = latest(receipts)
        heartbeat = next((r for r in reversed(receipts) if r.get('event_type') in ('accepted', 'heartbeat')), None)
        stage_change = next((r for r in reversed(receipts) if r.get('event_type') in ('accepted', 'blocked', 'resumed')), None)
        task_decisions = sorted((d for d in decisions if d['data']['opportunity_id'] == task['opportunity_id']), key=lambda d: d['merged_at'])
        last_decision = task_decisions[-1] if task_decisions else None
        for r in receipts:
            if r.get('event_type') in ('accepted', 'heartbeat'):
                t = stamp(r.get('timestamp'), now)
                if t: heartbeat_times.append(t)
        link = None
        entered = None
        if open_result:
            stage, entered, link = '待结果验收', open_result['created_at'], open_result['url']
        elif current_result:
            relevant = [d for d in task_decisions if d['data']['run_id'] == current_result['data']['run_id']]
            if relevant:
                d = relevant[-1]
                stage, entered, link = {'launch': '已立项', 'pause': '暂缓', 'close': '已关闭', 'continue': '继续验证'}[d['data']['action']], d['merged_at'], d['url']
            else:
                stage, entered, link = '待立项决定', current_result['merged_at'], issue['url'] if issue else current_result['url']
        elif last_decision and (last_decision['data']['action'] != 'continue' or last_decision['data']['new_task_id'] != task_id):
            stage = {'launch': '已立项', 'pause': '暂缓', 'close': '已关闭', 'continue': '已替代'}[last_decision['data']['action']]
            entered, link = last_decision['merged_at'], last_decision['url']
        elif len(matching_issues) > 1:
            stage = '状态未知'
        elif issue and issue.get('state') != 'open':
            stage = '状态未知'
            link = issue['url']
        elif state and entry.get('task_hash') and state['task_hash'] != entry['task_hash']:
            stage, entered, link = '待恢复', entry['merged_at'], issue['url'] if issue else None
        elif state:
            try: expired = parse_time(state['lease_until']) <= now
            except (TypeError, ValueError): expired = True
            stage = '待恢复' if expired else ('实践阻塞' if state['status'] == 'blocked' else '实践中')
            entered = state['lease_until'] if expired else (stage_change or {}).get('timestamp')
            link = issue['url'] if issue else None
        else:
            stage, entered, link = '待领取', entry['merged_at'], issue['url'] if issue else None
        history = [{'at': stamp(entry['merged_at'], now), 'action': '任务批准', 'actor': '人类', 'url': entry['url']}]
        for r in receipts:
            label = {'accepted': '领取确认', 'heartbeat': '心跳', 'blocked': '阻塞', 'resumed': '恢复', 'released': '释放'}.get(r.get('event_type'))
            if label: history.append({'at': stamp(r.get('timestamp'), now), 'action': label, 'actor': '实践 Agent' if label != '释放' else '中心回执', 'url': issue['url'] if issue else None})
        if current_result: history.append({'at': stamp(current_result['merged_at'], now), 'action': '结果合并', 'actor': '人类', 'url': current_result['url']})
        by_task[task_id] = {'public': public_fields(task, TASK_PUBLIC), 'stage': stage, 'entered_at': stamp(entered, now), 'waiting_seconds': elapsed(entered, now), 'url': link, 'started_at': stamp(state['started_at'], now) if state else None, 'heartbeat_at': stamp((heartbeat or {}).get('timestamp'), now), 'claimant': '实践 Agent' if state else None, 'latest_result': public_fields(current_result['data'], RESULT_PUBLIC) if current_result else None, 'history': history}
    cards = []
    for oid, entry in opps.items():
        opportunity = entry['data']
        if not opportunity.get('public'): continue
        members = [(tid, t) for tid, t in tasks.items() if t['data']['opportunity_id'] == oid]
        task_cards = [by_task[tid] for tid, _ in members]
        matching_prs = [p for p in decision_prs if oid in p['opportunity_ids']]
        ds = sorted((d for d in decisions if d['data']['opportunity_id'] == oid), key=lambda d: d['merged_at'])
        pending_review = next((p for p in review_prs if oid in p['opportunity_ids']), None)
        if pending_review: stage, url = '待评审合并', pending_review['url']
        elif matching_prs: stage, url = '决定待入库', matching_prs[0]['url']
        elif oid in waiting: stage, url = '待立项决定', next((t['url'] for t in task_cards if t['stage'] == '待立项决定'), None)
        else:
            priorities = ['待结果验收', '实践阻塞', '待恢复', '实践中', '待领取', '状态未知']
            active = next((t for name in priorities for t in task_cards if t['stage'] == name), None)
            if active: stage, url = active['stage'], active['url']
            elif ds:
                stage = {'launch': '已立项', 'pause': '暂缓', 'close': '已关闭', 'continue': '继续验证'}[ds[-1]['data']['action']]
                url = ds[-1]['url']
            else: stage, url = '尚无实践任务', entry['url']
        history = [{'at': stamp(entry['merged_at'], now), 'action': '机会入库', 'actor': '人类', 'url': entry['url']}]
        history += [{'at': stamp(d['merged_at'], now), 'action': {'launch':'立项','continue':'继续验证','pause':'暂缓','close':'关闭'}[d['data']['action']], 'actor': '人类', 'url': d['url']} for d in ds]
        history.sort(key=lambda x: x['at'] or '')
        relevant_task = next((t for t in task_cards if t['stage'] == stage), None)
        entered_at = (pending_review['created_at'] if stage == '待评审合并' else matching_prs[0]['created_at'] if stage == '决定待入库' else relevant_task['entered_at'] if relevant_task else ds[-1]['merged_at'] if ds else entry['merged_at'])
        cards.append({'public': public_fields(opportunity, OPP_PUBLIC), 'research_status': opportunity['research_status'] if opportunity['research_status'] in RESEARCH_STATUS else 'unknown', 'judge_recommendation': opportunity['judge_recommendation'], 'stage': stage, 'entered_at': stamp(entered_at, now), 'waiting_seconds': elapsed(entered_at, now), 'url': url, 'tasks': task_cards, 'history': history})
    for p in review_prs:
        for candidate in p.get('public_opportunities', []):
            if candidate['opportunity_id'] not in opps and candidate.get('public'):
                cards.append({'public': public_fields(candidate, OPP_PUBLIC), 'research_status': candidate['research_status'] if candidate['research_status'] in RESEARCH_STATUS else 'unknown', 'judge_recommendation': candidate['judge_recommendation'], 'stage': '待评审合并', 'entered_at': stamp(p['created_at'], now), 'waiting_seconds': elapsed(p['created_at'], now), 'url': p['url'], 'tasks': [], 'history': [{'at': stamp(p['created_at'], now), 'action': '评审提案', 'actor': 'Judge', 'url': p['url']}]})
    cohort_tasks = [t for t in tasks.values() if stamp(t['data']['created_at'], now) and parse_time(t['data']['created_at']) >= window]
    completed_ids = {r['data']['task_id'] for r in results}
    task_ids = {t['data']['task_id'] for t in cohort_tasks}
    cohort_opps = {oid for oid, o in opps.items() if stamp(o['data']['created_at'], now) and parse_time(o['data']['created_at']) >= window}
    validated_opps = {t['data']['opportunity_id'] for t in tasks.values()} & cohort_opps
    launched_opps = {d['data']['opportunity_id'] for d in decisions if d['data']['action'] == 'launch'} & validated_opps
    return {'schema_version': 'or-workflow-dashboard@1', 'generated_at': cutoff, 'window_start': window.isoformat(), 'observation_cutoff': cutoff, 'last_judge_at': stamp(data.get('last_judge_at'), now), 'last_heartbeat_at': max(heartbeat_times, default=None), 'github_synced_at': stamp(data.get('github_synced_at'), now), 'last_pages_deploy_at': stamp(data.get('last_pages_deploy_at'), now), 'counts': {'open_review_prs': len(review_prs), 'open_result_prs': len(result_prs), 'unverified_prs': len([p for p in prs if not p['verified']]), 'opportunities_awaiting_decision': len(waiting)}, 'completion': {'numerator': len(task_ids & completed_ids), 'denominator': len(task_ids)}, 'conversion': {'numerator': len(launched_opps), 'denominator': len(validated_opps)}, 'opportunities': cards}
