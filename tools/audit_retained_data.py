"""Audit retained manifests/scores and selected images without changing any split.

Optional --archives imports JSON only from original submission ZIPs, preserving
member bytes and archive hashes. It never executes archived code or loads pickle.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.evaluation_protocol import binary_metrics, split_audit, PROTOCOL


def digest(path):
    with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()


def run(archives, output):
    output.mkdir(parents=True,exist_ok=True)
    retained = output/'retained'; retained.mkdir(exist_ok=True)
    receipts = []
    if archives:
        for profile in ['mvtec_pill','mvtec_capsule','visa_capsules']:
            path = archives/(profile+'_Submission.zip')
            if not path.is_file(): continue
            with zipfile.ZipFile(path) as z:
                selected = [n for n in z.namelist() if n.endswith('/predictions.json') or
                            (n.startswith('evidence/data/') and n.endswith('_manifest.json'))]
                for name in selected:
                    data = z.read(name); json.loads(data)
                    dest = retained/(profile+'_'+Path(name).name)
                    dest.write_bytes(data)
                    receipts.append(dict(archive=path.name,archive_sha256=digest(path),
                                         member=name,file=dest.name,sha256=digest(dest)))
        (output/'archive_receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    receipt_path=output/'archive_receipts.json'
    if receipt_path.exists():
        for receipt in json.loads(receipt_path.read_text()):
            path=retained/receipt['file']
            if path.parent.resolve()!=retained.resolve() or digest(path)!=receipt['sha256']:
                raise ValueError('Retained source receipt mismatch')
    report = {'protocol':PROTOCOL,'scope':'Historical-score reanalysis and available-data audit; no new accuracy experiment',
              'profiles':{}, 'raw_training_images_available':False, 'retraining':'NOT RUN: raw train/validation/calibration pixels absent'}
    yolo=json.loads((ROOT/'evidence/historical/test_metrics.json').read_text())
    supports={r['Class']:int(r['Instances']) for r in yolo['per_class']}
    report['yolo']={'historical_test_instances':supports,'max_min_instance_ratio':max(supports.values())/min(supports.values()),
                    'train_class_imbalance':'NOT TESTED: original training labels absent',
                    'label_semantic_quality':'NOT TESTED: original labeled dataset absent',
                    'healthy_specificity':'NOT TESTED: original test has no healthy-only images',
                    'balancing_action':'None; test class counts must not determine a tuned training sampler'}
    for profile in ['mvtec_pill','mvtec_capsule','visa_capsules']:
        contract = json.loads((ROOT/'models/anomaly'/profile/'contract.json').read_text())
        local = json.loads((ROOT/'models/anomaly/samples'/profile/'manifest.json').read_text())
        pixel_ids = defaultdict(list); dhashes = []; bad = []; sample_labels = Counter()
        for row in local:
            path = ROOT/'models/anomaly/samples'/profile/row['file']
            if not path.is_file() or digest(path) != row['sha256']:
                bad.append(row['file']); continue
            with Image.open(path) as im:
                rgb = im.convert('RGB'); a = np.asarray(rgb)
                ident = hashlib.sha256(str(a.shape).encode()+a.tobytes()).hexdigest()
                pixel_ids[ident].append(row['file'])
                small = np.asarray(rgb.convert('L').resize((9,8),Image.Resampling.BILINEAR))
                dhashes.append((row['file'], small[:,1:] > small[:,:-1]))
            sample_labels[str(row.get('label'))] += 1
        near = []
        for i,(name,bits) in enumerate(dhashes):
            for other,other_bits in dhashes[:i]:
                distance = int(np.count_nonzero(bits != other_bits))
                if distance <= 4: near.append(dict(a=name,b=other,hamming=distance))
        result = dict(selected_sample_counts=dict(sample_labels),checksum_failures=bad,
                      exact_decoded_duplicate_groups=[v for v in pixel_ids.values() if len(v)>1],
                      near_duplicate_review_candidates=near,
                      near_duplicate_note='dHash <=4 is a review candidate, not proof of duplication; no automatic deletion',
                      training_eligible_local_images=0,
                      sample_scope='Selected demonstrations, including synthetic warnings; excluded from training, tuning and unbiased accuracy')
        manifest = list(retained.glob(profile+'_*manifest.json'))
        if manifest:
            result['split_audit'] = split_audit(json.loads(manifest[0].read_text()))
        predictions = retained/(profile+'_predictions.json')
        if predictions.exists():
            rows = json.loads(predictions.read_text())
            metrics = binary_metrics([r['label'] for r in rows],[r['score'] for r in rows],contract['thresholds']['image'])
            reference = next(iter(contract['evaluation']['per_category'].values()))
            assert metrics['confusion_matrix_tn_fp_fn_tp'] == reference['image_confusion_matrix_tn_fp_fn_tp']
            assert abs(metrics['image_auroc']-reference['image_auroc']) < 1e-10
            result['historical_recomputed'] = metrics
            result['historical_counts_and_auc_reproduced'] = True
            result['score_separation'] = {str(label):dict(zip(['p05','p50','p95'],map(float,np.quantile(
                [r['score'] for r in rows if r['label']==label],[.05,.5,.95])))) for label in [0,1]}
        result['calibration_tail_resolution'] = 1/contract['thresholds']['calibration_images']
        report['profiles'][profile] = result
    (output/'data_audit.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({p:r.get('historical_recomputed') for p,r in report['profiles'].items()},indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archives',type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'evidence/engineering_20261126')
    a=p.parse_args();run(a.archives,a.output)
