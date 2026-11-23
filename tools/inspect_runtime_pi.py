"""Read-only delegate/build evidence. Enumerates USB sysfs only, never CSI."""
import json,subprocess,importlib.util
from pathlib import Path
root=Path.home()/'blistertrace_llm_build/executorch'
out={}
for name in ['backends/xnnpack/third-party/XNNPACK','third-party/ao','extension/llm/tokenizers']:
    r=subprocess.run(['git','-C',str(root/name),'rev-parse','HEAD'],capture_output=True,text=True);out[name]=r.stdout.strip()
out['flatc']=[str(p) for p in (root/'cmake-out').rglob('flatc') if p.is_file()][:5]
out['schemas']=[str(p) for p in (root/'schema').glob('*')]
out['flatbuffers_python']=importlib.util.find_spec('flatbuffers') is not None
out['usb_video']={p.name:(p.resolve().as_posix(),(p/'name').read_text().strip()) for p in Path('/sys/class/video4linux').glob('video*') if '/usb' in p.resolve().as_posix()}
binary=Path.home()/'BlisterTrace/BlisterTrace_App/native/bin/aarch64/blistertrace_instrumented'
r=subprocess.run(['ldd',str(binary)],capture_output=True,text=True);out['native_dependencies']=r.stdout
libs=list((root/'cmake-out/examples/models/llama').glob('libllama_runner.so'))
if libs:
    r=subprocess.run(['nm','-D',str(libs[0])],capture_output=True,text=True)
    out['kleidi_exported_symbols']=[s for s in r.stdout.splitlines() if 'kai_' in s][:16]
    out['xnnpack_symbols']=[s for s in r.stdout.splitlines() if 'xnn_' in s][:12]
p=Path.home()/'BlisterTrace/releases/hardening_20261122/validation/hardening/20261122';p.mkdir(parents=True,exist_ok=True)
(p/'runtime_inspection.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
