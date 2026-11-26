"""Real EfficientAD ONNX inference. Category scores are never defect probabilities."""
from pathlib import Path
import hashlib
import json
import threading
import time
import cv2
import numpy as np
from PIL import Image

class AnomalyEngine:
    def __init__(self,root):
        self.root=Path(root);self.lock=threading.Lock();self.current=None;self.session=None
        self.contracts={}
        for path in sorted(self.root.glob('*/contract.json')):
            value=json.loads(path.read_text())
            if (path.parent/'model.onnx').is_file():self.contracts[path.parent.name]=value

    def profiles(self):
        titles={'mvtec_pill':'MVTec pill','mvtec_capsule':'MVTec capsule','visa_capsules':'VisA capsules'}
        return [{'id':key,'name':titles.get(key,key),'backend':'ONNX Runtime CPU',
            'threshold':value['thresholds']['image'],'pixel_threshold':value['thresholds']['pixel'],
            'warning':value['quality_warning'],'validated_for_local_camera':False,
            'model_sha256':value['artifact_sha256'],'license':value.get('license')}
            for key,value in self.contracts.items()]

    def samples(self,profile):
        if profile not in self.contracts:raise ValueError('Unknown anomaly profile')
        path=self.root/'samples'/profile/'manifest.json'
        return json.loads(path.read_text()) if path.is_file() else []

    def sample_path(self,profile,name):
        row=next((r for r in self.samples(profile) if r['file']==name),None)
        if row is None:raise ValueError('Unknown dataset test sample')
        root=(self.root/'samples'/profile).resolve();path=(root/name).resolve()
        if root not in path.parents or not path.is_file():raise ValueError('Test sample unavailable')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Test sample checksum mismatch')
        return path,row

    def predict(self,image,profile):
        if profile not in self.contracts:raise ValueError('Unknown anomaly profile')
        if image is None or image.dtype!=np.uint8 or image.ndim!=3 or image.shape[2]!=3 or min(image.shape[:2])<1:
            raise ValueError('Anomaly input must be a nonempty uint8 BGR image')
        started=time.perf_counter();contract=self.contracts[profile]
        rgb=Image.fromarray(cv2.cvtColor(image,cv2.COLOR_BGR2RGB)).resize((256,256),Image.Resampling.BILINEAR)
        tensor=np.ascontiguousarray(np.asarray(rgb,dtype=np.float32).transpose(2,0,1)[None]/255)
        prepared=time.perf_counter()
        with self.lock:
            acquired=time.perf_counter();cold=self.current!=profile
            if self.current!=profile:
                import onnxruntime as ort
                path=self.root/profile/'model.onnx'
                if hashlib.sha256(path.read_bytes()).hexdigest()!=contract['artifact_sha256']:
                    raise ValueError('Anomaly model checksum mismatch')
                options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
                self.session=None  # Keep one category resident to bound memory.
                self.session=ort.InferenceSession(str(path),sess_options=options,providers=['CPUExecutionProvider'])
                self.current=profile
            loaded=time.perf_counter()
            heatmap,score=self.session.run(['heatmap','score'],{'image':tensor})
            inferred=time.perf_counter()
        if heatmap.shape!=(1,1,256,256) or score.shape!=(1,) or not np.isfinite(heatmap).all() or not np.isfinite(score).all():
            raise RuntimeError('Invalid anomaly output contract')
        threshold=contract['thresholds']['image'];pixel=contract['thresholds']['pixel']
        value=float(score[0]);assessment={'profile':profile,'score':value,'threshold':threshold,
            'pixel_threshold':pixel,'flagged':value>=threshold,'classification':'ANOMALY' if value>=threshold else 'BELOW THRESHOLD',
            'backend':'ONNX Runtime CPU','model_sha256':contract['artifact_sha256'],
            'elapsed_ms':round((time.perf_counter()-started)*1000,2),'validated_for_local_camera':False,
            'scope':contract['quality_warning'],'score_note':'Uncalibrated anomaly score, not probability or drug safety',
            'color_scale_note':'Color scale is fixed at 0 to twice the saved pixel threshold; not a probability map'}
        # Actual map aligned back to the original image, using the saved model normalization.
        mapped=cv2.resize(heatmap[0,0],(image.shape[1],image.shape[0]),interpolation=cv2.INTER_LINEAR)
        scale=np.clip(mapped/max(2*pixel,1e-6),0,1)
        color=cv2.applyColorMap((scale*255).astype(np.uint8),cv2.COLORMAP_TURBO)
        alpha=(np.clip((scale-.12)/.88,0,1)*180).astype(np.uint8)
        rgba=cv2.cvtColor(color,cv2.COLOR_BGR2BGRA);rgba[:,:,3]=alpha
        overlay=(image.astype(np.float32)*(1-alpha[:,:,None]/255)+color.astype(np.float32)*(alpha[:,:,None]/255)).astype(np.uint8)
        finished=time.perf_counter()
        assessment['timings_ms']={'preprocess':(prepared-started)*1000,
            'queue_wait':(acquired-prepared)*1000,'session_prepare':(loaded-acquired)*1000,
            'model_inference':(inferred-loaded)*1000,'postprocess_and_overlay':(finished-inferred)*1000,
            'total':(finished-started)*1000}
        assessment['cold_profile_load']=cold
        assessment['timing_scope']='In-process anomaly path including overlay; excludes capture, persistence and advisory. Legacy elapsed_ms excludes overlay.'
        return assessment,rgba,overlay,heatmap[0,0]
