"""Verify attached Hailo-8, run real agreement, then switch the installed dashboard.

No device: leave CPU configuration untouched and exit with a useful explanation.
Agreement is a deployment sanity check, not labeled defect accuracy.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_HEF='43abc3f520b97894504d7d99f209846c9f0cc73542eb7b29e9546e7b6def8018'

def api(path,data=None):
    request=urllib.request.Request('http://127.0.0.1:8765'+path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={'Content-Type':'application/json'} if data is not None else {})
    with urllib.request.urlopen(request,timeout=15) as response:return json.load(response)

def start():
    with (Path.home()/'BlisterTrace_Data/launcher.log').open('ab') as log:
        subprocess.Popen([sys.executable,str(ROOT/'main.py'),'--no-browser'],cwd=ROOT,
            stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    for _ in range(60):
        time.sleep(.5)
        try:
            health=api('/api/health')
            if health.get('startup_error'):raise RuntimeError(health['startup_error'])
            if health['ready']:return api('/api/status')
        except OSError:pass
    raise RuntimeError('Dashboard did not become ready; read ~/BlisterTrace_Data/launcher.log')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate',action='store_true',help='Also run image/Llama/CSI/resource validation')
    args=parser.parse_args()
    output=ROOT/'validation'/('hailo_'+datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S'))
    output.mkdir(parents=True,exist_ok=True)
    report={'started_utc':datetime.now(timezone.utc).isoformat(),'ground_truth_accuracy_verified':False}
    config_path=ROOT/'config.json';previous=config_path.read_bytes();changed=False
    try:
        from hailo_platform import Device,HEF
        devices=Device.scan();report['devices']=[str(v) for v in devices]
        if not devices:raise RuntimeError('No Hailo device detected. Power off the Pi, connect the Hailo-8, boot, then rerun this command. CPU configuration has not changed.')
        hef=ROOT/'models/blistertrace.hef'
        report['hef_sha256']=hashlib.sha256(hef.read_bytes()).hexdigest()
        if report['hef_sha256']!=EXPECTED_HEF:raise RuntimeError('HEF checksum differs from the compiled seven-class artifact')
        metadata=HEF(str(hef));report['inputs']=[{'name':v.name,'shape':list(v.shape)} for v in metadata.get_input_vstream_infos()]
        report['outputs']=[{'name':v.name,'shape':list(v.shape)} for v in metadata.get_output_vstream_infos()]
        try:existing=api('/api/status')
        except OSError:existing=None
        if existing:
            api('/api/shutdown',{})
            for _ in range(40):
                time.sleep(.5)
                try:api('/api/health')
                except OSError:break
            else:raise RuntimeError('Existing dashboard did not release its camera/runtime')
        command=[sys.executable,str(ROOT/'tools/verify_hailo.py'),'--hef',str(hef),'--output',str(output/'agreement.json')]
        completed=subprocess.run(command,cwd=ROOT,timeout=300,capture_output=True,text=True)
        (output/'agreement.log').write_text(completed.stdout+'\n'+completed.stderr)
        if completed.returncode:raise RuntimeError('Hailo inference check failed; see '+str(output/'agreement.log'))
        agreement=json.loads((output/'agreement.json').read_text());report['agreement']=agreement
        # Check for a gross layout/contract failure; this does not certify accuracy.
        if agreement['agreement_matches']==0:raise RuntimeError('No FP32/INT8 matches; inspect output mapping before activating this artifact')
        cfg=json.loads(previous);cfg.update(vision_backend='hailo',hef=str(hef),camera_source='picamera2',profile_validated=False)
        (output/'config_before.json').write_bytes(previous)
        config_path.write_text(json.dumps(cfg,indent=2)+'\n');changed=True
        status=start();report['status']=status
        if status['vision_backend']!='hailo':raise RuntimeError('Dashboard did not select actual Hailo inference')
        print('Hailo-8 active. Real HEF inference and FP32 agreement ran successfully.',flush=True)
        if args.validate:
            result=subprocess.run([sys.executable,str(ROOT/'tools/validate_submission_target.py'),
                '--expected-backend','hailo','--camera-seconds','60','--output',str(output/'pipeline')],cwd=ROOT)
            report['pipeline_validation_exit_code']=result.returncode
            if result.returncode:raise RuntimeError('Hailo activated, but pipeline checks failed; inspect '+str(output/'pipeline/summary.json'))
        report['activation_passed']=True
        print('Evidence: '+str(output),flush=True)
        print('Open the dashboard with: ~/blistertrace',flush=True)
    except Exception as e:
        report['activation_passed']=False;report['error']=str(e)
        print(str(e),file=sys.stderr,flush=True)
        if changed:
            try:api('/api/shutdown',{});time.sleep(4)
            except Exception:pass
            config_path.write_bytes(previous)
        # If hardware preflight passed and a running service was stopped, restore it.
        if report.get('devices'):
            try:
                try:api('/api/status')
                except OSError:start()
            except Exception as restore:report['restore_error']=str(restore)
    finally:
        (output/'activation.json').write_text(json.dumps(report,indent=2)+'\n')
    return 0 if report.get('activation_passed') else 1

if __name__=='__main__':raise SystemExit(main())
