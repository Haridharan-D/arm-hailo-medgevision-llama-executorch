import subprocess,json
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122'
with (Path.home()/'BlisterTrace/Backups/continuation_20261122.log').open('ab') as log:
    p=subprocess.Popen([str(root/'.venv/bin/python'),str(root/'tools/continuation_jobs_pi.py')],cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
print(json.dumps({'pid':p.pid,'log':'~/BlisterTrace/Backups/continuation_20261122.log'}))
