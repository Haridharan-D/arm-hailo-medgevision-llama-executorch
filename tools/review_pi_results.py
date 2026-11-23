"""Engineering review flags on original target records; not a QA sign-off."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from advisor_src.advisor import Advisor,token_counter
class RecordedResponse:
    def __init__(self,value):self.value=value
    def generate(self,*args):return json.dumps(self.value)
def main():
    source=ROOT.parent/'Llama_ExecuTorch/pi_validation/pi_advisory_v2/cases.json'
    rows=json.loads(source.read_text());count=token_counter(ROOT/'llama/artifacts/tokenizer.model')
    checks=[]
    for row in rows:
        flags=[]
        if row['status']=='fallback':flags.append('Original generation was rejected; raw generation not retained by old evaluator')
        else:
            result=Advisor(RecordedResponse(row['advisory']),count).advise(row['inspection'])
            if result['status']=='fallback':flags.append('v3 rejects previously accepted advisory: inspect wording')
        if row['inspection_id']=='EVAL-008':flags.append('Draft omits specific broken label; refer to structured observations')
        checks.append({'inspection_id':row['inspection_id'],'original_status':row['status'],'flags':flags,
                       'qa_signoff':False})
    report={'source':str(source),'original_cases':36,'original_automatic_acceptances':33,
            'review_type':'Agent engineering review; not a human pharmaceutical QA sign-off',
            'new_guard_rejections':[r['inspection_id'] for r in checks if any('v3 rejects' in s for s in r['flags'])],
            'original_fallback_reasons_unavailable_beyond_type':True,'cases':checks}
    (ROOT/'validation/pi_advice_engineering_review.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
if __name__=='__main__':main()
