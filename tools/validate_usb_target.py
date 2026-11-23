"""Authorized USB camera test using the ONE running Hailo inspection API."""
import json,time,urllib.request,http.cookiejar,os
from pathlib import Path
base='http://127.0.0.1:8765';out=Path.home()/'BlisterTrace/releases/hardening_20261122/validation/hardening/20261122/usb';out.mkdir(parents=True,exist_ok=True)
jar=http.cookiejar.CookieJar();client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def call(path,data=None):
    request=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
    with client.open(request,timeout=30) as response:return json.load(response)
auth=call('/api/auth/me')
if auth['required']:
    account=Path.home()/'BlisterTrace/Backups/validation_account_20261122.json'
    if not account.exists():raise SystemExit('Target validator requires its locally provisioned test account; no credentials printed.')
    call('/api/auth/login',json.loads(account.read_text()))
report={'source':'USB video0','scope':'Observed scene acquisition and timing only; no labeled blister accuracy or factory throughput claim.','samples':[]}
try:
    call('/api/camera/start',{'source':'0'})
    for _ in range(60):
        status=call('/api/status')
        if status['camera'].get('frame_ready') and status['camera'].get('fps',0)>0:break
        if status['camera'].get('error'):raise RuntimeError(status['camera']['error'])
        time.sleep(.5)
    for _ in range(20):
        report['samples'].append(call('/api/status'));time.sleep(.5)
    start=time.perf_counter();record=call('/api/camera/inspect',{});report['snapshot_api_ms']=(time.perf_counter()-start)*1000
    report['inspection']=record
    with client.open(base+record['original_url'],timeout=10) as response:(out/'captured_usb.jpg').write_bytes(response.read())
    report['passed']=bool(record['inspection_id'] and report['samples'][-1]['camera']['fps']>0)
except Exception as e:report.update(passed=False,error=repr(e))
finally:
    try:call('/api/camera/stop',{})
    except Exception:pass
    (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in {'samples','inspection'}},indent=2))
