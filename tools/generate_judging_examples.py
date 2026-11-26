"""Render selected cases using the shipped CPU models and plot preserved evidence."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import sys

import cv2
import numpy as np
import onnxruntime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.anomaly import AnomalyEngine
from app.vision import Detector, annotate, disposition


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def render_pair(path, original, result, subtitle, right_label):
    """Fit both images without distorting their aspect ratios."""
    canvas = np.full((558, 1100, 3), (36, 27, 18), dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(canvas, subtitle, (20, 30), font, .64, (235, 239, 244), 1, cv2.LINE_AA)
    for index, (image, label) in enumerate(((original, 'INPUT'), (result, right_label))):
        x = 14 + index * 548
        height, width = image.shape[:2]
        scale = min(524 / width, 466 / height)
        fitted = cv2.resize(image, (max(1, round(width * scale)), max(1, round(height * scale))),
                            interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
        y = 49 + (466-fitted.shape[0])//2
        left = x + (524-fitted.shape[1])//2
        canvas[y:y+fitted.shape[0], left:left+fitted.shape[1]] = fitted
        cv2.putText(canvas, label, (x+6, 539), font, .55, (196, 228, 223), 1, cv2.LINE_AA)
    if not cv2.imwrite(str(path), canvas):
        raise RuntimeError(f'Could not write {path}')


def examples(output):
    assets = ROOT/'assets'
    artifact = assets/'blistertrace_yolov8s.onnx'
    detector = Detector({'asset_dir': assets, 'vision_backend': 'onnx'})
    records = []
    try:
        for name in ('crack', 'empty'):
            source = ROOT/'test_images/acceptance_demo/defective'/name/(name+'.jpg')
            image = cv2.imread(str(source))
            detections, _ = detector.predict(image)
            decision, _, _ = disposition(image, detections, False)
            if not any(d['type'] == name for d in detections):
                raise RuntimeError(f'Expected selected example result no longer present: {name}')
            filename = f'yolo_{name}_boxes.png'
            render_pair(output/filename, image, annotate(image, detections, decision),
                        f'YOLOv8s FP32 CPU | {len(detections)} retained detection(s)', 'MODEL BOXES')
            records.append(dict(output=filename, input=source.relative_to(ROOT).as_posix(),
                                input_sha256=digest(source), model_sha256=digest(artifact),
                                thresholds_sha256=digest(assets/'thresholds.json'), decision=decision,
                                detections=detections))
    finally:
        detector.close()
    engine = AnomalyEngine(ROOT/'models/anomaly')
    for profile in ('mvtec_pill', 'mvtec_capsule', 'visa_capsules'):
        source, row = engine.sample_path(profile, 'demo/defective/defective_01.png')
        image = cv2.imread(str(source))
        assessment, _, overlay, _ = engine.predict(image, profile)
        filename = f'{profile}_heatmap.png'
        render_pair(output/filename, image, overlay,
                    f'{profile} CPU | score {assessment["score"]:.4f} / threshold {assessment["threshold"]:.4f}',
                    'ALIGNED MODEL HEATMAP')
        records.append(dict(output=filename, input=source.relative_to(ROOT).as_posix(),
                            input_sha256=digest(source), sample_manifest=row,
                            **{key: assessment[key] for key in
                               ('profile','model_sha256','score','threshold','pixel_threshold','flagged','color_scale_note')}))
    for row in records:
        row['output_sha256'] = digest(output/row['output'])
    report = dict(scope='Fresh ONNX Runtime CPU inference on selected demo inputs. No test-set accuracy estimate.',
                  platform=platform.platform(), onnxruntime=onnxruntime.__version__, opencv=cv2.__version__,
                  cases=records)
    (output/'inference_receipt.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',
                                                 encoding='utf-8')


def plots(output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'axes.labelcolor':'#233746'})
    teal, blue, amber = '#08796e', '#526d86', '#bc6325'

    def rows(name):
        with (ROOT/'evidence/metrics'/name).open(newline='',encoding='utf-8') as stream:
            return list(csv.DictReader(stream))

    def chart():
        return plt.subplots(figsize=(8.4, 3.35), layout='constrained')

    def save(fig, filename):
        fig.savefig(output/filename,dpi=150,facecolor='white')
        plt.close(fig)

    data = rows('anomaly_image.csv')
    names = ['MVTec pill', 'MVTec capsule', 'VisA capsules']
    x = np.arange(3)
    fig, ax = chart()
    for offset, key, title, color in [(-.18,'auroc','Image AUROC',blue),(.18,'f1','Image F1 at threshold',teal)]:
        bars = ax.bar(x+offset,[float(r[key]) for r in data],.35,label=title,color=color)
        ax.bar_label(bars,fmt='%.3f',padding=2)
    ax.set(xticks=x,xticklabels=names,ylim=(0,1.19),ylabel='Score (0–1)')
    ax.legend(loc='upper center',ncols=2,frameon=False)
    save(fig,'fig2_macro_comparison.png')

    runtime = rows('cpu_vs_hailo.csv')
    fig, ax = chart()
    for index, row in enumerate(runtime):
        for offset, key, color, label in [(-.16,'mean_ms',teal,'Mean'),(.16,'p95_ms',blue,'p95')]:
            value=float(row[key])
            ax.scatter(value,index+offset,s=70,color=color,label=label if index==0 else None)
            ax.annotate(f'{value:.2f}',(value,index+offset),xytext=(8,0),
                        textcoords='offset points',ha='left',va='center')
    ax.set(xscale='log',xlim=(9,1700),yticks=[0,1],yticklabels=['Pi ONNX CPU (35 calls)','Pi Hailo-8 (3,948 calls)'],
           ylim=(-.5,1.5),xlabel='Detector-path latency (ms, logarithmic)')
    ax.invert_yaxis()
    ax.legend(loc='center',frameon=False)
    save(fig,'fig3_latency_breakdown.png')

    hardware=json.loads((ROOT/'evidence/historical/METRICS.json').read_text(encoding='utf-8'))
    agreement=hardware['agreement']
    fig, ax = chart()
    bars=ax.barh(['Matched','INT8 only','FP32 only'],
                 [agreement['agreement_matches'],agreement['int8_only_detections'],
                  agreement['fp32_only_detections']],color=[teal,amber,blue])
    ax.bar_label(bars,padding=4); ax.set(xlim=(0,43),xlabel='Detections across 18 unannotated images')
    ax.invert_yaxis()
    save(fig,'fig4_quantization_parity.png')

    audit=json.loads((ROOT/'evidence/engineering_20261126/data_audit.json').read_text(encoding='utf-8'))
    fig, ax = chart()
    duplicate_counts=[len(audit['profiles'][r['profile']]['exact_decoded_duplicate_groups']) for r in data]
    bars=ax.bar(names,duplicate_counts,color=blue)
    ax.bar_label(bars,padding=3); ax.set(ylim=(0,5),ylabel='Exact decoded duplicate groups')
    ax.set_title('Selected demo libraries (full-dataset leakage unverified)',loc='left',fontsize=11)
    save(fig,'fig5_leakage_distribution.png')

    fig, ax = chart()
    for index, row in enumerate(data):
        normal_rate=100*float(row['normal_false_alarm_rate'])
        recall=100*float(row['recall'])
        ax.scatter(normal_rate,recall,s=85,color=[teal,blue,amber][index])
        ax.annotate(names[index],(normal_rate,recall),xytext=(8,3),textcoords='offset points')
    ax.set(xlim=(-.4,7),ylim=(0,105),xlabel='Observed normal false-alarm rate (%)',
           ylabel='Defect recall (%)',title='Frozen profile operating points')
    ax.grid(axis='y',alpha=.25)
    save(fig,'fig6_operational_tradeoff.png')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'evidence/judging')
    parser.add_argument('--figures',action='store_true',help='also plot stored metrics (requires matplotlib)')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    examples(args.output)
    if args.figures:
        plots(args.output)


if __name__ == '__main__':
    main()
