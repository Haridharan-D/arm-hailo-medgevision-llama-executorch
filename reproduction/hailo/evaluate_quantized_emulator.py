"""DFC quantized-emulator agreement on frozen demo inputs, never accuracy prediction."""
import os
os.environ.update(TF_NUM_INTEROP_THREADS='2', TF_NUM_INTRAOP_THREADS='2', OMP_NUM_THREADS='2')
import hashlib
import json
from pathlib import Path
import sys
import time
import cv2
import numpy as np
from hailo_sdk_client import ClientRunner, InferenceContext

ROOT=Path('/mnt/c/arm_bharath_soc_2027')
APP=ROOT/'BlisterTrace_App'
sys.path.insert(0,str(APP))
from app.vision import letterbox,nms,NAMES
from tools.verify_hailo import iou

def main():
    out=ROOT/'Hailo_Compiler/output/quantized_emulator_20261120';out.mkdir(exist_ok=True)
    refs=json.loads((APP/'validation/cpu_predictions_pi_20261120.json').read_text())
    thresholds=json.loads((APP/'assets/thresholds.json').read_text())
    runner=ClientRunner(har=str(ROOT/'Hailo_Compiler/output/yolov8s.har'))
    rows=[];matched_total=fp=fn=0
    report={'backend':'DFC SDK_QUANTIZED software emulator on development host',
        'ground_truth_accuracy_verified':False,'npu_performance_measured':False,
        'scope':'FP32/INT8 agreement on unannotated training-source demo images; not a prediction of production accuracy',
        'hef_sha256':hashlib.sha256((ROOT/'Hailo_Compiler/output/blistertrace.hef').read_bytes()).hexdigest(),
        'runner_state':str(runner.state),'rows':rows}
    with runner.infer_context(InferenceContext.SDK_QUANTIZED) as context:
        for ref in refs:
            path=APP/'test_images'/ref['image'];frame=cv2.imread(str(path));rgb,scale,left,top=letterbox(frame)
            x=cv2.cvtColor(rgb,cv2.COLOR_BGR2RGB).astype(np.float32)[None]
            start=time.perf_counter();output=np.asarray(runner.infer(context,x,batch_size=1))
            assert output.shape==(1,7,5,100),output.shape
            assert np.isfinite(output).all()
            np.save(out/(path.stem+'_sdk_output.npy'),output)
            got=[]
            for cls in range(7):
                candidates=output[0,cls].T
                candidates=candidates[candidates[:,4]>=thresholds[NAMES[cls]]['threshold']]
                if not len(candidates):continue
                # SDK NMS output rows: ymin,xmin,ymax,xmax,score in normalized coordinates.
                boxes=candidates[:,[1,0,3,2]].copy()*640
                for j in nms(boxes,candidates[:,4],.7):
                    box=boxes[j].copy();box[[0,2]]=(box[[0,2]]-left)/scale;box[[1,3]]=(box[[1,3]]-top)/scale
                    box[[0,2]]=np.clip(box[[0,2]],0,frame.shape[1]);box[[1,3]]=np.clip(box[[1,3]],0,frame.shape[0])
                    if box[2]<=box[0] or box[3]<=box[1]:continue
                    got.append({'class_id':cls,'type':NAMES[cls],'confidence':round(float(candidates[j,4]),5),
                        'box_xyxy':[round(float(v),2) for v in box]})
            used=set();matched=0
            for item in sorted(ref['detections'],key=lambda d:-d['confidence']):
                choices=[(iou(item['box_xyxy'],d['box_xyxy']),j) for j,d in enumerate(got)
                    if j not in used and item['class_id']==d['class_id']]
                overlap,index=max(choices,default=(0,-1))
                if overlap>=.5:used.add(index);matched+=1
            matched_total+=matched;fp+=len(got)-matched;fn+=len(ref['detections'])-matched
            rows.append({'image':path.name,'image_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'fp32':ref['detections'],'quantized_emulator':got,'matched_iou_05':matched,
                'emulator_host_seconds':round(time.perf_counter()-start,3)})
            (out/'report.partial.json').write_text(json.dumps(report,indent=2))
            print(path.name,'FP32',len(ref['detections']),'emulator',len(got),'matched',matched,flush=True)
    report.update(images=len(rows),agreement_matches=matched_total,int8_only=fp,fp32_only=fn,
        agreement_precision=matched_total/(matched_total+fp) if matched_total+fp else None,
        agreement_recall=matched_total/(matched_total+fn) if matched_total+fn else None,
        hailo_accuracy_prediction=None,hardware_validation_still_required=True)
    (out/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2),flush=True)

if __name__=='__main__':main()
