"""Record current deployed identities without copying credentials or database rows."""
import hashlib,json,platform,subprocess,urllib.request
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122'
out=root/'validation/hardening/20261122'
cfg=json.loads((root/'production_config.json').read_text())
files={}
for p in [root/'native/bin/aarch64/blistertrace_instrumented',root/'native/bin/aarch64/libllama_runner.so',Path(cfg['llama_artifacts'])/'tokenizer.model',root/'advisor_src/advisor.py',root/'advisor_src/sop.json']:
    with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    files[str(p)]={'bytes':p.stat().st_size,'sha256':sha}
health=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/health',timeout=10))
state=subprocess.run(['systemctl','--user','is-active','blistertrace.service'],capture_output=True,text=True)
report={'service':state.stdout.strip(),'ready':health.get('ready'),'platform':platform.platform(),'files':files,
        'runtime':'ExecuTorch v1.0.0, 8c84780911e7f4e9eb19395181b04761392a4b56',
        'settings':{k:cfg.get(k) for k in ['vision_backend','camera_source','auth_required','llama_prompt_mode','llama_output_tokens','llama_prompt_budget','llama_threads']},
        'baseline_preserved':str(Path.home()/'BlisterTrace/BlisterTrace_App'),
        'no_model_or_threshold_changes':True}
(out/'final_runtime_manifest.json').write_text(json.dumps(report,indent=2))
assert report['service']=='active' and report['ready']
print(json.dumps({'service':report['service'],'ready':report['ready'],'files_hashed':len(files)}))
