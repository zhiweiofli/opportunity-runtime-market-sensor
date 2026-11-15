"""Deterministic task lease transitions; callers authenticate GitHub comments."""
from datetime import timedelta
from validate import parse_time


def latest(receipts):
    state = None
    for receipt in receipts:
        kind = receipt.get('event_type')
        if kind == 'accepted':
            state = {'run_id': receipt['run_id'], 'agent_id': receipt['agent_id'], 'task_hash': receipt['task_hash'], 'started_at': receipt['started_at'], 'lease_until': receipt['lease_until'], 'status': 'active'}
        elif kind in ('heartbeat', 'blocked', 'resumed') and state:
            state['lease_until'] = receipt['lease_until']
            if kind == 'blocked': state['status'] = 'blocked'
            if kind == 'resumed': state['status'] = 'active'
        elif kind == 'released':
            state = None
    return state


def transition(state, event, now, current_hash, budget_hours, runnable):
    """Return a receipt fragment or raise ValueError; never infer permission from expiry."""
    kind = event['event_type']
    if not runnable: raise ValueError('task is stopped or already complete')
    if event['task_hash'] != current_hash: raise ValueError('task hash is stale')
    if budget_hours is None or budget_hours <= 0: raise ValueError('duration budget is unknown or exhausted')
    if kind == 'claim':
        if state: raise ValueError('existing lease requires release or human recovery')
        until = min(now + timedelta(hours=2), now + timedelta(hours=budget_hours))
        return {'event_type': 'accepted', 'started_at': now.isoformat(), 'lease_until': until.isoformat(), 'reason': None}
    if not state: raise ValueError('no active lease')
    if (event['run_id'], event['agent_id'], event['task_hash']) != (state['run_id'], state['agent_id'], state['task_hash']):
        raise ValueError('request does not own lease')
    if parse_time(state['lease_until']) <= now: raise ValueError('expired lease requires human recovery')
    if kind in ('blocked', 'resume') and not event['reason']: raise ValueError('reason required')
    if kind == 'resume' and state['status'] != 'blocked': raise ValueError('lease is not blocked')
    if kind == 'blocked' and state['status'] == 'blocked': raise ValueError('lease is already blocked')
    if kind == 'released':
        return {'event_type': 'released', 'started_at': state['started_at'], 'lease_until': None, 'reason': event['reason']}
    if kind not in ('heartbeat', 'blocked', 'resume'): raise ValueError('unknown event type')
    end = parse_time(state['started_at']) + timedelta(hours=budget_hours)
    until = min(now + timedelta(hours=2), end)
    if until <= now: raise ValueError('duration budget exhausted')
    return {'event_type': {'resume': 'resumed'}.get(kind, kind), 'started_at': state['started_at'], 'lease_until': until.isoformat(), 'reason': event['reason']}


def recover(state, run_id, reason, now):
    if not state or state['run_id'] != run_id: raise ValueError('no matching lease to recover')
    if parse_time(state['lease_until']) > now: raise ValueError('lease has not expired')
    if not reason: raise ValueError('recovery reason required')
    return {'event_type': 'released', 'started_at': state['started_at'], 'lease_until': None, 'reason': reason}
