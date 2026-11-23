"""Preserve an unsuccessful compact pilot; run the relevant-example candidate."""
import psutil,signal,json,subprocess,time
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122';out=root/'validation/hardening/20261122/quality_1b_compact_v2'
for p in psutil.process_iter(['pid','cmdline']):
    cmd=' '.join(p.info.get('cmdline') or [])
    if 'evaluate_quality_50.py' in cmd and '--mode compact-v2' in cmd:
        p.send_signal(signal.SIGINT)
        try:p.wait(timeout=15)
        except psutil.TimeoutExpired:p.terminate()
rows=[json.loads(l) for l in (out/'cases.jsonl').read_text().splitlines()]
(out/'pilot_decision.json').write_text(json.dumps({'stopped_early':True,'cases':len(rows),'validated':sum(r.get('result',{}).get('status')=='llama_validated' for r in rows),
 'reason':'Compact prompt produced extra/input-schema fields and truncation; no validation relaxation or production adoption.'},indent=2))
time.sleep(1)
with (Path.home()/'BlisterTrace/Backups/continuation_20261122.log').open('ab') as log:
    p=subprocess.Popen([str(root/'.venv/bin/python'),str(root/'tools/continuation_jobs_pi.py')],cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
print(json.dumps({'started':p.pid,'preserved_failed_trials':len(rows)}))
