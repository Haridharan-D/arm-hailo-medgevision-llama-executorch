"""Temporary isolated-data API for controlled Hailo concurrency. No CSI calls."""
import json,os,subprocess,time,urllib.request
import psutil
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'validation/hardening/controlled_load';out.mkdir(parents=True,exist_ok=True)
try:
    req=urllib.request.Request('http://127.0.0.1:8765/api/shutdown',data=b'{}',headers={'Content-Type':'application/json'})
    urllib.request.urlopen(req,timeout=10).read()
except Exception:pass
for _ in range(60):
    try:urllib.request.urlopen('http://127.0.0.1:8765/api/health',timeout=.5);time.sleep(.5)
    except Exception:break
cfg=json.loads((Path.home()/'BlisterTrace/BlisterTrace_App/config.json').read_text());cfg.update(advice_enabled=False,auth_required=False)
path=out/'config.json';path.write_text(json.dumps(cfg))
env=dict(os.environ,BLISTERTRACE_CONFIG=str(path),BLISTERTRACE_DATA=str(out/'data'))
with (out/'api.log').open('ab') as log:
    p=subprocess.Popen([str(root/'.venv/bin/python'),str(root/'main.py'),'--no-browser'],cwd=root,env=env,stdout=log,stderr=log,stdin=subprocess.DEVNULL,start_new_session=True)
(out/'process.json').write_text(json.dumps({'pid':p.pid,'advice_disabled':True,'isolated_data':env['BLISTERTRACE_DATA']}))
print('Controlled API started:',p.pid)
for _ in range(120):
    if p.poll() is not None:raise RuntimeError('Controlled API exited; inspect api.log')
    try:
        value=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/status',timeout=2))
        if value.get('ready') and value['vision_backend']=='hailo':print('Controlled Hailo API ready');break
    except Exception:pass
    time.sleep(.5)
else:raise RuntimeError('Controlled API failed readiness; do not benchmark')
