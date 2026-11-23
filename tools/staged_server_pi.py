"""Start/stop the candidate with isolated evidence before any production promotion."""
import argparse,json,os,subprocess,time,urllib.request,signal
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('action',choices=['start','stop']);p.add_argument('--advice',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parents[1];out=root/'validation/hardening/20261122/staged_service';out.mkdir(parents=True,exist_ok=True)
if a.action=='stop':
    if (out/'pid.json').exists():
        pid=json.loads((out/'pid.json').read_text())['pid']
        try:os.kill(pid,signal.SIGTERM)
        except ProcessLookupError:pass
    raise SystemExit(0)
try:urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8765/api/shutdown',data=b'{}'),timeout=5).read()
except Exception:pass
for _ in range(60):
    try:urllib.request.urlopen('http://127.0.0.1:8765/api/health',timeout=.3);time.sleep(.5)
    except Exception:break
cfg=json.loads((Path.home()/'BlisterTrace/BlisterTrace_App/config.json').read_text());cfg.update(auth_required=False,advice_enabled=a.advice,camera_source='0',llama_runtime=str(root/'native/bin/aarch64/blistertrace_instrumented'),llama_prompt_budget=1536)
selection=root/'validation/hardening/20261122/model_selection.json'
if selection.exists():cfg.update(json.loads(selection.read_text()).get('production_config',{}))
path=out/'config.json';path.write_text(json.dumps(cfg))
env=dict(os.environ,BLISTERTRACE_CONFIG=str(path),BLISTERTRACE_DATA=str(out/'data'))
with (out/'server.log').open('ab') as log:
    child=subprocess.Popen([str(root/'.venv/bin/python'),str(root/'main.py'),'--no-browser'],cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
(out/'pid.json').write_text(json.dumps({'pid':child.pid}))
for _ in range(90):
    if child.poll() is not None:raise SystemExit('Staged server exited')
    try:
        ready=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/ready',timeout=2))
        if ready['ready']:print('Staged Hailo service ready:',child.pid);raise SystemExit(0)
    except Exception:pass
    time.sleep(1)
raise SystemExit('Staged service readiness failed')
