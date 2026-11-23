"""Sync the final reviewed source without replacing models, state or native binaries."""
import hashlib,json,runpy,subprocess,time,urllib.request
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122'
def hashes():
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['app','advisor_src'] for p in (root/folder).rglob('*.py')}
before=hashes()
runpy.run_path(str(root/'tools/stage_hardening_pi.py'),run_name='__main__')
after=hashes();changed=[p for p,v in after.items() if before.get(p)!=v]
if changed:subprocess.run(['systemctl','--user','restart','blistertrace.service'],check=True)
for _ in range(60):
    try:
        health=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/ready',timeout=3))
        if health.get('ready'):break
    except Exception:pass
    time.sleep(1)
else:raise RuntimeError('Service not ready after final source sync')
out={'ready':True,'changed_python':changed,'restarted':bool(changed),'models_and_native_binary_replaced':False}
(root/'validation/hardening/20261122/final_source_sync.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
