import numpy as np
import pytest
from app.integrity import verify,verify_runtime
from app.vision import letterbox,disposition
from app.severity import explanation

def test_model_corruption_fails_closed(tmp_path):
    p=tmp_path/'blistertrace.hef';p.write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='checksum'):verify(p)

def test_wrong_native_architecture_rejected(tmp_path):
    p=tmp_path/'worker';h=bytearray(20);h[:6]=b'\x7fELF\x02\x01';h[18:20]=(62).to_bytes(2,'little');p.write_bytes(h)
    with pytest.raises(ValueError,match='architecture'):verify_runtime(p,'aarch64')

def test_missing_runtime_library_rejected(tmp_path):
    p=tmp_path/'worker';h=bytearray(20);h[:6]=b'\x7fELF\x02\x01';h[18:20]=(183).to_bytes(2,'little');p.write_bytes(h)
    with pytest.raises(FileNotFoundError):verify_runtime(p,'aarch64')

def test_rectangular_letterbox_contract():
    im=np.zeros((5,10,3),dtype=np.uint8);im[:]=[20,40,60]
    result,scale,left,top=letterbox(im)
    assert result.shape==(640,640,3) and (scale,left,top)==(64,0,160)
    assert result[0,0].tolist()==[114,114,114]
    assert result[320,320].tolist()==[20,40,60]

def test_severity_explanation_preserves_hold_and_unknown_clinical_risk():
    row={'detections':[{'type':'crack'}],'severity':'major','decision':'HOLD'}
    assert explanation(row)['rule']=='configured-defect-hold'
    assert row['decision']=='HOLD' and 'not validated' in explanation(row)['rationale']

def test_unvalidated_clear_image_cannot_release():
    im=np.random.default_rng(3).integers(0,255,(100,100,3),dtype=np.uint8)
    assert disposition(im,[],False)[0]=='REVIEW'
