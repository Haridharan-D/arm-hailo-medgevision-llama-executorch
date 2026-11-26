"""Compare frozen candidate/baseline scores on identical independent test identities.

Input JSON: {model_sha256, threshold, threshold_origin: 'calibration',
calibration_image_sha256: [...], rows: [{image_sha256, label_sha256, label,
split: 'test', score}]}. This tool never selects thresholds or promotes a model.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.evaluation_protocol import binary_metrics, validate_pairs, PROTOCOL


def compare(a,b):
    paired=validate_pairs(a['rows'],b['rows'])
    for report in [a,b]:
        if not report.get('model_sha256') or report.get('threshold_origin')!='calibration':
            raise ValueError('Model identity and calibration-derived frozen threshold required')
        calibration=set(report['calibration_image_sha256'])
        if not calibration:raise ValueError('Calibration identities required')
        if calibration & {r['image_sha256'] for r in report['rows']}:
            raise ValueError('Calibration/test overlap')
        if any(not r.get('label_sha256') for r in report['rows']):
            raise ValueError('Label identity required')
    reports={}
    for name,report in [('baseline',a),('candidate',b)]:
        reports[name]=binary_metrics([r['label'] for r in report['rows']],
                                    [r['score'] for r in report['rows']],report['threshold'])
    old,new=reports['baseline'],reports['candidate']
    deltas={k:new[k]-old[k] if new[k] is not None and old[k] is not None else None
            for k in ['f1','recall','specificity','false_positive_rate','false_negative_rate','image_auroc']}
    return dict(protocol=PROTOCOL,paired_images=len(paired),metrics=reports,deltas=deltas,
                interpretation='Paired observed differences only; no automatic promotion or statistical superiority claim',
                f1_increased_without_observed_fpr_increase=(deltas['f1'] is not None and deltas['f1']>0 and
                    deltas['false_positive_rate'] is not None and deltas['false_positive_rate']<=0))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=compare(json.loads(a.baseline.read_text()),json.loads(a.candidate.read_text()))
    result['input_sha256']={k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in [('baseline',a.baseline),('candidate',a.candidate)]}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
