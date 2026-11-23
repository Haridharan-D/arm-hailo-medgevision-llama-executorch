"""Archive raw measurements/reports, excluding runtime data and credentials."""
import tarfile,json,hashlib
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122';source=root/'validation/hardening/20261122';dest=Path.home()/'BlisterTrace/Backups/HARDENING_EVIDENCE_20261122.tar.gz'
files=[]
with tarfile.open(dest,'w:gz') as tar:
    for p in source.rglob('*'):
        if not p.is_file() or any(x in p.relative_to(source).parts for x in ['data','backups','images','spool']):continue
        if p.name in {'users.json','validation_account_20261122.json'}:continue
        if p.stat().st_size>20*1024*1024:continue
        tar.add(p,arcname=p.relative_to(source));files.append(str(p.relative_to(source)))
print(json.dumps({'path':str(dest),'files':len(files),'sha256':hashlib.file_digest(dest.open('rb'),'sha256').hexdigest()}))
