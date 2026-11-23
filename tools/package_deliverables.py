"""Collect the reviewed Pi demo and frozen model for local/release handoff."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parent
OUTPUT=PROJECT/'BlisterTrace_Deliverables'

def main():
    OUTPUT.mkdir(exist_ok=True)
    source=PROJECT/'YOLO_Model/v2'
    files=[p for p in source.iterdir() if p.is_file() and p.suffix in {'.json','.csv','.txt','.yaml','.py'}]
    for folder in ['export','calibration_train_only']:
        files.extend(p for p in (source/folder).rglob('*') if p.is_file())
    files.append(source/'yolov8s/weights/best.pt')
    bundle=OUTPUT/'BlisterTrace_Frozen_Vision.zip'
    with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as archive:
        for path in files:
            archive.write(path,'YOLO_Model/v2/'+path.relative_to(source).as_posix())
    with zipfile.ZipFile(bundle) as archive:
        assert archive.testzip() is None
    shutil.copy2(PROJECT/'BlisterTrace_Pi_Application.zip',OUTPUT/'BlisterTrace_Pi_Application.zip')
    shutil.copy2(PROJECT/'Hailo_Compiler/output/blistertrace.hef',OUTPUT/'blistertrace.hef')
    shutil.copy2(ROOT/'validation/browser/video/page@dc8f049cc226b179a3eec921d4107c46.webm',OUTPUT/'BlisterTrace_Pi_Hailo_Demo.webm')
    shutil.copy2(ROOT/'TECHNICAL_REPORT.md',OUTPUT/'TECHNICAL_REPORT.md')
    shutil.copy2(PROJECT/'Hailo_Compiler/output/compile_receipt.json',OUTPUT/'compile_receipt.json')
    report={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in OUTPUT.iterdir() if p.is_file() and p.name!='SHA256SUMS.json'}
    (OUTPUT/'SHA256SUMS.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
