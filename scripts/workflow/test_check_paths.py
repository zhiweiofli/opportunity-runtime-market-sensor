import unittest
import subprocess
import sys
import tempfile
from pathlib import Path
from check_paths import allowed


class PathBoundaryTests(unittest.TestCase):
    def test_permitted_business_changes(self):
        for kind, status, path in [
            ('review', 'A', 'opportunities/opp-1/opportunity.json'),
            ('review', 'A', 'practice/inbox/task-1/task.json'),
            ('review', 'M', 'or-archive/manifest.json'),
            ('practice-result', 'A', 'practice/results/task-1/run-1/result.json'),
            ('decision', 'A', 'opportunities/opp-1/decisions/decision-1.json'),
            ('archive', 'M', 'or-archive/research/doc.md'),
        ]:
            with self.subTest(kind=kind, path=path):
                self.assertTrue(allowed(kind, status, path))

    def test_rejects_scope_escape_and_history_changes(self):
        for kind, status, path in [
            ('review', 'M', '.github/workflows/market-ci.yml'),
            ('review', 'M', 'scripts/workflow/check_paths.py'),
            ('review', 'M', 'practice/inbox/task-1/task.json'),
            ('practice-result', 'M', 'practice/results/task-1/run-1/result.json'),
            ('decision', 'D', 'opportunities/opp-1/decisions/d.json'),
            ('archive', 'A', 'or-archive/../site/index.html'),
            ('decision', 'A', 'opportunities/../decisions/d.json'),
        ]:
            with self.subTest(kind=kind, path=path):
                self.assertFalse(allowed(kind, status, path))

    def test_cli_reads_the_actual_git_diff(self):
        script = Path(__file__).with_name('check_paths.py').resolve()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
            git('init', '-q')
            git('config', 'user.name', 'Test')
            git('config', 'user.email', 'test@example.invalid')
            (root / 'README').write_text('base')
            git('add', '.')
            git('commit', '-qm', 'base')
            base = git('rev-parse', 'HEAD')
            path = root / 'practice/inbox/task-1/task.json'
            path.parent.mkdir(parents=True)
            path.write_text('{}')
            git('add', '.')
            git('commit', '-qm', 'task')
            def check():
                return subprocess.run([sys.executable, str(script), '--type', 'review', '--base', base, '--head', 'HEAD'], cwd=root, capture_output=True)
            self.assertEqual(check().returncode, 0)
            (root / 'README').write_text('changed')
            git('add', '.')
            git('commit', '-qm', 'unrelated change')
            self.assertEqual(check().returncode, 1)


if __name__ == '__main__':
    unittest.main()
