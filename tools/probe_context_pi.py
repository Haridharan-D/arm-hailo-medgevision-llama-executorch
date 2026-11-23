"""Probe supported 2K export capacity; do not fabricate a4K artifact."""
import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from advisor_src.advisor import NativeWorker,token_counter
art=Path.home()/'BlisterTrace/Llama_ExecuTorch/artifacts';out=ROOT/'validation/hardening/20261122/context';out.mkdir(parents=True,exist_ok=True)
count=token_counter(art/'tokenizer.model');prompt='<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n'+('Evidence remains immutable. '*320)+'Give one short action.<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n'
w=NativeWorker(ROOT/'native/bin/aarch64/blistertrace_instrumented',art/'Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte',art/'tokenizer.model',3,timeout=240)
report={'prompt_tokens':count(prompt),'export_capacity':2048,'four_k':'Unsupported by this exact exported artifact; no re-export or4K claim.'}
try:
    report['text']=w.generate(prompt,8);report['metrics']=w.last_metrics;report['passed']=True
    report['loaded_runner_library']=[s for s in Path(f'/proc/{w.process.pid}/maps').read_text().splitlines() if 'libllama_runner.so' in s]
except Exception as e:report.update(passed=False,error=repr(e))
finally:w.close()
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
