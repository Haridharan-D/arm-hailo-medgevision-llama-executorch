import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from fastapi.testclient import TestClient
from app.operator import answer
from app.server import create_app
from app.store import Store
from app.camera import Camera
import threading


def record(**updates):
    value={'inspection_id':'FIXTURE-001','created_at':'2026-11-19T00:00:00Z','source':'fixture',
        'decision':'HOLD','severity':'major','defects':[{'type':'crack','count':1}],
        'capture_valid':True,'profile_validated':False,'advice':None}
    value.update(updates);return value


class AOITests(unittest.TestCase):
    def test_restarting_camera_does_not_expose_previous_frames_or_fps(self):
        gate=threading.Event();image=np.full((80,80,3),128,np.uint8)
        class Capture:
            def set(self,*args):pass
            def isOpened(self):return True
            def read(self):gate.wait(2);return True,image.copy()
            def release(self):pass
        class Service:
            def analyze(self,im):return ([], 'REVIEW','unknown',{'valid':True},1.)
            def inspect(self,*args):return {'inspection_id':'new-frame'}
        camera=Camera(Service());camera.frame=image.copy();camera.jpeg=b'old';camera.frame_at=1
        camera.status.update(fps=15,last_inspection_id='old',frame_ready=True)
        with patch('app.camera.cv2.VideoCapture',return_value=Capture()):
            try:
                camera.start('0');self.assertIsNone(camera.original());self.assertIsNone(camera.snapshot())
                self.assertEqual(camera.status['fps'],0);self.assertIsNone(camera.status['last_inspection_id'])
                self.assertFalse(camera.status['frame_ready'])
                gate.set();until=time.monotonic()+2
                while not camera.status['frame_ready'] and time.monotonic()<until:time.sleep(.01)
                self.assertIsNotNone(camera.original())
            finally:gate.set();camera.stop()

    def test_rectification_is_grounded_handling_and_preserves_hold(self):
        result=answer(record(),'How can I rectify this?')
        self.assertEqual(result['intent'],'rectify');self.assertEqual(result['clause_id'],'BT-02')
        self.assertEqual(result['decision'],'HOLD');self.assertIn('QA',result['reply'])
        self.assertIn('do not repair',result['reply'])

    def test_questions_do_not_change_review_or_assert_safe(self):
        row=record(decision='REVIEW',severity='unknown',defects=[])
        result=answer(row,'Why is it review?')
        self.assertIn('unvalidated',result['reply']);self.assertEqual(result['decision'],'REVIEW')
        unsupported=answer(row,'Is this safe to release?')
        self.assertEqual(unsupported['intent'],'unsupported')

    def test_llama_source_only_claimed_for_recorded_model_text(self):
        advisory={'status':'llama_validated','advisory':{'clause_id':'BT-02',
            'operator_message':'Keep the pack on HOLD.','qa_note':'Draft: crack observed. QA review pending.'}}
        row=record(advice=advisory)
        self.assertEqual(answer(row,intent='next_action')['source'],'recorded_llama_advisory')
        self.assertEqual(answer(row,intent='rectify')['source'],'inspection_rules_and_sop')
        with self.assertRaises(ValueError):answer(row,intent='free_sql')

    def test_health_and_ui_serve_before_vision_initialization_and_audit_api(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);store=Store(root);store.add(record())
            class Service:
                detector=type('Detector',(),{'backend':'onnx'})()
                def __init__(self,config):time.sleep(.35);self.store=store;self.closed=False
                def close(self):self.closed=True
            cfg={'data_dir':root,'test_images':root,'profile_validated':False}
            with patch('app.server.InspectionService',Service):
                with TestClient(create_app(cfg)) as client:
                    self.assertEqual(client.get('/').status_code,200)
                    health=client.get('/api/health').json()
                    self.assertEqual(health['application'],'BlisterTrace')
                    self.assertFalse(health['ready'])
                    self.assertEqual(client.post('/api/library/inspect',json={'name':'none.jpg'}).status_code,404)
                    until=time.monotonic()+3
                    while not client.get('/api/health').json()['ready'] and time.monotonic()<until:time.sleep(.02)
                    response=client.post('/api/inspections/FIXTURE-001/ask',json={'intent':'explain'})
                    self.assertEqual(response.status_code,200);self.assertEqual(response.json()['decision'],'HOLD')
                    self.assertEqual(client.get('/api/inspections/FIXTURE-001/report').json()['decision'],'HOLD')
                    self.assertEqual(client.post('/api/camera/inspect').status_code,409)
                    self.assertEqual(store.get('FIXTURE-001')['decision'],'HOLD')


if __name__=='__main__':unittest.main()
