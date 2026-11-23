"""Measure actual Pi camera pipeline while native Llama runs independently."""
import json
import time
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1];BASE='http://127.0.0.1:8770'
def main():
    until=time.monotonic()+40
    while True:
        try:status=requests.get(BASE+'/api/status',timeout=3).json();break
        except requests.RequestException:
            if time.monotonic()>=until:raise
            time.sleep(.5)
    assert status['vision_backend']=='hailo',status
    sample=next((ROOT/'test_images').glob('*.jpg'))
    start=time.perf_counter()
    response=requests.post(BASE+'/api/inspect',files={'file':(sample.name,sample.read_bytes(),'image/jpeg')},timeout=15)
    response.raise_for_status();record=response.json();response_time=time.perf_counter()-start
    assert record['backend']=='hailo' and record['decision']=='HOLD',record
    requests.post(BASE+'/api/camera/start',json={'source':'0'},timeout=5).raise_for_status()
    observations=[]
    try:
        for _ in range(18):
            time.sleep(1)
            state=requests.get(BASE+'/api/status',timeout=5).json()
            observations.append({'camera':state['camera'],'llama_state':state['llama_state'],
                                 'temperature_c':state['temperature_c']})
            if state['camera']['error']:raise RuntimeError(state['camera']['error'])
    finally:requests.post(BASE+'/api/camera/stop',timeout=15)
    until=time.monotonic()+180
    while time.monotonic()<until:
        record=requests.get(BASE+'/api/inspections/'+record['inspection_id'],timeout=5).json()
        if record['advice'] is not None:break
        time.sleep(.5)
    assert record['advice'] and record['advice']['status']=='llama_validated',record['advice']
    samples=[r['camera']['fps'] for r in observations[4:] if r['camera']['fps']>0]
    report={'backend':'Hailo-8 through HailoRT','camera':'Physical Lenovo USB webcam 1280x720 MJPEG',
            'image_response_seconds':response_time,'image_vision_ms':record['vision_ms'],
            'advisory_status':record['advice']['status'],'advisory_elapsed_ms':record['advice']['elapsed_ms'],
            'camera_observed_fps_mean':sum(samples)/len(samples) if samples else None,
            'fps_scope':'Acquisition + preprocessing + detector + annotation/JPEG + pacing; sliding window estimate',
            'concurrent_llama_generation_observed':any(r['llama_state']=='generating' for r in observations),
            'observations':observations,'record':record,'camera_accuracy_verified':False}
    (ROOT/'validation/pi_hailo_live.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in {'record','observations'}},indent=2))
if __name__=='__main__':main()
