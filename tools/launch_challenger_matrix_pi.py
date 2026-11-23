import subprocess,json
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122'
with (Path.home()/'BlisterTrace/Backups/matrix_3b_pilot_20261122.log').open('ab') as log:
    p=subprocess.Popen([str(root/'.venv/bin/python'),str(root/'tools/challenger_matrix_jobs_pi.py')],cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
print(json.dumps({'pid':p.pid,'scope':'Sequential bounded 3B timing pilot; waits for1B experiments.'}))
