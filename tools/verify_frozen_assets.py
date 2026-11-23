"""Assert frozen weights, threshold contract and detector code are unchanged."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];baseline=ROOT/'validation/hardening/baseline_manifest.json';data=json.loads(baseline.read_text());rows=[]
for name,expected in data.items():
    frozen=(name in {'app/vision.py','app/hailo_backend.py','app/anomaly.py','assets/thresholds.json'} or Path(name).suffix in {'.onnx','.hef','.pte'})
    if not frozen:continue
    p=ROOT/name
    if not p.exists():rows.append({'path':name,'matched':False,'error':'Missing'});continue
    with p.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    rows.append({'path':name,'sha256':actual,'expected':expected['sha256'],'matched':actual==expected['sha256']})
report={'passed':bool(rows) and all(r['matched'] for r in rows),'checks':rows,'scope':'Frozen preexisting assets and vision implementation; new separate candidate artifacts are outside this baseline.'}
out=ROOT/'validation/hardening/20261122';out.mkdir(parents=True,exist_ok=True);(out/'frozen_assets.json').write_text(json.dumps(report,indent=2));print(json.dumps({'passed':report['passed'],'frozen_files':len(rows)}))
if not report['passed']:raise SystemExit(1)
