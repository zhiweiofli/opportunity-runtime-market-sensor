import re
import unittest
from pathlib import Path


class WorkflowPermissionsTest(unittest.TestCase):
    def test_task_handoff_can_read_protocol_status(self):
        workflow = (Path(__file__).resolve().parents[2] / '.github/workflows/practice-handoff.yml').read_text()
        permissions = re.search(r'(?ms)^permissions:\n((?:  [^\n]+\n)+)', workflow)
        self.assertIsNotNone(permissions)
        self.assertRegex(permissions.group(1), r'(?m)^  statuses: read$')


if __name__ == '__main__':
    unittest.main()
