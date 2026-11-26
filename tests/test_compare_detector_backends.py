from copy import deepcopy

import pytest

from tools.compare_detector_backends import compare


def reports():
    box = {'class_id': 0, 'box_xyxy': [0, 0, 10, 10]}
    rows = [
        dict(image_sha256='defect', label_sha256='defect-label', labels=[box],
             predictions=[dict(box, confidence=.99)]),
        dict(image_sha256='healthy', label_sha256='empty-label', labels=[], predictions=[]),
    ]
    cpu = dict(backend='onnx', thresholds_sha256='thresholds', model_sha256='cpu', rows=rows)
    hailo = deepcopy(cpu)
    hailo.update(backend='hailo', model_sha256='npu')
    return cpu, hailo


def test_compares_paired_metrics_and_recomputes_counts():
    cpu, hailo = reports()
    hailo['rows'][0]['predictions'] = []
    hailo['rows'].reverse()
    result = compare(cpu, hailo)
    assert result['paired_images'] == 2
    assert result['hailo_minus_onnx']['micro_box']['f1'] == -1
    assert result['hailo']['image_presence']['tn_fp_fn_tp'] == [1, 0, 1, 0]
    assert result['hailo_minus_onnx']['image_presence']['specificity'] == 0


@pytest.mark.parametrize('field', ['image_sha256', 'label_sha256', 'labels', 'thresholds_sha256'])
def test_rejects_changed_comparison_inputs(field):
    cpu, hailo = reports()
    if field == 'thresholds_sha256':
        hailo[field] = 'other'
    else:
        hailo['rows'][0][field] = [] if field == 'labels' else 'other'
    with pytest.raises(ValueError):
        compare(cpu, hailo)
