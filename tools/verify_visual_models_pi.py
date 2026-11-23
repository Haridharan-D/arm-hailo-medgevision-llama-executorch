import hashlib,json
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122';receipt=json.loads((root/'validation/hardening/20261122/frozen_target.json').read_text());rows=[]
for row in receipt['checks']:
    p=Path(row['path'])
    with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    rows.append({'path':str(p),'expected':row['expected'],'actual':sha,'matched':sha==row['expected']})
out=root/'validation/visual_suite_20261122';out.mkdir(exist_ok=True);report={'passed':all(r['matched'] for r in rows),'checks':rows};(out/'frozen_models.json').write_text(json.dumps(report,indent=2));assert report['passed'];print(json.dumps({'passed':True,'unchanged_artifacts':len(rows)}))
