"""CSI-free isolated challenger probe; never edits production config/artifacts."""
import json,sys,time,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from advisor_src.advisor import NativeWorker,Advisor,token_counter
def main():
    out=ROOT/'validation/hardening/20261122/challenger';out.mkdir(parents=True,exist_ok=True)
    base=Path.home()/'BlisterTrace/Llama_ExecuTorch/artifacts'
    candidate=Path.home()/'BlisterTrace/Llama_Candidates/3b_mediatek_2048'
    facts=dict(inspection_id='CHALLENGER-001',decision='HOLD',severity='major',defects=[dict(type='crack',count=1)],capture_valid=True,profile_validated=False)
    for name,model,tok,mode,tokens in [('1b_compact',base/'Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte',base/'tokenizer.model','compact-v1',128),
                                     ('3b_baseline',candidate/'llama3_2-2048-spin.pte',candidate/'tokenizer.bin','baseline',192)]:
        w=NativeWorker(ROOT/'native/bin/aarch64/blistertrace_instrumented',model,tok,3,timeout=240)
        row=dict(candidate=name,model=str(model),prompt_mode=mode)
        try:
            a=Advisor(w,token_counter(tok),max_new_tokens=tokens,prompt_mode=mode)
            row['result']=a.advise(facts);row['diagnostics']=a.last_diagnostics
        except Exception as e:row.update(error=repr(e),logs=list(w.logs))
        finally:w.close()
        (out/(name+'.json')).write_text(json.dumps(row,indent=2));print(json.dumps(row),flush=True)
if __name__=='__main__':main()
