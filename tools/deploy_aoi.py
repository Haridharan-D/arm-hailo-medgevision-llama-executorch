"""Deploy only application source to the authorized Pi; retain models and logs."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    archive=ROOT/'validation/BlisterTrace_AOI_Update.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as zipped:
        for folder in ['app','web','tests']:
            for path in (ROOT/folder).rglob('*'):
                if path.is_file() and '__pycache__' not in path.parts:zipped.write(path,path.relative_to(ROOT).as_posix())
        for name in ['main.py','launch_pi.sh','install_pi.sh']:
            zipped.writestr(name,(ROOT/name).read_bytes().replace(b'\r\n',b'\n'))
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    key=str(Path.home()/'.ssh/blistertrace_pi');host='saul@10.217.96.102'
    subprocess.run(['scp','-i',key,'-o','BatchMode=yes',str(archive),host+':/home/saul/BlisterTrace/BlisterTrace_AOI_Update.zip'],check=True)
    script='''
import hashlib,json,os,subprocess,time,urllib.request,zipfile
from datetime import datetime
from pathlib import Path
base=Path.home()/'BlisterTrace';root=base/'BlisterTrace_App'
archive=base/'BlisterTrace_AOI_Update.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==EXPECTED
assert root.is_dir() and (root/'.venv/bin/python').exists()
try:
    urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8765/api/shutdown',method='POST'),timeout=5).read()
    time.sleep(3)
except OSError:pass
backups=base/'Backups';backups.mkdir(exist_ok=True)
backup=backups/('before_aoi_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.zip')
with zipfile.ZipFile(archive) as source,zipfile.ZipFile(backup,'w',zipfile.ZIP_DEFLATED) as dest:
    for name in source.namelist():
        target=(root/name).resolve();assert target.is_relative_to(root.resolve())
        if target.exists():dest.write(target,name)
    for name in source.namelist():
        target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read(name))
(root/'launch_pi.sh').chmod(0o755)
launcher=Path.home()/'blistertrace'
if launcher.exists() and 'BlisterTrace' not in launcher.read_text(errors='replace'):
    raise RuntimeError('A different home launcher exists; no overwrite performed')
launcher.write_text('#!/usr/bin/env bash\\nexec bash "'+str(root/'launch_pi.sh')+'" "$@"\\n');launcher.chmod(0o755)
desktop=Path.home()/'Desktop/BlisterTrace.desktop'
desktop.write_text('[Desktop Entry]\\nType=Application\\nName=BlisterTrace AOI\\nComment=Offline optical inspection workstation\\nExec=bash "'+str(root/'launch_pi.sh')+'"\\nTerminal=false\\nCategories=Science;\\n');desktop.chmod(0o755)
subprocess.run([str(root/'.venv/bin/python'),'-m','compileall','-q',str(root/'app'),str(root/'main.py')],check=True)
began=time.monotonic()
with (root/'application_server.log').open('ab') as log:
    process=subprocess.Popen([str(root/'.venv/bin/python'),'main.py','--no-browser'],cwd=root,
        stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(root/'server.pid').write_text(str(process.pid))
served=None
for _ in range(120):
    if process.poll() is not None:raise RuntimeError('Service exited. Read application_server.log')
    try:
        with urllib.request.urlopen('http://127.0.0.1:8765/api/health',timeout=2) as response:health=json.load(response)
        if served is None:served=round(time.monotonic()-began,3)
        if health.get('startup_error'):raise RuntimeError(health['startup_error'])
        if health['ready']:break
    except OSError:pass
    time.sleep(.25)
else:raise RuntimeError('Runtime readiness timed out')
with urllib.request.urlopen('http://127.0.0.1:8765/api/status',timeout=5) as response:status=json.load(response)
print(json.dumps({'source_deployed':True,'backup':str(backup),'service_pid':process.pid,
 'health_served_seconds':served,'vision_ready_seconds':round(time.monotonic()-began,3),
 'backend':status['vision_backend'],'version':status['version'],'one_command':'~/blistertrace',
 'model_files_preserved':True,'camera':status['camera']},indent=2))
'''.replace('EXPECTED',repr(digest))
    result=subprocess.run(['ssh','-i',key,'-o','BatchMode=yes',host,'python3','-'],
                          input=script,capture_output=True,text=True,check=True)
    report=json.loads(result.stdout);(ROOT/'validation/aoi_pi_deployment.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
