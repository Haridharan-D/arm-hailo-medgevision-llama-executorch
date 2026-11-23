"""Screen actual model outputs to build a clearly marked demonstration set."""
import json,hashlib,shutil,zipfile,sys
from pathlib import Path
import cv2,numpy as np
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from app.anomaly import AnomalyEngine
out=root/'validation/visual_suite_20261122';out.mkdir(exist_ok=True)
dest=root.parent/'BlisterTrace_TestSuite_20261122';dest.mkdir(exist_ok=True)
archive=root.parent/'Dataset/SCOA Pharmaceutical Blister Image Dataset/SCOA_blister_images_v1.0/SCOA_blister_images_v1.0.zip1'
with zipfile.ZipFile(archive) as z:
    for id in [1447,4627,6977,7468]:
        p=out/f'SCOA_{id}.jpg'
        if not p.exists():p.write_bytes(z.read(f'images/{id}.jpg'))
engine=AnomalyEngine(root/'models/anomaly');manifest=[];screen=[]
def save(profile,state,index,image,source,label,note):
    rel=Path('Anomaly')/profile/state/f'{state}_{index:02d}.png';p=dest/rel;p.parent.mkdir(parents=True,exist_ok=True)
    assert cv2.imwrite(str(p),image)
    manifest.append(dict(file=rel.as_posix(),pipeline='anomaly',profile=profile,expected_visual=state.upper(),source=source,source_label=label,note=note,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
for profile in engine.contracts:
    rows=engine.samples(profile);evaluated=[]
    for row in rows:
        if row.get('demo_suite'):continue
        path,_=engine.sample_path(profile,row['file']);image=cv2.imread(str(path));a,*_=engine.predict(image,profile)
        value=dict(profile=profile,file=row['file'],source_path=row['source_path'],label=row['label'],score=a['score'],threshold=a['threshold'],flagged=a['flagged'])
        evaluated.append((row,image,a));screen.append(value)
    normal=[r for r in evaluated if r[0]['label']==0 and not r[2]['flagged']]
    flagged=[r for r in evaluated if r[0]['label']==1 and r[2]['flagged']]
    assert len(normal)>=2,(profile,'Fewer than2 actual normal CLEAR samples')
    if len(flagged)<2:print('INSUFFICIENT REAL POSITIVES',profile,len(flagged),flush=True)
    for i,(row,image,a) in enumerate(normal[:2],1):save(profile,'safe',i,image,row['source_path'],'dataset normal','Original held-out normal; selected for demonstration after inference, not unbiased evaluation')
    for i,(row,image,a) in enumerate(flagged[:2],1):save(profile,'defective',i,image,row['source_path'],'dataset anomaly','Original held-out anomaly actually exceeding the unchanged threshold; selected demo, not accuracy evidence')
    for i,(row,image,a) in enumerate(normal[:2],1):
        if i==1:
            altered=np.clip(image.astype(np.float32)*.01,0,255).astype(np.uint8);note='Synthetic acquisition challenge: brightness multiplied by0.01'
        else:
            tiny=cv2.resize(image,(1,1),interpolation=cv2.INTER_AREA);altered=cv2.resize(tiny,(image.shape[1],image.shape[0]),interpolation=cv2.INTER_NEAREST);note='Synthetic acquisition challenge: spatial detail removed with1x1 downsampling'
        save(profile,'warning',i,altered,row['source_path'],'synthetic unusable capture',note+'; not a naturally occurring defect or new independent sample')
    print(profile,'normals',len(normal),'detected defects',len(flagged),flush=True)
(dest/'manifest_candidates.json').write_text(json.dumps(manifest,indent=2))
(out/'screened_anomaly_outputs.json').write_text(json.dumps(screen,indent=2))
print('Candidates:',dest,flush=True)
