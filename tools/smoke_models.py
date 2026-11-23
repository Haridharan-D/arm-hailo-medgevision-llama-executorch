"""Run actual CPU models on five selected demo images; not an accuracy benchmark."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import cv2
from app.anomaly import AnomalyEngine
from app.vision import Detector


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('smoke_results.json'))
    args = parser.parse_args()
    detector = Detector({'vision_backend': 'onnx', 'asset_dir': ROOT/'assets'})
    results = []
    try:
        for name, expected in [('defective/crack/crack.jpg', True), ('safe/safe_01.jpg', False)]:
            path = ROOT/'test_images/acceptance_demo'/name
            image = cv2.imread(str(path))
            if image is None:
                raise RuntimeError('Missing sample: '+str(path))
            detections, elapsed = detector.predict(image)
            passed = bool(detections) == expected
            results.append(dict(pipeline='yolo', image=name, detections=detections,
                                elapsed_ms=elapsed, expected_defect=expected, matched=passed))
    finally:
        detector.close()
    engine = AnomalyEngine(ROOT/'models/anomaly')
    for profile in ['mvtec_pill', 'mvtec_capsule', 'visa_capsules']:
        path, _ = engine.sample_path(profile, 'demo/defective/defective_01.png')
        assessment, _, _, _ = engine.predict(cv2.imread(str(path)), profile)
        results.append(dict(pipeline=profile, **assessment, matched=assessment['flagged']))
    report = dict(scope='Selected real-model CPU demo smoke test; not held-out accuracy or Hailo/Llama validation',
                  all_matched=all(row['matched'] for row in results), results=results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    for row in results:
        print(row['pipeline'], 'OK' if row['matched'] else 'MISMATCH')
    print('Saved:', args.output)
    return 0 if report['all_matched'] else 1


if __name__ == '__main__':
    raise SystemExit(run())
