"""Install local command launchers on the configured Raspberry Pi."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def main():
    commands={
        'blistertrace-hailo':'exec "$APP/.venv/bin/python" "$APP/tools/activate_hailo.py" --validate "$@"',
        'blistertrace-validate':'exec "$APP/.venv/bin/python" "$APP/tools/validate_current.py" "$@"',
    }
    for name,body in commands.items():
        path=Path.home()/name
        path.write_text('#!/usr/bin/env bash\nset -euo pipefail\nAPP="'+str(ROOT)+'"\n'+body+'\n')
        path.chmod(0o755)
    print(json.dumps({'commands':list(commands),'app':str(ROOT)},indent=2))

if __name__=='__main__':main()
