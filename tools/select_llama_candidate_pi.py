"""Select only a fully completed, strictly revalidated prompt candidate."""
import json,sys,statistics,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from advisor_src.advisor import Advisor,token_counter
out=root/'validation/hardening/20261122';candidate=out/'quality_1b_adaptive_v1'
summary=json.loads((candidate/'summary.json').read_text());assert summary['cases']==50 and summary['decision_preserved']
rows=[json.loads(l) for l in (candidate/'cases.jsonl').read_text().splitlines()]
class Replay:
    def __init__(self,text):self.text=text
    def generate(self,*args):return self.text
counter=token_counter(Path.home()/'BlisterTrace/Llama_ExecuTorch/artifacts/tokenizer.model')
rechecked=[]
for r in rows:
    if r['expected']!='bounded_advice':continue
    raw=r.get('diagnostics',{}).get('raw_response')
    a=Advisor(Replay(raw or ''),counter,max_new_tokens=128,prompt_mode='adaptive-v1',prompt_budget=1536)
    result=a.advise(r['evidence']);rechecked.append({'case_id':r['case_id'],'status':result['status'],'fallback':a.last_diagnostics.get('fallback_detail')})
accepted=sum(r['status']=='llama_validated' for r in rechecked)
assert accepted>26
comparisons={}
for name,path,mode,limit in [('1b_baseline',Path.home()/'BlisterTrace/BlisterTrace_App/validation/hardening/quality_1b_baseline/cases.jsonl','baseline',192),
                             ('3b_baseline',out/'quality_3b/cases.jsonl','baseline',192)]:
    checked=[]
    for row in [json.loads(l) for l in path.read_text().splitlines()]:
        if row['expected']!='bounded_advice':continue
        a=Advisor(Replay(row.get('diagnostics',{}).get('raw_response') or ''),counter,max_new_tokens=limit,prompt_mode=mode,prompt_budget=1536)
        value=a.advise(row['evidence']);checked.append(dict(case_id=row['case_id'],status=value['status'],reason=a.last_diagnostics.get('fallback_detail')))
    comparisons[name]={'accepted':sum(r['status']=='llama_validated' for r in checked),'cases':checked}
report={'primary':'Existing Llama3.2 1B Instruct SpinQuant INT4 EO8, adaptive-v1 prompt',
 'production_config':{'llama_prompt_mode':'adaptive-v1','llama_output_tokens':128,'llama_prompt_budget':1536,'llama_threads':3},
 'frozen_model_unchanged':True,'automated_revalidation':rechecked,'human_review_complete':False,
 'baseline_accepted':comparisons['1b_baseline']['accepted'],'selected_accepted':accepted,'observed_experiment_guard_accepted':summary['validated'],'bounded_cases':39,'rejected_invalid_inputs':11,
 'other_candidate_final_guards':comparisons,
 'reason':'Retain the1B artifact and persistent ExecuTorch Arm runtime. The relevant-example prompt improved automated guard acceptance from26/39 to'+str(accepted)+'/39 while reducing observed advisory latency. Keep3B as an evaluated quality challenger because its~39s warm generation has a substantial latency cost and human semantic review remains unavailable. Original prompt/source/binary stay recoverable. These counts are not pharmaceutical or human-judged accuracy.',
 'revalidation_scope':'Replay of the actually observed candidate raw text through the final conservative guards; no fabricated new generation timings.'}
(out/'model_selection.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='automated_revalidation'},indent=2))
