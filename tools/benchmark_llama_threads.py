"""Measure native ExecuTorch thread options on fixed facts; no fabricated token rate."""
import json
from pathlib import Path
import sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.config import settings
from advisor_src.advisor import Advisor,NativeWorker,token_counter

def main():
    cfg=settings();artifacts=Path(cfg['llama_artifacts']);rows=[]
    output=ROOT/'validation/v4_llama_threads';output.mkdir(parents=True,exist_ok=True)
    for threads in [2,3,4]:
        worker=NativeWorker(cfg['llama_runtime'],artifacts/'Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte',artifacts/'tokenizer.model',threads)
        advisor=Advisor(worker,token_counter(artifacts/'tokenizer.model'))
        try:
            for index,defect in enumerate(['black_dot','broken','crack']):
                facts={'inspection_id':f'THREAD-{threads}-{index}','decision':'HOLD','severity':'major',
                    'defects':[{'type':defect,'count':1}],'capture_valid':True,'profile_validated':False}
                result=advisor.advise(facts)
                rows.append({'threads':threads,'warmup':index==0,'defect':defect,
                    'elapsed_ms':result['elapsed_ms'],'status':result['status']})
                (output/'report.json').write_text(json.dumps({'rows':rows,'scope':'Isolated fixed-fact generation; first request per worker is warmup. No prompt/model changes.'},indent=2))
                print(rows[-1],flush=True)
        finally:worker.close()

if __name__=='__main__':main()
