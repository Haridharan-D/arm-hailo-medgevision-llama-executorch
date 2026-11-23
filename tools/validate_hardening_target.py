"""Real image/API/batch/audit/failure/stability checks; no CSI operations."""
import json,time,urllib.request,http.cookiejar,concurrent.futures,hashlib,sqlite3,secrets,os,sys,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'validation/hardening/20261122/target';out.mkdir(parents=True,exist_ok=True)
if (out/'report.json').exists():shutil.copy2(out/'report.json',out/f'report_previous_{time.time_ns()}.json')
base='http://127.0.0.1:8765';jar=http.cookiejar.CookieJar();client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def call(path,data=None):
    request=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
    with client.open(request,timeout=60) as response:return json.load(response)
for _ in range(90):
    try:
        ready=call('/api/ready')
        if ready['ready']:break
    except Exception:time.sleep(1)
else:raise SystemExit('Target did not become ready')
account=Path.home()/'BlisterTrace/Backups/validation_account_20261122.json';me=call('/api/auth/me')
if me.get('needs_setup'):
    credentials={'username':'station-admin','password':secrets.token_urlsafe(18)}
    account.write_text(json.dumps(credentials));os.chmod(account,0o600)
    call('/api/auth/bootstrap',credentials)
if me['required']:
    if not account.exists():raise SystemExit('Existing accounts found; no test credentials available')
    call('/api/auth/login',json.loads(account.read_text()))
checks=[];report={'checks':checks,'scope':'Image API and system integration. No new accuracy claim and no CSI.'}
status=call('/api/status');assert status['vision_backend']=='hailo';checks.append('Hailo pipeline ready')
lot='TARGET-'+str(time.time_ns());call('/api/batches',dict(batch_id=lot,sku='DEMO-SKU',description='Hardware integration evidence',category='blister',operator='validation'))
call('/api/batches/'+lot+'/select',{});checks.append('Batch created and selected')
library=call('/api/library');sample=next((r for r in library if r.get('group')=='crack'),library[0])
start=time.perf_counter();record=call('/api/library/inspect',{'name':sample['name']});report['image_api_ms']=(time.perf_counter()-start)*1000
assert record['batch_id']==lot and record['original_image_sha256'];checks.append('Real frozen HEF inspection with batch and hashes')
id=record['inspection_id'];original_decision=record['decision']
for _ in range(240):
    record=call('/api/inspections/'+id)
    if record.get('advice'):break
    time.sleep(.5)
assert record.get('advice');report['advisory']=record['advice'];report['inspection']=record
assert record['advice']['decision']==original_decision;checks.append('Async advisory/fallback preserves decision')
call('/api/inspections/'+id+'/qa',dict(reviewer='validation',comment='Integration review only; no product-release approval.'))
assert call('/api/inspections/'+id)['decision']==original_decision and len(call('/api/inspections/'+id+'/reviews'))>=1;checks.append('Append-only QA review preserves original')
assert call('/api/audit/verify')['valid'];checks.append('Audit chain and hashed original images verified')
backup=call('/api/database/backup',{});report['backup']=backup
with sqlite3.connect(backup['path']) as db:assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
checks.append('Consistent database backup integrity checked')
with client.open(base+'/api/batches/'+lot+'/report?format=pdf',timeout=20) as response:pdf=response.read()
assert pdf.startswith(b'%PDF');(out/'batch_report.pdf').write_bytes(pdf);checks.append('Actual batch PDF generated')
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    rows=list(pool.map(lambda _:call('/api/library/inspect',{'name':sample['name']}),range(3)))
assert len({r['inspection_id'] for r in rows})==3;checks.append('Concurrent image requests receive unique records')
report['concurrent_records']=[r['inspection_id'] for r in rows]
report['stability_samples']=[]
for i in range(60):
    report['stability_samples'].append(call('/api/status'));time.sleep(1)
checks.append('60-second camera-free API health soak')
report['final_operations_health']=call('/api/operations/health');report['batch']=call('/api/batches/'+lot+'/report')['batch'];report['passed']=True
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({'passed':True,'checks':checks,'advisory_status':record['advice']['status'],'image_api_ms':report['image_api_ms']},indent=2))
