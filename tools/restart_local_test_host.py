import os,subprocess,psutil,sys,time,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for p in psutil.process_iter(['pid','name','cmdline']):
    if p.pid!=os.getpid() and (p.info.get('name') or '').lower().startswith('python') and any(str(a).endswith('start_test_host.py') for a in p.info.get('cmdline') or []):
        p.terminate()
        try:p.wait(timeout=10)
        except psutil.TimeoutExpired:p.kill()
out=root/'validation/hardening/local_test_data';out.mkdir(parents=True,exist_ok=True)
with (out/'host.log').open('ab') as log:
    p=subprocess.Popen([sys.executable,str(root/'tools/start_test_host.py')],cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
(out/'host_pid.json').write_text(json.dumps({'pid':p.pid}));print('Test host restarted:',p.pid)
