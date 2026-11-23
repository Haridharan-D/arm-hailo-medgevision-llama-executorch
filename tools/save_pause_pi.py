"""Persist experiments and restore the preserved baseline before overnight stop."""
import json,os,signal,subprocess,tarfile,time,urllib.request,hashlib
from pathlib import Path
import psutil
root=Path.home()/'BlisterTrace/BlisterTrace_App'
out=root/'validation/hardening/pause_20261121';out.mkdir(parents=True,exist_ok=True)
stopped=[]
for p in psutil.process_iter(['pid','cmdline']):
    cmd=' '.join(p.info.get('cmdline') or [])
    if p.pid!=os.getpid() and any('/tools/'+name in cmd or 'tools/'+name in cmd for name in ['benchmark_native_matrix.py','evaluate_quality_50.py','download_3b_candidate_pi.py']):
        try:p.terminate();stopped.append({'pid':p.pid,'command':cmd})
        except psutil.Error:pass
backup=Path.home()/'BlisterTrace/Backups/hardening_20261121_201140/source.tar.gz'
with tarfile.open(out/'candidate_advisor_before_restore.tar.gz','w:gz') as tar:tar.add(root/'advisor_src',arcname='advisor_src')
with tarfile.open(backup) as tar:
    for name in ['advisor_src/advisor.py','advisor_src/sop.json']:
        (root/name).write_bytes(tar.extractfile(name).read())
# Stop only the temporary isolated-data API, if that process still exists.
info=root/'validation/hardening/controlled_load/process.json'
if info.exists():
    pid=json.loads(info.read_text())['pid']
    try:
        process=psutil.Process(pid)
        env=process.environ()
        if 'controlled_load' in env.get('BLISTERTRACE_DATA',''):
            process.terminate();process.wait(timeout=10);stopped.append({'pid':pid,'command':'temporary controlled-load API'})
    except (psutil.Error,subprocess.TimeoutExpired):pass
status=None
try:status=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/status',timeout=5))
except Exception:
    env=dict(os.environ);env.pop('BLISTERTRACE_CONFIG',None);env.pop('BLISTERTRACE_DATA',None)
    with (out/'restored_baseline_server.log').open('ab') as log:
        subprocess.Popen([str(root/'.venv/bin/python'),str(root/'main.py'),'--no-browser'],cwd=root,env=env,stdout=log,stderr=log,stdin=subprocess.DEVNULL,start_new_session=True)
    for _ in range(20):
        try:status=json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/status',timeout=2));break
        except Exception:time.sleep(.25)
receipt={'stopped':stopped,'baseline_advisor_restored':True,'baseline_server_status':status,'saved_at':time.time(),
         'candidate_artifacts':[],'quality_summary':None,'concurrent_errors':[]}
candidate=Path.home()/'BlisterTrace/Llama_Candidates/3b_mediatek_2048'
for p in candidate.glob('*'):
    if p.is_file():receipt['candidate_artifacts'].append({'name':p.name,'size':p.stat().st_size})
q=root/'validation/hardening/quality_1b_baseline/summary.json'
if q.exists():receipt['quality_summary']=json.loads(q.read_text())
trials=root/'validation/hardening/matrix_concurrent/trials.jsonl'
if trials.exists():receipt['concurrent_errors']=list({str(json.loads(line).get('load_errors')) for line in trials.read_text().splitlines()})
for p in candidate.glob('*.json'):(out/p.name).write_bytes(p.read_bytes())
logs={}
for name in ['matrix_20261121.log','matrix_concurrent.log','quality_1b.log','3b_download.log']:
    p=Path.home()/'BlisterTrace/Backups'/name
    if p.exists():logs[name]=p.read_text(errors='replace')[-16000:]
(out/'experiment_log_tails.json').write_text(json.dumps(logs,indent=2))
(out/'pause_receipt.json').write_text(json.dumps(receipt,indent=2))
with tarfile.open(out/'saved_evidence.tar.gz','w:gz') as tar:
    for part in ['matrix/trials.jsonl','matrix/summary.json','matrix/summary.csv','matrix_concurrent/trials.jsonl','matrix_concurrent/summary.json','matrix_concurrent/summary.csv','quality_1b_baseline','pause_20261121/pause_receipt.json','pause_20261121/experiment_log_tails.json','pause_20261121/provenance.json','pause_20261121/download_receipt.json','pause_20261121/candidate_advisor_before_restore.tar.gz']:
        p=root/'validation/hardening'/part
        if p.exists():tar.add(p,arcname=part)
print(json.dumps({'saved':str(out),'baseline_ready':bool(status and status['ready']),'backend':status.get('vision_backend') if status else None,'stopped_experiments':len(stopped),'candidate_files':receipt['candidate_artifacts'],'concurrency_errors':receipt['concurrent_errors']},indent=2))
