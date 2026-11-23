"""Preserve reviewed sources and inventory before the hardening changes."""
from pathlib import Path
import hashlib,json,zipfile,datetime
root=Path(__file__).resolve().parents[1]
out=root/'validation/hardening';out.mkdir(parents=True,exist_ok=True)
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
files=[]
with zipfile.ZipFile(out/f'baseline_{stamp}.zip','w',zipfile.ZIP_DEFLATED) as z:
    for part in ['app','advisor_src','web','tools','tests']:
        for p in (root/part).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                z.write(p,p.relative_to(root));files.append(p)
    for p in root.glob('*'):
        if p.is_file():z.write(p,p.name);files.append(p)
manifest={str(p.relative_to(root)):{'bytes':p.stat().st_size,'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()} for p in files}
for pattern in ['assets/*','models/*.hef','models/anomaly/*/*.onnx','llama/artifacts/*.pte']:
    for p in root.glob(pattern):
        if p.is_file():manifest[str(p.relative_to(root))]={'bytes':p.stat().st_size,'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()}
(out/'baseline_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Protected local source archive:',out/f'baseline_{stamp}.zip')
