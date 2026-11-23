from app.visual_result import visual_result

def test_clear_visual_does_not_change_unvalidated_qa_disposition():
    record=dict(decision='REVIEW',capture_valid=True,profile_validated=False,detections=[])
    assert visual_result(record)['status']=='SAFE'
    assert record['decision']=='REVIEW' and record['profile_validated'] is False

def test_warning_for_bad_capture_and_defect_for_vision_evidence():
    assert visual_result(dict(capture_valid=False,decision='REVIEW'))['status']=='WARNING'
    assert visual_result(dict(capture_valid=True,decision='HOLD',detections=[{'type':'crack'}]))['status']=='DEFECTIVE'

def test_anomaly_decision_does_not_use_filename_or_ground_truth():
    for label in [0,1]:
        base=dict(capture_valid=True,decision='REVIEW',sample_ground_truth={'label':label},anomaly={'flagged':False})
        assert visual_result(base)['status']=='SAFE'
        base['anomaly']['flagged']=True
        assert visual_result(base)['status']=='DEFECTIVE'
        base['capture_valid']=False
        assert visual_result(base)['status']=='WARNING'

def test_incomplete_anomaly_and_runtime_fault_cannot_clear():
    assert visual_result(dict(capture_valid=True,anomaly={"score":.1}))['status']=='WARNING'
    assert visual_result(dict(error='offline',capture_valid=True,decision='PASS'))['status']=='WARNING'
