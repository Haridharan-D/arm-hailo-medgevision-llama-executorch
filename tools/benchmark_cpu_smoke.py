"""Measure the local CPU smoke process tree, including Windows venv child interpreters."""
import json,platform,subprocess,sys,time
from pathlib import Path
import psutil
root=Path(__file__).resolve().parents[1]
out=root/'evidence';out.mkdir(exist_ok=True)
samples=[];known={};started=time.perf_counter()
with (out/'final_smoke_console.txt').open('w') as log:
    p=subprocess.Popen([sys.executable,str(root/'tools/smoke_models.py'),'--output',str(out/'final_cpu_smoke.json')],stdout=log,stderr=subprocess.STDOUT,cwd=root)
    parent=psutil.Process(p.pid)
    while p.poll() is None:
        rss=cpu=0;ids=[]
        try:processes=[parent,*parent.children(recursive=True)]
        except psutil.Error:processes=[]
        for process in processes:
            try:
                if process.pid not in known:
                    known[process.pid]=process;process.cpu_percent()
                item=known[process.pid];rss+=item.memory_info().rss;cpu+=item.cpu_percent();ids.append(process.pid)
            except psutil.Error:pass
        samples.append(dict(rss_mib=rss/1024**2,cpu_percent=cpu,pids=ids));time.sleep(.1)
report=dict(platform=platform.platform(),machine=platform.machine(),scope='Local CPU cold five-image smoke process tree; not Pi or Llama',
    returncode=p.returncode,elapsed_s=time.perf_counter()-started,peak_rss_mib=max(x['rss_mib'] for x in samples),
    peak_cpu_percent=max(x['cpu_percent'] for x in samples),cpu_units='100% is one logical core; sum of process-tree samples',
    memory_units='Sum of process RSS; shared pages may be counted more than once; not PSS',samples=samples)
(out/'final_cpu_resources.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='samples'}))
raise SystemExit(p.returncode)
