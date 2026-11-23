"""Run all bundled held-out samples through real exported models; retain misses."""
import argparse
import json
from pathlib import Path
import sys
import cv2
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.anomaly import AnomalyEngine

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'validation/anomaly_samples')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    engine=AnomalyEngine(ROOT/'models/anomaly');report={'profiles':{},'scope':'Selected held-out dataset sample execution check; not the full benchmark or local blister-camera accuracy'}
    for profile in engine.profiles():
        rows=[]
        for sample in engine.samples(profile['id']):
            path,meta=engine.sample_path(profile['id'],sample['file']);image=cv2.imread(str(path))
            assessment,rgba,overlay,raw=engine.predict(image,profile['id'])
            cv2.imwrite(str(args.output/(profile['id']+'_'+sample['file']+'_overlay.jpg')),overlay)
            rows.append({'file':sample['file'],'label':sample['label'],'score':assessment['score'],
                'threshold':assessment['threshold'],'flagged':assessment['flagged'],'elapsed_ms':assessment['elapsed_ms'],
                'correct_at_saved_threshold':int(assessment['flagged'])==sample['label']})
            print(profile['id'],sample['file'],'GT',sample['label'],'score',round(assessment['score'],4),'flag',assessment['flagged'],flush=True)
        report['profiles'][profile['id']]={'n':len(rows),'correct':sum(r['correct_at_saved_threshold'] for r in rows),'rows':rows}
        (args.output/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:{'n':v['n'],'correct':v['correct']} for k,v in report['profiles'].items()},indent=2))

if __name__=='__main__':main()
