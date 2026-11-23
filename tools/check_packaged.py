"""Launch the actual EXE, exercise real vision/Llama, then close gracefully."""
import json
import os
import subprocess
import time
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
def main():
    executable=ROOT/'dist/BlisterTrace/BlisterTrace.exe'
    env=os.environ.copy();env['BLISTERTRACE_DATA']=str(ROOT/'validation/packaged_run_data')
    process=subprocess.Popen([str(executable),'--no-browser','--port','8766'],env=env,
                             creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    base='http://127.0.0.1:8766';report={'executable':str(executable),'checks':[]}
    try:
        until=time.monotonic()+60
        while time.monotonic()<until:
            if process.poll() is not None:raise RuntimeError('Executable exited during startup')
            try:
                response=requests.get(base+'/api/status',timeout=2)
                response.raise_for_status();status=response.json();break
            except requests.RequestException:time.sleep(.5)
        else:raise TimeoutError('Executable failed to serve status')
        assert status['packaged'] is True;report['checks'].append('Actual frozen executable started its own service')
        sample=next((ROOT/'test_images').glob('*.jpg'));start=time.perf_counter()
        response=requests.post(base+'/api/inspect',files={'file':(sample.name,sample.read_bytes(),'image/jpeg')},timeout=30)
        response.raise_for_status();row=response.json();report['vision_response_seconds']=time.perf_counter()-start
        assert row['decision']=='HOLD' and row['detections'];report['checks'].append('Frozen executable ran the trained YOLO model')
        until=time.monotonic()+200
        while time.monotonic()<until:
            row=requests.get(base+'/api/inspections/'+row['inspection_id'],timeout=3).json()
            if row['advice'] is not None:break
            time.sleep(.5)
        assert row['advice'] is not None and row['advice']['status']=='llama_validated',row.get('advice')
        report['checks'].append('Frozen executable received real bundled ExecuTorch/Llama inference via WSL')
        report['record']=row
        requests.post(base+'/api/shutdown',timeout=10).raise_for_status()
        process.wait(timeout=20);assert process.returncode==0
        report['checks'].append('Graceful workstation shutdown')
        report['all_passed']=True
    finally:
        if process.poll() is None:process.terminate();process.wait(timeout=20)
        (ROOT/'validation/packaged_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='record'},indent=2))
if __name__=='__main__':main()
