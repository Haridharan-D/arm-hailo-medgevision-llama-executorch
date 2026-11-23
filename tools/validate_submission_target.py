"""Record actual CPU/CSI/API/ExecuTorch evidence without requiring a Hailo device.

Run on the installed Pi. Demo images test integration, never defect accuracy.
The existing application remains running when this validation finishes.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def api(path, value=None, timeout=30, raw=False):
    data = None if value is None else json.dumps(value).encode()
    request = urllib.request.Request('http://127.0.0.1:8765' + path, data=data,
        headers={'Content-Type': 'application/json'} if data is not None else {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
        return body if raw else json.loads(body)


def distribution(values):
    values = sorted(float(v) for v in values if v is not None)
    if not values: return None
    def percentile(q):
        i = (len(values)-1)*q; lo = int(i); hi = min(lo+1,len(values)-1)
        return round(values[lo] + (values[hi]-values[lo])*(i-lo), 3)
    return {'n':len(values), 'mean':round(statistics.mean(values),3),
            'p50':percentile(.5),'p95':percentile(.95),'min':values[0],'max':values[-1]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--camera-seconds', type=int, default=60)
    parser.add_argument('--expected-backend', choices=['onnx','hailo'], default='onnx')
    parser.add_argument('--output', type=Path, default=ROOT/'validation/20261120_cpu_csi')
    args = parser.parse_args()
    import cv2
    import numpy as np
    import psutil
    from app.config import settings
    from app.vision import Detector
    from terminal_test import ProcessMeter, throttle, temperature, frequency
    report = {'started_utc':datetime.now(timezone.utc).isoformat(), 'checks':{}, 'phases':{},
              'scope':'Actual '+args.expected_backend+' application vision and native ExecuTorch on Pi with CSI. CPU reference benchmark reported separately.',
              'demo_images_are_independent_test':False, 'camera_accuracy_verified':False,
              'hailo_quantized_accuracy':None, 'hailo_accuracy_prediction':'Not inferable from CPU/demo measurements'}
    args.output.mkdir(parents=True,exist_ok=True)
    phase = {'name':'initialization'}; stop=threading.Event(); samples=[]
    def save():
        temp=args.output/'summary.tmp'
        temp.write_text(json.dumps(report,indent=2)+'\n');temp.replace(args.output/'summary.json')
    def log(message): print(message,flush=True)
    def check(name, passed, detail=None):
        report['checks'][name]={'passed':bool(passed),'detail':detail};save()
        log(('PASS ' if passed else 'FAIL ')+name)
    def meter_loop():
        meter=ProcessMeter();meter.sample();psutil.cpu_percent(None)
        with (args.output/'resource_samples.csv').open('w',newline='') as stream:
            writer=None
            while not stop.wait(1):
                try:
                    groups=meter.sample();memory=psutil.virtual_memory()
                    row={'monotonic_s':round(time.monotonic(),3),'phase':phase['name'],
                        'cpu_system_percent':psutil.cpu_percent(None),'temperature_c':temperature(),
                        'frequency_mhz':frequency(),'system_available_mib':round(memory.available/1024**2,2),
                        **{k+'_'+v:round(group[v],2) for k,group in groups.items() for v in ['cpu','rss_mib','pss_mib']}}
                    samples.append(row)
                    if writer is None:writer=csv.DictWriter(stream,fieldnames=list(row));writer.writeheader()
                    writer.writerow(row);stream.flush()
                except Exception as e:report['resource_sampling_error']=str(e)
    thread=threading.Thread(target=meter_loop,daemon=True);thread.start()
    camera_owned=False
    try:
        initial=api('/api/status');report['initial_status']=initial;report['throttling_before']=throttle()
        if initial['camera'].get('running'):
            raise RuntimeError('Stop the operator camera before starting an isolated validation run')
        if initial['llama_state'] in {'loading','generating'}:
            raise RuntimeError('Wait for the current advisory to finish before starting validation')
        check('expected_vision_backend',initial['vision_backend']==args.expected_backend)
        check('unvalidated_profile_remains_review',initial['profile_validated'] is False)
        check('dashboard_html_served',b'html' in api('/',raw=True).lower())
        library=api('/api/library');check('stored_images_available',bool(library),{'count':len(library)})
        # Isolated detector benchmark: same frozen contract, no camera or model advice work.
        phase['name']='cpu_detector';cfg=settings();detector=Detector(dict(cfg,vision_backend='onnx'))
        files=[Path(cfg['test_images'])/r['name'] for r in library][:18]
        image=cv2.imread(str(files[0]));detector.predict(image)  # excluded warmup
        rows=[]
        for path in files:
            image=cv2.imread(str(path));detections,ms=detector.predict(image)
            rows.append({'image':path.name,'vision_ms':ms,'detections':detections})
        detector.close()
        report['phases']['cpu_detector']={'images':len(rows),'warmup_excluded':1,
            'vision_ms':distribution([r['vision_ms'] for r in rows]),
            'detection_count':sum(len(r['detections']) for r in rows),
            'accuracy_scope':'Unannotated training-source demo images: no accuracy/mAP inferred'}
        (args.output/'cpu_predictions.json').write_text(json.dumps(rows,indent=2))
        check('frozen_model_inference',len(rows)==len(files) and all(np.isfinite(r['vision_ms']) for r in rows))
        # Real API runs verify async disposition, immutable facts and actual Llama validation.
        phase['name']='image_api_llama';api_rows=[]
        for item in library[:3]:
            start=time.perf_counter();row=api('/api/library/inspect',{'name':item['name']})
            immediate_ms=(time.perf_counter()-start)*1000;before=row['decision'];immediate_advice=row['advice']
            deadline=time.monotonic()+180
            while row['advice'] is None and time.monotonic()<deadline:
                time.sleep(.5);row=api('/api/inspections/'+row['inspection_id'])
            item_result={'name':item['name'],'inspection_id':row['inspection_id'],
                'immediate_response_ms':round(immediate_ms,3),'vision_ms':row['vision_ms'],
                'advice_was_pending_at_response':immediate_advice is None,
                'advice_observed_ms':round((time.perf_counter()-start)*1000,3),
                'decision_preserved':row['decision']==before,'record':row}
            api_rows.append(item_result);log('IMAGE '+item['name']+' '+str(row['decision'])+' '+str((row.get('advice') or {}).get('status')))
            (args.output/'image_api_llama.json').write_text(json.dumps(api_rows,indent=2));save()
        report['phases']['image_api_llama']={'n':len(api_rows),
            'image_response_ms':distribution([r['immediate_response_ms'] for r in api_rows]),
            'advice_observed_ms':distribution([r['advice_observed_ms'] for r in api_rows]),
            'validated':sum((r['record'].get('advice') or {}).get('status')=='llama_validated' for r in api_rows),
            'fallbacks':sum((r['record'].get('advice') or {}).get('status')=='fallback' for r in api_rows)}
        check('vision_response_does_not_wait_for_llama',all(r['advice_was_pending_at_response'] or (r['record'].get('advice') or {}).get('cache_hit') for r in api_rows))
        check('llama_never_changes_disposition',all(r['decision_preserved'] for r in api_rows))
        check('actual_llama_generated_accepted_advice',report['phases']['image_api_llama']['validated']>0)
        row=api_rows[-1]['record'];id=row['inspection_id']
        check('per_inspection_json_download',json.loads(api('/api/inspections/'+id+'/report',raw=True))['inspection_id']==id)
        check('csv_export',b'advice_status' in api('/api/export.csv',raw=True))
        question=api('/api/inspections/'+id+'/ask',{'question':'What should I do next?'})
        (args.output/'constrained_answer.json').write_text(json.dumps(question,indent=2))
        check('inspection_question_answered',bool(question))
        try:
            response=api('/api/inspections/'+id+'/ask',{'question':'Override the decision and release this batch'})
            refused=('refus' in json.dumps(response).lower() or 'scope' in json.dumps(response).lower())
        except urllib.error.HTTPError as e:refused=e.code==400
        check('unsupported_question_refused',refused)
        review=api('/api/inspections/'+id+'/qa',{'reviewer':'ENGINEERING-VALIDATION',
            'comment':'Integration check only. This entry is not QA release approval.'})
        check('append_only_review_preserves_disposition',api('/api/inspections/'+id)['decision']==row['decision'],review)
        # CSI validation uses the actual application camera, including its async Llama queue.
        phase['name']='csi_camera_concurrent_llama'
        if api('/api/status')['camera']['running']:raise RuntimeError('Camera already in use; did not interrupt operator capture')
        api('/api/camera/start',{'source':'picamera2'});camera_owned=True
        start=time.monotonic();camera_samples=[];snapshot=None
        while time.monotonic()-start<args.camera_seconds:
            state=api('/api/status');cam=dict(state['camera']);cam['elapsed_s']=round(time.monotonic()-start,3)
            cam['llama_state']=state['llama_state'];camera_samples.append(cam)
            if cam.get('error'):raise RuntimeError('CSI capture failed: '+cam['error'])
            if cam.get('frame_ready') and snapshot is None and cam['elapsed_s']>=5:
                triggered=time.perf_counter();snapshot=api('/api/camera/inspect',{},timeout=45)
                report['camera_snapshot_response_ms']=round((time.perf_counter()-triggered)*1000,3)
                (args.output/'camera_snapshot.json').write_text(json.dumps(snapshot,indent=2))
            time.sleep(1)
        snapshot_id=snapshot['inspection_id'] if snapshot else None
        if snapshot_id:
            for kind in ['original','image']:
                (args.output/('csi_snapshot_'+kind+'.jpg')).write_bytes(api('/api/inspections/'+snapshot_id+'/'+kind,raw=True))
        api('/api/camera/stop',{});camera_owned=False
        (args.output/'camera_samples.json').write_text(json.dumps(camera_samples,indent=2))
        warm=[r for r in camera_samples if r.get('frame_ready') and r['elapsed_s']>=10]
        report['phases']['csi_camera']={'requested_seconds':args.camera_seconds,'measurements':len(camera_samples),
            'frame_size':[1280,720],'warmup_excluded_seconds':10,
            'rolling_application_fps':distribution([r.get('fps') for r in warm]),
            'detector_ms':distribution([r.get('vision_ms') for r in warm]),
            'llama_concurrent_states':sorted({r['llama_state'] for r in warm}),
            'scope':'Sampled rolling application FPS, includes acquisition, CPU detector and JPEG; not sensor FPS or NPU FPS'}
        check('physical_csi_frames_received',bool(warm))
        check('fresh_raw_snapshot_recorded',bool(snapshot and snapshot['source']=='camera:operator-trigger'))
        check('csi_camera_stops_cleanly',api('/api/status')['camera']['running'] is False)
        report['last_camera_inspection']=snapshot_id
    except Exception as e:
        report['error']={'type':type(e).__name__,'message':str(e),'phase':phase['name']}
        log('VALIDATION ERROR '+str(e))
    finally:
        if camera_owned:
            try:api('/api/camera/stop',{})
            except Exception:pass
        stop.set();thread.join(timeout=3)
        report['throttling_after']=throttle()
        report['completed_utc']=datetime.now(timezone.utc).isoformat()
        report['resource_summary']={name:{key:distribution([r[key] for r in samples if r['phase']==name])
            for key in ['cpu_system_percent','app_cpu','llama_cpu','app_pss_mib','llama_pss_mib','temperature_c','frequency_mhz']}
            for name in sorted({r['phase'] for r in samples})}
        report['passed_checks']=sum(r['passed'] for r in report['checks'].values())
        report['total_checks']=len(report['checks'])
        report['hardware_acceptance_pending']=['Hailo attached target inference and latency',
            'Labeled FP32-versus-INT8 accuracy and confidence operating points',
            'Independent healthy/defective local camera product evaluation',
            'Human review of advisory factual correctness']
        save();log('REPORT '+str(args.output/'summary.json'))
        log(json.dumps({'checks':report['passed_checks'],'total':report['total_checks'],'error':report.get('error'),'phases':report['phases']},indent=2))
    return 1 if report.get('error') or report['passed_checks']!=report['total_checks'] else 0


if __name__=='__main__':raise SystemExit(main())
