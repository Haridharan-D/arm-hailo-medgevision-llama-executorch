"""Prepare an unscored QA worksheet; no automated claim of human correctness."""
import csv,json,random
from pathlib import Path
root=Path(__file__).resolve().parents[1];dest=root.parent/'BlisterTrace_Deliverables/Hardening_20261122';dest.mkdir(parents=True,exist_ok=True)
sources={'A':root/'validation/hardening/quality_1b_baseline/cases.jsonl','B':root/'validation/hardening/20261122/quality_3b/cases.jsonl','C':root/'validation/hardening/20261122/quality_1b_adaptive_v1/cases.jsonl'}
rows=[]
for candidate,p in sources.items():
    if not p.exists():continue
    for line in p.read_text().splitlines():
        r=json.loads(line);rows.append(dict(candidate=candidate,case_id=r['case_id'],category=r['category'],evidence=json.dumps(r['evidence']),
           automated_status=r.get('result',{}).get('status','input rejected'),advisory=json.dumps(r.get('result',{}).get('advisory')),
           evidence_consistent='',explanation_correct='',recommendation_appropriate='',sop_reference_valid='',unsupported_claim='',unsafe_recommendation='',fallback_appropriate='',reviewer='',notes=''))
random.Random(42).shuffle(rows)
with (dest/'HUMAN_QA_REVIEW.csv').open('w',newline='',encoding='utf8') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
(dest/'HUMAN_REVIEW_KEY.json').write_text(json.dumps({'A':'Existing1B baseline prompt','B':'3B SpinQuant baseline prompt','C':'1B adaptive-v1 prompt','human_review_complete':False,'instruction':'Reviewers must consult approved SOPs before operational endorsement; blank scores must not be reported as successful human evaluation.'},indent=2))
print('Unscored human-review worksheet saved:',len(rows),'rows')
