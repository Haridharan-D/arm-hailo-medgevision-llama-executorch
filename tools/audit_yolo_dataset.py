"""Read-only audit of images/{train,val,test} and labels/{train,val,test}.

Writes a candidate training manifest only when label checks and decoded-image
cross-split checks pass. It never deletes data, changes labels or resplits test.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image


def label_boxes(path,nclasses):
    if not path.is_file():raise ValueError('Missing label; not assumed healthy')
    boxes=[]
    for line in path.read_text().splitlines():
        if not line.strip():continue
        fields=line.split()
        if len(fields)!=5:raise ValueError('Expected class x y width height')
        cls=int(fields[0]);x,y,w,h=map(float,fields[1:])
        if not 0<=cls<nclasses or not all(np.isfinite([x,y,w,h])) or w<=0 or h<=0 or min(x-w/2,y-h/2)<-1e-6 or max(x+w/2,y+h/2)>1+1e-6:
            raise ValueError('Invalid class or normalized box geometry')
        boxes.append([cls,x,y,w,h])
    if len({tuple(b) for b in boxes})!=len(boxes):raise ValueError('Duplicate label boxes')
    return boxes


def audit(root,nclasses=7):
    root=Path(root);rows=[];errors=[];owners=defaultdict(list);counts={}
    for split in ['train','val','test']:
        paths=sorted(p for p in (root/'images'/split).rglob('*') if p.suffix.lower() in {'.png','.jpg','.jpeg','.bmp'})
        counts[split]=Counter();stems=set()
        if not paths:errors.append({'split':split,'error':'No images'})
        for path in paths:
            rel=path.relative_to(root/'images'/split);label=root/'labels'/split/rel.with_suffix('.txt')
            try:
                if str(rel.with_suffix('')) in stems:raise ValueError('Ambiguous stem across extensions')
                stems.add(str(rel.with_suffix('')));boxes=label_boxes(label,nclasses)
                with Image.open(path) as im:
                    array=np.asarray(im.convert('RGB'))
                pixel_hash=hashlib.sha256(str(array.shape).encode()+array.tobytes()).hexdigest()
                row=dict(split=split,image=path.relative_to(root).as_posix(),label=label.relative_to(root).as_posix(),
                         image_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         label_sha256=hashlib.sha256(label.read_bytes()).hexdigest(),decoded_sha256=pixel_hash,
                         classes=[b[0] for b in boxes])
                rows.append(row);owners[pixel_hash].append(row)
                counts[split].update(row['classes'])
            except (ValueError,OSError) as e:errors.append({'image':str(path.relative_to(root)),'error':str(e)})
    overlap=[v for v in owners.values() if len({r['split'] for r in v})>1]
    conflicts=[v for v in owners.values() if len({r['label_sha256'] for r in v})>1]
    # Exact same pixels and labels are redundant within training. Keep deterministic first.
    clean=[];seen=set()
    for r in rows:
        if r['split']=='train' and r['decoded_sha256'] not in seen:
            clean.append(r);seen.add(r['decoded_sha256'])
    eligible=not errors and not overlap and not conflicts
    return dict(schema='medge-yolo-audit-v1',rows=rows,errors=errors,cross_split_decoded_duplicates=overlap,
                duplicate_label_conflicts=conflicts,instances_per_class={s:dict(v) for s,v in counts.items()},
                training_manifest=clean if eligible else [],training_ready=eligible,
                note='Exact decoded-image checks only. Physical strip leakage, near duplicates, label semantics and split independence require review. No images modified.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=audit(a.root)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n')
    print('Training manifest eligible:',r['training_ready'])
    raise SystemExit(0 if r['training_ready'] else 2)
