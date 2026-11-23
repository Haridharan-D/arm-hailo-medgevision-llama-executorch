"""Offline SOP-grounded advice through a persistent ExecuTorch native worker.

Vision/rules supply the immutable inspection decision. The LLM has no authority
to change it. Generation is prompted for JSON, then schema/grounding validated;
this is NOT token-level grammar-constrained decoding. Failures are explicit.
"""
from collections import deque
from pathlib import Path
import argparse
import base64
import hashlib
import json
import queue
import re
import subprocess
import sys
import threading
import time
import math
import os

ROOT = Path(__file__).resolve().parent
ADVISOR_VERSION = '2026-11-22-json-v4'
KNOWN = {'black_dot','broken','color_mismatch','crack','dual_cap','empty','foreign_particle'}
SPECIAL = {'<|begin_of_text|>':128000,'<|end_of_text|>':128001,
           '<|start_header_id|>':128006,'<|end_header_id|>':128007,'<|eot_id|>':128009}
PATTERN = r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?+\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]++[\r\n]*+|\s*[\r\n]|\s+(?!\S)|\s+"


def stable_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate_inspection(value):
    required = {'inspection_id','decision','severity','defects','capture_valid','profile_validated'}
    if not isinstance(value,dict) or not required<=set(value) or set(value)-required-{'context'}:
        raise ValueError('Inspection must match the documented input schema')
    if not isinstance(value['inspection_id'],str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',value['inspection_id']):
        raise ValueError('Invalid inspection ID')
    if value['decision'] not in {'HOLD','REVIEW','PASS'} or value['severity'] not in {'major','minor','none','unknown'}:
        raise ValueError('Invalid upstream decision/severity')
    if type(value['capture_valid']) is not bool or type(value['profile_validated']) is not bool:
        raise ValueError('Capture and profile flags must be boolean')
    if not isinstance(value['defects'],list) or len(value['defects']) > 8:
        raise ValueError('Expected a bounded list of defect observations')
    seen=set()
    for defect in value['defects']:
        if not isinstance(defect,dict) or set(defect) != {'type','count'}:
            raise ValueError('Each defect requires type and count')
        if defect['type'] not in KNOWN|{'unknown_anomaly'} or defect['type'] in seen:
            raise ValueError('Unsupported/duplicate defect name')
        if type(defect['count']) is not int or not 1 <= defect['count'] <= 1000000:
            raise ValueError('Invalid observation count')
        seen.add(defect['type'])
    context=value.get('context',{})
    if not isinstance(context,dict) or set(context)-{'batch_id','product_type','observations','anomaly_score','batch_counts','warnings'}:
        raise ValueError('Unsupported advisory context')
    if 'batch_id' in context and (not isinstance(context['batch_id'],str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',context['batch_id'])):raise ValueError('Invalid batch ID')
    if context.get('product_type','unspecified') not in {'tablet','capsule','blister','unspecified'}:raise ValueError('Invalid product category')
    observations=context.get('observations',[])
    if not isinstance(observations,list) or len(observations)>8:raise ValueError('Advisory observations must be bounded')
    for obs in observations:
        if not isinstance(obs,dict) or set(obs)!={'type','confidence','box_xyxy'} or obs['type'] not in seen:raise ValueError('Observation/context mismatch')
        if type(obs['confidence']) not in {int,float} or not math.isfinite(obs['confidence']) or not 0<=obs['confidence']<=1:raise ValueError('Invalid confidence')
        if not isinstance(obs['box_xyxy'],list) or len(obs['box_xyxy'])!=4 or not all(type(x) in {int,float} and math.isfinite(x) and 0<=x<=100000 for x in obs['box_xyxy']):raise ValueError('Invalid bounding box')
    score=context.get('anomaly_score')
    if score is not None and (type(score) not in {int,float} or not math.isfinite(score)):raise ValueError('Invalid anomaly score')
    counts=context.get('batch_counts',{})
    if not isinstance(counts,dict) or set(counts)-{'total','HOLD','PASS','REVIEW'} or not all(type(x) is int and 0<=x<=1000000000 for x in counts.values()):raise ValueError('Invalid batch counts')
    warnings=context.get('warnings',[])
    if not isinstance(warnings,list) or len(warnings)>3 or not set(warnings)<={'capture_invalid','profile_unvalidated','anomaly_flag'}:raise ValueError('Invalid evidence warnings')
    if value['decision']=='PASS' and (value['defects'] or not value['capture_valid'] or not value['profile_validated']):
        raise ValueError('Upstream PASS conflicts with inspection prerequisites')
    if seen & KNOWN and value['decision']!='HOLD':
        raise ValueError('Known-defect observations require the upstream HOLD decision')
    if value['decision']=='HOLD' and not seen & KNOWN:
        raise ValueError('This adapter requires known defect evidence for HOLD')
    return json.loads(json.dumps(value))


def retrieve(facts,sop):
    tags={d['type'] for d in facts['defects']}
    tags.add(facts['decision'].lower())
    if not facts['capture_valid']: tags.add('capture_invalid')
    candidates=[c for c in sop['clauses'] if facts['decision'] in c['decisions']]
    ranked=sorted(candidates,key=lambda c:(-len(tags & set(c['tags'])),c['id']))
    selected=[c for c in ranked if tags & set(c['tags'])][:2]
    if not selected: raise ValueError('No applicable SOP clause')
    return selected


def prompt_for(facts,clauses,sop=None):
    sop=sop or json.loads((ROOT/'sop.json').read_text(encoding='utf8'))
    system=('You are a manufacturing inspection assistant. Convert the supplied observations and SOP into '
            'a short JSON advisory. The upstream decision is fixed. Select clause_id and action_id '
            'from allowed_sop only. Return exactly four string keys: clause_id, action_id, '
            'operator_message, qa_note. Write operator_message under 120 characters. '
            'Write qa_note under 160 characters: observation, decision, next action, QA review pending. '
            'Use only the supplied facts. Keep counts in the inspection record; omit numbers from prose. JSON only.')
    def message(role,value):
        return '<|start_header_id|>'+role+'<|end_header_id|>\n\n'+value+'<|eot_id|>'
    def payload(record,selected):
        # Keep audit identifiers outside the language task: a small model can
        # otherwise confuse inspection_id with clause_id.
        return json.dumps({'decision':record['decision'],'observations':record['defects'],
                           'capture_valid':record['capture_valid'],
                           **({'context':record['context']} if record.get('context') else {}),
                           'allowed_sop':[{'clause_id':c['id'],'action_ids':c['actions'],
                                           'instruction':c['text']} for c in selected]},separators=(',',':'))
    example=dict(facts);example.pop('context',None)
    sample=dict(example,decision='HOLD',defects=[{'type':'black_dot','count':2}])
    reply={'clause_id':'BT-01','action_id':'ISOLATE_AND_QA_REVIEW',
           'operator_message':'Keep the pack on HOLD. Isolate it and preserve evidence for QA review.',
           'qa_note':'Draft: black_dot observed. HOLD recorded. Isolate the pack and preserve evidence. QA review pending.'}
    review=dict(example,decision='REVIEW',defects=[],capture_valid=False)
    review_reply={'clause_id':'BT-03','action_id':'RECAPTURE_AND_REVIEW',
                  'operator_message':'Keep the pack pending REVIEW. Check lighting and alignment, then recapture for human review.',
                  'qa_note':'Draft: invalid capture. REVIEW recorded. Check capture conditions and recapture. QA review pending.'}
    passed=dict(example,decision='PASS',defects=[],capture_valid=True,profile_validated=True)
    pass_reply={'clause_id':'BT-04','action_id':'RECORD_INSPECTION',
                'operator_message':'Record the existing rule-engine PASS and preserve inspection evidence.',
                'qa_note':'Draft: no defects reported by inspection. Existing PASS recorded. Preserve evidence. QA review pending.'}
    return ('<|begin_of_text|>'+message('system',system)+
            message('user',payload(sample,retrieve(sample,sop)))+message('assistant',json.dumps(reply))+
            message('user',payload(review,retrieve(review,sop)))+message('assistant',json.dumps(review_reply))+
            message('user',payload(passed,retrieve(passed,sop)))+message('assistant',json.dumps(pass_reply))+
            message('user',payload(facts,clauses))+
            '<|start_header_id|>assistant<|end_header_id|>\n\n')


def token_counter(path):
    import tiktoken
    # Parse the local, checksum-verified BPE file directly. tiktoken.load's
    # generic file loader otherwise pulls in blobfile for a local path.
    ranks={base64.b64decode(token,validate=True):int(rank)
           for token,rank in (line.split() for line in Path(path).read_bytes().splitlines() if line)}
    encoder=tiktoken.Encoding(name='blistertrace_llama32',pat_str=PATTERN,
                              mergeable_ranks=ranks,special_tokens=SPECIAL)
    return lambda text:len(encoder.encode(text,allowed_special=set(SPECIAL)))

def compact_prompt_for(facts,clauses):
    """Experimental shorter template, selected only after measured evaluation."""
    instruction=('You explain visual inspection evidence. The QA decision is immutable. '
        'Use only evidence and allowed SOP. Do not infer causes, drug identity or safety. '
        'JSON only: clause_id, action_id, operator_message, qa_note (all strings). '
        'Choose clause_id/action_id from allowed_sop. operator_message: short operator action. '
        'qa_note: short DRAFT observation and action, QA review pending. Omit numbers. '
        'Do not introduce other defect names. Advice is informational.')
    evidence={'decision':facts['decision'],'observations':facts['defects'],'capture_valid':facts['capture_valid'],
        'allowed_sop':[dict(clause_id=c['id'],action_ids=c['actions'],instruction=c['text']) for c in clauses]}
    if facts.get('context'):evidence['context']=facts['context']
    return '<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n'+instruction+'<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n'+json.dumps(evidence,separators=(',',':'))+'<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n'

def adaptive_prompt_for(facts,clauses):
    """One relevant schema demonstration; no input labels or decisions invented."""
    clause=clauses[0]
    instruction=('You are a visual inspection assistant. The upstream QA decision cannot change. '
        'Return JSON with exactly four string keys: clause_id, action_id, operator_message, qa_note. '
        'Choose clause/action from allowed_sop. Use only supplied observations. '
        'No safety, drug-identity, contamination or root-cause claims. '
        'operator_message under120 characters; qa_note under160 characters, marked Draft and QA review pending. '
        'Omit numbers and avoid mentioning unobserved defects. The example demonstrates the schema; answer the final evidence.')
    sample={'decision':facts['decision'],'observations':facts['defects'][:1],'capture_valid':facts['capture_valid'],
            'allowed_sop':[{'clause_id':clause['id'],'action_ids':clause['actions'],'instruction':clause['text']}]}
    action={'HOLD':'Keep the pack on HOLD. Preserve evidence and request QA review.','REVIEW':'Keep the pack pending REVIEW. Preserve evidence and request human review.','PASS':'Record the existing rule-engine PASS and preserve inspection evidence.'}[facts['decision']]
    example={'clause_id':clause['id'],'action_id':clause['actions'][0],'operator_message':action,
             'qa_note':'Draft: observation and existing decision recorded. Preserve evidence. QA review pending.'}
    final={'decision':facts['decision'],'observations':facts['defects'],'capture_valid':facts['capture_valid'],
           'allowed_sop':[{'clause_id':c['id'],'action_ids':c['actions'],'instruction':c['text']} for c in clauses]}
    if facts.get('context'):final['context']=facts['context']
    def message(role,value):return '<|start_header_id|>'+role+'<|end_header_id|>\n\n'+value+'<|eot_id|>'
    return '<|begin_of_text|>'+message('system',instruction)+message('user',json.dumps(sample,separators=(',',':')))+message('assistant',json.dumps(example,separators=(',',':')))+message('user',json.dumps(final,separators=(',',':')))+'<|start_header_id|>assistant<|end_header_id|>\n\n'


def validate_proposal(raw,clauses):
    # Permit only a single JSON object and optional model stop token; no prose,
    # duplicate keys, NaN, additional properties or changed decision fields.
    raw=raw.strip()
    for stop in ('<|eot_id|>','<|end_of_text|>'):
        raw=raw.removesuffix(stop).strip()
    def pairs(items):
        result={}
        for k,v in items:
            if k in result: raise ValueError('Duplicate JSON key')
            result[k]=v
        return result
    value=json.loads(raw,object_pairs_hook=pairs,
                     parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Non-finite JSON')))
    keys={'clause_id','action_id','operator_message','qa_note'}
    if not isinstance(value,dict) or set(value)!=keys or not all(isinstance(v,str) for v in value.values()):
        raise ValueError('Advisory JSON schema mismatch')
    clause=next((c for c in clauses if c['id']==value['clause_id']),None)
    if clause is None or value['action_id'] not in clause['actions']:
        raise ValueError('Ungrounded clause/action')
    for name,limit in [('operator_message',180),('qa_note',240)]:
        if not 1<=len(value[name])<=limit or any(ord(c)<32 for c in value[name]):
            raise ValueError('Invalid advisory text')
    # Conservative rejection, not a semantic proof of no hallucination.
    text=' '.join(value[k] for k in ('operator_message','qa_note')).lower()
    forbidden=r'\b(release(?:d)?|safe|sterile|approved|guarantee(?:d)?|root cause is|caused by|contaminat(?:ed|ion)|microbial|bacterial|chemical|toxic(?:ity)?|dosage)\b'
    if re.search(forbidden,text): raise ValueError('Unsupported advisory claim')
    return value


class NativeWorker:
    def __init__(self,binary,model,tokenizer,threads=2,timeout=180):
        self.command=[str(Path(binary).resolve()),str(Path(model).resolve()),str(Path(tokenizer).resolve()),str(threads)]
        self.timeout=timeout
        self.process=None
        self.events=queue.Queue()
        self.logs=deque(maxlen=60)
        self.lock=threading.Lock()
        self.close_lock=threading.Lock()
        self.last_metrics={}

    def _reader(self,process,events):
        try:
            while True:
                line=process.stdout.readline(16384)
                if not line: raise RuntimeError('Native worker exited')
                if not line.startswith(b'BT1 '): continue
                _,status,length=line.decode('ascii').split()
                length=int(length)
                if length<0 or length>8192: raise RuntimeError('Invalid worker frame size')
                content=bytearray()
                while len(content)<length:
                    block=process.stdout.read(length-len(content))
                    if not block: raise RuntimeError('Truncated worker frame')
                    content.extend(block)
                events.put((status,content.decode('utf8')))
        except Exception as error:
            events.put(('ERROR',str(error)))

    def _stderr(self,process):
        try:
            for line in iter(process.stderr.readline,b''):
                self.logs.append(line.decode('utf8',errors='replace').rstrip())
        except (OSError,ValueError):
            pass  # Pipes may close when a timed-out worker is terminated.

    def _event(self,events):
        try:return events.get(timeout=self.timeout)
        except queue.Empty:raise TimeoutError('ExecuTorch worker timed out') from None

    def _start(self):
        self.events=queue.Queue()
        env=dict(os.environ)
        directory=str(Path(self.command[0]).resolve().parent)
        if os.name!='nt':env['LD_LIBRARY_PATH']=directory+os.pathsep+env.get('LD_LIBRARY_PATH','')
        self.process=subprocess.Popen(self.command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,bufsize=0,env=env,
                                      creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        threading.Thread(target=self._reader,args=(self.process,self.events),daemon=True).start()
        threading.Thread(target=self._stderr,args=(self.process,),daemon=True).start()
        status,_=self._event(self.events)
        if status!='READY':raise RuntimeError('ExecuTorch failed to load model')

    def generate(self,prompt,max_new_tokens=192):
        if not self.lock.acquire(blocking=False): raise RuntimeError('Advisor is busy')
        try:
            self.last_metrics={}
            if self.process is None or self.process.poll() is not None:self._start()
            raw=prompt.encode('utf8')
            if not 1<=len(raw)<=32768 or not 1<=max_new_tokens<=256:raise ValueError('Invalid generation request')
            self.process.stdin.write(f'BT1 {len(raw)} {max_new_tokens}\n'.encode()+raw)
            self.process.stdin.flush()
            status,content=self._event(self.events)
            while status=='STATS':
                self.last_metrics=json.loads(content)
                status,content=self._event(self.events)
            if status!='OK':raise RuntimeError(content)
            return content
        except Exception:
            self.close()
            raise
        finally:self.lock.release()

    def close(self):
        # Shutdown can race with a generation failure closing the same worker.
        # Serialize cleanup and keep a local handle throughout; never dereference
        # self.process after another thread has cleared it.
        with self.close_lock:
            process=self.process
            if process is None:return
            self.process=None
            if process.poll() is None:process.kill()
            process.wait(timeout=10)
            for stream in (process.stdin,process.stdout,process.stderr):
                if stream is not None:stream.close()


class Advisor:
    def __init__(self,worker,count_tokens,sop=None,max_new_tokens=192,prompt_mode='baseline',prompt_budget=768):
        self.worker=worker
        self.count_tokens=count_tokens
        self.sop=sop or json.loads((ROOT/'sop.json').read_text(encoding='utf8'))
        self.last_diagnostics={}
        self.max_new_tokens=max_new_tokens
        self.prompt_mode=prompt_mode
        self.prompt_budget=prompt_budget

    def advise(self,inspection):
        facts=validate_inspection(inspection)
        identity=stable_hash(facts)
        clauses=retrieve(facts,self.sop)
        start=time.monotonic()
        compact=self.prompt_mode in {'compact-v1','compact-v2'}
        prompt=compact_prompt_for(facts,clauses) if compact else prompt_for(facts,clauses,self.sop)
        if self.prompt_mode=='adaptive-v1':prompt=adaptive_prompt_for(facts,clauses)
        if self.prompt_mode=='compact-v2':prompt+='{'  # Fixed JSON prefix, still fully validated after completion.
        prompt_tokens=self.count_tokens(prompt)
        generated=None
        reason=None
        raw=None
        try:
            if prompt_tokens>self.prompt_budget:raise ValueError('Prompt exceeds the configured token budget')
            raw=self.worker.generate(prompt,self.max_new_tokens)
            if self.prompt_mode=='compact-v2':raw='{'+raw
            generated=validate_proposal(raw,clauses)
            text=' '.join([generated['operator_message'],generated['qa_note']]).lower()
            forbidden_decisions={'HOLD':r'\bpass(?:ed)?\b',
                                 'REVIEW':r'\b(?:pass(?:ed)?|hold)\b',
                                 'PASS':r'\b(?:hold|reject(?:ed)?)\b'}
            if re.search(forbidden_decisions[facts['decision']],text):
                raise ValueError('Advisory text conflicts with the upstream decision')
            if facts['decision'] in {'HOLD','REVIEW'} and re.search(
                    r'\bno\s+(?:further\s+)?action\s+(?:is\s+)?(?:needed|required|necessary)\b|\b(?:do nothing|nothing to do)\b',text):
                raise ValueError('Advisory incorrectly dismisses the required SOP action')
            if facts['capture_valid'] and re.search(
                    r'\b(?:invalid capture|image quality issues?|poor image quality|blurry image|out of focus)\b',text):
                raise ValueError('Advisory invents a capture-quality issue')
            numeric_claims=set(re.findall(r'(?<![\w-])\d+(?![\w-])',' '.join([generated['operator_message'],generated['qa_note']])))
            allowed_counts={str(d['count']) for d in facts['defects']}
            if not numeric_claims<=allowed_counts:raise ValueError('Unsupported numeric claim')
            observed={d['type'] for d in facts['defects']}
            if not observed and re.search(
                    r'\b(?:anomal(?:y|ies)[ _-](?:detected|observed)|unknown[ _-]anomaly|defect[ _-](?:detected|observed))\b',text):
                raise ValueError('Advisory asserts an anomaly without an observation')
            for kind in KNOWN|{'unknown_anomaly'}:
                pattern=r'\b'+re.escape(kind).replace('_',r'[_ -]')+r'(?:s|ed)?\b'
                if kind not in observed and re.search(pattern,text):
                    raise ValueError('Advisory invents an unobserved defect type')
        except Exception as error:
            reason=type(error).__name__
            # Never return a candidate rejected by a later semantic guard.
            generated=None
            detail=str(error)
        self.last_diagnostics={'advisor_version':ADVISOR_VERSION,
                               'raw_response':raw,'generation_returned':raw is not None,
                               'fallback_reason':reason,'fallback_detail':detail if reason else None,
                               'worker_logs':list(getattr(self.worker,'logs',[]))}
        if generated is None:
            clause=clauses[0]
            generated={'clause_id':clause['id'],'action_id':clause['actions'][0],
                       'operator_message':{'HOLD':'Keep the pack on HOLD. Preserve the evidence and request QA review.',
                                           'REVIEW':'Keep the pack pending REVIEW. Check capture conditions and request human review.',
                                           'PASS':'Record the existing rule-engine PASS and preserve its evidence.'}[facts['decision']],
                       'qa_note':'Draft: '+facts['decision']+' recorded. Preserve evidence and obtain QA review.'}
        structured={'inspection_id':facts['inspection_id'],'summary':generated['operator_message'],
            'observed_evidence':facts['defects'],'defect_explanation':'Visual observations only; no chemical, microbial or root-cause conclusion.',
            'recommended_actions':[generated['operator_message']],'escalation_required':facts['decision']!='PASS',
            'sop_references':[{'document_id':self.sop['document_id'],'revision':self.sop['revision'],'section':generated['clause_id'],
                'approval_status':self.sop.get('approval_status','Approval unavailable')}],
            'limitations':['General technical demonstration; consult an approved SOP.','Authorized QA retains disposition authority.'],
            'generation_status':'fallback' if reason else 'llama_validated'}
        return {'advisor_version':ADVISOR_VERSION,'prompt_mode':self.prompt_mode,'structured_advisory':structured,
                'inspection_id':facts['inspection_id'],'decision':facts['decision'],'severity':facts['severity'],
                'facts_sha256':identity,'advisory':generated,'status':'fallback' if reason else 'llama_validated',
                'fallback_reason':reason,'qa_signoff_required':True,
                'sop_document':self.sop['document_id'],'sop_revision':self.sop['revision'],
                'sop_sha256':stable_hash(self.sop),'prompt_tokens':prompt_tokens,
                'elapsed_ms':round((time.monotonic()-start)*1000,1),
                'runtime_metrics':getattr(self.worker,'last_metrics',{}),
                'sop_approval_status':self.sop.get('status','Approval unavailable'),
                'operational_use':'General technical demonstration; consult an approved procedure and authorized QA.',
                'validation_limit':'Schema, clause/action and bounded claim checks; free-text meaning still requires human review.'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--inspection',type=Path,required=True)
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--artifacts',type=Path,default=ROOT/'artifacts')
    parser.add_argument('--threads',type=int,choices=range(1,5),default=2)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--debug-output',type=Path,
                        help='Save raw generation and rejection details for local diagnosis')
    args=parser.parse_args()
    artifact=args.artifacts/'Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte'
    tokenizer=args.artifacts/'tokenizer.model'
    worker=NativeWorker(args.runtime,artifact,tokenizer,args.threads)
    try:
        advisor=Advisor(worker,token_counter(tokenizer))
        result=advisor.advise(json.loads(args.inspection.read_text(encoding='utf8')))
        if args.debug_output:
            args.debug_output.parent.mkdir(parents=True,exist_ok=True)
            args.debug_output.write_text(json.dumps(advisor.last_diagnostics,indent=2),encoding='utf8')
    finally:worker.close()
    text=json.dumps(result,indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding='utf8')
    return 0 if result['status']=='llama_validated' else 2


if __name__=='__main__':raise SystemExit(main())
