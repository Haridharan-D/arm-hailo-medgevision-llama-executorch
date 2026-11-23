"""Run on the Pi after installation; no invented target benchmark numbers."""
import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def command(args):
    if not shutil.which(args[0]):return {'available':False}
    result=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
    return {'available':True,'returncode':result.returncode,'output':result.stdout}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--camera',choices=['0','1','2','picamera2']);parser.add_argument('--seconds',type=int,default=10)
    args=parser.parse_args()
    from app.config import settings
    from app.service import InspectionService
    config=settings();output=config['data_dir']/'target_validation';output.mkdir(exist_ok=True)
    report={'platform':platform.platform(),'architecture':platform.machine(),
            'hailo_identification':command(['hailortcli','fw-control','identify']),
            'memory':command(['free','-h']),'throttling':command(['vcgencmd','get_throttled']),
            'temperature':command(['vcgencmd','measure_temp']),
            'configured_backend':config['vision_backend'],'physical_camera_test_requested':args.camera is not None}
    service=InspectionService(config)
    try:
        import cv2
        sample=next((ROOT/'test_images').glob('*.jpg'));frame=cv2.imread(str(sample))
        record=service.inspect(frame,'target-check:'+sample.name)
        until=time.monotonic()+200
        while time.monotonic()<until:
            record=service.store.get(record['inspection_id'])
            if record['advice'] is not None:break
            time.sleep(.5)
        report['sample_inspection']=record
        report['sample_advice_accepted']=bool(record['advice'] and record['advice']['status']=='llama_validated')
        if args.camera:
            from app.camera import Camera
            camera=Camera(service);camera.start(args.camera);started=time.monotonic();samples=[]
            while time.monotonic()-started<args.seconds:
                time.sleep(.5);samples.append(dict(camera.status))
                if not camera.status['running']:break
            jpeg=camera.snapshot();camera.stop()
            if jpeg:(output/'camera_last_frame.jpg').write_bytes(jpeg)
            report['camera']={'final_status':camera.status,'measurements':samples,'frame_received':jpeg is not None}
    finally:service.close()
    report['post_temperature']=command(['vcgencmd','measure_temp'])
    (output/'target_check.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2));print('Saved target evidence:',output)

if __name__=='__main__':main()
