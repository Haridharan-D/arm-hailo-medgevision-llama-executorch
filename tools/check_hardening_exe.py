"""Launch the actual packaged executable with isolated state and exercise APIs."""
import json,os,subprocess,time,urllib.request,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'validation/hardening/20261122/windows';out.mkdir(parents=True,exist_ok=True)
if (out/'report.json').exists():shutil.copy2(out/'report.json',out/f'report_previous_{time.time_ns()}.json')
cfg=out/'config.json';cfg.write_text(json.dumps({'vision_backend':'onnx','profile_validated':False,'advice_enabled':True,'llama_threads':3,'llama_prompt_mode':'adaptive-v1','llama_output_tokens':128,'auth_required':False,'port':8771}))
env=dict(os.environ,BLISTERTRACE_DATA=str(out/'data'),BLISTERTRACE_CONFIG=str(cfg));exe=root/'dist_hardening/BlisterTrace/BlisterTrace.exe'
proc=subprocess.Popen([str(exe),'--no-browser','--port','8771'],cwd=exe.parent,env=env)
base='http://127.0.0.1:8771'
def call(path,value=None):
    req=urllib.request.Request(base+path,data=json.dumps(value).encode() if value is not None else None,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=40) as r:return json.load(r)
report={'executable':str(exe),'scope':'Actual Windows packaged build, CPU vision and WSL native ExecuTorch; no Hailo/camera claims.'}
try:
    for _ in range(120):
        try:
            if call('/api/health')['ready']:break
        except OSError:pass
        time.sleep(.5)
    report['status']=call('/api/status');assert report['status']['packaged']
    report['authentication']=call('/api/auth/me');assert report['authentication']['required'] is False
    with urllib.request.urlopen(base+'/display',timeout=10) as r:assert r.status==200
    batch='WINDOWS-'+str(time.time_ns());call('/api/batches',dict(batch_id=batch,sku='DEMO',description='Packaged executable validation',category='tablet',operator='test'));call('/api/batches/'+batch+'/select',{})
    samples=call('/api/library');sample=next((s for s in samples if s.get('group')=='crack'),samples[0]);r=call('/api/library/inspect',{'name':sample['name']});id=r['inspection_id'];assert r['batch_id']==batch
    for _ in range(400):
        r=call('/api/inspections/'+id)
        if r.get('advice'):break
        time.sleep(.5)
    assert r.get('advice');report['record']=r
    if any(row.get('group')=='demo_safe' for row in samples):
        safe=next(row for row in samples if row.get('group')=='demo_safe')
        y=call('/api/library/inspect',{'name':safe['name']});assert y['visual_result']['status']=='SAFE' and y['decision']=='REVIEW'
        a=call('/api/anomaly/inspect',{'profile':'mvtec_capsule','sample':'demo/safe/safe_01.png'});assert a['visual_result']['status']=='SAFE' and a['decision']=='REVIEW'
        report['visual_examples']={'yolo':y,'anomaly':a}
    report['audit']=call('/api/audit/verify');assert report['audit']['valid'];report['passed']=True
except Exception as e:report.update(passed=False,error=repr(e))
finally:
    try:call('/api/shutdown',{})
    except Exception:pass
    try:proc.wait(timeout=20)
    except subprocess.TimeoutExpired:proc.terminate()
    (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({'passed':report.get('passed'),'error':report.get('error'),'advice_status':report.get('record',{}).get('advice',{}).get('status')},indent=2))
if not report.get('passed'):raise SystemExit(1)
