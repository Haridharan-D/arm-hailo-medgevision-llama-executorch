import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import cv2
import numpy as np
from app.config import ROOT
from app.vision import Detector,disposition,nms
from app.store import Store
from app.camera import Camera

class PipelineTests(unittest.TestCase):
    def test_rules_never_auto_pass_unvalidated_or_invalid_capture(self):
        image=np.random.default_rng(1).integers(20,220,(100,100,3),dtype=np.uint8)
        self.assertEqual(disposition(image,[],False)[0],'REVIEW')
        self.assertEqual(disposition(np.zeros_like(image),[],True)[0],'REVIEW')
        self.assertEqual(disposition(image,[],True)[0],'PASS')
        self.assertEqual(disposition(image,[{'type':'crack'}],False)[:2],('HOLD','major'))

    def test_actual_frozen_detector_class_order_threshold_and_coordinates(self):
        raw=np.zeros((1,11,8400),np.float32)
        raw[0,:4,0]=[320,320,100,80];raw[0,7,0]=.95 # crack is class 3
        raw[0,:4,1]=[320,320,100,80];raw[0,7,1]=.90 # same-class overlap suppressed
        raw[0,:4,2]=[100,100,30,30];raw[0,4,2]=.89 # black_dot below frozen .90
        class Session:
            def get_inputs(self):return [type('Input',(),{'name':'images'})()]
            def run(self,_,data):
                self.tensor=data['images'];return [raw]
        d=Detector.__new__(Detector);d.session=Session();d.hailo=None
        import threading
        d.lock=threading.Lock();d.thresholds=json.loads((ROOT/'assets/thresholds.json').read_text())
        result,_=d.predict(np.zeros((320,640,3),np.uint8))
        self.assertEqual(len(result),1);self.assertEqual(result[0]['type'],'crack')
        self.assertEqual(result[0]['box_xyxy'],[270.,120.,370.,200.])

    def test_store_review_preserves_original_disposition_and_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(Path(tmp));record=dict(inspection_id='abc',created_at='2026-11-18T00:00:00',source='test',decision='HOLD',severity='major')
            store.add(record);store.advice('abc',{'status':'llama_validated'})
            store.review('abc',{'reviewer':'Tester','comment':'Reinspect'})
            store.review('abc',{'reviewer':'QA','comment':'Evidence reviewed'})
            self.assertEqual(store.get('abc')['decision'],'HOLD')
            with store.connection() as db:self.assertEqual(db.execute('SELECT count(*) FROM qa_events').fetchone()[0],2)
            self.assertEqual(store.stats()['HOLD'],1)

    def test_camera_loop_records_live_alert_and_releases_capture(self):
        image=np.full((80,80,3),128,np.uint8)
        class Capture:
            released=False
            def set(self,*args):pass
            def isOpened(self):return True
            def read(self):return True,image.copy()
            def release(self):self.released=True
        cap=Capture()
        class Service:
            def analyze(self,image):return ([{'type':'crack','confidence':.95,'box_xyxy':[10,10,50,50]}],'HOLD','major',{'valid':True},5.)
            def inspect(self,*args):return {'inspection_id':'camera-fixture'}
        camera=Camera(Service())
        with patch('app.camera.cv2.VideoCapture',return_value=cap):
            camera.start('0')
            until=time.monotonic()+2
            while camera.snapshot() is None and time.monotonic()<until:time.sleep(.01)
            camera.stop()
        self.assertEqual(camera.status['decision'],'HOLD')
        self.assertEqual(camera.status['last_inspection_id'],'camera-fixture')
        self.assertTrue(cap.released)
        self.assertIsNotNone(camera.snapshot())

if __name__=='__main__':unittest.main()
