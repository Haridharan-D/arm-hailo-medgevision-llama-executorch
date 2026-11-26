"""Freeze a normal-only calibration threshold without reading held-out labels.

Input: {model_sha256, rows: [{split:'calibration', label:0, score,
image_sha256}]}. Output is an experimental candidate, never deployed automatically.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.evaluation_protocol import calibrate_normal

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True)
    p.add_argument('--quantile',type=float,default=.995);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();data=json.loads(a.input.read_text())
    result=calibrate_normal(data['rows'],a.quantile)
    result.update(model_sha256=data['model_sha256'],threshold_origin='calibration',
                  calibration_image_sha256=[r['image_sha256'] for r in data['rows']],
                  input_sha256=hashlib.sha256(a.input.read_bytes()).hexdigest(),
                  deployment_status='EXPERIMENTAL_NOT_DEPLOYED')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
