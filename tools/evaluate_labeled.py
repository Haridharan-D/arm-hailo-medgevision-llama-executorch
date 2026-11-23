"""Evaluate deployed operating thresholds against explicit YOLO box labels.

Run with the dashboard stopped when using Hailo (one NPU owner). Every image
must have a label file; an explicitly empty label file denotes a healthy image.
This reports precision/recall at frozen thresholds, not an mAP sweep.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def overlap(a,b):
    width=max(0,min(a[2],b[2])-max(a[0],b[0]));height=max(0,min(a[3],b[3])-max(a[1],b[1]))
    intersection=width*height
    union=max(0,a[2]-a[0])*max(0,a[3]-a[1])+max(0,b[2]-b[0])*max(0,b[3]-b[1])-intersection
    return intersection/union if union else 0

def counts_for_image(predictions,labels,nclasses=7,iou=.5):
    counts=[dict(tp=0,fp=0,fn=0) for _ in range(nclasses)];used=set()
    for prediction in sorted(predictions,key=lambda p:-p['confidence']):
        cls=prediction['class_id']
        candidates=[(overlap(prediction['box_xyxy'],label['box_xyxy']),i) for i,label in enumerate(labels)
            if i not in used and label['class_id']==cls]
        score,index=max(candidates,default=(0,-1))
        if score>=iou:used.add(index);counts[cls]['tp']+=1
        else:counts[cls]['fp']+=1
    for index,label in enumerate(labels):
        if index not in used:counts[label['class_id']]['fn']+=1
    return counts

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--images',type=Path,required=True)
    parser.add_argument('--labels',type=Path,required=True)
    parser.add_argument('--backend',choices=['onnx','hailo'],required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--dataset-note',required=True,help='Dataset origin, split and physical grouping limits')
    args=parser.parse_args()
    import cv2
    from app.config import settings
    from app.vision import Detector,NAMES
    paths=sorted(p for p in args.images.iterdir() if p.suffix.lower() in {'.jpg','.jpeg','.png','.bmp','.webp'})
    if not paths:parser.error('No images found')
    if len({p.stem for p in paths})!=len(paths):parser.error('Duplicate image stems would make label mapping ambiguous')
    missing=[p.name for p in paths if not (args.labels/(p.stem+'.txt')).is_file()]
    if missing:parser.error('Missing labels are not assumed healthy: '+str(missing[:10]))
    cfg=settings();detector=Detector(dict(cfg,vision_backend=args.backend))
    totals=[dict(tp=0,fp=0,fn=0) for _ in NAMES];rows=[];false_pass=false_hold=positive=negative=0
    try:
        for path in paths:
            image=cv2.imread(str(path))
            if image is None:raise ValueError('Unreadable image: '+str(path))
            h,w=image.shape[:2];labels=[];labelpath=args.labels/(path.stem+'.txt')
            for line in labelpath.read_text().splitlines():
                if not line.strip():continue
                parts=line.split()
                if len(parts)!=5:raise ValueError('Expected YOLO detection boxes in '+str(labelpath))
                cls=int(parts[0]);x,y,bw,bh=map(float,parts[1:])
                if not 0<=cls<len(NAMES) or not all(0<=v<=1 for v in [x,y,bw,bh]) or bw<=0 or bh<=0:
                    raise ValueError('Invalid normalized label in '+str(labelpath))
                labels.append({'class_id':cls,'box_xyxy':[(x-bw/2)*w,(y-bh/2)*h,(x+bw/2)*w,(y+bh/2)*h]})
            predictions,latency=detector.predict(image)
            counts=counts_for_image(predictions,labels)
            for cls,values in enumerate(counts):
                for key,value in values.items():totals[cls][key]+=value
            if labels:positive+=1;false_pass+=not bool(predictions)
            else:negative+=1;false_hold+=bool(predictions)
            rows.append({'image':path.name,'image_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'label_sha256':hashlib.sha256(labelpath.read_bytes()).hexdigest(),
                'counts':counts,'vision_ms':latency,'labels':labels,'predictions':predictions})
            print(f'{len(rows)}/{len(paths)} {path.name}',flush=True)
    finally:detector.close()
    per_class={}
    for name,counts in zip(NAMES,totals):
        tp,fp,fn=counts['tp'],counts['fp'],counts['fn']
        per_class[name]={**counts,'support':tp+fn,'precision':tp/(tp+fp) if tp+fp else None,
            'recall':tp/(tp+fn) if tp+fn else None}
    artifact=Path(cfg['hef']) if args.backend=='hailo' else cfg['asset_dir']/'blistertrace_yolov8s.onnx'
    report={'created_utc':datetime.now(timezone.utc).isoformat(),'backend':args.backend,'images':len(rows),
        'model_sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'dataset_note':args.dataset_note,
        'independent_physical_grouping_verified_by_this_tool':False,
        'metric':'Per-class box precision/recall at frozen deployment thresholds and IoU 0.5; not mAP',
        'per_class':per_class,'image_level':{'defective':positive,'normal':negative,
        'false_no_defect_images':false_pass,'false_hold_images':false_hold,
        'false_no_defect_rate':false_pass/positive if positive else None,
        'false_hold_rate':false_hold/negative if negative else None},
        'decision_note':'Image-level no-defect is not application PASS while the capture profile is unvalidated',
        'rows':rows}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))

if __name__=='__main__':main()
