"""Run target checks using the configured backend and a new evidence directory."""
from datetime import datetime,timezone
from pathlib import Path
import json
import os
import sys
ROOT=Path(__file__).resolve().parents[1]

def main():
    config=json.loads((ROOT/'config.json').read_text())
    output=ROOT/'validation'/('target_'+datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S'))
    os.execv(sys.executable,[sys.executable,str(ROOT/'tools/validate_submission_target.py'),
        '--expected-backend',config.get('vision_backend','onnx'),'--output',str(output),*sys.argv[1:]])

if __name__=='__main__':main()
