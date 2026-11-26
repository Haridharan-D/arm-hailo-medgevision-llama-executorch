"""101-point interpolated box AP at IoU .50:.95 on precomputed predictions.

Not the official COCO evaluator: no crowd handling, size buckets or maxDet policy.
Rows contain unique image_sha256, label_sha256, split='test', labels and predictions
(class_id, box_xyxy; confidence for predictions). Supply low-confidence candidate
predictions, NOT frozen operating-threshold output, for a useful PR sweep.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.evaluate_labeled import overlap


def evaluate(rows,nclasses=7):
    ids=[r['image_sha256'] for r in rows]
    if not rows or len(set(ids))!=len(ids):raise ValueError('Unique nonempty image set required')
    for row in rows:
        if row.get('split')!='test' or not row.get('label_sha256'):raise ValueError('Test/label identity required')
        for kind in ['labels','predictions']:
            for box in row[kind]:
                xy=np.asarray(box['box_xyxy'],dtype=float)
                if xy.shape!=(4,) or not np.isfinite(xy).all() or np.any(xy[2:]<=xy[:2]):raise ValueError('Invalid box')
                if not isinstance(box['class_id'],int) or not 0<=box['class_id']<nclasses:raise ValueError('Invalid class')
                if kind=='predictions' and not 0<=box['confidence']<=1:raise ValueError('Invalid confidence')
    per_class={}
    for cls in range(nclasses):
        labels={i:[v for v in r['labels'] if v['class_id']==cls] for i,r in enumerate(rows)}
        support=sum(map(len,labels.values()))
        predictions=sorted([(i,v) for i,r in enumerate(rows) for v in r['predictions'] if v['class_id']==cls],key=lambda x:-x[1]['confidence'])
        aps=[]
        for iou in np.linspace(.5,.95,10):
            used=set();hits=[]
            for i,prediction in predictions:
                candidates=[(overlap(prediction['box_xyxy'],v['box_xyxy']),j) for j,v in enumerate(labels[i]) if (i,j) not in used]
                score,j=max(candidates,default=(0,-1));hit=score>=iou
                hits.append(int(hit))
                if hit:used.add((i,j))
            if not support:aps.append(None);continue
            tp=np.cumsum(hits);fp=np.cumsum(1-np.asarray(hits,dtype=int))
            recall=tp/support;precision=tp/np.maximum(tp+fp,1)
            aps.append(float(np.mean([np.max(precision[recall>=r],initial=0) for r in np.linspace(0,1,101)])))
        per_class[str(cls)]=dict(support=support,ap50=aps[0],ap50_95=float(np.mean(aps)) if support else None,ap_by_iou=aps)
    valid=[r for r in per_class.values() if r['support']]
    return dict(protocol='medge-box-ap101-v1',per_class=per_class,
                map50=float(np.mean([r['ap50'] for r in valid])) if valid else None,
                map50_95=float(np.mean([r['ap50_95'] for r in valid])) if valid else None,
                note='Custom AP101 protocol, not official COCO/Ultralytics equivalence; absent classes excluded from macro')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--predictions',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    data=json.loads(a.predictions.read_text())
    if not 0<=data['score_floor']<=.01:raise ValueError('Declare a low score floor <= .01; operating-threshold exports are not accepted')
    result=evaluate(data['rows']);result['declared_score_floor']=data['score_floor']
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
