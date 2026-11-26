"""Alternate baseline/current CPU inference on identical images; not Pi or accuracy validation."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import types
import cv2
import numpy as np
import onnxruntime as ort
import psutil

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.vision import Detector, NAMES
from app.anomaly import AnomalyEngine


def summary(values):
    return {'n':len(values),'p50_ms':float(np.percentile(values,50)),
            'p95_ms':float(np.percentile(values,95)),'mean_ms':float(np.mean(values))}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',default='90302af');p.add_argument('--repeats',type=int,default=10)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.repeats<2:p.error('At least two repetitions required')
    source=subprocess.check_output(['git','show',a.baseline+':app/vision.py'],cwd=ROOT,text=True)
    baseline=types.ModuleType('app._baseline');baseline.__package__='app'
    exec(compile(source,'baseline_vision.py','exec'),baseline.__dict__)
    config={'vision_backend':'onnx','asset_dir':ROOT/'assets'}
    engines={'baseline':baseline.Detector(config),'candidate':Detector(config)}
    files=[ROOT/'test_images/acceptance_demo'/x for x in ['defective/crack/crack.jpg','safe/safe_01.jpg']]
    images=[cv2.imread(str(path)) for path in files]
    if any(im is None for im in images):raise ValueError('Missing selected sample')
    report={'scope':'Actual local CPU execution on selected samples, not held-out accuracy, Hailo, Pi or complete service latency',
            'baseline_commit':subprocess.check_output(['git','rev-parse',a.baseline],cwd=ROOT,text=True).strip(),
            'environment':{'platform':platform.platform(),'processor':platform.processor(),'python':platform.python_version(),
                           'numpy':np.__version__,'onnxruntime':ort.__version__,'opencv':cv2.__version__},
            'images':[{'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path in files],
            'warmup_per_engine':2,'samples':[]}
    process=psutil.Process();cpu_start=process.cpu_times();wall_start=time.perf_counter()
    rss=[process.memory_info().rss]
    try:
        for engine in engines.values():
            for image in images:engine.predict(image)
        measurements={key:[] for key in engines};outputs_equal=True
        for repeat in range(a.repeats):
            for idx,image in enumerate(images):
                outputs={};timings={}
                for key in (['baseline','candidate'] if repeat%2==0 else ['candidate','baseline']):
                    started=time.perf_counter();outputs[key],_=engines[key].predict(image)
                    timings[key]=(time.perf_counter()-started)*1000;measurements[key].append(timings[key])
                equal=outputs['baseline']==outputs['candidate'];outputs_equal &= equal
                report['samples'].append({'repeat':repeat,'image':idx,'ms':timings,'exact_output_equal':equal})
                rss.append(process.memory_info().rss)
            print(f'Paired repetition {repeat+1}/{a.repeats}; outputs identical: {outputs_equal}',flush=True)
        report['detector']={key:summary(values) for key,values in measurements.items()}
        report['exact_detection_outputs_equal']=outputs_equal
        # Isolate the changed stage using simulated class IDs. No simulated inference claim.
        classes=np.random.default_rng(42).integers(0,7,8400)
        old=engines['baseline'].thresholds;vector=np.array([old[name]['threshold'] for name in NAMES],dtype=np.float64)
        assert np.array_equal(np.array([old[NAMES[c]]['threshold'] for c in classes]),vector[classes])
        stage={'baseline':[],'candidate':[]}
        for rep in range(1000):
            for key in (['baseline','candidate'] if rep%2==0 else ['candidate','baseline']):
                start=time.perf_counter()
                result=np.array([old[NAMES[c]]['threshold'] for c in classes]) if key=='baseline' else np.array([old[name]['threshold'] for name in NAMES],dtype=np.float64)[classes]
                stage[key].append((time.perf_counter()-start)*1000)
        report['threshold_lookup_microbenchmark']={'scope':'Simulated seeded class indices; stage timing only',
                                                    **{k:summary(v) for k,v in stage.items()}}
    finally:
        for engine in engines.values():engine.close()
    anomaly=AnomalyEngine(ROOT/'models/anomaly');report['anomaly']={}
    for profile in anomaly.contracts:
        path,_=anomaly.sample_path(profile,'demo/defective/defective_01.png');image=cv2.imread(str(path))
        cold,*_=anomaly.predict(image,profile);rows=[]
        for _ in range(3):
            assessment,*_=anomaly.predict(image,profile);rows.append(assessment['timings_ms'])
        report['anomaly'][profile]={'cold_ms':cold['timings_ms'],'warm_samples':rows,
                                   'warm_summary':{key:summary([r[key] for r in rows]) for key in rows[0]}}
        rss.append(process.memory_info().rss)
    wall=time.perf_counter()-wall_start;cpu_end=process.cpu_times()
    report['resources']={'sampled_peak_process_rss_mib':max(rss)/2**20,
        'average_process_cpu_percent':100*((cpu_end.user-cpu_start.user)+(cpu_end.system-cpu_start.system))/wall,
        'scope':'Entire experiment process; two detector sessions coexist; sampled RSS, not isolated per-model peak'}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'detector':report['detector'],'exact_detection_outputs_equal':report['exact_detection_outputs_equal'],
                      'lookup':report['threshold_lookup_microbenchmark']},indent=2))
    if not report['exact_detection_outputs_equal']:raise SystemExit('Output regression; candidate must not be promoted')


if __name__=='__main__':main()
