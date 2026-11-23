"""Retain suite receipts and mark synthetic warnings as having no dataset label."""
import json
from pathlib import Path
base=Path.home()/'BlisterTrace/BlisterTrace_App';root=Path.home()/'BlisterTrace/releases/hardening_20261122'
for profile in ['mvtec_pill','mvtec_capsule','visa_capsules']:
    path=base/'models/anomaly/samples'/profile/'manifest.json';rows=json.loads(path.read_text())
    for row in rows:
        if row.get('demo_suite') and row.get('expected_visual')=='WARNING':row['label']=None
    path.write_text(json.dumps(rows,indent=2))
suite=Path.home()/'BlisterTrace_TestSuite_20261122';report=json.loads((suite/'verification.json').read_text());assert report['passed'] and report['checked']==29
print(json.dumps({'passed':True,'verified_suite':str(suite),'labeled_normal_defective_and_synthetic_warnings_separate':True}))
