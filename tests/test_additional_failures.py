import time,sqlite3,json
import pytest
from fastapi.testclient import TestClient
from app.store import Store
from app.server import create_app
from app.advisory_cache import AdvisoryCache

def test_running_jobs_marked_interrupted_without_changing_result(tmp_path):
    s=Store(tmp_path);s.add(dict(inspection_id='X',created_at='now',source='test',decision='HOLD',severity='major'));s.job('X','running')
    assert Store(tmp_path).recover_jobs()==['X'] and s.get('X')['decision']=='HOLD'
    with s.connection() as db:assert db.execute('SELECT state FROM advisory_jobs').fetchone()[0]=='interrupted'

def test_runtime_fault_is_not_an_acceptable_result(tmp_path):
    class Service:
        store=Store(tmp_path)
        def close(self):pass
        def inspect(self,*args,**kwargs):raise RuntimeError('Hailo unavailable')
    import cv2,numpy as np
    folder=tmp_path/'samples';folder.mkdir();cv2.imwrite(str(folder/'sample.jpg'),np.zeros((64,64,3),np.uint8))
    with TestClient(create_app({'data_dir':tmp_path,'test_images':folder},Service())) as c:
        for _ in range(30):
            if c.get('/api/health').json()['ready']:break
            time.sleep(.01)
        r=c.post('/api/library/inspect',json={'name':'sample.jpg'})
        assert r.status_code==503 and r.json()['outcome']=='SYSTEM_FAULT'
        assert Service.store.stats()['total']==0

def test_cache_updates_nested_inspection_identifier():
    f=dict(inspection_id='A',decision='REVIEW',severity='unknown',defects=[],capture_valid=True,profile_validated=False)
    c=AdvisoryCache({'model':'hash','prompt':'v1','sop':'rev1'})
    c.put(f,dict(inspection_id='A',status='llama_validated',elapsed_ms=100,structured_advisory={'inspection_id':'A'}))
    result=c.get(dict(f,inspection_id='B'))
    assert result['inspection_id']=='B' and result['structured_advisory']['inspection_id']=='B'

def test_invalid_upload_is_rejected_and_audited(tmp_path):
    class Service:
        store=Store(tmp_path)
        def close(self):pass
    with TestClient(create_app({'data_dir':tmp_path},Service())) as c:
        for _ in range(30):
            if c.get('/api/health').json()['ready']:break
            time.sleep(.01)
        assert c.post('/api/inspect',files={'file':('bad.png',b'not an image','image/png')}).status_code==400
        assert any(r['event_type']=='api.action' and json.loads(r['payload'])['status']==400 for r in Service.store.audit())
