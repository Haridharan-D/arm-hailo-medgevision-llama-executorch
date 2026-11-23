"""Deploy static assets only; do not restart or modify backend/models/database."""
import hashlib,json,subprocess,zipfile,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
before=json.loads((root/'validation/premium_backend_before.json').read_text())
changed=[name for name,sha in before.items() if hashlib.sha256((root/name).read_bytes()).hexdigest()!=sha]
assert not changed,changed
archive=root.parent/'BlisterTrace_Premium_UI.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in (root/'web').rglob('*'):
        if p.is_file():z.write(p,p.relative_to(root/'web'))
target=root/'dist/BlisterTrace/_internal/web'
if target.exists():shutil.copytree(root/'web',target,dirs_exist_ok=True)
key=Path.home()/'.ssh/blistertrace_pi'
host='saul@10.217.96.102'
options=['-i',str(key),'-o','BatchMode=yes','-o','ConnectTimeout=10']
subprocess.run(['scp',*options,str(archive),host+':/home/saul/BlisterTrace_Premium_UI.zip'],check=True)
remote="""
from pathlib import Path
import zipfile,datetime,json
root=Path('/home/saul/BlisterTrace/BlisterTrace_App/web').resolve()
assert root.name=='web' and root.parent.name=='BlisterTrace_App'
backup=root.parent/('web_before_premium_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.zip')
with zipfile.ZipFile(backup,'w',zipfile.ZIP_DEFLATED) as z:
    for p in root.rglob('*'):
        if p.is_file():z.write(p,p.relative_to(root))
with zipfile.ZipFile('/home/saul/BlisterTrace_Premium_UI.zip') as z:
    for name in z.namelist():
        dest=(root/name).resolve()
        assert dest.is_relative_to(root)
    z.extractall(root)
print(json.dumps({'web_deployed':str(root),'backup':str(backup),'backend_restart':False}))
"""
result=subprocess.run(['ssh',*options,host,'python3 -'],input=remote,text=True,capture_output=True,check=True)
report={'backend_hashes_unchanged':True,'archive':str(archive),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'windows_static_updated':target.exists(),'pi':json.loads(result.stdout)}
(root/'validation/premium_deployment.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
