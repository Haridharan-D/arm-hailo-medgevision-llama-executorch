"""Bounded 3B pilot across all CPU threads; keep its sample limits explicit."""
from pathlib import Path
import time,subprocess,json
root=Path(__file__).resolve().parents[1];out=root/'validation/hardening/20261122'
while not (out/'continuation_complete.json').exists():time.sleep(10)
candidate=Path.home()/'BlisterTrace/Llama_Candidates/3b_mediatek_2048'
command=[str(root/'.venv/bin/python'),'tools/benchmark_native_matrix.py','--model',str(candidate/'llama3_2-2048-spin.pte'),'--tokenizer',str(candidate/'tokenizer.bin'),'--repeats','6','--output',str(out/'matrix_3b_pilot')]
result=subprocess.run(command,cwd=root);(out/'matrix_3b_job.json').write_text(json.dumps({'exit_code':result.returncode,'sample_limit':'6 repeats per thread/load cell (3 per prompt size);48 trials total. Pilot tails are not robust.'}))
