"""Visual observations for operator tests; separate from immutable QA disposition."""
POLICY='visual-check-v1'

def visual_result(record):
    status='WARNING';reason='Image capture is unsuitable or missing; recapture before assessment'
    if record.get('system_fault') or record.get('error'):
        reason='Inspection runtime fault; no visual clearance available'
    elif record.get('detections') or record.get('decision')=='HOLD':
        status='DEFECTIVE';reason='Configured defect detected by the vision model'
    elif record.get('capture_valid') is True:
        anomaly=record.get('anomaly')
        if anomaly and anomaly.get('flagged') is True:
            status='DEFECTIVE';reason='Anomaly score exceeds the saved model threshold'
        elif anomaly and anomaly.get('flagged') is not False:
            reason='Anomaly assessment is incomplete; no visual clearance available'
        else:
            status='SAFE';reason='Below the saved anomaly threshold' if anomaly else 'No configured defect detected'
    return {'status':status,'reason':reason,'qa_decision':record.get('decision'),
            'scope':'Visual model check only; not pharmaceutical safety or QA release approval',
            'policy':POLICY}
