"""Reuse a prior bounded advisory only for identical decision/evidence/SOP facts."""
from collections import OrderedDict
import copy
import time
from advisor_src.advisor import stable_hash,validate_inspection

class AdvisoryCache:
    def __init__(self,identity,limit=32):self.identity=identity;self.limit=limit;self.entries=OrderedDict()
    def key(self,facts):
        facts=validate_inspection(facts)
        return stable_hash({'identity':self.identity,'facts':{k:v for k,v in facts.items() if k!='inspection_id'}})
    def put(self,facts,result):
        if result['status']!='llama_validated' and result.get('fallback_reason') not in {'ValueError','JSONDecodeError'}:return
        self.entries[self.key(facts)]=(time.monotonic(),copy.deepcopy(result))
        while len(self.entries)>self.limit:self.entries.popitem(last=False)
    def get(self,facts):
        start=time.perf_counter();key=self.key(facts);entry=self.entries.get(key)
        if not entry:return None
        at,value=entry;ttl=600 if value['status']=='llama_validated' else 60
        if time.monotonic()-at>ttl:self.entries.pop(key,None);return None
        result=copy.deepcopy(value);result.update(inspection_id=facts['inspection_id'],facts_sha256=stable_hash(facts),
            cache_hit=True,cache_source_inspection_id=value['inspection_id'],original_generation_ms=value['elapsed_ms'],
            elapsed_ms=round((time.perf_counter()-start)*1000,3),
            response_source='Reused prior advisory for identical observation/decision/SOP facts; no new generation')
        if result.get('structured_advisory'):result['structured_advisory']['inspection_id']=facts['inspection_id']
        return result
