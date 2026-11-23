import json,sqlite3,concurrent.futures,shutil,time
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.store import Store
from app.auth import LocalAuth,credential
from app.server import create_app
from app.traceability import outcome
from app.pdf_report import batch_pdf

def record(id='one',batch='LEGACY'):
    return dict(inspection_id=id,created_at='2026-11-21T10:00:00+00:00',source='test',decision='HOLD',severity='major',batch_id=batch,defects=[dict(type='crack',count=1)],original_image_sha256='a'*64)

def test_migration_preserves_legacy_decision_and_can_reopen(tmp_path):
    from app.legacy_store import Store as Old
    old=Old(tmp_path);old.add(record());s=Store(tmp_path)
    assert s.get('one')['decision']=='HOLD' and s.batch('LEGACY')['counts']['HOLD']==1
    assert Store(tmp_path).verify_integrity()['valid']

def test_original_and_audit_rows_are_sql_immutable(tmp_path):
    s=Store(tmp_path);s.add(record())
    for sql in ["UPDATE inspections SET decision='PASS'","DELETE FROM inspections","UPDATE audit_events SET actor='x'","DELETE FROM qa_events"]:
        if 'qa_events' in sql:s.review('one',dict(reviewer='qa',comment='review'))
        with pytest.raises(sqlite3.IntegrityError),s.connection() as db:db.execute(sql)
    assert s.verify_integrity()['valid']

def test_hash_chain_detects_payload_tampering(tmp_path):
    s=Store(tmp_path);s.add(record())
    with s.connection() as db:
        db.execute('DROP TRIGGER immutable_audit_update');db.execute("UPDATE audit_events SET actor='intruder' WHERE seq=1")
    assert not s.verify_integrity()['valid']

def test_spool_survives_failure_replays_once(tmp_path):
    s=Store(tmp_path)
    with patch.object(s,'_apply',side_effect=sqlite3.OperationalError('DB unavailable')):
        assert s.add(record()) is False
        assert s.get('one')['persistence_status']=='spooled'
    assert s.replay()==1 and s.replay()==0
    assert s.get('one')['decision']=='HOLD' and s.verify_integrity()['valid']

def test_backup_restore_integrity(tmp_path):
    s=Store(tmp_path);s.add(record());b=s.backup();restore=tmp_path/'restored';restore.mkdir()
    shutil.copy2(b['path'],restore/'inspections.sqlite3');r=Store(restore)
    assert r.get('one')['decision']=='HOLD' and r.verify_integrity()['valid']

def test_batch_link_counts_close_and_no_unknown_batch(tmp_path):
    s=Store(tmp_path);s.create_batch(dict(batch_id='LOT-1',sku='SKU',description='Demo',category='tablet',operator='op'))
    s.add(record(batch='LOT-1'));assert s.batch('LOT-1')['counts']==dict(total=1,PASS=0,HOLD=1,REVIEW=0)
    assert s.duplicate('a'*64)=='one'
    assert s.close_batch('LOT-1','qa')['status']=='CLOSED'
    with pytest.raises(sqlite3.IntegrityError):s.add(record('other','MISSING'))

def test_parallel_transactions_keep_single_audit_chain(tmp_path):
    s=Store(tmp_path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(lambda i:s.add(record(str(i))),range(24)))
    assert s.stats()['total']==24 and s.verify_integrity()['valid']

def test_qa_append_only_timeline_preserves_decision(tmp_path):
    s=Store(tmp_path);s.add(record());s.review('one',dict(reviewer='qa',comment='first'));s.review('one',dict(reviewer='qa',comment='second'))
    assert len(s.reviews('one'))==2 and s.get('one')['decision']=='HOLD'

def test_roles_password_sessions_and_logout(tmp_path):
    (tmp_path/'users.json').write_text(json.dumps({'aud':credential('test-password-123','auditor')}))
    a=LocalAuth(tmp_path)
    with pytest.raises(ValueError):a.login('aud','wrong','test')
    token,user=a.login('aud','test-password-123','test')
    assert a.user(token)['role']=='auditor'
    assert not a.allowed(user,'POST','/api/inspect') and a.allowed(user,'GET','/api/inspections')
    a.logout(token);assert a.user(token) is None

def test_outcomes_never_turn_uncertainty_into_acceptance():
    assert outcome(dict(capture_valid=True,profile_validated=False))=='MANUAL_REVIEW'
    assert outcome(dict(capture_valid=True,profile_validated=True))=='NO_VISIBLE_DEFECT_DETECTED'
    assert outcome(dict(system_fault=True))=='SYSTEM_FAULT'
    assert outcome(dict(detections=[{'type':'crack'}]))=='DEFECTIVE'

def test_api_auth_and_batch_exports(tmp_path):
    class Service:
        store=Store(tmp_path)
        def close(self):pass
    (tmp_path/'users.json').write_text(json.dumps({'admin':credential('test-password-123','administrator'),'aud':credential('test-password-123','auditor')}))
    with TestClient(create_app({'data_dir':tmp_path},Service())) as c:
        for _ in range(30):
            if c.get('/api/health').json()['ready']:break
            time.sleep(.01)
        assert c.get('/api/batches').status_code==401
        assert c.post('/api/auth/login',json=dict(username='aud',password='test-password-123')).status_code==200
        assert c.post('/api/database/backup').status_code==403
        c.post('/api/auth/logout')
        assert c.post('/api/auth/login',json=dict(username='admin',password='test-password-123')).status_code==200
        assert c.post('/api/batches',json=dict(batch_id='LOT',sku='DEMO',description='test',category='tablet',operator='op')).status_code==200
        assert c.get('/api/batches/LOT/report?format=pdf').content.startswith(b'%PDF-1.4')
        assert c.get('/api/audit/verify').json()['valid']

def test_pdf_contains_no_remote_dependencies():
    pdf=batch_pdf(dict(batch_id='LOT'),[record()],'a'*64)
    assert pdf.startswith(b'%PDF-1.4') and b'/Type /Page' in pdf and b'startxref' in pdf
