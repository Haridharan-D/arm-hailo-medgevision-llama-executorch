"""One authoritative, lightweight second-screen state, independent of Llama."""
from .visual_result import visual_result

def compact(record):
    if record is None:return None
    keys=['inspection_id','created_at','source','decision','capture_valid','profile_validated','detections','anomaly','system_fault','error']
    result={k:record[k] for k in keys if k in record}
    result['visual_result']=visual_result(record)
    return result

def current_display(service,camera):
    if getattr(service,'last_vision_error',None):return {'mode':'fault','record':compact({'error':'Vision runtime fault','decision':'REVIEW'})}
    manual=getattr(service,'display_record',None)
    if manual:return {'mode':'inspection','record':compact(manual)}
    status=camera.status
    if status.get('running') or status.get('error'):
        age=camera.frame_age_ms()
        if status.get('error') or not status.get('running') or not status.get('decision') or age is None or age>3000:
            return {'mode':'live_camera','record':compact({'error':'Camera frame unavailable or stale','decision':'REVIEW'})}
        return {'mode':'live_camera','record':compact({'inspection_id':status.get('last_inspection_id'),
            'decision':status['decision'],'capture_valid':status.get('capture',{}).get('valid') is True})}
    rows=service.store.recent(1)
    return {'mode':'latest_record' if rows else 'idle','record':compact(service.store.get(rows[0]['inspection_id'])) if rows else None}
