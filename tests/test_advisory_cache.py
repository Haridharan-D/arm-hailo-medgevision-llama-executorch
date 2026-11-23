from app.advisory_cache import AdvisoryCache
from advisor_src.advisor import stable_hash

def facts(id='ONE',count=1):return {'inspection_id':id,'decision':'HOLD','severity':'major','defects':[{'type':'crack','count':count}],'capture_valid':True,'profile_validated':False}
def response():return {'inspection_id':'ONE','decision':'HOLD','status':'llama_validated','elapsed_ms':17000,'advisory':{'clause_id':'BT-02'}}

def test_cached_response_gets_current_identity_without_mutating_original():
    cache=AdvisoryCache('SOP1');result=response();cache.put(facts(),result)
    reused=cache.get(facts('TWO'))
    assert reused['inspection_id']=='TWO' and reused['facts_sha256']==stable_hash(facts('TWO'))
    assert reused['cache_hit'] and reused['original_generation_ms']==17000
    assert result['inspection_id']=='ONE' and 'cache_hit' not in result

def test_different_observation_count_cannot_reuse_advice():
    cache=AdvisoryCache('SOP1');cache.put(facts(),response())
    assert cache.get(facts('TWO',2)) is None

def test_infrastructure_failure_is_not_cached():
    cache=AdvisoryCache('SOP1');cache.put(facts(),dict(response(),status='fallback',fallback_reason='RuntimeError'))
    assert cache.get(facts('TWO')) is None
