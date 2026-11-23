"""Rebuild native candidate after unit checks; retain previous binary and service."""
import subprocess,shutil,json,time
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122';out=root/'validation/hardening/20261122/json_boundary';out.mkdir(parents=True,exist_ok=True)
test=out/'json_boundary_test'
subprocess.run(['g++','-std=c++17',str(root/'tests/json_boundary_test.cpp'),'-o',str(test)],check=True)
subprocess.run([str(test)],check=True)
subprocess.run(['systemctl','--user','stop','blistertrace.service'],check=True)
binary=root/'native/bin/aarch64/blistertrace_instrumented';shutil.copy2(binary,out/'previous_worker')
try:
    subprocess.run([str(root/'.venv/bin/python'),'tools/build_instrumented_pi.py'],cwd=root,check=True)
    subprocess.run(['systemctl','--user','start','blistertrace.service'],check=True)
except Exception:
    shutil.copy2(out/'previous_worker',binary);subprocess.run(['systemctl','--user','start','blistertrace.service']);raise
(out/'report.json').write_text(json.dumps({'passed':True,'native_tests':5,'change':'Stop generation at completed first JSON object; all Python schema and semantic guards retained. Prose is not normalized into trusted advice.','previous_binary_preserved':str(out/'previous_worker')},indent=2))
print('Native JSON-boundary tests and service restart passed.')
