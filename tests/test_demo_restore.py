import hashlib,io,json,zipfile
import pytest
from tools.restore_demo_backup import restore

def bundle(tmp_path,name='evidence.txt'):
    raw=b'original measured evidence';entry=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w') as z:
        z.writestr(name,raw);z.writestr('manifest.json',json.dumps({name:entry}))
    data=buffer.getvalue();(tmp_path/'data.part').write_bytes(data)
    (tmp_path/'BUNDLE_MANIFEST.json').write_text(json.dumps(dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),parts=[dict(file='data.part',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())])))

def test_restore_verifies_and_refuses_existing_data(tmp_path):
    bundle(tmp_path);target=tmp_path/'new';restore(tmp_path,target)
    assert (target/'evidence.txt').read_bytes()==b'original measured evidence'
    with pytest.raises(ValueError,match='existing station data'):restore(tmp_path,target)

def test_corruption_is_rejected_without_creating_target(tmp_path):
    bundle(tmp_path);(tmp_path/'data.part').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='checksum'):restore(tmp_path,tmp_path/'new')
    assert not (tmp_path/'new').exists()

def test_traversal_is_rejected_before_extraction(tmp_path):
    bundle(tmp_path,'../escape')
    with pytest.raises(ValueError,match='Unsafe'):restore(tmp_path,tmp_path/'new')
    assert not (tmp_path/'escape').exists()
