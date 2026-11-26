import numpy as np
import pytest
from tools.evaluation_protocol import binary_metrics, calibrate_normal, validate_pairs, split_audit


def test_binary_metrics_counts_and_healthy_specificity():
    m=binary_metrics([0,0,1,1],[.1,.9,.2,.8],.5)
    assert m['confusion_matrix_tn_fp_fn_tp']==[1,1,1,1]
    assert m['f1']==m['specificity']==m['false_negative_rate']==.5


def test_auc_ties_and_undefined_population():
    assert binary_metrics([0,1],[.5,.5],.5)['image_auroc']==.5
    assert binary_metrics([0,1],[.1,.9],.5)['image_auroc']==1
    assert binary_metrics([1,1],[.2,.9],.5)['specificity'] is None
    assert binary_metrics([1,1],[.2,.9],.5)['image_auroc'] is None


@pytest.mark.parametrize('labels,scores', [([0,2],[.1,.2]),([0,1],[.1,float('nan')]),([],[])])
def test_invalid_scores_fail_closed(labels,scores):
    with pytest.raises(ValueError):binary_metrics(labels,scores,.5)


def test_calibration_cannot_consume_test_images_or_defects():
    row=dict(split='test',label=0,score=.2,image_sha256='a')
    with pytest.raises(ValueError):calibrate_normal([row])
    row.update(split='calibration',label=1)
    with pytest.raises(ValueError):calibrate_normal([row])
    row['label']=0
    with pytest.raises(ValueError):calibrate_normal([row,row])
    assert calibrate_normal([row])['empirical_tail_resolution']==1


def test_comparison_rejects_changed_images_labels_and_split():
    row=dict(image_sha256='a',label=1,label_sha256='label',split='test')
    assert len(validate_pairs([row],[dict(row)]))==1
    for change in [dict(image_sha256='b'),dict(label=0),dict(split='train')]:
        with pytest.raises(ValueError):validate_pairs([row],[dict(row,**change)])


def test_split_audit_detects_path_alias_and_overlap():
    result=split_audit({'train':[dict(image='a\\b.png',label=0)],'test':[dict(image='a/b.png',label=0)]})
    assert len(result['repeated_path_identities'])==1


def test_threshold_lookup_preserves_comparison_at_boundaries():
    from app.vision import NAMES
    thresholds={n:{'threshold':.9-i*.01} for i,n in enumerate(NAMES)}
    classes=np.tile(np.arange(7),1200)
    old=np.array([thresholds[NAMES[c]]['threshold'] for c in classes])
    vector=np.array([thresholds[n]['threshold'] for n in NAMES],dtype=np.float64)
    scores=old.astype(np.float32)
    assert np.array_equal(old,vector[classes])
    assert np.array_equal(scores>=old,scores>=vector[classes])


@pytest.mark.parametrize('image',[None,np.zeros((4,4),np.uint8),np.zeros((4,4,3),np.float32),np.zeros((0,4,3),np.uint8)])
def test_anomaly_invalid_input_rejected_before_runtime(image):
    from app.anomaly import AnomalyEngine
    engine=AnomalyEngine.__new__(AnomalyEngine);engine.contracts={'profile':{}}
    with pytest.raises(ValueError,match='uint8 BGR'):engine.predict(image,'profile')


def test_ap_perfect_missing_and_wrong_class():
    from tools.detection_ap import evaluate
    box={'class_id':0,'box_xyxy':[0,0,10,10]}
    row={'image_sha256':'a','label_sha256':'l','split':'test','labels':[box],
         'predictions':[dict(box,confidence=.9)]}
    assert evaluate([row])['map50_95']==1
    row['predictions']=[]
    assert evaluate([row])['map50_95']==0
    row['predictions']=[dict(box,class_id=1,confidence=.9)]
    assert evaluate([row])['map50']==0


def test_ap_false_positive_before_true_positive_and_iou_sweep():
    from tools.detection_ap import evaluate
    label={'class_id':0,'box_xyxy':[0,0,10,10]}
    row={'image_sha256':'a','label_sha256':'l','split':'test','labels':[label],
         'predictions':[dict(label,box_xyxy=[20,20,30,30],confidence=.99),dict(label,confidence=.9)]}
    assert evaluate([row])['map50']==.5
    row['predictions']=[dict(label,box_xyxy=[0,0,8,10],confidence=.9)]
    result=evaluate([row])
    assert result['map50']==1 and 0<result['map50_95']<1


def test_pair_comparison_refuses_calibration_leakage():
    from tools.compare_scores import compare
    report={'model_sha256':'m','threshold':.5,'threshold_origin':'calibration','calibration_image_sha256':['a'],
            'rows':[dict(image_sha256='a',label_sha256='l',label=1,score=.8,split='test')]}
    with pytest.raises(ValueError,match='overlap'):compare(report,report)


def test_yolo_audit_missing_labels_and_cross_split_pixels(tmp_path):
    from PIL import Image
    from tools.audit_yolo_dataset import audit
    for split in ['train','val','test']:
        (tmp_path/'images'/split).mkdir(parents=True)
        (tmp_path/'labels'/split).mkdir(parents=True)
        Image.new('RGB',(16,16),'red').save(tmp_path/'images'/split/'sample.png')
        (tmp_path/'labels'/split/'sample.txt').write_text('0 .5 .5 .2 .2\n')
    r=audit(tmp_path)
    assert not r['training_ready'] and len(r['cross_split_decoded_duplicates'])==1
    (tmp_path/'labels/test/sample.txt').unlink()
    assert any('Missing label' in e['error'] for e in audit(tmp_path)['errors'])


def test_yolo_audit_rejects_outside_and_duplicate_boxes(tmp_path):
    from tools.audit_yolo_dataset import label_boxes
    path=tmp_path/'label.txt'
    for text in ['0 .05 .5 .2 .2','0 .5 .5 .2 .2\n0 .5 .5 .2 .2']:
        path.write_text(text)
        with pytest.raises(ValueError):label_boxes(path,7)
