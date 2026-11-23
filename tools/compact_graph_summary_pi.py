import json,subprocess
from pathlib import Path
root=Path.home()/'blistertrace_llm_build/executorch';out=Path.home()/'BlisterTrace/releases/hardening_20261122/validation/hardening/20261122/graph'
data=json.loads((out/'delegation.json').read_text());f=data['methods'][0]
result={'delegate_partitions':len(f['delegates']),'backends':list({d['id'] for d in f['delegates']}),'remaining_operators':f['operators'],'instruction_types':f['instruction_types'],
        'constant_getters':{m['name']:m.get('values') for m in data['constant_methods']}}
binary=Path.home()/'BlisterTrace/releases/hardening_20261122/native/bin/aarch64/blistertrace_instrumented'
r=subprocess.run(['nm','-C',str(binary)],capture_output=True,text=True)
result['compiled_kleidi_symbols']=[s for s in r.stdout.splitlines() if 'kai_run_' in s][:10]
result['compiled_neon_dotprod_kleidi_symbols']=[s for s in r.stdout.splitlines() if 'kai_run_' in s and 'dotprod' in s][:10]
result['hardware_features']=[s for s in Path('/proc/cpuinfo').read_text().splitlines() if s.startswith('Features')][:1]
result['compiled_xnnpack_symbols']=[s for s in r.stdout.splitlines() if 'xnn_create_runtime' in s][:3]
for p in (root/'cmake-out').glob('kleidiai/**/libkleidiai.a'):
    r=subprocess.run(['nm',str(p)],capture_output=True,text=True);result['kleidi_archive']=str(p);result['kleidi_archive_definitions']=[s for s in r.stdout.splitlines() if ' T kai_' in s][:5]
(out/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2)[:8000])
