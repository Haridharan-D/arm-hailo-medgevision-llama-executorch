"""Decode the extended-header bounded metadata, excluding appended weights."""
import json,struct,subprocess
from pathlib import Path
root=Path.home()/'blistertrace_llm_build/executorch';dest=Path.home()/'BlisterTrace/releases/hardening_20261122/validation/hardening/20261122/graph';dest.mkdir(parents=True,exist_ok=True)
model=Path.home()/'BlisterTrace/Llama_ExecuTorch/artifacts/Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte'
with model.open('rb') as f:
    header=f.read(32)
    if header[8:12]!=b'eh00':raise ValueError('Unsupported extended header')
    size=struct.unpack_from('<Q',header,16)[0]
    if not 64<size<8*1024*1024:raise ValueError('Unexpected metadata length')
    f.seek(0);(dest/'metadata.pte').write_bytes(f.read(size))
flatc=root/'cmake-out/third-party/flatc_ep/bin/flatc'
r=subprocess.run([str(flatc),'-t','--strict-json','--defaults-json','-o',str(dest),str(root/'schema/program.fbs'),'--',str(dest/'metadata.pte')],capture_output=True,text=True)
receipt={'flatc_exit':r.returncode,'stderr':r.stderr,'metadata_bytes':size,'methods':[]}
if r.returncode==0:
    data=json.loads((dest/'metadata.json').read_text())
    for method in data.get('execution_plan',[]):
        chains=method.get('chains',[]);calls=[]
        for c in chains:
            for i in c.get('instructions',[]):
                calls.append(i.get('instr_args_type',i.get('instr_args',{})))
        receipt['methods'].append({'name':method.get('name'),'delegates':method.get('delegates'),
            'operators':method.get('operators'),'instruction_types':{str(t):calls.count(t) for t in set(str(x) for x in calls)},'instruction_count':len(calls)})
    # Constant getters provide exact exported configuration, not family guesses.
    receipt['constant_methods']=[m for m in data.get('execution_plan',[]) if m.get('name','').startswith('get_')]
binary=root/'cmake-out/examples/models/llama/runner/libllama_runner.so'
r=subprocess.run(['nm','-C',str(binary)],capture_output=True,text=True)
receipt['kleidi_symbols']=[s for s in r.stdout.splitlines() if 'kai_' in s][:12]
for lib in (root/'cmake-out').glob('backends/xnnpack/**/*.a'):
    r=subprocess.run(['nm',str(lib)],capture_output=True,text=True)
    found=[s for s in r.stdout.splitlines() if 'kai_' in s and ' U ' not in s]
    if found:receipt['kleidi_archive']={'path':str(lib),'defined_symbols':found[:12]};break
(dest/'delegation.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2)[:10000])
