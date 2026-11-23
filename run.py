"""One-command launch after installing requirements; no automatic package downloads."""
import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--no-browser', action='store_true')
args = parser.parse_args()
missing = [name for name in ['fastapi', 'uvicorn', 'cv2', 'numpy', 'onnxruntime', 'PIL', 'tiktoken', 'psutil']
           if importlib.util.find_spec(name) is None]
if missing:
    raise SystemExit('Missing dependencies: '+', '.join(missing)+'\nRun: python -m pip install -r requirements.txt')
subprocess.run([sys.executable, str(root/'tools/verify_repository_artifacts.py')], cwd=root, check=True)
command = [sys.executable, str(root/'main.py'), '--no-browser' if args.no_browser else '--desktop']
raise SystemExit(subprocess.call(command, cwd=root))
