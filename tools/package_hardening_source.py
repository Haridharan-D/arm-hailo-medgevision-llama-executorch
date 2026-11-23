"""Reviewable source-only archive; existing frozen assets remain external."""
import hashlib,json,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'validation/hardening/HARDENING_SOURCE_20261122.zip'
files=[]
for d in ['app','advisor_src','web','tools','tests','docs','native','deploy']:
    files += [p for p in (root/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'bin' not in p.parts]
files += [p for p in root.iterdir() if p.is_file() and p.suffix not in {'.log'}]
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(set(files)):z.write(p,p.relative_to(root))
manifest={'archive':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_files':len(files),'model_weights_included':False}
out.with_suffix('.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest))
