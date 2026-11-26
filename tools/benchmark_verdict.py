"""Measure decoded-image -> persisted verdict on CPU with advisory explicitly disabled.

Includes preprocessing, inference, QA policy, image encoding, SQLite and fallback
recording. Excludes camera acquisition, HTTP/browser and native Llama generation.
Uses a new temporary station; never modifies an existing operator database.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import time
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.config import settings
from app.service import InspectionService


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--repeats',type=int,default=3);a=p.parse_args()
    if a.repeats<1:p.error('Positive repetition count required')
    with tempfile.TemporaryDirectory(prefix='medge-verdict-') as tmp:
        previous=os.environ.get('BLISTERTRACE_DATA');os.environ['BLISTERTRACE_DATA']=tmp
        try:config=settings()
        finally:
            if previous is None:os.environ.pop('BLISTERTRACE_DATA',None)
            else:os.environ['BLISTERTRACE_DATA']=previous
        config.update(vision_backend='onnx',advice_enabled=False,profile_validated=False,
                      llama_runtime=str(ROOT/'unavailable-runtime'),llama_artifacts=str(ROOT/'llama/artifacts'))
        service=InspectionService(config);rows=[]
        try:
            names=['defective/crack/crack.jpg','safe/safe_01.jpg']
            images=[cv2.imread(str(ROOT/'test_images/acceptance_demo'/name)) for name in names]
            for image in images:service.analyze(image)
            for repeat in range(a.repeats):
                for name,image in zip(names,images):
                    start=time.perf_counter();r=service.inspect(image,source='cpu-verdict-benchmark')
                    rows.append(dict(sample=name,repeat=repeat,elapsed_ms=(time.perf_counter()-start)*1000,
                        detector_ms=r['vision_ms'],decision=r['decision'],advice_status=(r.get('advice') or {}).get('status','pending'),
                        persisted=service.store.get(r['inspection_id']) is not None))
        finally:service.close()
    result={'scope':__doc__,'platform':platform.platform(),'warmup_detector_calls':2,'rows':rows,
            'p50_ms':float(np.percentile([r['elapsed_ms'] for r in rows],50)),
            'p95_ms':float(np.percentile([r['elapsed_ms'] for r in rows],95)),
            'native_llama':'NOT TESTED','hailo':'NOT TESTED','dashboard_paint':'NOT TESTED'}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['rows','scope']},indent=2))


if __name__=='__main__':main()
