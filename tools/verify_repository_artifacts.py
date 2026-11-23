"""Verify frozen artifacts; missing gated Llama files are reported, not fabricated."""
from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[1]
failed=False
for item in json.loads((root/'ARTIFACT_MANIFEST.json').read_text()):
 p=root/item['path']
 if not p.exists():
  print(('MISSING REQUIRED ' if item['included_in_git'] else 'EXTERNAL REQUIRED FOR LLAMA ')+item['path'])
  failed |= item['included_in_git'];continue
 with p.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
 ok=digest==item['sha256'] and p.stat().st_size==item['bytes']
 print(('OK ' if ok else 'MISMATCH ')+item['path']);failed |= not ok
sys.exit(1 if failed else 0)
