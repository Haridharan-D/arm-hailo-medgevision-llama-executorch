import hashlib
from app.store import Store
def test_image_hash_does_not_replace_audit_chain_link(tmp_path):
    s=Store(tmp_path);data=b'controlled stored image bytes';(tmp_path/'images/T_original.jpg').write_bytes(data)
    s.add(dict(inspection_id='T',created_at='now',source='test',decision='REVIEW',severity='unknown',original_image_sha256=hashlib.sha256(data).hexdigest()))
    s.advice('T',{'status':'fallback'});s.event('test.after_image',{})
    r=s.verify_integrity(verify_images=True)
    assert r['valid'] and r['images_checked']==1
    (tmp_path/'images/T_original.jpg').write_bytes(b'changed')
    r=s.verify_integrity(verify_images=True)
    assert not r['valid'] and r['invalid_images']==['T'] and not r['invalid_sequences']
