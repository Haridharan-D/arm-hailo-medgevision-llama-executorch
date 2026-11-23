"""Read-only runtime audit plus protected source/SQLite backup. Never touches CSI."""
import hashlib,json,sqlite3,subprocess,tarfile,time
from pathlib import Path
root=Path('/home/saul/BlisterTrace/BlisterTrace_App')
stamp=time.strftime('%Y%m%d_%H%M%S')
out=Path.home()/'BlisterTrace/Backups'/('hardening_'+stamp)
out.mkdir(parents=True,exist_ok=False)
out.chmod(0o700)
files=[]
with tarfile.open(out/'source.tar.gz','w:gz') as tar:
    for part in ['app','advisor_src','web','tools','tests','main.py','config.json','launch_pi.sh']:
        p=root/part
        if p.exists():tar.add(p,arcname=part)
data=Path.home()/'BlisterTrace_Data'
if (data/'inspections.sqlite3').exists():
    with sqlite3.connect(data/'inspections.sqlite3') as src,sqlite3.connect(out/'inspections.sqlite3') as dst:src.backup(dst)
for pattern in ['app/*.py','advisor_src/*','assets/*.json','assets/*.onnx','models/*.hef','llama/artifacts/*.pte']:
    for p in root.glob(pattern):
        if p.is_file():files.append({'path':str(p),'size':p.stat().st_size,'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()})
build=Path.home()/'blistertrace_llm_build/executorch'
report={'backup':str(out),'files':files,'tree':[str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and not any(x in p.parts for x in ('.venv','__pycache__','.git'))]}
for name in ['examples/models/llama/runner/runner.h','extension/llm/runner/stats.h','extension/llm/runner/text_llm_runner.h','extension/llm/runner/text_llm_runner.cpp']:
    p=build/name
    if p.exists():report[name]=p.read_text()
report['build_flags']={str(p.relative_to(build)):[s for s in p.read_text(errors='replace').splitlines() if any(k in s.lower() for k in ['kleidi','xnnpack','threadpool','torchao'])] for p in build.glob('cmake-out/**/CMakeCache.txt')}
for name,cmd in [('services',['systemctl','--user','list-units','--type=service','--all','--no-pager']),('device',['hailortcli','fw-control','identify'])]:
    r=subprocess.run(cmd,text=True,capture_output=True,timeout=20);report[name]={'code':r.returncode,'output':r.stdout+r.stderr}
(out/'audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
