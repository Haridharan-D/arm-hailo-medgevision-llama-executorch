"""Promote staged validated code; preserve source/model/data rollback checkpoints."""
import json,os,shutil,sqlite3,subprocess,time,urllib.request,hashlib
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122';old=Path.home()/'BlisterTrace/BlisterTrace_App'
back=Path.home()/'BlisterTrace/Backups/promotion_20261122';back.mkdir(parents=True,exist_ok=True)
cfg=json.loads((old/'config.json').read_text());cfg.update(port=8765,camera_source='0',auth_required=True,advice_enabled=True,llama_threads=3,
    llama_runtime=str(root/'native/bin/aarch64/blistertrace_instrumented'),llama_prompt_budget=1536)
# Prompt/model choice remains baseline unless measured challenger selection file
# explicitly records a validated template selection.
selection=root/'validation/hardening/20261122/model_selection.json'
if selection.exists():
    value=json.loads(selection.read_text());cfg.update({k:v for k,v in value.get('production_config',{}).items() if k in {'llama_prompt_mode','llama_output_tokens','llama_prompt_budget','llama_threads'}})
(root/'production_config.json').write_text(json.dumps(cfg,indent=2));os.chmod(root/'production_config.json',0o600)
data=Path.home()/'BlisterTrace_Data'
if (data/'inspections.sqlite3').exists():
    with sqlite3.connect(data/'inspections.sqlite3') as src,sqlite3.connect(back/'before_migration.sqlite3') as dst:src.backup(dst)
# Freeze artifact checks before altering launchers.
receipt={'model_files':{}}
for path in [old/'assets/blistertrace_yolov8s.onnx',old/'assets/thresholds.json',old/'models/blistertrace.hef',Path(cfg['llama_artifacts'])/'Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte']:
    with path.open('rb') as f:receipt['model_files'][str(path)]=hashlib.file_digest(f,'sha256').hexdigest()
try:urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8765/api/shutdown',data=b'{}'),timeout=5).read()
except Exception:pass
for _ in range(60):
    try:urllib.request.urlopen('http://127.0.0.1:8765/api/health',timeout=.3);time.sleep(.5)
    except Exception:break
service=Path.home()/'.config/systemd/user/blistertrace.service';service.parent.mkdir(parents=True,exist_ok=True)
if service.exists():shutil.copy2(service,back/'previous.service')
shutil.copy2(root/'deploy/blistertrace.service',service)
subprocess.run(['systemctl','--user','daemon-reload'],check=True)
subprocess.run(['systemctl','--user','enable','--now','blistertrace.service'],check=True)
for _ in range(60):
    try:
        status=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/ready',timeout=2))
        if status['ready']:break
    except Exception:time.sleep(1)
else:raise RuntimeError('Promoted service did not become ready; preserved launchers remain unchanged')
for name,url in [('blistertrace','/'),('blistertrace-b','/classic')]:
    launcher=Path.home()/name
    if launcher.is_file():shutil.copy2(launcher,back/(name+'.original'))
    text='#!/bin/sh\nset -eu\nsystemctl --user start blistertrace.service\nexec chromium --password-store=basic --user-data-dir="$HOME/.config/blistertrace-browser" --start-fullscreen http://127.0.0.1:8765'+url+'\n'
    launcher.write_text(text);launcher.chmod(0o755)
receipt.update(ready=True,baseline_preserved=str(old),rollback_backup=str(back),service='blistertrace.service',config=cfg)
(back/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({'ready':True,'service':'blistertrace.service','backup':str(back)}))
