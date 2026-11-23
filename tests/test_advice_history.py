from app.store import Store
def test_retry_preserves_prior_advice_in_immutable_history(tmp_path):
    s=Store(tmp_path);s.add(dict(inspection_id='T',created_at='now',source='test',decision='REVIEW',severity='unknown'))
    s.advice('T',dict(status='fallback',message='first'));s.advice('T',None);s.advice('T',dict(status='llama_validated',message='second'))
    history=s.advice_history('T')
    assert len(history)==3 and history[0]['advice']['message']=='first' and history[1]['advice'] is None
    assert s.get('T')['advice']['message']=='second' and s.verify_integrity()['valid']
