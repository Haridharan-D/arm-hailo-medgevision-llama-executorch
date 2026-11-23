"""Actual Hailo/FP32 agreement check, explicitly not ground-truth accuracy."""
import argparse
import json
import sys
import time
from pathlib import Path
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.config import settings
from app.vision import Detector

def iou(a,b):
    lo=np.maximum(a[:2],b[:2]);hi=np.minimum(a[2:],b[2:]);inter=np.prod(np.maximum(hi-lo,0))
    return float(inter/(np.prod(np.maximum(np.array(a[2:])-a[:2],0))+np.prod(np.maximum(np.array(b[2:])-b[:2],0))-inter+1e-9))

def main():
    p=argparse.ArgumentParser();p.add_argument('--hef',type=Path,required=True)
    p.add_argument('--images',type=Path,default=ROOT/'test_images');p.add_argument('--limit',type=int,default=18)
    p.add_argument('--output',type=Path,default=Path.home()/'BlisterTrace_Data/target_validation/hailo_agreement.json')
    args=p.parse_args();base=settings();cpu=Detector(dict(base,vision_backend='onnx'))
    accelerator=Detector(dict(base,vision_backend='hailo',hef=str(args.hef)))
    rows=[];tp=fp=fn=0
    try:
        for path in sorted(args.images.glob('*.jpg'))[:args.limit]:
            frame=cv2.imread(str(path));ref,ref_ms=cpu.predict(frame);got,got_ms=accelerator.predict(frame)
            used=set();matched=0
            for item in sorted(ref,key=lambda d:-d['confidence']):
                candidates=[(iou(item['box_xyxy'],d['box_xyxy']),j) for j,d in enumerate(got)
                            if j not in used and item['type']==d['type']]
                best=max(candidates,default=(0,-1))
                if best[0]>=.5:matched+=1;used.add(best[1])
            tp+=matched;fp+=len(got)-matched;fn+=len(ref)-matched
            rows.append({'image':path.name,'fp32':ref,'hailo_int8':got,'matched_at_iou_05':matched,
                         'fp32_ms':ref_ms,'hailo_ms':got_ms})
    finally:accelerator.close();cpu.close()
    report={'backend':'Actual HailoRT / Hailo-8','hef':str(args.hef),'images':len(rows),
            'reference':'Frozen FP32 ONNX with identical preprocessing, thresholds and NMS',
            'agreement_matches':tp,'int8_only_detections':fp,'fp32_only_detections':fn,
            'agreement_precision':tp/(tp+fp) if tp+fp else None,
            'agreement_recall':tp/(tp+fn) if tp+fn else None,
            'warm_hailo_ms_p50':float(np.median([r['hailo_ms'] for r in rows[1:]])) if len(rows)>1 else None,
            'ground_truth_accuracy_verified':False,
            'scope':'Unannotated training-source demo samples; agreement is not defect recall, mAP or independent test evidence',
            'rows':rows}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))

if __name__=='__main__':main()
