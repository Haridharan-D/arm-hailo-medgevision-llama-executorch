import hashlib
import json
import threading
import uuid
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import cv2
from .store import Store
from .vision import Detector,annotate,disposition
from .llm import LlamaManager
from .anomaly import AnomalyEngine
from .traceability import enrich,storage_health,advisory_facts,save_image,save_blob

class InspectionService:
    def __init__(self,config):
        self.config=config;self.store=Store(config['data_dir']);self.detector=Detector(config)
        self.last_vision_error=None;self.display_record=None
        self.store.recover_jobs()
        config['active_batch']=self.store.active_batch()
        self.llm=LlamaManager(config,self.store)
        self.anomaly=AnomalyEngine(config.get('anomaly_models',config['asset_dir'].parent/'models/anomaly'))
        for row in self.store.recent(500):
            if row['advice_status']=='pending':
                previous=self.store.get(row['inspection_id'])
                facts={k:previous[k] for k in ('inspection_id','decision','severity','defects','capture_valid','profile_validated')}
                self.store.advice(row['inspection_id'],self.llm._fallback(facts,'Previous session ended before advisory completion; request advice again if needed'))
        self.source_onnx_sha256=hashlib.sha256((config['asset_dir']/'blistertrace_yolov8s.onnx').read_bytes()).hexdigest()
        self.model_sha256=(hashlib.sha256(Path(config['hef']).read_bytes()).hexdigest()
                           if self.detector.backend=='hailo' else self.source_onnx_sha256)
        self.maintenance_stop=threading.Event()
        self.maintenance_thread=threading.Thread(target=self._maintain,daemon=True);self.maintenance_thread.start()

    def _maintain(self):
        import logging
        while not self.maintenance_stop.wait(5):
            try:self.store.replay()
            except Exception:logging.exception('Durable spool replay failed; evidence remains on disk')

    def analyze(self,image):
        try:detections,latency=self.detector.predict(image);self.last_vision_error=None
        except Exception as error:self.last_vision_error=str(error);raise RuntimeError('Vision runtime unavailable; original decision not created') from error
        decision,severity,capture=disposition(image,detections,self.config['profile_validated'])
        return detections,decision,severity,capture,latency

    def inspect(self,image,source='upload',analysis=None,source_bytes=None):
        if storage_health(self.config['data_dir'])['state']=='critical':raise RuntimeError('Evidence disk critically low; inspection blocked, no acceptable result issued')
        detections,decision,severity,capture,latency=analysis or self.analyze(image)
        id=uuid.uuid4().hex
        counts=Counter(d['type'] for d in detections)
        facts={'inspection_id':id,'decision':decision,'severity':severity,
               'defects':[{'type':k,'count':v} for k,v in sorted(counts.items())],
               'capture_valid':capture['valid'],'profile_validated':self.config['profile_validated']}
        record={**facts,'created_at':datetime.now(timezone.utc).isoformat(),'source':str(source)[:240],
                'detections':detections,'capture':capture,'vision_ms':latency,'backend':self.detector.backend,
                'model_sha256':self.model_sha256,'model_name':'Basler v4 YOLOv8s seven-class',
                'source_onnx_sha256':self.source_onnx_sha256,
                'decision_reason':'Configured defects observed' if detections else
                    ('Capture profile not validated' if not self.config['profile_validated'] else
                     ('Capture quality requires review' if not capture['valid'] else 'No configured defects observed')),
                'image_url':f'/api/inspections/{id}/image','original_url':f'/api/inspections/{id}/original',
                'unit':'image inspection; not a validated production strip decision'}
        root=self.config['data_dir']/'images'
        save_image(root/(id+'_original.jpg'),image)
        save_image(root/(id+'.jpg'),annotate(image,detections,decision))
        record['inference_pixels_sha256']=hashlib.sha256(image.tobytes()).hexdigest()
        if source_bytes is not None:
            save_blob(root/(id+'_source.bin'),source_bytes)
            record.update(source_image_sha256=hashlib.sha256(source_bytes).hexdigest(),source_image_url=f'/api/inspections/{id}/source',source_image_kind='Exact original input file bytes')
        else:record['source_image_kind']='Decoded camera frame; original view retained as JPEG'
        enrich(record,self.config,self.store)
        committed=self.store.add(record)
        if not committed:record['persistence_status']='spooled'
        self.llm.submit(advisory_facts(record))
        result=self.store.get(id)
        if not str(source).startswith('camera:') or str(source)=='camera:operator-trigger':self.display_record=result
        return result

    def request_advice(self,id):
        record=self.store.get(id)
        if not record:raise KeyError(id)
        facts=advisory_facts(record)
        # Publish pending before queuing: otherwise polling can mistake the old
        # cached response for completion and never display the fresh generation.
        self.store.advice(id,None)
        return self.llm.submit(facts,force=True)

    def inspect_anomaly(self,image,profile,source,parent=None,sample=None):
        """Record a new auxiliary assessment; never rewrite its parent decision."""
        assessment,rgba,overlay,raw_map=self.anomaly.predict(image,profile)
        id=uuid.uuid4().hex
        detections=parent['detections'] if parent else []
        decision,severity,capture=disposition(image,detections,False)
        counts=Counter(d['type'] for d in detections)
        if assessment['flagged']:counts['unknown_anomaly']=1
        facts={'inspection_id':id,'decision':decision,'severity':severity,
            'defects':[{'type':k,'count':v} for k,v in sorted(counts.items())],
            'capture_valid':capture['valid'],'profile_validated':False}
        assessment.update(heatmap_url=f'/api/inspections/{id}/heatmap',
            observation_note='unknown_anomaly count denotes one image-level flag, not a localized defect count')
        record={**facts,'created_at':datetime.now(timezone.utc).isoformat(),'source':source,
            'detections':detections,'capture':capture,'vision_ms':parent['vision_ms'] if parent else assessment['elapsed_ms'],
            'backend':parent['backend'] if parent else 'anomaly_onnx_cpu','anomaly':assessment,
            'parent_inspection_id':parent['inspection_id'] if parent else None,
            'inspection_kind':'anomaly_assessment','model_name':(parent.get('model_name','Recorded vision model')+' + auxiliary EfficientAD' if parent else 'EfficientAD-S '+profile),
            'model_sha256':parent['model_sha256'] if parent else assessment['model_sha256'],
            'source_onnx_sha256':parent.get('source_onnx_sha256') if parent else assessment['model_sha256'],
            'parent_detector_reused':parent is not None,
            'decision_reason':('Configured YOLO defect evidence retained; auxiliary anomaly assessment recorded' if detections else
                'Anomaly score above threshold; human review required' if assessment['flagged'] else
                'Below anomaly threshold; camera/product profile remains unvalidated'),
            'image_url':f'/api/inspections/{id}/image','original_url':f'/api/inspections/{id}/original',
            'unit':'Category anomaly assessment; no local-camera or product-release validation',
            'sample_ground_truth':sample}
        root=self.config['data_dir']/'images'
        save_image(root/(id+'_original.jpg'),image)
        save_image(root/(id+'.jpg'),annotate(overlay,detections,decision))
        save_image(root/(id+'_heatmap.png'),rgba)
        record['inference_pixels_sha256']=hashlib.sha256(image.tobytes()).hexdigest()
        import numpy as np
        np.save(root/(id+'_heatmap.npy'),raw_map)
        enrich(record,self.config,self.store)
        self.store.add(record);self.llm.submit(advisory_facts(record))
        result=self.store.get(id);self.display_record=result
        return result

    def close(self):
        if hasattr(self,'maintenance_stop'):
            self.maintenance_stop.set();self.maintenance_thread.join(timeout=2)
        self.llm.close();self.detector.close()
