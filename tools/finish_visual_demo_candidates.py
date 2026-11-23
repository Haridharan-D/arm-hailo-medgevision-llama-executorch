"""Assemble requested folder counts with provenance; target verification follows."""
import hashlib,json,shutil
from pathlib import Path
import cv2,numpy as np
root=Path(__file__).resolve().parents[1];out=root/'validation/visual_suite_20261122'
dest=root.parent/'BlisterTrace_TestSuite_20261122';manifest=json.loads((dest/'manifest_candidates.json').read_text())
for row in json.loads((out/'extra_visa/manifest.json').read_text())[:2]:
    index=1+sum(r['pipeline']=='anomaly' and r['profile']=='visa_capsules' and r['expected_visual']=='DEFECTIVE' for r in manifest)
    rel=Path('Anomaly/visa_capsules/defective')/f'defective_{index:02d}.png';p=dest/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(out/'extra_visa'/row['file'],p)
    manifest.append(dict(file=rel.as_posix(),pipeline='anomaly',profile='visa_capsules',expected_visual='DEFECTIVE',source=row['path'],source_label='dataset anomaly',source_url=row['source_url'],note=row['selection']+'; rerun on deployed model required',sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
def yolo(rel,source,note,label,defect=None,image=None):
    p=dest/'YOLO'/rel;p.parent.mkdir(parents=True,exist_ok=True)
    if image is None:shutil.copy2(source,p)
    else:assert cv2.imwrite(str(p),image)
    entry=dict(file=p.relative_to(dest).as_posix(),pipeline='yolo',expected_visual=rel.split('/')[0].upper(),source=str(source),source_label=label,note=note,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    if defect:entry['expected_class']=defect
    manifest.append(entry)
for i,id in enumerate([1447,4627],1):
    source=out/f'SCOA_{id}.jpg';yolo(f'safe/safe_{i:02d}.jpg',source,'SCOA image visually reviewed for12 occupied cavities; no published ground truth. Different source images, not a resized duplicate. Selected demonstration; no camera-domain accuracy claim.','visually reviewed candidate; no formal annotation')
    image=cv2.imread(str(source))
    if i==1:altered=np.clip(image.astype(np.float32)*.01,0,255).astype(np.uint8);note='Synthetic acquisition challenge: exposure reduced by100x'
    else:altered=cv2.resize(cv2.resize(image,(1,1),interpolation=cv2.INTER_AREA),(image.shape[1],image.shape[0]),interpolation=cv2.INTER_NEAREST);note='Synthetic acquisition challenge: spatial detail removed with1x1 resampling'
    yolo(f'warning/warning_{i:02d}.png',source,note+'; not natural defect data','synthetic unusable capture',image=altered)
for cls in ['black_dot','broken','color_mismatch','crack','dual_cap','empty','foreign_particle']:
    yolo(f'defective/{cls}/{cls}.jpg',root/'test_images/defects'/cls/'CASE-001.jpg','Existing demonstration chosen by frozen detector output; not human ground-truth accuracy','detector prediction demo',cls)
assert len(manifest)==29,len(manifest)
(dest/'manifest_candidates.json').write_text(json.dumps(manifest,indent=2))
readme='''# Verified visual demonstration images

Requested contents: YOLO has2SAFE,2WARNING, and1DEFECTIVE example for each of7classes (11images). Each of3anomaly profiles has2SAFE,2WARNING and2DEFECTIVE examples (18images).

These folders are selected demonstrations, not an independent accuracy dataset. See verification.json / results.csv for actual Raspberry Pi/Hailo/ONNX outputs and immutable QA decisions. No thresholds or model weights were changed to obtain these outcomes. Folder names are never used by prediction logic. SAFE means no configured visual defect was detected in a usable image, not pharmaceutical safety or release approval. The separate unvalidated QA disposition can remain REVIEW.

WARNING examples intentionally simulate unusable acquisition: dark exposure or spatial detail removed with1x1 resampling. They are marked synthetic, derived from the listed source, and are not new independent samples. YOLO SAFE SCOA photos have all12cavities apparently occupied on visual review, but the downloaded SCOA release supplies no formal defect labels. Basler defect examples are chosen by detector output; their source confidence is not human truth.

VisA's old20-example subset missed all10defects. The2new VisA positives were selected from saved true-positive test predictions and downloaded from the public dataset mirror, then rerun on the deployment. This cherry-picked demonstration does not improve its overall24%held-out defect recall or make it reliable. The original20examples and all historical benchmark results remain intact. MVTec data retains CC BY-NC-SA4.0 restrictions; VisA and SCOA notices retain their source licenses.

Run the main dashboard with ~/blistertrace. Under Defect detection -> Local images, choose a 'demo ...' folder. Under Anomaly heatmap -> Stored test folder choose the profile and a named DEMO case. No credentials required. This package includes images/provenance, not model weights.
'''
(dest/'README.md').write_text(readme,encoding='utf8')
print(json.dumps({'folder':str(dest),'images':len(manifest),'ready_for_target_test':True}))
