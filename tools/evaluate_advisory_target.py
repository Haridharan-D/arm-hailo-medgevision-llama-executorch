"""Resume-safe 36-case evaluation of the exact adviser shipped in the application."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from advisor_src.advisor import Advisor,NativeWorker,KNOWN,token_counter,ADVISOR_VERSION

def cases():
    rows=[]
    for name in sorted(KNOWN):
        for count in (1,2,3,4):
            rows.append({'inspection_id':f'EVAL-{len(rows)+1:03}','decision':'HOLD','severity':'major',
                'defects':[{'type':name,'count':count}],'capture_valid':True,'profile_validated':False})
    for index in range(4):
        rows.append({'inspection_id':f'EVAL-{len(rows)+1:03}','decision':'REVIEW','severity':'unknown',
            'defects':[{'type':'unknown_anomaly','count':1}] if index%2 else [],
            'capture_valid':bool(index%2),'profile_validated':False})
    for _ in range(4):
        rows.append({'inspection_id':f'EVAL-{len(rows)+1:03}','decision':'PASS','severity':'none',
            'defects':[],'capture_valid':True,'profile_validated':True})
    return rows

def temperature():
    try:return float(Path('/sys/class/thermal/thermal_zone0/temp').read_text())/1000
    except OSError:return None

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'validation/20261120_advisory_v3')
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    from app.config import settings
    cfg=settings();artifacts=Path(cfg['llama_artifacts']);model=artifacts/'Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte'
    tokenizer=artifacts/'tokenizer.model';runtime=Path(cfg['llama_runtime'])
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    identity={'advisor_version':ADVISOR_VERSION,'advisor_sha256':sha(ROOT/'advisor_src/advisor.py'),
        'sop_sha256':sha(ROOT/'advisor_src/sop.json'),'model_sha256':sha(model),'runtime_sha256':sha(runtime),
        'threads':cfg['llama_threads']}
    ipath=args.output/'identity.json'
    if ipath.exists() and json.loads(ipath.read_text())!=identity:raise ValueError('Changed artifacts: use a new output directory')
    ipath.write_text(json.dumps(identity,indent=2))
    path=args.output/'cases.json';results=json.loads(path.read_text()) if path.exists() else []
    completed={r['inspection']['inspection_id'] for r in results}
    worker=NativeWorker(runtime,model,tokenizer,cfg['llama_threads'])
    advisor=Advisor(worker,token_counter(tokenizer));started=time.monotonic();error=None
    try:
        for case in cases():
            if case['inspection_id'] in completed:continue
            temp=temperature()
            if temp is not None and temp>=80:
                deadline=time.monotonic()+120
                print('Cooling pause at '+str(temp)+' C',flush=True)
                while temperature()>=70 and time.monotonic()<deadline:time.sleep(2)
                if temperature()>=80:raise RuntimeError('Thermal pause: saved cases can be resumed with the same command')
            result=advisor.advise(case)
            result.update(inspection=case,temperature_c=temperature(),
                diagnostics=advisor.last_diagnostics,
                human_review={'no_invented_facts':None,'action_appropriate':None,'notes':''})
            results.append(result)
            temp_path=args.output/'cases.tmp';temp_path.write_text(json.dumps(results,indent=2));temp_path.replace(path)
            print(case['inspection_id'],result['status'],result['elapsed_ms'],'temp',result['temperature_c'],flush=True)
    except Exception as e:error=str(e);print('EVALUATION STOPPED '+error,flush=True)
    finally:worker.close()
    valid=sum(r['status']=='llama_validated' for r in results)
    summary={**identity,'completed_utc':datetime.now(timezone.utc).isoformat(),
        'cases':len(results),'expected_cases':36,'complete':len(results)==36,'error':error,
        'validated_llama_responses':valid,'fallbacks':len(results)-valid,
        'validated_fraction':valid/len(results) if results else None,
        'elapsed_this_process_seconds':round(time.monotonic()-started,3),
        'decision_preserved':all(r['decision']==r['inspection']['decision'] for r in results),
        'human_semantic_review_complete':False,
        'scope':'Synthetic advisory development fixtures, not image accuracy or QA release evidence. Automatic acceptance is schema/clause/content guard acceptance.'}
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)
    return 0 if summary['complete'] and not error else 1

if __name__=='__main__':raise SystemExit(main())
