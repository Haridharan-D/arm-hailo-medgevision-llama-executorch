"""Assemble verified trained vision weights and existing ExecuTorch artifacts."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parent

def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists() or dst.stat().st_size!=src.stat().st_size or src.stat().st_mtime>dst.stat().st_mtime:
        shutil.copy2(src,dst)

def main():
    source=PROJECT/'YOLO_Model/v2';assets=ROOT/'assets'
    for src,name in [(source/'export/blistertrace_yolov8s.onnx','blistertrace_yolov8s.onnx'),
                     (source/'thresholds.json','thresholds.json'),(source/'model_spec.json','model_spec.json'),
                     (source/'source_attribution.json','source_attribution.json')]:copy(src,assets/name)
    llm=PROJECT/'Llama_ExecuTorch'
    for name in ['advisor.py','sop.json']:
        copy(llm/name,ROOT/'advisor_src'/name)
    (ROOT/'advisor_src/__init__.py').write_text('"""Versioned BlisterTrace advisory adapter."""\n')
    for name in ['Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte','tokenizer.model','params.json','README.md',
                 'Export_Recipe_Llama_3_2_1B_Instruct_SpinQuant_INT4_EO8.ipynb']:
        copy(llm/'artifacts'/name,ROOT/'llama/artifacts'/name)
    copy(llm/'references/EXECUTORCH_LICENSE',ROOT/'llama/EXECUTORCH_LICENSE')
    copy(llm/'bin/x86_64/blistertrace_worker',ROOT/'llama/bin/x86_64/blistertrace_worker')
    # WSL command arguments are literal; no shell interpolation or credentials.
    target=ROOT/'llama/bin/x86_64/libllama_runner.so'
    if not target.exists():
        result=subprocess.run(['wsl.exe','--exec','cat','/home/priyadarsan_d/blistertrace_llm_build/executorch/cmake-out/examples/models/llama/runner/libllama_runner.so'],stdout=subprocess.PIPE,check=True)
        target.write_bytes(result.stdout)
    samples=sorted((source/'calibration_train_only').glob('*.jpg'))[:18]
    for image in samples:copy(image,ROOT/'test_images'/image.name)
    (ROOT/'test_images/README.txt').write_text('These are unannotated training-source demonstration images, NOT an independent test set. Add your own camera test images here.\n')
    hef=PROJECT/'Hailo_Compiler/output/blistertrace.hef'
    if hef.exists():
        copy(hef,ROOT/'models/blistertrace.hef')
        copy(PROJECT/'Hailo_Compiler/output/compile_receipt.json',ROOT/'models/compile_receipt.json')
    manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
              for folder in ['assets','llama','advisor_src','test_images','models'] for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    (ROOT/'asset_hashes.json').write_text(json.dumps(manifest,indent=2))
    print('Prepared',len(manifest),'assets; custom Hailo HEF included:',hef.exists())

if __name__=='__main__':main()
