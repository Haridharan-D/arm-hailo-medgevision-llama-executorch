import json
from tools import medge_demo as demo

def test_terminal_demo_prints_actual_defect_and_advice_without_forcing_label(tmp_path,monkeypatch,capsys):
    calls=[];state={'batch':'DEMO','folder':str(tmp_path),'records':[]}
    monkeypatch.setattr(demo,'ready',lambda:True);monkeypatch.setattr(demo,'state',lambda:(tmp_path/'state.json',state));monkeypatch.setattr(demo,'save_state',lambda v:None)
    value=dict(inspection_id='DEMO-1',backend='hailo',visual_result={'status':'DEFECTIVE'},decision='HOLD',vision_ms=15.5,capture_valid=True,
        detections=[{'type':'crack','confidence':.91,'box_xyxy':[1,2,30,40]}],advice={'status':'llama_validated','cache_hit':True,'advisory':{'operator_message':'Preserve evidence.','qa_note':'Draft: QA review pending.','clause_id':'BT-02'},'sop_document':'DEMO-SOP','elapsed_ms':.2})
    def api(path,value_in=None,timeout=0):calls.append((path,value_in));return value
    monkeypatch.setattr(demo,'call',api)
    assert demo.run_case('1')
    output=capsys.readouterr().out;assert 'Medge' not in output or 'MEDGE VISION' in output
    assert 'crack' in output and 'Preserve evidence.' in output and 'REUSED' in output and 'BT-02' in output
    assert calls[0][1]=={'name':'acceptance_demo/defective/crack/crack.jpg'}
    assert json.loads(next(tmp_path.glob('test_*.json')).read_text())['decision']=='HOLD'

def test_terminal_demo_reports_model_miss_as_unexpected(tmp_path,monkeypatch,capsys):
    state={'folder':str(tmp_path),'records':[]};monkeypatch.setattr(demo,'ready',lambda:True);monkeypatch.setattr(demo,'state',lambda:(tmp_path/'state.json',state));monkeypatch.setattr(demo,'save_state',lambda v:None)
    value=dict(inspection_id='MISS',backend='anomaly_onnx_cpu',visual_result={'status':'SAFE'},decision='REVIEW',vision_ms=20,capture_valid=True,detections=[],anomaly={'score':.01,'threshold':.3,'flagged':False},advice={'status':'fallback','fallback_reason':'rejected','advisory':{},'elapsed_ms':1})
    monkeypatch.setattr(demo,'call',lambda *args,**kwargs:value)
    assert demo.run_case('3') is False
    text=capsys.readouterr().out;assert 'UNEXPECTED' in text and 'fallback' in text
    assert state['records'][0]['matched'] is False
