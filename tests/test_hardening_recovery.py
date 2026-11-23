import json,time,threading,sys,sqlite3
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.store import Store
from app.server import create_app
from app.camera import Camera
from app.auth import credential
from advisor_src.advisor import NativeWorker,validate_inspection

def facts():return dict(inspection_id='T',decision='HOLD',severity='major',defects=[dict(type='crack',count=1)],capture_valid=True,profile_validated=False)

def test_context_rejects_invented_defect_and_nonfinite_confidence():
    f=facts();f['context']=dict(batch_id='LOT',product_type='tablet',observations=[dict(type='crack',confidence=.4,box_xyxy=[0,0,20,20])])
    assert validate_inspection(f)['context']['observations'][0]['confidence']==.4
    f['context']['observations'][0]['confidence']=float('nan')
    with pytest.raises(ValueError):validate_inspection(f)
    f['context']['observations'][0].update(confidence=.4,type='broken')
    with pytest.raises(ValueError):validate_inspection(f)

def test_active_batch_survives_restart(tmp_path):
    s=Store(tmp_path);s.create_batch(dict(batch_id='LOT',sku='S',description='D',category='tablet',operator='O'));s.select_batch('LOT','supervisor')
    assert Store(tmp_path).active_batch()=='LOT'

def test_metadata_columns_cannot_be_changed(tmp_path):
    s=Store(tmp_path);s.add(dict(inspection_id='T',created_at='now',source='test',decision='HOLD',severity='major'))
    with pytest.raises(sqlite3.IntegrityError),s.connection() as db:db.execute("UPDATE inspections SET batch_id='OTHER'")

def test_fresh_usb_snapshot_waits_for_new_frame():
    c=Camera(object());c.status['running']=True;c.frame=np.zeros((2,2,3));c.frame_at=time.monotonic()-1
    def update():
        time.sleep(.03)
        with c.condition:c.frame=np.ones((2,2,3));c.frame_at=time.monotonic();c.condition.notify_all()
    t=threading.Thread(target=update);t.start()
    assert c.fresh_original(timeout=.5).mean()==1;t.join()
    assert c.fresh_original(timeout=.01) is None

def test_native_stats_protocol_is_backward_compatible(tmp_path):
    script=tmp_path/'worker.py';script.write_text("import sys,json\nprint('BT1 READY 0',flush=True)\nwhile True:\n h=sys.stdin.buffer.readline()\n if not h:break\n n=int(h.split()[1]);sys.stdin.buffer.read(n)\n s=json.dumps({'prompt_tokens':2,'generated_tokens':3});v='{}'\n print('BT1 STATS '+str(len(s))+'\\n'+s+'\\nBT1 OK 2\\n'+v,flush=True)\n")
    w=NativeWorker(sys.executable,tmp_path/'missing',tmp_path/'missing');w.command=[sys.executable,str(script)]
    try:assert w.generate('hello',4)=='{}' and w.last_metrics['generated_tokens']==3
    finally:w.close()

def test_native_load_failure_recovers_on_next_request(tmp_path):
    w=NativeWorker(tmp_path/'missing_binary',tmp_path/'missing',tmp_path/'missing',timeout=.05)
    for _ in range(2):
        with pytest.raises(OSError):w.generate('hello',4)
        assert w.process is None

def test_first_local_account_setup_once(tmp_path):
    class Service:
        store=Store(tmp_path)
        def close(self):pass
    with TestClient(create_app({'data_dir':tmp_path,'auth_required':True},Service())) as c:
        assert c.get('/api/auth/me').json()['needs_setup']
        assert c.post('/api/auth/bootstrap',json={'username':'admin','password':'long-password-123'}).status_code==200
        assert c.post('/api/auth/bootstrap',json={'username':'other','password':'long-password-123'}).status_code==409
        assert c.post('/api/auth/login',json={'username':'admin','password':'long-password-123'}).status_code==200
