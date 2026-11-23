"""Evidence metadata around the frozen decision engine; never modifies it."""
import hashlib,json,platform,shutil,os
from pathlib import Path
VERSION='2026.11.23-display-sync-v1'
def save_image(path,image):
    import cv2
    tmp=path.with_name(path.stem+'.tmp'+path.suffix)
    if not cv2.imwrite(str(tmp),image):raise RuntimeError('Could not write image evidence')
    with tmp.open('r+b') as f:os.fsync(f.fileno())
    tmp.replace(path)
    if os.name!='nt':
        fd=os.open(str(path.parent),os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
def save_blob(path,data):
    tmp=path.with_suffix(path.suffix+'.part')
    with tmp.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    tmp.replace(path)
    if os.name!='nt':
        fd=os.open(str(path.parent),os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
def outcome(record):
    if record.get('system_fault'):return 'SYSTEM_FAULT'
    if record.get('detections'):return 'DEFECTIVE'
    if not record.get('capture_valid',False) or record.get('anomaly',{}).get('flagged'):return 'WARNING'
    if not record.get('profile_validated',False):return 'MANUAL_REVIEW'
    return 'NO_VISIBLE_DEFECT_DETECTED'
def enrich(record,config,store):
    from .visual_result import visual_result
    record['visual_result']=visual_result(record)
    original=config['data_dir']/'images'/(record['inspection_id']+'_original.jpg')
    sha=hashlib.sha256(original.read_bytes()).hexdigest()
    from .config import ROOT
    thresholds=(config.get('asset_dir',ROOT/'assets')/'thresholds.json').read_bytes()
    frozen={'thresholds_sha256':hashlib.sha256(thresholds).hexdigest(),'profile_validated':config.get('profile_validated',False),'policy':'frozen-v6','preprocess':'RGB letterbox640','nms_iou':.7}
    revision=hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()
    batch=config.get('active_batch','LEGACY')
    value=store.batch(batch)
    if not value or value['status']!='OPEN':raise ValueError('Choose an open batch before inspecting')
    from .auth import actor
    record.update(original_image_sha256=sha,duplicate_of=store.duplicate(sha),batch_id=batch,
        operator=actor.get(),software_version=VERSION,configuration_revision=revision,
        frozen_configuration=frozen,outcome=outcome(record),
        runtime_identity={'vision':'HailoRT' if record['backend']=='hailo' else 'ONNX Runtime CPU','advisory':'ExecuTorch v1.0.0 Arm CPU','platform':platform.machine()},
        persistence_status='committed',product_sku=value['sku'],product_category=value['category'])
    return record

def advisory_facts(record):
    facts={k:record[k] for k in ('inspection_id','decision','severity','defects','capture_valid','profile_validated')}
    if record.get('batch_id'):
        facts['context']={'batch_id':record['batch_id'],'product_type':record.get('product_category','unspecified'),
            'observations':[{'type':d['type'],'confidence':d['confidence'],'box_xyxy':d['box_xyxy']} for d in record.get('detections',[])[:2]],
            'anomaly_score':record.get('anomaly',{}).get('score'),'warnings':
                ([] if facts['capture_valid'] else ['capture_invalid'])+([] if facts['profile_validated'] else ['profile_unvalidated'])}
    return facts
def storage_health(root):
    usage=shutil.disk_usage(root);free=usage.free/1024**3
    return {'free_gib':round(free,3),'used_percent':round(100*usage.used/usage.total,2),'state':'critical' if free<.25 else 'warning' if free<1 else 'ok',
            'retention':'No automatic evidence deletion. Export and verify backups before authorized archival.'}
