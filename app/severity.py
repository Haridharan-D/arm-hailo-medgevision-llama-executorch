"""Explain the existing conservative rule; not a clinical severity prediction."""
def explanation(record):
    if record.get('detections'):
        return dict(policy='conservative-qa-v1',level=record.get('severity','major'),
                    rule='configured-defect-hold',classes=sorted({d['type'] for d in record['detections']}),
                    rationale='Any configured localized defect requires HOLD and human QA review; class-specific clinical severity is not validated.')
    if record.get('anomaly'):
        return dict(policy='conservative-qa-v1',level=record.get('severity','unknown'),rule='category-anomaly-review',
                    rationale='Anomaly score is category-specific and does not identify defect type or clinical severity.')
    return dict(policy='conservative-qa-v1',level=record.get('severity','unknown'),rule='capture-and-profile-gate',
                rationale='QA release requires usable capture and a validated product profile. Visual SAFE alone does not authorize release.')
