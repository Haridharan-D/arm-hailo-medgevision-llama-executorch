from types import SimpleNamespace
from app.display_state import current_display

class Camera:
    def __init__(self,running=False,age=5,error=None):
        self.status=dict(running=running,error=error,decision='REVIEW',capture={'valid':True},last_inspection_id='CAMERA');self.age=age
    def frame_age_ms(self):return self.age
class Store:
    def recent(self,n):return [{'inspection_id':'LATEST'}]
    def get(self,id):return dict(inspection_id=id,decision='HOLD',capture_valid=True,detections=[{'type':'crack'}])

def test_manual_completed_inspection_wins_over_background_camera():
    s=SimpleNamespace(display_record=dict(inspection_id='MANUAL',decision='REVIEW',capture_valid=True,detections=[]),store=Store())
    result=current_display(s,Camera(running=True))
    assert result['mode']=='inspection' and result['record']['inspection_id']=='MANUAL'
    assert result['record']['visual_result']['status']=='SAFE'
    s.display_record=None
    assert current_display(s,Camera(running=True))['record']['inspection_id']=='CAMERA'

def test_stale_camera_or_runtime_fault_cannot_show_safe():
    s=SimpleNamespace(display_record=None,store=Store())
    assert current_display(s,Camera(running=True,age=4000))['record']['visual_result']['status']=='WARNING'
    s.display_record=dict(decision='REVIEW',capture_valid=True);s.last_vision_error='failed'
    assert current_display(s,Camera())['record']['visual_result']['status']=='WARNING'

def test_restart_restores_latest_record_without_manual_pointer():
    s=SimpleNamespace(store=Store());value=current_display(s,Camera())
    assert value['record']['inspection_id']=='LATEST' and value['record']['visual_result']['status']=='DEFECTIVE'
