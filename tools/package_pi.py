"""Small Pi/source handoff; reuse the model and Arm Llama build already on Pi."""
import hashlib
import json
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    names=['main.py','config.json','requirements.txt','requirements-build.txt','README.md','TECHNICAL_REPORT.md',
           'install_pi.sh','launch_pi.sh','install_hailo_pi.sh','BlisterTrace.spec','.gitignore','asset_hashes.json','TERMINAL_TESTS.md']
    files=[ROOT/name for name in names]
    for folder in ['app','web','advisor_src','assets','test_images','tests','tools','models']:
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    target=ROOT.parent/'BlisterTrace_Pi_Application.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for p in files:z.write(p,'BlisterTrace_App/'+p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    report={'file':str(target),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'llama_weights':'Reuse ~/BlisterTrace/Llama_ExecuTorch/artifacts on the Pi',
            'llama_runtime':'Reuse verified native aarch64 build','custom_hef_included':(ROOT/'models/blistertrace.hef').exists()}
    (ROOT/'validation/pi_package.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
