"""Create neutral physical filenames while preserving original labels/provenance privately in manifests."""
from pathlib import Path
import hashlib,json,random,shutil
ROOT=Path(__file__).resolve().parents[1]
for profile in ('mvtec_pill','mvtec_capsule','visa_capsules'):
    folder=ROOT/'models/anomaly/samples'/profile;manifest=folder/'manifest.json'
    rows=json.loads(manifest.read_text());assert len(rows)==20
    if all(r.get('case_id') for r in rows):continue
    random.Random(20261120).shuffle(rows)
    for i,row in enumerate(rows,1):
        old=folder/row['file'];name='CASE-'+str(i).zfill(3)+old.suffix.lower()
        assert hashlib.sha256(old.read_bytes()).hexdigest()==row['sha256']
        dest=folder/name;shutil.copy2(old,dest);row.update(file=name,case_id='CASE-'+str(i).zfill(3),blind_display=True)
    manifest.write_text(json.dumps(rows,indent=2))
    keep={r['file'] for r in rows}
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in {'.jpg','.png'} and p.name not in keep:
            dest=ROOT/'models/anomaly/legacy_samples_v5'/profile/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(p),str(dest))
    assert sum(r['label']==0 for r in rows)==sum(r['label']==1 for r in rows)==10
folder=ROOT/'test_images/defects';manifest=folder/'manifest.json';rows=json.loads(manifest.read_text())
counts={}
for row in rows:
    counts[row['group']]=counts.get(row['group'],0)+1
    old=ROOT/'test_images'/row['file'];name='CASE-'+str(counts[row['group']]).zfill(3)+old.suffix.lower();dest=old.parent/name
    if old!=dest:
        shutil.copy2(old,dest)
        previous=ROOT/'test_images_legacy_v5'/row['file'];previous.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(old),str(previous))
    row.update(file=dest.relative_to(ROOT/'test_images').as_posix(),case_id=Path(name).stem)
manifest.write_text(json.dumps(rows,indent=2));print(json.dumps({'defect_folders':counts,'anomaly':'20 per profile, 10 normal / 10 defect, shuffled independently of scores'}))
