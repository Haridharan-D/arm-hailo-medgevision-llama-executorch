"""Crash ONLY the isolated staging service during a pending advisory, then recover."""
import json,os,signal,subprocess,time,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'validation/hardening/20261122/restart';out.mkdir(parents=True,exist_ok=True)
service=root/'validation/hardening/20261122/staged_service'
def call(path,data=None):
    request=urllib.request.Request('http://127.0.0.1:8765'+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=30) as r:return json.load(r)
pid=json.loads((service/'pid.json').read_text())['pid']
import psutil
env=psutil.Process(pid).environ()
if 'staged_service/data' not in env.get('BLISTERTRACE_DATA',''):raise SystemExit('Refusing crash test outside isolated staging data')
image=call('/api/library')[0]['name'];row=call('/api/library/inspect',{'name':image});id=row['inspection_id']
call('/api/inspections/'+id+'/advice',{});time.sleep(.2)
os.killpg(pid,signal.SIGKILL);time.sleep(2)
subprocess.run([str(root/'.venv/bin/python'),str(root/'tools/staged_server_pi.py'),'start','--advice'],check=True)
restored=call('/api/inspections/'+id);audit=call('/api/audit/verify')
result={'inspection_id':id,'decision_before':row['decision'],'decision_after':restored['decision'],'advice_after':restored.get('advice'),'audit':audit,
        'passed':restored['decision']==row['decision'] and audit['valid'],'scope':'Abrupt process-group kill of isolated-data staging service, never production.'}
(out/'report.json').write_text(json.dumps(result,indent=2));print(json.dumps({'passed':result['passed'],'inspection_id':id}))
