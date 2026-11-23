"""Durable CSI-free native timing matrix. Resume skips completed trial keys."""
import argparse,csv,json,os,sys,time,threading,statistics,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from advisor_src.advisor import NativeWorker
import psutil

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--repeats',type=int,default=30);p.add_argument('--active-only',action='store_true');p.add_argument('--model',type=Path);p.add_argument('--tokenizer',type=Path);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True);raw=a.output/'trials.jsonl'
    rows=[json.loads(x) for x in raw.read_text().splitlines()] if raw.exists() else []
    done={r['key'] for r in rows};art=Path.home()/'BlisterTrace/Llama_ExecuTorch/artifacts'
    binary=ROOT/'native/bin/aarch64/blistertrace_instrumented'
    prompts={
      'short':'<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\nGive one short technical instruction for preserving an inspection image for QA review.<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n',
      'medium':'<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n'+('Inspection evidence is immutable. Advice cannot change the detector decision. Consult the approved SOP. '*12)+'Write one short technical instruction for evidence preservation.<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n'}
    for active in ([True] if a.active_only else [False,True]):
      load_stop=threading.Event();load_error=[];load_count=[0];load_thread=None
      if active:
        def load():
          try:
            import urllib.request
            base='http://127.0.0.1:8765'
            for _ in range(120):
                try:
                    status=json.load(urllib.request.urlopen(base+'/api/status',timeout=2))
                    if status.get('ready'):break
                except Exception:pass
                load_stop.wait(.5)
            else:raise RuntimeError('Load API never became ready')
            status=json.load(urllib.request.urlopen(base+'/api/status',timeout=10))
            if status['vision_backend']!='hailo':raise RuntimeError('Concurrent load requires Hailo')
            library=json.load(urllib.request.urlopen(base+'/api/library',timeout=10));name=library[0]['name']
            while not load_stop.is_set():
                req=urllib.request.Request(base+'/api/library/inspect',data=json.dumps({'name':name}).encode(),headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=20) as response:json.load(response)
                load_count[0]+=1;load_stop.wait(.1)
          except Exception as e:load_error.append(repr(e))
        load_thread=threading.Thread(target=load,daemon=True);load_thread.start();time.sleep(1)
      try:
       for threads in [1,2,3,4]:
        worker=NativeWorker(binary,a.model or art/'Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte',a.tokenizer or art/'tokenizer.model',threads,timeout=240)
        try:
         warm=time.perf_counter();worker.generate(prompts['short'],4);warm_ms=(time.perf_counter()-warm)*1000
         for i in range(a.repeats):
          length='short' if i%2==0 else 'medium';key=f'{active}-{threads}-{i}'
          if key in done:continue
          stop=threading.Event();samples=[]
          def sample():
            proc=psutil.Process(worker.process.pid);proc.cpu_percent()
            while not stop.wait(.2):
              try:
                temp=Path('/sys/class/thermal/thermal_zone0/temp')
                samples.append({'rss_mib':proc.memory_info().rss/1024**2,'process_cpu_percent':proc.cpu_percent(),
                  'temperature_c':float(temp.read_text())/1000 if temp.exists() else None,
                  'available_mib':psutil.virtual_memory().available/1024**2,'swap_used_bytes':psutil.swap_memory().used})
              except psutil.Error:break
          monitor=threading.Thread(target=sample,daemon=True);monitor.start();start=time.perf_counter();error=None
          try:worker.generate(prompts[length],24)
          except Exception as e:error=repr(e)
          finally:stop.set();monitor.join(timeout=1)
          row={'key':key,'threads':threads,'concurrent_hailo_db':active,'prompt_size':length,'repeat':i,'warmup_ms':warm_ms,
               'elapsed_ms':(time.perf_counter()-start)*1000,'metrics':worker.last_metrics,'error':error,'resources':samples,
               'load_calls':load_count[0],'load_errors':list(load_error),'output_limit':24,'model':str(a.model or art/'Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte')}
          rows.append(row)
          with raw.open('a') as f:f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
          print(key,round(row['elapsed_ms']),error,flush=True)
        finally:worker.close()
      finally:
        load_stop.set()
        if load_thread:load_thread.join(timeout=10)
    summary=[]
    for active in [False,True]:
     for threads in [1,2,3,4]:
      for length in prompts:
       selected=[r for r in rows if r['threads']==threads and r['concurrent_hailo_db']==active and r['prompt_size']==length]
       vals=sorted(r['elapsed_ms'] for r in selected if not r['error'])
       if not vals:continue
       q=lambda x:vals[min(len(vals)-1,int((len(vals)-1)*x))]
       summary.append(dict(threads=threads,active=active,prompt_size=length,n=len(vals),mean_ms=statistics.mean(vals),median_ms=statistics.median(vals),p95_ms=q(.95),p99_ms=q(.99),std_ms=statistics.pstdev(vals),failures=sum(bool(r['error']) for r in selected),concurrent_load_valid=not active or all(r['load_calls']>0 and not r['load_errors'] for r in selected)))
    (a.output/'summary.json').write_text(json.dumps({'rows':summary,'scope':f'24-token timing workload; each thread/load pair has {a.repeats} trials split across two prompt sizes. Small groups are pilot estimates, not stable tail-latency estimates. Not advisory quality. No CSI.','complete':True},indent=2))
    with (a.output/'summary.csv').open('w',newline='') as f:
      w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
if __name__=='__main__':main()
