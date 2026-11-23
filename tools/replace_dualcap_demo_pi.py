"""Select an actually detected example; retain all failed trial records."""
import hashlib,json,shutil,urllib.request
from pathlib import Path
base='http://127.0.0.1:8765';suite=Path.home()/'BlisterTrace_TestSuite_20261122';library=Path.home()/'BlisterTrace/BlisterTrace_App/test_images'
def call(path,data=None):
    req=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
rows=call('/api/library');trials=[];selected=None
for row in [r for r in rows if r['group']=='dual_cap']:
    r=call('/api/library/inspect',{'name':row['name']});types={d['type'] for d in r['detections']}
    trials.append({'source':row['name'],'inspection_id':r['inspection_id'],'types':sorted(types),'visual_result':r['visual_result']})
    if 'dual_cap' in types:selected=row;break
(suite/'dualcap_selection_trials.json').write_text(json.dumps(trials,indent=2))
if selected is None:raise RuntimeError('No existing dual_cap demo actually detected at frozen thresholds')
rel='YOLO/defective/dual_cap/dual_cap.jpg';dest=suite/rel;shutil.copy2(library/selected['name'],dest);sha=hashlib.sha256(dest.read_bytes()).hexdigest()
manifest=json.loads((suite/'manifest_candidates.json').read_text())
for row in manifest:
    if row['file']==rel:row.update(sha256=sha,source=selected['name'],note='Selected after actual Hailo inference; original CASE-001 miss retained in raw trials. Demonstration, not accuracy evidence.')
(suite/'manifest_candidates.json').write_text(json.dumps(manifest,indent=2))
shutil.copy2(dest,library/'acceptance_demo/defective/dual_cap/dual_cap.jpg')
for p in [suite/'YOLO/manifest.json',library/'acceptance_demo/manifest.json']:
    values=json.loads(p.read_text())
    for row in values:
        if row['file'].endswith('dual_cap/dual_cap.jpg'):row['sha256']=sha
    p.write_text(json.dumps(values,indent=2))
print(json.dumps({'selected':selected['name'],'trials':len(trials),'sha256':sha}))
