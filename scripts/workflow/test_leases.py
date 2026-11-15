import unittest
from datetime import datetime, timedelta, timezone
from leases import consumed_seconds, latest, recover, transition

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class LeaseTests(unittest.TestCase):
    def event(self, kind='claim', **extra):
        return {'event_type': kind, 'task_hash': 'a'*64, 'run_id': 'r1', 'agent_id': 'a1', 'reason': None, **extra}

    def state(self):
        receipt = {**self.event(), **transition(None, self.event(), NOW, 'a'*64, 3, True)}
        return latest([receipt])

    def test_competing_claims_and_expiry_require_recovery(self):
        state = self.state()
        with self.assertRaises(ValueError): transition(state, self.event(run_id='r2'), NOW, 'a'*64, 3, True)
        with self.assertRaises(ValueError): transition(state, self.event(run_id='r2'), NOW + timedelta(hours=3), 'a'*64, 3, True)
        with self.assertRaises(ValueError): recover(state, 'r1', 'checked', NOW)
        changed = recover(state, 'r1', 'old run inspected', NOW, 'b'*64)
        self.assertEqual(changed['event_type'], 'released')
        receipt = recover(state, 'r1', 'checked', NOW + timedelta(hours=3))
        self.assertIsNone(latest([{**self.event(), **transition(None, self.event(), NOW, 'a'*64, 3, True)}, receipt]))

    def test_heartbeat_block_resume_and_budget(self):
        state = self.state()
        blocked = transition(state, self.event('blocked', reason='need input'), NOW + timedelta(minutes=1), 'a'*64, 3, True)
        state = latest([{**self.event(), 'event_type': 'accepted', 'started_at': state['started_at'], 'lease_until': state['lease_until']}, blocked])
        self.assertEqual(state['status'], 'blocked')
        heartbeat = transition(state, self.event('heartbeat'), NOW + timedelta(hours=1), 'a'*64, 3, True)
        self.assertEqual(heartbeat['lease_until'], (NOW + timedelta(hours=3)).isoformat())
        self.assertEqual(transition(state, self.event('resume', reason='input received'), NOW + timedelta(hours=1), 'a'*64, 3, True)['event_type'], 'resumed')
        with self.assertRaises(ValueError): transition(state, self.event('heartbeat', run_id='other'), NOW, 'a'*64, 3, True)
        with self.assertRaises(ValueError): transition(None, self.event(), NOW, 'b'*64, 3, True)
        with self.assertRaises(ValueError): transition(None, self.event(), NOW, 'a'*64, None, True)
        with self.assertRaises(ValueError): transition(None, self.event(), NOW, 'a'*64, 3, False)

    def test_budget_is_shared_across_released_runs(self):
        accepted = {**self.event(), **transition(None, self.event(), NOW, 'a'*64, 3, True)}
        state = latest([accepted])
        released = {**transition(state, self.event('released'), NOW + timedelta(hours=1), 'a'*64, 3, True), 'timestamp': (NOW + timedelta(hours=1)).isoformat()}
        receipts = [accepted, released]
        self.assertEqual(consumed_seconds(receipts), 3600)
        second = transition(None, self.event(run_id='r2'), NOW + timedelta(hours=1), 'a'*64, 3, True, consumed_seconds(receipts))
        self.assertEqual(second['lease_until'], (NOW + timedelta(hours=3)).isoformat())
        with self.assertRaises(ValueError): transition(None, self.event(run_id='r3'), NOW, 'a'*64, 3, True, 3*3600)


if __name__ == '__main__': unittest.main()
