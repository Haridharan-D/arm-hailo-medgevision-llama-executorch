"""Install short terminal and web launch aliases on the existing offline Pi."""
import os,shutil,subprocess,time,json
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122'
assert (root/'tools/medge_demo.py').is_file()
backup=Path.home()/('BlisterTrace/Backups/MedgeRename_'+time.strftime('%Y%m%d_%H%M%S'));backup.mkdir(parents=True)
for name,body in {
 'medge-demo':'#!/bin/sh\nset -eu\nexec "$HOME/BlisterTrace/releases/hardening_20261122/.venv/bin/python" "$HOME/BlisterTrace/releases/hardening_20261122/tools/medge_demo.py" "$@"\n',
 'medge-vision':'#!/bin/sh\nset -eu\nexec "$HOME/blistertrace" "$@"\n',
}.items():
    p=Path.home()/name
    if p.exists():shutil.copy2(p,backup/name)
    p.write_text(body);p.chmod(0o755)
service=Path.home()/'.config/systemd/user/blistertrace.service'
if service.exists():
    shutil.copy2(service,backup/'previous.service')
    service.write_text(service.read_text().replace('Description=BlisterTrace','Description=Medge Vision'))
    subprocess.run(['systemctl','--user','daemon-reload'],check=True)
print(json.dumps({'terminal':'~/medge-demo','dashboard':'~/medge-vision','branding':'Medge Vision','baseline_paths_preserved':True,'backup':str(backup)}))
