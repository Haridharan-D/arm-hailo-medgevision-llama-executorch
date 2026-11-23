from app.service import InspectionService


def test_retry_publishes_pending_before_forcing_generation():
    facts={'inspection_id':'RETRY','decision':'HOLD','severity':'major',
           'defects':[{'type':'crack','count':1}],'capture_valid':True,'profile_validated':False}
    events=[]
    class Store:
        def get(self,id):return dict(facts,advice={'cache_hit':True})
        def advice(self,id,value):events.append(('stored',id,value))
    class Llama:
        def submit(self,value,force=False):
            assert events==[('stored','RETRY',None)]
            assert value==facts and force
            return True
    service=InspectionService.__new__(InspectionService);service.store=Store();service.llm=Llama()
    assert service.request_advice('RETRY')
