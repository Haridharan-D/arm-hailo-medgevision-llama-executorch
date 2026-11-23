"""Optional Drive mirror download. File IDs must refer to an actual uploaded artifact."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--artifact',required=True,help='Exact path in ARTIFACT_MANIFEST.json')
p.add_argument('--file-id',required=True,help='Shared Google Drive file ID, not folder ID')
a=p.parse_args()
entry=next((v for v in json.loads((root/'ARTIFACT_MANIFEST.json').read_text()) if v['path']==a.artifact),None)
if entry is None:raise SystemExit('Unregistered artifact')
if not a.file_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in a.file_id):raise SystemExit('Invalid Drive file ID')
target=root/entry['path'];target.parent.mkdir(parents=True,exist_ok=True);partial=target.with_suffix(target.suffix+'.partial')
subprocess.run([sys.executable,'-m','gdown','https://drive.google.com/uc?id='+a.file_id,'-O',str(partial)],check=True)
with partial.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
if sha!=entry['sha256'] or partial.stat().st_size!=entry['bytes']:raise SystemExit('Download rejected: artifact checksum/size mismatch')
os.replace(partial,target);print('Verified:',target)
