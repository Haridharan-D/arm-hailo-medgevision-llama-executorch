"""Frozen seven-class YOLO contract. No Ultralytics/Torch dependency at runtime."""
import json
import threading
import time
from pathlib import Path
import cv2
import numpy as np

NAMES=['black_dot','broken','color_mismatch','crack','dual_cap','empty','foreign_particle']

def letterbox(image,size=640):
    h,w=image.shape[:2]
    scale=min(size/w,size/h)
    nw,nh=round(w*scale),round(h*scale)
    dw,dh=(size-nw)/2,(size-nh)/2
    left,top=round(dw-.1),round(dh-.1)
    padded=cv2.copyMakeBorder(cv2.resize(image,(nw,nh)),top,round(dh+.1),left,round(dw+.1),
                              cv2.BORDER_CONSTANT,value=(114,114,114))
    return padded,scale,left,top

def nms(boxes,scores,iou=.7):
    order=np.argsort(-scores,kind='stable');keep=[]
    while len(order):
        i=order[0];keep.append(int(i))
        if len(order)==1:break
        rest=order[1:]
        lo=np.maximum(boxes[i,:2],boxes[rest,:2]);hi=np.minimum(boxes[i,2:],boxes[rest,2:])
        wh=np.maximum(hi-lo,0);inter=wh[:,0]*wh[:,1]
        area=np.prod(np.maximum(boxes[i,2:]-boxes[i,:2],0))
        others=np.prod(np.maximum(boxes[rest,2:]-boxes[rest,:2],0),axis=1)
        order=rest[inter/(area+others-inter+1e-9)<=iou]
    return keep

class Detector:
    def __init__(self,config):
        self.config=config;self.lock=threading.Lock();self.session=None;self.hailo=None
        self.thresholds=json.loads((config['asset_dir']/'thresholds.json').read_text())
        self.backend=config['vision_backend']
        if self.backend=='onnx':
            import onnxruntime as ort
            options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
            self.session=ort.InferenceSession(str(config['asset_dir']/'blistertrace_yolov8s.onnx'),
                                             sess_options=options,providers=['CPUExecutionProvider'])
        elif self.backend=='hailo':
            from .hailo_backend import HailoDetector
            self.hailo=HailoDetector(config['hef'])
        else:raise ValueError('vision_backend must be onnx or hailo')

    def predict(self,image):
        start=time.perf_counter()
        rgb,scale,left,top=letterbox(image)
        rgb=cv2.cvtColor(rgb,cv2.COLOR_BGR2RGB)
        with self.lock:
            if self.hailo is not None:
                rows=self.hailo.predict(rgb)
                boxes=np.array([r[:4] for r in rows],dtype=np.float32).reshape(-1,4)
                scores=np.array([r[4] for r in rows]);classes=np.array([r[5] for r in rows],dtype=int)
            else:
                tensor=np.ascontiguousarray(rgb.transpose(2,0,1)[None],dtype=np.float32)/255.
                raw=self.session.run(None,{self.session.get_inputs()[0].name:tensor})[0]
                if raw.shape!=(1,11,8400):raise RuntimeError(f'Unexpected YOLO output shape: {raw.shape}')
                pred=raw[0].T;classes=pred[:,4:].argmax(axis=1);scores=pred[np.arange(len(pred)),classes+4]
                thresholds=np.array([self.thresholds[NAMES[c]]['threshold'] for c in classes])
                mask=np.isfinite(pred).all(axis=1)&(scores>=thresholds)
                pred=pred[mask];scores=scores[mask];classes=classes[mask]
                boxes=np.column_stack((pred[:,:2]-pred[:,2:4]/2,pred[:,:2]+pred[:,2:4]/2))
        detections=[]
        for cls in sorted(set(classes.tolist())):
            selected=np.flatnonzero(classes==cls)
            selected=selected[scores[selected]>=self.thresholds[NAMES[cls]]['threshold']]
            for j in nms(boxes[selected],scores[selected]):
                i=selected[j];box=boxes[i].copy();box[[0,2]]=(box[[0,2]]-left)/scale;box[[1,3]]=(box[[1,3]]-top)/scale
                box[[0,2]]=np.clip(box[[0,2]],0,image.shape[1]);box[[1,3]]=np.clip(box[[1,3]],0,image.shape[0])
                if box[2]<=box[0] or box[3]<=box[1]:continue
                detections.append({'class_id':int(cls),'type':NAMES[cls],'confidence':round(float(scores[i]),5),
                                   'box_xyxy':[round(float(x),2) for x in box]})
        return detections,round((time.perf_counter()-start)*1000,2)

    def close(self):
        if self.hailo is not None:self.hailo.close()

def annotate(image,detections,decision):
    result=image.copy()
    for item in detections:
        x1,y1,x2,y2=[int(v) for v in item['box_xyxy']]
        cv2.rectangle(result,(x1,y1),(x2,y2),(70,85,245),2)
        label=f"{item['type']} {item['confidence']:.2f}"
        cv2.putText(result,label,(x1,max(18,y1-7)),cv2.FONT_HERSHEY_SIMPLEX,.5,(70,85,245),2,cv2.LINE_AA)
    color={'HOLD':(70,85,245),'REVIEW':(30,185,245),'PASS':(95,210,50)}[decision]
    cv2.rectangle(result,(0,0),(min(180,result.shape[1]),35),(20,25,30),-1)
    cv2.putText(result,decision,(12,25),cv2.FONT_HERSHEY_SIMPLEX,.7,color,2)
    return result

def disposition(image,detections,profile_validated):
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    capture={'mean_luma':round(float(gray.mean()),2),'sharpness':round(float(cv2.Laplacian(gray,cv2.CV_64F).var()),2)}
    capture['valid']=8<capture['mean_luma']<247 and capture['sharpness']>2 and min(image.shape[:2])>=64
    if detections:return 'HOLD','major',capture
    if not capture['valid'] or not profile_validated:return 'REVIEW','unknown',capture
    return 'PASS','none',capture
