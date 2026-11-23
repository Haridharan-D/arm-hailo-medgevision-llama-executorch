from tools.evaluate_labeled import counts_for_image

def test_one_ground_truth_cannot_match_two_predictions():
    label={'class_id':0,'box_xyxy':[0,0,10,10]}
    high=dict(label,confidence=.9);low=dict(label,confidence=.8)
    assert counts_for_image([high,low],[label])[0]=={'tp':1,'fp':1,'fn':0}

def test_wrong_class_is_false_positive_and_false_negative():
    label={'class_id':0,'box_xyxy':[0,0,10,10]}
    pred={'class_id':1,'box_xyxy':[0,0,10,10],'confidence':.99}
    result=counts_for_image([pred],[label])
    assert result[0]=={'tp':0,'fp':0,'fn':1}
    assert result[1]=={'tp':0,'fp':1,'fn':0}

def test_empty_ground_truth_does_not_hide_false_positive():
    pred={'class_id':2,'box_xyxy':[0,0,10,10],'confidence':.9}
    assert counts_for_image([pred],[])[2]=={'tp':0,'fp':1,'fn':0}
