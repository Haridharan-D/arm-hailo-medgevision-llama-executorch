"""Apply requested no-login kiosk mode; preserve credentials and baseline."""
import json,shutil,subprocess,time,urllib.request
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122'
backup=Path.home()/('BlisterTrace/Backups/kiosk_'+time.strftime('%Y%m%d_%H%M%S'));backup.mkdir(parents=True)
cfg=root/'production_config.json';shutil.copy2(cfg,backup/'production_config.json')
v=json.loads(cfg.read_text());v['auth_required']=False;cfg.write_text(json.dumps(v,indent=2))
for name,extra in [('blistertrace',''),('blistertrace-b',' --classic')]:
    path=Path.home()/name
    if path.exists():shutil.copy2(path,backup/name)
    path.write_text('#!/bin/sh\nset -eu\nexec "$HOME/BlisterTrace/releases/hardening_20261122/.venv/bin/python" "$HOME/BlisterTrace/releases/hardening_20261122/tools/launch_monitors.py"'+extra+'\n');path.chmod(0o755)
subprocess.run(['systemctl','--user','restart','blistertrace.service'],check=True)
for _ in range(60):
    try:
        me=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/auth/me',timeout=2))
        ready=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/ready',timeout=2))
        if ready.get('ready') and not me['required']:break
    except Exception:pass
    time.sleep(.5)
else:raise RuntimeError('No-login station failed readiness check')
report={'ready':True,'authentication_required':me['required'],'credentials_preserved':True,'backup':str(backup)}
out=root/'validation/kiosk_20261122';out.mkdir(exist_ok=True);(out/'install.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
