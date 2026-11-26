"""Compare frozen operating points from two evaluate_labeled.py reports."""
import argparse
import hashlib
import json
from pathlib import Path

try:
    from .evaluate_labeled import counts_for_image
except ImportError:
    from evaluate_labeled import counts_for_image


CLASSES = ('black_dot', 'broken', 'color_mismatch', 'crack', 'dual_cap', 'empty', 'foreign_particle')


def indexed_rows(report):
    rows = report['rows']
    result = {row['image_sha256']: row for row in rows}
    if not rows or len(result) != len(rows):
        raise ValueError('Reports must contain nonempty unique image identities')
    return result


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def metrics(rows):
    counts = [[0, 0, 0] for _ in CLASSES]
    tn = fp_images = fn_images = tp_images = 0
    for row in rows:
        labels = row['labels']
        predictions = row['predictions']
        for total, image_counts in zip(counts, counts_for_image(predictions, labels)):
            for index, key in enumerate(('tp', 'fp', 'fn')):
                total[index] += image_counts[key]
        if labels:
            tp_images += bool(predictions)
            fn_images += not predictions
        else:
            fp_images += bool(predictions)
            tn += not predictions

    def box_result(tp, fp, fn):
        return dict(tp=tp, fp=fp, fn=fn, precision=ratio(tp, tp+fp),
                    recall=ratio(tp, tp+fn), f1=ratio(2*tp, 2*tp+fp+fn))

    return {
        'per_class': {name: box_result(*count) for name, count in zip(CLASSES, counts)},
        'micro_box': box_result(*map(sum, zip(*counts))),
        'image_presence': {
            'tn_fp_fn_tp': [tn, fp_images, fn_images, tp_images],
            'specificity': ratio(tn, tn+fp_images),
            'false_alarm_rate': ratio(fp_images, tn+fp_images),
            'miss_rate': ratio(fn_images, fn_images+tp_images),
        },
    }


def compare(cpu, hailo):
    if (cpu.get('backend'), hailo.get('backend')) != ('onnx', 'hailo'):
        raise ValueError('Expected ONNX CPU reference and Hailo candidate reports')
    if not cpu.get('thresholds_sha256') or cpu['thresholds_sha256'] != hailo.get('thresholds_sha256'):
        raise ValueError('Reports must share the same frozen threshold hash')
    if not cpu.get('model_sha256') or not hailo.get('model_sha256'):
        raise ValueError('Both model identities are required')
    a, b = indexed_rows(cpu), indexed_rows(hailo)
    if a.keys() != b.keys():
        raise ValueError('Reports must cover exactly the same image bytes')
    for image_id in a:
        if not a[image_id].get('label_sha256') or a[image_id]['label_sha256'] != b[image_id].get('label_sha256'):
            raise ValueError('Label bytes differ for image '+image_id)
        if a[image_id]['labels'] != b[image_id]['labels']:
            raise ValueError('Parsed labels differ for image '+image_id)
    baseline, candidate = metrics(a.values()), metrics(b.values())

    def delta(old, new, fields):
        return {key: new[key]-old[key] if old[key] is not None and new[key] is not None else None
                for key in fields}

    fields = ('precision', 'recall', 'f1')
    return dict(protocol='medge-detector-backends-v1', paired_images=len(a),
                thresholds_sha256=cpu['thresholds_sha256'],
                model_sha256={'onnx':cpu['model_sha256'], 'hailo':hailo['model_sha256']},
                onnx=baseline, hailo=candidate,
                hailo_minus_onnx={
                    'micro_box': delta(baseline['micro_box'], candidate['micro_box'], fields),
                    'per_class': {key: delta(baseline['per_class'][key], candidate['per_class'][key], fields)
                                  for key in CLASSES},
                    'image_presence': delta(baseline['image_presence'], candidate['image_presence'],
                                            ('specificity', 'false_alarm_rate', 'miss_rate')),
                },
                scope='Fixed host thresholds and box IoU 0.50. HEF NMS is part of the deployed backend. '
                      'Image presence ignores box class/location. No AP sweep, timing, or physical split certification.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('onnx', 'hailo', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    cpu, hailo = args.onnx.read_bytes(), args.hailo.read_bytes()
    result = compare(json.loads(cpu), json.loads(hailo))
    result['input_sha256'] = {name: hashlib.sha256(data).hexdigest()
                              for name, data in [('onnx', cpu), ('hailo', hailo)]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
