"""Group original training-source demo images by frozen predictions, never invented ground truth."""
from pathlib import Path
import hashlib,json,shutil,sys
import cv2
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.vision import Detector,NAMES
SOURCE=ROOT.parent/'YOLO_Model/v2/calibration_train_only'
OUT=ROOT/'test_images/defects';OUT.mkdir(parents=True,exist_ok=True)
detector=Detector({'vision_backend':'onnx','asset_dir':ROOT/'assets'})
rows={name:[] for name in NAMES};seen=set()
for i,path in enumerate(sorted(SOURCE.glob('*.jpg'))):
    detections,ms=detector.predict(cv2.imread(str(path)))
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest in seen:continue
    seen.add(digest)
    for name in sorted(set(d['type'] for d in detections)):
        if len(rows[name])>=20:continue
        folder=OUT/name;folder.mkdir(exist_ok=True);target=folder/path.name;shutil.copy2(path,target)
        rows[name].append({'file':target.relative_to(ROOT/'test_images').as_posix(),'group':name,
            'sha256':digest,'source_file':path.name,'split':'train/calibration',
            'label_origin':'Frozen YOLO prediction; not human ground truth',
            'predicted_types':sorted(set(d['type'] for d in detections)),
            'selection':'First distinct source images with a prediction above the unchanged class threshold; not accuracy evidence',
            'dataset':'SastraAji Basler v4','license':'CC BY 4.0',
            'source_url':'https://universe.roboflow.com/sastraaji/basler_blisterpack_01.08.2024'})
    if i%50==0:print(i,{k:len(v) for k,v in rows.items()},flush=True)
    (OUT/'manifest.json').write_text(json.dumps([r for group in rows.values() for r in group],indent=2))
    if all(len(v)==20 for v in rows.values()):break
for name,group in rows.items():
    originals=list(group)
    for source in originals:
        if len(group)>=20:break
        image=cv2.imread(str(ROOT/'test_images'/source['file']))
        transformed=cv2.flip(image,1);detections,_=detector.predict(transformed)
        if name not in {d['type'] for d in detections}:continue
        target=OUT/name/('flip_'+Path(source['file']).name);cv2.imwrite(str(target),transformed)
        group.append(dict(source,file=target.relative_to(ROOT/'test_images').as_posix(),
            sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            source_file=source['source_file'],transform='Horizontal flip of the named original; not an independent image',
            label_origin='Frozen prediction on derived training-source demo; not ground truth'))
(OUT/'manifest.json').write_text(json.dumps([r for group in rows.values() for r in group],indent=2))
print(json.dumps({k:len(v) for k,v in rows.items()},indent=2))
detector.close()
