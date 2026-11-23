"""Inspect published PTE execution plans without exporting/changing the graph."""
import json,subprocess,struct,mmap
from pathlib import Path
root=Path.home()/'blistertrace_llm_build/executorch'
out=Path.home()/'BlisterTrace/releases/hardening_20261122/validation/hardening/20261122/graph';out.mkdir(parents=True,exist_ok=True)
flatc=root/'cmake-out/third-party/flatc_ep/bin/flatc'
model=Path.home()/'BlisterTrace/Llama_ExecuTorch/artifacts/Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte'
# flatc parses metadata only. Avoid text serialization of constant/delegate byte arrays.
schema=(root/'schema/program.fbs').read_text()
receipt={'pte_header_hex':model.open('rb').read(64).hex(),'schema_fields':[s for s in schema.splitlines() if any(k in s for k in ['delegate','BackendDelegate','execution_plan'])]}
for name in ['schema/extended_header.h','schema/extended_header.cpp']:
    receipt[name]=(root/name).read_text()
lib=root/'cmake-out/examples/models/llama/runner/libllama_runner.so'
r=subprocess.run(['nm','-D',str(lib)],capture_output=True,text=True)
receipt['kleidi_symbols']=[s for s in r.stdout.splitlines() if 'kai_' in s][:16]
receipt['xnn_symbols']=[s for s in r.stdout.splitlines() if 'xnn_' in s][:12]
(out/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({k:v for k,v in receipt.items() if not k.startswith('schema/')},indent=2))
