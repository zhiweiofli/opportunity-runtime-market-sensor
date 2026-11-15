import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from validate import Validator


class SyntheticPackageTests(unittest.TestCase):
    def test_package_is_explicitly_synthetic_and_valid(self):
        source=Path(__file__).resolve().parents[2]/'examples/synthetic'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'repo'; root.mkdir()
            dest=root/'examples/synthetic'; dest.mkdir(parents=True)
            shutil.copy2(source/'build_review.py',dest/'build_review.py')
            shutil.copy2(source/'research.md',dest/'research.md')
            def git(*args): return subprocess.run(['git',*args],cwd=root,check=True,capture_output=True,text=True).stdout.strip()
            git('init','-q');git('config','user.name','Test');git('config','user.email','test@example.invalid')
            git('add','.');git('commit','-qm','fixture');base=git('rev-parse','HEAD')
            package=Path(tmp)/'package'
            subprocess.run([sys.executable,str(dest/'build_review.py'),'--id','example','--input-commit',base,'--output',str(package)],check=True,capture_output=True,text=True)
            shutil.copytree(package,root,dirs_exist_ok=True)
            self.assertEqual(Validator(root,base).run(),[])
            repeat=subprocess.run([sys.executable,str(dest/'build_review.py'),'--id','example','--input-commit',base,'--output',str(package)],capture_output=True,text=True)
            self.assertNotEqual(repeat.returncode,0)


if __name__ == '__main__': unittest.main()
