"""Install29marked demo images, retaining original test examples and manifests."""
import json,shutil,zipfile,hashlib,time
from pathlib import Path
base=Path.home()/'BlisterTrace/BlisterTrace_App';suite=Path.home()/'BlisterTrace_TestSuite_20261122'
archive=Path.home()/'BlisterTrace/Backups/VISUAL_SUITE_CANDIDATES_20261122.zip'
suite.mkdir(exist_ok=True)
with zipfile.ZipFile(archive) as z:
    for name in z.namelist():
        p=(suite/name).resolve()
        if suite.resolve() not in p.parents:raise ValueError('Invalid suite archive path')
    z.extractall(suite)
rows=json.loads((suite/'manifest_candidates.json').read_text());backup=Path.home()/('BlisterTrace/Backups/VisualSuiteManifests_'+time.strftime('%Y%m%d_%H%M%S'));backup.mkdir()
exposed=[]
for row in rows:
    p=suite/row['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
    if row['pipeline']=='yolo':
        rel=p.relative_to(suite/'YOLO');group='demo_'+(row.get('expected_class') or row['expected_visual'].lower())
        exposed.append({'file':(Path('acceptance_demo')/rel).as_posix(),'group':group,'case_id':row['expected_visual']+' · '+(row.get('expected_class') or p.stem),
            'label_origin':'Selected demonstration; visual model result only; see provenance','sha256':row['sha256']})
(suite/'YOLO/manifest.json').write_text(json.dumps(exposed,indent=2))
link=base/'test_images/acceptance_demo'
if link.is_symlink():
    assert link.resolve()==(suite/'YOLO').resolve();link.unlink()
shutil.copytree(suite/'YOLO',link,dirs_exist_ok=True)
for profile in ['mvtec_pill','mvtec_capsule','visa_capsules']:
    samples=base/'models/anomaly/samples'/profile;manifest=samples/'manifest.json';old=json.loads(manifest.read_text());shutil.copy2(manifest,backup/(profile+'.json'))
    original=[r for r in old if not r.get('demo_suite')];new=[]
    for row in rows:
        if row.get('profile')!=profile:continue
        source=suite/row['file'];rel=Path('demo')/row['expected_visual'].lower()/source.name;target=samples/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        new.append(dict(file=rel.as_posix(),profile=profile,label=None if row['expected_visual']=='WARNING' else 1 if row['expected_visual']=='DEFECTIVE' else 0,
            label_name=row['source_label'],source_path=row['source'],source_url=row.get('source_url','Retained local dataset provenance'),
            sha256=row['sha256'],case_id='DEMO '+row['expected_visual']+' · '+source.stem,expected_visual=row['expected_visual'],
            split='selected demonstration',demo_suite=True,selection=row['note'],blind_display=False))
    assert len(new)==6,(profile,len(new));manifest.write_text(json.dumps(new+original,indent=2))
print(json.dumps({'suite':str(suite),'images':len(rows),'originals_retained':True,'manifest_backup':str(backup)}))
