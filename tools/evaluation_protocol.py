"""Versioned, dependency-light binary evaluation and split-safety primitives.

Scores are ordered evidence, never probabilities. No threshold is fit on test data.
"""
import hashlib
import json
import math
import numpy as np

PROTOCOL = 'medge-paired-v1'


def binary_metrics(labels, scores, threshold):
    y = np.asarray(labels)
    s = np.asarray(scores, dtype=float)
    if y.ndim != 1 or s.shape != y.shape or not len(y):
        raise ValueError('Nonempty, equally sized label and score vectors required')
    if not np.isin(y, [0, 1]).all() or not np.isfinite(s).all() or not math.isfinite(threshold):
        raise ValueError('Binary labels and finite scores/threshold required')
    pred = s >= threshold
    tp = int(np.sum(pred & (y == 1))); fp = int(np.sum(pred & (y == 0)))
    fn = int(np.sum(~pred & (y == 1))); tn = int(np.sum(~pred & (y == 0)))
    def ratio(a, b): return a / b if b else None
    # AUROC as Mann-Whitney rank statistic, with average ranks for ties.
    order = np.argsort(s, kind='stable'); sorted_scores = s[order]
    ranks = np.empty(len(s), dtype=float)
    starts = np.r_[0, np.flatnonzero(np.diff(sorted_scores)) + 1]
    ends = np.r_[starts[1:], len(s)]
    for start, end in zip(starts, ends):
        ranks[order[start:end]] = (start + 1 + end) / 2
    npos = tp + fn; nneg = tn + fp
    auc = (float(ranks[y == 1].sum()) - npos*(npos+1)/2)/(npos*nneg) if npos*nneg else None
    return dict(confusion_matrix_tn_fp_fn_tp=[tn, fp, fn, tp], images=len(y),
                precision=ratio(tp,tp+fp), recall=ratio(tp,tp+fn),
                f1=ratio(2*tp,2*tp+fp+fn), specificity=ratio(tn,tn+fp),
                false_positive_rate=ratio(fp,tn+fp), false_negative_rate=ratio(fn,tp+fn),
                accuracy=(tp+tn)/len(y), image_auroc=auc, threshold=float(threshold))


def calibrate_normal(rows, quantile=.995):
    """Only explicitly separate normal calibration rows may set a threshold."""
    if not rows or not 0 < quantile < 1:
        raise ValueError('Normal calibration rows and a quantile in (0,1) required')
    if any(r.get('split') != 'calibration' or r.get('label') != 0 for r in rows):
        raise ValueError('Calibration must contain only explicitly labeled calibration normals')
    ids = [r['image_sha256'] for r in rows]
    if len(set(ids)) != len(ids): raise ValueError('Duplicate calibration images')
    scores = np.array([r['score'] for r in rows], dtype=float)
    if not np.isfinite(scores).all(): raise ValueError('Non-finite calibration score')
    return dict(threshold=float(np.quantile(scores, quantile, method='linear')),
                method='normal_quantile_linear', quantile=quantile, n=len(rows),
                empirical_tail_resolution=1/len(rows),
                calibration_identity=hashlib.sha256(json.dumps(sorted(ids)).encode()).hexdigest(),
                note='Finite calibration sample does not guarantee a population false-positive rate')


def validate_pairs(baseline, candidate):
    """Reject different identities, labels or split ownership before comparison."""
    def index(rows):
        if not rows: raise ValueError('Empty paired evaluation')
        keys = [r['image_sha256'] for r in rows]
        if len(set(keys)) != len(keys): raise ValueError('Duplicate image identity')
        return dict(zip(keys, rows))
    a, b = index(baseline), index(candidate)
    if a.keys() != b.keys(): raise ValueError('Paired evaluation requires identical images')
    for key in a:
        for field in ['label','label_sha256','split']:
            if a[key].get(field) != b[key].get(field): raise ValueError('Changed label or split: '+key)
        if a[key].get('split') != 'test': raise ValueError('Independent test split required')
    return [(a[k], b[k]) for k in sorted(a)]


def split_audit(splits):
    """Path identity audit; physical/byte independence requires additional evidence."""
    owners = {}; counts = {}; errors = []
    for split, rows in splits.items():
        counts[split] = {'images':len(rows), 'normal':sum(r['label']==0 for r in rows),
                         'defect':sum(r['label']==1 for r in rows)}
        for row in rows:
            path = row['image'].replace('\\','/')
            if path in owners: errors.append({'image':path, 'splits':[owners[path],split]})
            owners[path] = split
    return dict(counts=counts, repeated_path_identities=errors,
                physical_group_independence='NOT TESTED',
                full_dataset_byte_duplicates='NOT TESTED: raw images required')
