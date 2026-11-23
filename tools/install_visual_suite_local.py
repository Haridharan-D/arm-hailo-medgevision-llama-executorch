"""Reuse verified Pi suite in the PC dashboard, preserving historical samples."""
import json,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1];suite=root.parent/'BlisterTrace_TestSuite_20261122'
report=json.loads((suite/'verification.json').read_text());assert report['passed'] and report['checked']==29
shutil.copytree(suite/'YOLO',root/'test_images/acceptance_demo',dirs_exist_ok=True)
rows=json.loads((suite/'manifest_candidates.json').read_text())
for profile in ['mvtec_pill','mvtec_capsule','visa_capsules']:
    samples=root/'models/anomaly/samples'/profile;path=samples/'manifest.json'
    old=json.loads(path.read_text());backup=samples/'manifest_before_visual_suite.json'
    if not backup.exists():shutil.copy2(path,backup)
    original=[r for r in old if not r.get('demo_suite')];new=[]
    for row in rows:
        if row.get('profile')!=profile:continue
        p=suite/row['file'];rel=Path('demo')/row['expected_visual'].lower()/p.name;target=samples/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
        new.append(dict(file=rel.as_posix(),profile=profile,label=None if row['expected_visual']=='WARNING' else int(row['expected_visual']=='DEFECTIVE'),
            label_name=row['source_label'],source_path=row['source'],sha256=row['sha256'],source_url=row.get('source_url','Retained dataset provenance'),
            demo_suite=True,case_id='DEMO '+row['expected_visual']+' · '+p.stem,split='selected demonstration',selection=row['note'],expected_visual=row['expected_visual']))
    assert len(new)==6;path.write_text(json.dumps(new+original,indent=2))
print('Installed verified demo folders in PC source and model sample libraries.')
