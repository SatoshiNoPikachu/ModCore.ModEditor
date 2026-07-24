from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).parent.parent

sources = ['ui']

files = [str(p) for p in PROJECT_ROOT.glob('*.py')]

for source in sources:
    files.extend([str(p) for p in (PROJECT_ROOT / source).glob('*.py')])

subprocess.run(["pylupdate5", *files, "-ts", "zh_CN.ts"], cwd=PROJECT_ROOT, check=True)
