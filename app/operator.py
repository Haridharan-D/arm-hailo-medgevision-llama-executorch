"""Bounded operator questions grounded in an immutable inspection and its SOP."""
import re
import json
from advisor_src.advisor import ROOT, retrieve

INTENTS={'next_action','rectify','explain','qa_note','evidence'}


def answer(record, question='', intent=None):
    if not isinstance(question,str) or len(question)>500:
        raise ValueError('Use a question of up to 500 characters')
    if intent is not None and intent not in INTENTS:
        raise ValueError('Unsupported inspection question')
    if intent is None:
        value=question.strip().lower()
        if not value:raise ValueError('Enter a question about this inspection')
        if re.search(r'\b(release|safe to|dosage|sterile|prescrib|root cause|sql|delete|ignore.*rule)\b',value):
            intent='unsupported'
        elif re.search(r'\b(rectif|fix|rework|repair|correct)',value):intent='rectify'
        elif re.search(r'\b(why|explain|detected|defect|result|pass|hold|review)\b',value):intent='explain'
        elif re.search(r'\b(qa|deviation|draft|note)\b',value):intent='qa_note'
        elif re.search(r'\b(evidence|record|log|save|image)\b',value):intent='evidence'
        elif re.search(r'\b(action|next|do|handle|recommend|suggest|suggestion|steps)\b',value):intent='next_action'
        else:intent='unsupported'
    facts={k:record[k] for k in ('inspection_id','decision','severity','defects','capture_valid','profile_validated')}
    sop=json.loads((ROOT/'sop.json').read_text(encoding='utf8'));clauses=retrieve(facts,sop)
    advice=record.get('advice');valid=bool(advice and advice.get('status')=='llama_validated')
    clause=clauses[0]
    if advice:
        clause=next((c for c in clauses if c['id']==advice['advisory']['clause_id']),clause)
    observations=', '.join(str(d['count'])+' '+d['type'].replace('_',' ') for d in facts['defects']) or 'no configured defect observations'
    if intent=='unsupported':
        reply='I can explain this inspection, show its recorded next action, draft QA note or evidence. Product release, drug safety, repair instructions and manufacturing root cause require qualified human review.'
    elif intent=='explain':
        reply=f"The vision/rule engine recorded {facts['decision']} with {observations}. "
        if not facts['capture_valid']:reply+='Capture quality also requires review. '
        if not facts['profile_validated']:reply+='The camera/pack profile is unvalidated; no detections therefore remains REVIEW. '
        reply+='Llama cannot change that recorded decision.'
    elif intent=='rectify':
        reply=clause['text']+' This is a handling/reinspection action; do not repair or release the pack based on model output.'
    elif intent=='qa_note':
        reply=(advice['advisory']['qa_note'] if advice else f"Draft: {observations}. {facts['decision']} recorded. QA review pending.")
    elif intent=='evidence':
        reply='The original image, annotated image, defect coordinates, model fingerprint, disposition and advisory are linked to inspection '+facts['inspection_id']+'. Open Evidence or export the inspection record. QA comments append a review event and preserve the decision.'
    else:
        reply=advice['advisory']['operator_message'] if advice else clause['text']
    evidence=[f"Detector/rules: {facts['decision']}; severity: {facts['severity']}.",
        'Observed contents: '+observations+'.',
        'Capture quality: '+('passed configured image checks.' if facts['capture_valid'] else 'requires recapture/review.'),
        'Camera/product profile: '+('validated in the recorded facts.' if facts['profile_validated'] else 'unvalidated; absence of detections does not establish PASS.')]
    anomaly=record.get('anomaly')
    if anomaly:
        evidence.append(f"{anomaly['profile']} anomaly score {anomaly['score']:.4f}; saved threshold {anomaly['threshold']:.4f}. This score is not a probability.")
    steps=[clause['text'],
        'Preserve the original and annotated image with this inspection ID, model fingerprint and SOP clause.',
        'Ask QA to confirm the expected product/pack recipe and review the evidence before any disposition or rework decision.']
    if not facts['capture_valid'] or not facts['profile_validated']:
        steps.insert(1,'Check camera focus, fixed lighting and pack positioning before recapturing; a clearer image does not itself validate the product profile.')
    sections=[] if intent=='unsupported' else [
        {'title':'Suggested workflow','items':steps},
        {'title':'Recorded evidence','items':evidence},
        {'title':'QA handoff','items':[(advice['advisory']['qa_note'] if advice else 'No generated draft is recorded yet; preserve evidence and request QA review.'),
            'Append a reviewer note. The detector decision remains preserved; a draft is not product-release approval.']}]
    return {'inspection_id':facts['inspection_id'],'intent':intent,'reply':reply,'sections':sections,
            'decision':facts['decision'],'clause_id':clause['id'],'sop_document':sop['document_id'],
            'source':'recorded_llama_advisory' if valid and intent in {'next_action','qa_note'} else 'inspection_rules_and_sop',
            'advisory_status':advice['status'] if advice else 'pending',
            'scope':'Constrained intents over this inspection and its existing advisory; no new free-form Llama generation or repair diagnosis.'}
