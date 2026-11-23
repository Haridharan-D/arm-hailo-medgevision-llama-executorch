"""Sequential experiments: no competing Llama model workers; durable outputs."""
import json,subprocess,time,sys,os
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122';py=root/'.venv/bin/python';out=root/'validation/hardening/20261122';out.mkdir(parents=True,exist_ok=True)
while not (out/'quality_3b/summary.json').exists():time.sleep(10)
commands=[
 [str(py),'tools/evaluate_quality_50.py','--mode','adaptive-v1','--tokens','128','--output',str(out/'quality_1b_adaptive_v1')],
 [str(py),'tools/start_controlled_load_pi.py'],
 [str(py),'tools/benchmark_native_matrix.py','--active-only','--output',str(out/'matrix_concurrent_validated')]]
for i,cmd in enumerate(commands):
    print('Starting',cmd,flush=True)
    p=subprocess.run(cmd,cwd=root)
    (out/f'job_{i}.json').write_text(json.dumps({'command':cmd,'exit_code':p.returncode}))
    if p.returncode:raise SystemExit(p.returncode)
(out/'continuation_complete.json').write_text(json.dumps({'complete':True}))
