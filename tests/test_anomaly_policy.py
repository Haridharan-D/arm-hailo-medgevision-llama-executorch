import numpy as np
from app.service import InspectionService
from app.store import Store

class Engine:
    def __init__(self,flag):self.flag=flag
    def predict(self,image,profile):
        value={'profile':profile,'score':.8 if self.flag else .01,'threshold':.3,'flagged':self.flag,
            'elapsed_ms':10,'model_sha256':'ANOMALY'}
        return value,np.zeros((*image.shape[:2],4),np.uint8),image.copy(),np.zeros((256,256),np.float32)
class Llm:
    def submit(self,facts):self.last=facts

def service(tmp_path,flag):
    result=InspectionService.__new__(InspectionService);result.config={'data_dir':tmp_path}
    result.store=Store(tmp_path);result.anomaly=Engine(flag);result.llm=Llm();result.source_onnx_sha256='YOLO'
    return result

def test_unknown_anomaly_requires_review_without_invented_defect_type(tmp_path):
    s=service(tmp_path,True);r=s.inspect_anomaly(np.zeros((80,80,3),np.uint8),'mvtec_pill','test')
    assert r['decision']=='REVIEW' and r['defects']==[{'type':'unknown_anomaly','count':1}]
    assert r['profile_validated'] is False

def test_parent_hold_is_preserved_in_new_assessment(tmp_path):
    s=service(tmp_path,False)
    parent={'inspection_id':'ORIGINAL','decision':'HOLD','severity':'major','created_at':'2026-11-20','source':'test',
        'detections':[{'class_id':3,'type':'crack','confidence':.98,'box_xyxy':[10,10,30,30]}],
        'vision_ms':12,'backend':'hailo','model_sha256':'YOLO'}
    s.store.add(parent)
    r=s.inspect_anomaly(np.zeros((80,80,3),np.uint8),'mvtec_pill','test',parent)
    assert r['decision']=='HOLD' and r['parent_inspection_id']=='ORIGINAL'
    assert s.store.get('ORIGINAL')['decision']=='HOLD' and 'anomaly' not in s.store.get('ORIGINAL')

def test_dataset_label_cannot_turn_model_miss_into_anomaly_observation(tmp_path):
    s=service(tmp_path,False)
    r=s.inspect_anomaly(np.zeros((80,80,3),np.uint8),'visa_capsules','test',sample={'label':1})
    assert r['anomaly']['flagged'] is False and r['defects']==[] and r['decision']=='REVIEW'
