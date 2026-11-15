#!/usr/bin/env python3
"""Run a local synthetic lease handshake without contacting GitHub."""
import json
from datetime import datetime, timedelta, timezone
from leases import latest, recover, transition


def main():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    event = {'event_type':'claim', 'task_hash':'a'*64, 'run_id':'synthetic-run-1', 'agent_id':'synthetic-consumer', 'reason':None}
    accepted = {**event, **transition(None, event, now, 'a'*64, 3, True)}
    state = latest([accepted])
    try:
        transition(state, {**event, 'run_id':'synthetic-run-2'}, now, 'a'*64, 3, True)
    except ValueError:
        competitor = 'rejected'
    else:
        raise RuntimeError('competing claim unexpectedly accepted')
    heartbeat = transition(state, {**event, 'event_type':'heartbeat'}, now + timedelta(minutes=30), 'a'*64, 3, True)
    state = latest([accepted, heartbeat])
    try:
        transition(state, event, now + timedelta(hours=4), 'a'*64, 3, True)
    except ValueError:
        expired = 'requires human recovery'
    else:
        raise RuntimeError('expired lease unexpectedly accepted')
    recovered = recover(state, 'synthetic-run-1', 'synthetic side effects checked', now + timedelta(hours=4))
    print(json.dumps({'consumer_type':'synthetic', 'github_contacted':False, 'first_claim':accepted['event_type'], 'competing_claim':competitor, 'heartbeat':heartbeat['event_type'], 'expired_lease':expired, 'recovery':recovered['event_type']}, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
