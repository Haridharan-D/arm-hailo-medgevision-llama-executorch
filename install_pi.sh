#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install --timeout 120 --retries 10 -r requirements.txt
python3 - "$APP_DIR" <<'PY'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]);config=root/'config.json'
value=json.loads(config.read_text()) if config.exists() else {}
value.update(vision_backend='onnx',profile_validated=False)
hef=root/'models/blistertrace.hef'
if hef.is_file():
    value['hef']=str(hef)
    print('Compiled HEF found. Retaining CPU until actual device/inference verification.')
    print('After connecting Hailo, activate and validate with: ~/blistertrace-hailo')
llm=Path.home()/'BlisterTrace/Llama_ExecuTorch'
value['llama_runtime']=str(llm/'bin/aarch64/blistertrace_worker')
value['llama_artifacts']=str(llm/'artifacts')
config.write_text(json.dumps(value,indent=2))
desktop=Path.home()/'Desktop';desktop.mkdir(exist_ok=True)
entry=desktop/'BlisterTrace.desktop'
entry.write_text('[Desktop Entry]\nType=Application\nName=BlisterTrace\nComment=Offline blister-pack inspection\nExec=bash "'+str(root/'launch_pi.sh')+'"\nTerminal=false\nCategories=Science;\n')
entry.chmod(0o755)
launcher=root/'launch_pi.sh';launcher.chmod(0o755)
command=Path.home()/'blistertrace'
if not command.exists() or 'BlisterTrace' in command.read_text(errors='replace'):
    command.write_text('#!/usr/bin/env bash\nexec bash "'+str(launcher)+'" "$@"\n')
    command.chmod(0o755)
print('Pi launcher created:',entry)
print('Selected vision backend:',value['vision_backend'])
print('One-command launch: ~/blistertrace')
diagnostic=Path.home()/'blistertrace-test'
if not diagnostic.exists() or 'BlisterTrace' in diagnostic.read_text(errors='replace'):
    diagnostic.write_text('#!/usr/bin/env bash\nexec "'+str(root/'.venv/bin/python')+'" "'+str(root/'tools/terminal_test.py')+'" "$@"\n')
    diagnostic.chmod(0o755)
print('Terminal diagnostics: ~/blistertrace-test --seconds 60')
PY
.venv/bin/python tools/install_validation_commands.py
printf 'Ready. Run: bash "%s/launch_pi.sh"\n' "$APP_DIR"
