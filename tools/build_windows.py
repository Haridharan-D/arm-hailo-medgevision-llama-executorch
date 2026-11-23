"""Build the desktop launcher and assemble its model/runtime sidecars."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from prepare_assets import copy

def main():
    if sys.platform!='win32':raise SystemExit('Build the Windows application on Windows.')
    subprocess.run([sys.executable,str(ROOT/'tools/verify_repository_artifacts.py')],cwd=ROOT,check=True)
    # Never invoke prepare_assets here: it would replace reviewed advisor code.
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--distpath','dist_hardening','--workpath','build_hardening',str(ROOT/'BlisterTrace.spec')],cwd=ROOT,check=True)
    dist=ROOT/'dist_hardening/BlisterTrace'
    for folder in ['llama','test_images','models']:
        for source in (ROOT/folder).rglob('*'):
            if source.is_file() and '__pycache__' not in source.parts:copy(source,dist/source.relative_to(ROOT))
    for name in ['config.json','README.md','TECHNICAL_REPORT.md','SUBMISSION_CHECKLIST.md','asset_hashes.json']:
        if (ROOT/name).exists():copy(ROOT/name,dist/name)
    cfg=json.loads((dist/'config.json').read_text());cfg.update(auth_required=False,llama_prompt_mode='adaptive-v1',llama_output_tokens=128)
    # Resolve sidecars from the distribution, not the builder's absolute checkout.
    for key in ['llama_runtime','llama_artifacts','test_images','anomaly_models','hef']:
        cfg.pop(key,None)
    (dist/'config.json').write_text(json.dumps(cfg,indent=2))
    report={'executable':str(dist/'BlisterTrace.exe'),'model_files_included':(dist/'models/blistertrace.hef').is_file(),
            'llama_model_included':(dist/'llama/artifacts/Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte').is_file(),
            'llama_worker_included':(dist/'llama/bin/x86_64/blistertrace_worker').is_file(),
            'windows_llama_runtime':'Bundled x86-64 ExecuTorch worker through installed WSL Ubuntu 24.04',
            'standalone_without_wsl':False,'pi_uses_native_arm_runtime':True}
    (ROOT/'validation').mkdir(exist_ok=True)
    (ROOT/'validation/windows_build.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
