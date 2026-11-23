import pytest
from advisor_src.advisor import validate_proposal
import json
@pytest.mark.parametrize('claim',['chemical contamination','microbial contamination','bacterial growth','toxicity','dosage'])
def test_generated_visual_advice_cannot_establish_chemical_or_microbiology(claim):
    clauses=[{'id':'BT-01','actions':['ISOLATE_AND_QA_REVIEW']}]
    text=json.dumps(dict(clause_id='BT-01',action_id='ISOLATE_AND_QA_REVIEW',operator_message='Finding establishes '+claim,qa_note='Draft: QA review pending.'))
    with pytest.raises(ValueError):validate_proposal(text,clauses)
