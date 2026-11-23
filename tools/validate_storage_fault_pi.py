"""Actual SQLite writer lock -> durable spool -> replay, isolated from production."""
import json,sqlite3,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from app.store import Store
out=root/'validation/hardening/20261122/storage_fault';out.mkdir(parents=True,exist_ok=True);s=Store(out/'data')
id='LOCK-'+str(time.time_ns());r=dict(inspection_id=id,created_at='2026-11-22',source='controlled DB lock test',decision='HOLD',severity='major')
blocker=sqlite3.connect(s.path);blocker.execute('BEGIN IMMEDIATE');at=time.perf_counter()
try:committed=s.add(r)
finally:blocker.rollback();blocker.close()
spooled=s.get(id);count=s.replay();restored=s.get(id)
report={'passed':committed is False and spooled.get('persistence_status')=='spooled' and restored['decision']=='HOLD' and count>=1,'replayed':count,'elapsed_ms':(time.perf_counter()-at)*1000,'audit_valid':s.verify_integrity()['valid'],'scope':'Real SQLite writer lock on separate test database; production database untouched.'}
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
