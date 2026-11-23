"""Actual deployment inference per demo; compares observations, never forces outputs."""
import csv,json,time,urllib.request
from pathlib import Path
suite=Path.home()/'BlisterTrace_TestSuite_20261122';root=Path.home()/'BlisterTrace/releases/hardening_20261122';out=root/'validation/visual_suite_20261122';out.mkdir(exist_ok=True)
rows=json.loads((suite/'manifest_candidates.json').read_text());base='http://127.0.0.1:8765'
def call(path,data=None):
    request=urllib.request.Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=150) as r:return json.load(r)
assert not call('/api/auth/me')['required']
status=call('/api/status');assert status['vision_backend']=='hailo'
if status.get('camera',{}).get('running'):call('/api/camera/stop',{})
previous={}
if (out/'results.jsonl').exists():
    for line in (out/'results.jsonl').read_text().splitlines():
        try:value=json.loads(line);previous[value['file']]=value
        except json.JSONDecodeError:pass
batch='VISUAL-DEMO-'+str(time.time_ns());call('/api/batches',dict(batch_id=batch,sku='SELECTED-DEMO',description='Selected29-case functionality demonstration; not accuracy evaluation',category='blister',operator='local-operator'));call('/api/batches/'+batch+'/select',{})
results=[]
for row in rows:
    old=previous.get(row['file'])
    if old and old.get('matched') and old['sha256']==row['sha256']:
        saved=call('/api/inspections/'+old['inspection_id'])
        if saved.get('visual_result',{}).get('status')==old['actual_visual']:
            results.append(old);print('Previously executed and record verified:',row['file'],old['actual_visual'],flush=True);continue
    start=time.perf_counter()
    if row['pipeline']=='yolo':
        rel=(Path('acceptance_demo')/Path(row['file']).relative_to('YOLO')).as_posix();r=call('/api/library/inspect',{'name':rel})
    else:
        rel=(Path('demo')/Path(row['file']).relative_to(Path('Anomaly')/row['profile'])).as_posix();r=call('/api/anomaly/inspect',dict(profile=row['profile'],sample=rel))
    result=dict(row,inspection_id=r['inspection_id'],actual_visual=r['visual_result']['status'],qa_decision=r['decision'],capture_valid=r['capture_valid'],
        detections=r['detections'],anomaly=r.get('anomaly'),model_sha256=r['model_sha256'],api_elapsed_ms=round((time.perf_counter()-start)*1000,2))
    result['matched']=result['actual_visual']==row['expected_visual'] and (not row.get('expected_class') or row['expected_class'] in {d['type'] for d in r['detections']})
    results.append(result)
    with (out/'results.jsonl').open('a') as f:f.write(json.dumps(result)+'\n');f.flush()
    print(row['file'],result['actual_visual'],'expected',row['expected_visual'],'matched',result['matched'],flush=True)
report={'passed':all(r['matched'] for r in results),'checked':len(results),'matched':sum(r['matched'] for r in results),'batch':batch,'results':results,
    'scope':'Selected29-image demo, including synthetic bad-capture warnings and previously screened positives. Not unbiased accuracy; QA decisions and model thresholds unchanged.'}
for path in [suite/'verification.json',out/'report.json']:path.write_text(json.dumps(report,indent=2))
with (suite/'results.csv').open('w',newline='') as f:
    keys=['file','expected_visual','actual_visual','matched','qa_decision','capture_valid','inspection_id','api_elapsed_ms'];w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(results)
print(json.dumps({'passed':report['passed'],'checked':len(results),'matched':report['matched']}))
if not report['passed']:raise SystemExit(1)
