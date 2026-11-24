"""Rebuild published metric tables from preserved evidence (standard library only).

This does not run inference, change thresholds, or overwrite historical evidence.
Use --check in CI to reject stale tables or changed source evidence.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
YOLO = 'evidence/historical/test_metrics.json'
METRICS = 'evidence/historical/METRICS.json'
BENCH = 'evidence/historical/BENCHMARKS.json'
TARGET = 'evidence/target_20261124/eight_test_report.json'
SUMMARY = 'evidence/target_20261124/summary.json'
PROFILES = ('mvtec_pill', 'mvtec_capsule', 'visa_capsules')


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding='utf-8-sig'))


def count_metrics(tp: int, fp: int, fn: int) -> dict:
    """Object-level rates; true negatives do not exist in this representation."""
    return {
        'precision': tp / (tp + fp) if tp + fp else None,
        'recall': tp / (tp + fn) if tp + fn else None,
        'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
        'f2': 5 * tp / (5 * tp + fp + 4 * fn) if 5 * tp + fp + 4 * fn else None,
    }


def csv_text(rows: list[dict]) -> str:
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def table(headers, rows) -> str:
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    return '\n'.join([
        '| ' + ' | '.join(map(cell, headers)) + ' |',
        '| ' + ' | '.join('---' for _ in headers) + ' |',
        *['| ' + ' | '.join(map(cell, row)) + ' |' for row in rows],
    ])


def pct(value):
    return 'Not measured' if value is None else f'{value * 100:.2f}%'


def number(value, digits=3):
    return 'Not measured' if value is None else f'{value:,.{digits}f}'


def bar_chart(title, subtitle, rows, unit, maximum, note):
    """Offline SVG, one scale per chart, explicit values and sample scopes."""
    height = 160 + 67 * len(rows)
    pieces = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}" role="img" aria-labelledby="title description">',
        f'<title id="title">{escape(title)}</title><desc id="description">{escape(subtitle + ". " + note)}</desc>',
        f'<rect width="1000" height="{height}" rx="16" fill="#101a2b"/>',
        '<g font-family="Arial, sans-serif" fill="#edf4ff">',
        f'<text x="32" y="38" font-size="23" font-weight="700">{escape(title)}</text>',
        f'<text x="32" y="65" font-size="14" fill="#b3c5db">{escape(subtitle)}</text>',
    ]
    for index, (label, value, color, annotation) in enumerate(rows):
        y = 94 + index * 67
        width = 530 * value / maximum
        pieces.extend([
            f'<text x="32" y="{y + 18}" font-size="16">{escape(label)}</text>',
            f'<rect x="245" y="{y}" width="530" height="24" rx="6" fill="#243249"/>',
            f'<rect x="245" y="{y}" width="{width:.3f}" height="24" rx="6" fill="{color}"/>',
            f'<text x="795" y="{y + 18}" font-size="17" font-weight="700">{value:.3f} {escape(unit)}</text>',
            f'<text x="245" y="{y + 43}" font-size="13" fill="#b3c5db">{escape(annotation)}</text>',
        ])
    pieces.extend([f'<text x="32" y="{height - 25}" font-size="13" fill="#b3c5db">{escape(note)}</text>', '</g></svg>'])
    return '\n'.join(pieces) + '\n'


def build() -> dict[str, str]:
    yolo, metrics, bench, target, summary = map(load, (YOLO, METRICS, BENCH, TARGET, SUMMARY))
    threshold_path = 'assets/thresholds.json'
    thresholds = load(threshold_path)
    source_paths = [YOLO, METRICS, BENCH, TARGET, SUMMARY, threshold_path]
    contracts = {}
    for profile in PROFILES:
        path = f'models/anomaly/{profile}/contract.json'
        contracts[profile] = load(path)
        source_paths.append(path)

    native = [dict(row, source=YOLO, source_pointer=f'/per_class/{i}',
                   scope='Original FP32 evaluator; not frozen deployment thresholds')
              for i, row in enumerate(yolo['per_class'])]
    operating = []
    for name, row in yolo['operating_point']['per_class'].items():
        operating.append(dict(
            class_name=name, threshold=thresholds[name]['threshold'], **row,
            f1=count_metrics(row['tp'], row['fp'], row['fn'])['f1'],
            source=YOLO, source_pointer=f'/operating_point/per_class/{name}',
            scope='Frozen per-class operating point; F1 derived from stored counts',
        ))
    tp, fp, fn = (sum(row[k] for row in operating) for k in ('tp', 'fp', 'fn'))
    micro = dict(class_name='micro_all', threshold='per-class', tp=tp, fp=fp, fn=fn,
                 support=tp + fn, **count_metrics(tp, fp, fn), source=YOLO,
                 source_pointer='/operating_point/per_class',
                 scope='Derived by summing class counts; not evaluator aggregate')
    # Keep CSV column order identical for class rows and the micro row.
    operating.append({key: micro[key] for key in operating[0]})

    anomaly_image, anomaly_pixel = [], []
    for profile in PROFILES:
        row = metrics['anomaly_historical'][profile]
        tn, fp, fn, tp = row['image_confusion_matrix_tn_fp_fn_tp']
        rates = count_metrics(tp, fp, fn)
        for key in ('precision', 'recall', 'f1'):
            if abs(rates[key] - row['image_' + key]) > 1e-12:
                raise ValueError(f'Inconsistent stored image metric: {profile}/{key}')
        anomaly_image.append(dict(
            profile=profile, images=row['images'], normal_images=row['images'] - row['defects'],
            defective_images=row['defects'], tn=tn, fp=fp, fn=fn, tp=tp,
            precision=row['image_precision'], recall=row['image_recall'], f1=row['image_f1'],
            auroc=row['image_auroc'], aupr=row['image_aupr'], accuracy=row['accuracy'],
            specificity=row['specificity'], normal_false_alarm_rate=row['normal_false_alarm_rate'],
            image_threshold=contracts[profile]['thresholds']['image'], source=METRICS,
            source_pointer=f'/anomaly_historical/{profile}', scope='Original labeled category held-out evaluation',
        ))
        tn, fp, fn, tp = row['pixel_confusion_matrix_tn_fp_fn_tp']
        anomaly_pixel.append(dict(
            profile=profile, annotated_images=row['annotated_images'], tn=tn, fp=fp, fn=fn, tp=tp,
            pixel_auroc=row['pixel_auroc'], pixel_f1=row['pixel_f1'], dice=row['dice'],
            aupro=row['aupro'], aupro_max_fpr=row['aupro_max_fpr'], aupro_steps=row['aupro_steps'],
            source=METRICS, source_pointer=f'/anomaly_historical/{profile}',
            scope='Original mask-based evaluation; pixel F1 is separate from image F1',
        ))
    hardware = []
    for backend, row in metrics['hardware']['backends'].items():
        hardware.append(dict(
            backend=backend, n=row['n'], seconds=row['seconds'], mean_ms=row['mean_ms'],
            p95_ms=row['p95_ms'], p99_ms=row['p99_ms'], throughput_images_s=row['throughput_images_s'],
            mean_cpu_percent=row['resources']['cpu_percent']['mean'],
            mean_rss_mib=row['resources']['rss_mib']['mean'], peak_rss_mib=row['resources']['rss_mib']['peak'],
            mean_temperature_c=row['resources']['temperature_c']['mean'],
            source=METRICS, source_pointer=f'/hardware/backends/{backend}',
            scope='21 November repeated-image backend benchmark; not live camera FPS',
        ))
    llama = []
    for name in ('1b_baseline', '1b_adaptive_v1', '3b_baseline'):
        row = bench['quality'][name]
        llama.append(dict(
            candidate=name, scenarios=row['total_scenarios'], bounded_cases=row['bounded_cases'],
            experiment_guard_validated=row['validated'], final_guard_accepted=row['final_guard_accepted'],
            latency_samples=row['elapsed_ms']['n'], median_ms=row['elapsed_ms']['median'],
            p95_ms=row['elapsed_ms']['p95'], median_callback_ttft_ms=row['stages']['callback_ttft_ms']['median'],
            median_decode_tokens_s=row['decode_tps']['median'], peak_rss_mib=row['peak_rss_mib'],
            mean_process_cpu_percent=(row.get('process_cpu_percent') or {}).get('mean'),
            source=BENCH, source_pointer=f'/quality/{name}',
            scope='Historical paired comparison; timings predate final JSON stop boundary; no semantic accuracy claim',
        ))
    cases, advice_rows = [], []
    for index, (selected, record) in enumerate(zip(target['selected_tests'], target['records'])):
        if selected['inspection_id'] != record['inspection_id']:
            raise ValueError('Target selection and record identity differ')
        advice = record['advice']
        anomaly = record.get('anomaly', {})
        observation = (f"score {anomaly['score']:.6f} / threshold {anomaly['threshold']:.6f}" if anomaly
                       else ', '.join(f"{d['type']} {d['confidence']:.5f}" for d in record['detections']) or 'No configured defect')
        cases.append(dict(
            case=selected['test'], title=selected['title'], inspection_id=record['inspection_id'],
            backend=record['backend'], visual_result=record['visual_result']['status'],
            qa_decision=record['decision'], observation=observation,
            anomaly_score=anomaly.get('score'), anomaly_threshold=anomaly.get('threshold'),
            vision_ms=record['vision_ms'], advisory_ms=advice['elapsed_ms'],
            advisory_status=advice['status'], expected=selected['expected'], matched=selected['matched'],
            source=TARGET, source_pointer=f'/records/{index}', scope='Selected 24 November target functional test, not accuracy estimate',
        ))
        advice_rows.append(dict(
            case=selected['test'], inspection_id=record['inspection_id'], status=advice['status'],
            clause_id=advice['advisory']['clause_id'], action_id=advice['advisory']['action_id'],
            operator_message=advice['advisory']['operator_message'], qa_note=advice['advisory']['qa_note'],
            prompt_mode=advice['prompt_mode'], prompt_tokens=advice['prompt_tokens'],
            generated_tokens=advice['runtime_metrics']['generated_tokens'],
            callback_ttft_ms=advice['runtime_metrics']['callback_ttft_ms'],
            source=TARGET, source_pointer=f'/records/{index}/advice',
        ))
    source_index = [dict(path=path, sha256=hashlib.sha256((ROOT / path).read_bytes()).hexdigest()) for path in source_paths]
    data = dict(
        schema_version=1, generated_by='python tools/build_results_docs.py',
        scope='Reformatted stored evidence. No inference or training was run by this generator.',
        units='Rates are fractions [0,1]; times ms unless named seconds; memory MiB.',
        derivations=dict(f1='2*TP/(2*TP+FP+FN)', precision='TP/(TP+FP)', recall='TP/(TP+FN)',
                         f2='5*TP/(5*TP+FP+4*FN)', micro='Sum class TP, FP, FN before computing rates'),
        sources=source_index, yolo_evaluator_aggregate=yolo['mAP'], yolo_evaluator_classes=native,
        yolo_operating_point=operating, anomaly_image=anomaly_image, anomaly_pixel=anomaly_pixel,
        hardware=hardware, quantization_agreement=metrics['agreement'],
        llama_historical=llama, target_selected_cases=cases, target_advisory_outputs=advice_rows,
        target_summary=summary,
        unmeasured=['Labeled INT8 held-out mAP delta', 'Healthy-only YOLO specificity',
                    'Human-judged Llama recommendation accuracy', 'Production camera domain accuracy',
                    'Power/energy', 'NPU utilization', 'Eight-hour line endurance'],
    )
    outputs = {'evidence/metrics/summary.json': json.dumps(data, indent=2, ensure_ascii=False) + '\n'}
    for name, rows in [('yolo_evaluator', native), ('yolo_operating_point', operating),
                       ('anomaly_image', anomaly_image), ('anomaly_pixel', anomaly_pixel),
                       ('cpu_vs_hailo', hardware), ('llama_comparison', llama),
                       ('target_eight_cases', cases), ('target_advisory_outputs', advice_rows)]:
        outputs[f'evidence/metrics/{name}.csv'] = csv_text(rows)

    sections = [
        '# Results and benchmark evidence',
        '> Generated from preserved JSON and frozen contracts by `python tools/build_results_docs.py`. '
        'This page publishes existing measurements and explicitly labeled arithmetic; it does not rerun models. '
        'Run `python tools/build_results_docs.py --check` to verify it.',
        '## Read the experiments separately',
        table(['Experiment', 'What it measures', 'Original evidence'], [
            ['YOLO original labeled test', '1,303 images / 2,956 boxes; FP32 evaluator and separate fixed-threshold counts', '[test_metrics.json](../' + YOLO + ')'],
            ['Anomaly original labeled tests', 'Image decisions and mask-based localization for three category profiles', '[METRICS.json / anomaly_historical](../' + METRICS + ')'],
            ['21 Nov CPU / Hailo', 'Repeated-image detector latency/resources; unequal trial counts', '[METRICS.json / hardware](../' + METRICS + ')'],
            ['FP32 / INT8 agreement', '18 unannotated reference-comparison images, not labeled accuracy', '[METRICS.json / agreement](../' + METRICS + ')'],
            ['Historical Llama candidates', 'Paired scenario validation and instrumented latency; final guard replay separate', '[BENCHMARKS.json / quality](../' + BENCH + ')'],
            ['24 Nov complete station', 'Eight selected outcomes plus eight fresh on-device advisory responses', '[eight_test_report.json](../' + TARGET + ')'],
        ]),
        'All rates in the tables below are percentages except AUROC/AUPR/AUPRO, which are fractions. '
        'CSV/JSON exports retain full precision. **None of the selected demo results is a population accuracy estimate.**',
        '## 1. YOLOv8s: original FP32 held-out evaluator',
        f"Aggregate evaluator precision **{pct(yolo['mAP']['metrics/precision(B)'])}**, recall **{pct(yolo['mAP']['metrics/recall(B)'])}**, "
        f"mAP50 **{pct(yolo['mAP']['metrics/mAP50(B)'])}**, mAP50-95 **{pct(yolo['mAP']['metrics/mAP50-95(B)'])}**. "
        'The stored evaluator Box-F1 values below are retained verbatim before display rounding. '
        'They do not describe the frozen deployment thresholds in the next table.',
        table(['Class', 'Images*', 'Instances', 'Precision', 'Recall', 'Box-F1', 'mAP50', 'mAP50-95'],
              [[r['Class'], r['Images'], r['Instances'], *[pct(r[k]) for k in ('Box-P', 'Box-R', 'Box-F1', 'mAP50', 'mAP50-95')]] for r in native]),
        '*A multi-class image can appear in more than one class count. Do not sum class image counts. '
        'The curated split excludes unresolved conflicts/invalid families and uses source-family/perceptual grouping; '
        'it is not the publisher benchmark and does not prove physical strip independence. '
        '**No normal-only images occur in this test. Healthy specificity and false-reject rate are not established.**',
        '## 2. YOLO: fixed class-threshold operating point',
        'Precision, recall and F2 are stored historical values. **F1 is derived** from the recorded TP/FP/FN. '
        'The micro row sums those counts before computing its rates; it is not the evaluator aggregate above. '
        'Thresholds are the unchanged [deployment values](../assets/thresholds.json), selected using validation rather than this table.',
        table(['Class', 'Threshold', 'TP', 'FP', 'FN', 'Precision', 'Recall', 'F1 (derived)', 'F2'],
              [[r['class_name'], r['threshold'], r['tp'], r['fp'], r['fn'], *[pct(r[k]) for k in ('precision', 'recall', 'f1', 'f2')]] for r in operating]),
        '`Precision = TP/(TP+FP)`; `Recall = TP/(TP+FN)`; `F1 = 2TP/(2TP+FP+FN)`; '
        '`F2 = 5TP/(5TP+FP+4FN)`. Object matching and image decisions are different units. '
        'The historical image-level operating point recorded **6 false-pass images / 1,303 defective images (0.4605%)**. '
        'With zero healthy images, its healthy false-hold rate is undefined, not zero. '
        '[Download fixed-threshold CSV](../evidence/metrics/yolo_operating_point.csv).',
        '## 3. EfficientAD-S: labeled image-level results',
        'These are three independent normal-only trained category models, not EfficientNet and not seven-class YOLO. '
        'Each completed 70,000 FP32 steps with batch size 1. Checkpoint selection/map normalization and threshold calibration '
        'use separate normal subsets; test data are held out. Normal calibration quantile is 0.995. '
        'The scalar anomaly score is not a probability.',
        table(['Profile', 'Test / normal / defect', 'Precision', 'Recall', 'F1', 'AUROC', 'AUPR', 'Accuracy', 'Normal FAR'],
              [[r['profile'], f"{r['images']} / {r['normal_images']} / {r['defective_images']}",
                pct(r['precision']), pct(r['recall']), pct(r['f1']), number(r['auroc'], 4), number(r['aupr'], 4),
                pct(r['accuracy']), pct(r['normal_false_alarm_rate'])] for r in anomaly_image]),
        table(['Profile', 'TN', 'FP', 'FN', 'TP', 'Image threshold', 'Specificity'],
              [[r['profile'], r['tn'], r['fp'], r['fn'], r['tp'], number(r['image_threshold'], 6), pct(r['specificity'])] for r in anomaly_image]),
        '**Interpretation:** pill and capsule perform better than VisA at their saved operating points. '
        'VisA misses 76 of 100 anomalous test images (recall 24%); it remains a weak research/demo profile. '
        'High pixel AUROC does not repair its poor image-level recall. A 0/26 observed false-alarm count for pill '
        'does not prove zero future false alarms. No selected demo image was used to tune these thresholds.',
        '## 4. Anomaly localization: mask-based results',
        table(['Profile', 'Annotated images', 'Pixel AUROC', 'Pixel F1 / Dice', 'AUPRO (FPR <= 0.3)'],
              [[r['profile'], r['annotated_images'], number(r['pixel_auroc'], 4), pct(r['pixel_f1']), number(r['aupro'], 4)] for r in anomaly_pixel]),
        'AUPRO uses 200 threshold steps and maximum false-positive rate 0.3. Pixel F1/Dice compares foreground masks, '
        'not image classification or bounding-box mAP. Raw pixel TN/FP/FN/TP are in '
        '[anomaly_pixel.csv](../evidence/metrics/anomaly_pixel.csv).',
        '## 5. Actual Pi detector benchmark: CPU versus Hailo-8',
        '21 November 2026. Same unannotated training-source demonstration images, repeated for timing. '
        'CPU and Hailo trials have different sample counts/durations. No camera was available for this experiment. '
        '**This is detector-path performance, not live-camera FPS, full inspection+Llama throughput, or production-line capacity.**',
        table(['Backend', 'Calls', 'Duration (s)', 'Mean (ms)', 'P95 (ms)', 'P99 (ms)', 'Calls/s', 'Mean CPU*', 'Mean RSS (MiB)', 'Mean temp (C)'],
              [[r['backend'], r['n'], number(r['seconds']), number(r['mean_ms']), number(r['p95_ms']),
                number(r['p99_ms']), number(r['throughput_images_s']), number(r['mean_cpu_percent'], 2) + '%',
                number(r['mean_rss_mib'], 2), number(r['mean_temperature_c'], 2)] for r in hardware]),
        f"Mean-latency ratio: **{metrics['speedup']:.2f}x** (CPU mean / Hailo mean). "
        '*CPU percentages retain the original sampler convention; do not compare them directly with the process-tree '
        'CPU sums in the final station test. [Machine-readable comparison](../evidence/metrics/cpu_vs_hailo.csv).',
        '![Measured detector latency](assets/cpu_vs_hailo.svg)',
        '## 6. Quantization and export: what was verified',
        table(['Check', 'Recorded outcome', 'Status'], [
            ['FP32 export', 'Eight validation images; raw output [1,11,8400]; opset 11; maximum recorded absolute difference 0.003753662109375', 'PASS: raw-tensor parity check'],
            ['Hailo-8 deployment', 'Frozen INT8 HEF actually loaded and executed on HailoRT', 'PASS: execution'],
            ['Reference agreement', '18 images; 37 matched, 2 INT8-only, 1 FP32-only detections; agreement P 94.87%, R 97.37%', 'Measured model agreement only'],
            ['Labeled FP32 versus INT8 accuracy delta', 'Same labeled held-out dataset was not evaluated on both backends', 'NOT TESTED'],
        ]),
        'The raw tensor difference is not an accuracy drop. Reference-agreement precision/recall is not ground-truth '
        'defect precision/recall. No post-quantization mAP, F1 or accuracy prediction is substituted. '
        '[Export record](../evidence/historical/export_status.json); '
        '[compilation/preprocessing methodology](MODEL_LIFECYCLE.md).',
        '## 7. ExecuTorch Llama: candidate and prompt comparison',
        'Historical paired 50-scenario experiment: 39 bounded advisory inputs and 11 invalid inputs. '
        'Elapsed/TTFT summaries contain 38 timed samples and decode summaries 39; preserve those differing denominators. '
        'These timings predate the final native first-JSON-object stop boundary. '
        '**Acceptance means schema/evidence/SOP guard acceptance, not human-judged recommendation accuracy or classification F1.**',
        table(['Candidate', 'Median (s)', 'P95 (s)', 'Median callback TTFT (s)', 'Median decode tokens/s', 'Peak RSS (MiB)', 'Experiment accepted', 'Final guard replay'],
              [[r['candidate'], number(r['median_ms']/1000), number(r['p95_ms']/1000),
                number(r['median_callback_ttft_ms']/1000), number(r['median_decode_tokens_s']),
                number(r['peak_rss_mib'], 2), f"{r['experiment_guard_validated']}/{r['bounded_cases']}",
                f"{r['final_guard_accepted']}/{r['bounded_cases']}"] for r in llama]),
        'The baseline 1B RSS was not recorded; it is not zero. Adaptive-v1 final-guard replay accepted 36/39, '
        'rather than the experimental 37/39. Selection preserves the existing 1B SpinQuant INT4 EO8 artifact, '
        'three threads, 128-token output limit and 1,536-token prompt budget under a 2,048-token exported context. '
        'Persistent workers, bounded queue/cache and JSON stopping reduce repeated work. '
        'Human semantic review remains incomplete. [Full optimization notes](LLAMA_EXECUTORCH_OPTIMIZATION.md).',
        '![Historical Llama comparison](assets/llama_latency.svg)',
        '## 8. Complete station: actual 24 November execution',
        'Raspberry Pi 5, Hailo-8 YOLO, Arm CPU anomaly/ExecuTorch advisory. '
        'Each of eight selected cases matched its expected visual outcome and produced a fresh `llama_validated` '
        'response; cache reuse was zero. **Selected demonstration cases are not an unbiased test set.** '
        'The stored QA decision is separate from the visual model check.',
        table(['Case', 'Pipeline / selected case', 'Visual', 'QA', 'Vision (ms)', 'Advice (ms)', 'Observation'],
              [[r['case'], r['title'], r['visual_result'], r['qa_decision'], number(r['vision_ms'], 2),
                number(r['advisory_ms'], 1), r['observation']] for r in cases]),
        f"Advisory median **{summary['advisory_median_ms']/1000:.4f} s**; range "
        f"{summary['advisory_min_ms']/1000:.4f}-{summary['advisory_max_ms']/1000:.4f} s. "
        f"Service-tree peak RSS **{summary['peak_service_tree_rss_mib']:.2f} MiB**; "
        f"peak summed CPU **{summary['peak_service_tree_cpu_percent']:.1f}%**, where 100% is one logical core. "
        'Shared pages can be counted more than once. Regression/dependency validation overlapped the run; '
        'these are observed demo timings, not an isolated optimal-performance comparison. '
        'The first request also includes worker startup in application elapsed time.',
        '### Actual advisory outputs',
        'These messages are copied from the measured records, not rewritten example recommendations. '
        'All use the unapproved demo SOP `BT-DEMO-SOP-01`; authorized QA retains disposition authority.',
        table(['Case', 'SOP clause', 'Action', 'Actual operator message'],
              [[r['case'], r['clause_id'], r['action_id'], r['operator_message']] for r in advice_rows]),
        'The [original JSON](../' + TARGET + ') also preserves each inspection ID, bounding boxes, '
        'hashes, prompt/generated token counts, callback TTFT, raw response, validation trace and QA note. '
        'See [target_advisory_outputs.csv](../evidence/metrics/target_advisory_outputs.csv) and the '
        '[47-image actual Pi screenshot gallery](../evidence/gallery/README.md). Terminal screenshots are '
        'explicitly labeled replay of recorded outputs, not a second inference run.',
        '## 9. Measurement and reproduction map',
        table(['Task', 'Entry point', 'Prerequisites / boundary'], [
            ['Original YOLO training/evaluation', '[Notebook and helper](../reproduction/yolo)', 'Original dataset, split and licensed training environment; not needed for inference'],
            ['Original anomaly training', '[Three independent notebooks](../reproduction/anomaly/notebooks)', 'Publisher datasets; full training separate from selected demo tests'],
            ['Anomaly ONNX export', '[export_deployment.py](../reproduction/anomaly/export_deployment.py)', 'Final checkpoints and normalization/threshold metadata'],
            ['Hailo compilation', '[compile_hef.sh](../reproduction/hailo/compile_hef.sh)', 'Licensed Linux x86-64 DFC; original training-only calibration data; included HEF avoids recompilation'],
            ['New frozen-threshold labeled comparison', '[evaluate_labeled.py](../tools/evaluate_labeled.py)', 'Explicit labels for every image; empty label = normal; one Hailo owner; not an mAP sweep'],
            ['Native thread/load timing', '[benchmark_native_matrix.py](../tools/benchmark_native_matrix.py)', 'Actual native runtime/model; fixed workload and sampling protocol'],
            ['Paired advisory guard evaluation', '[evaluate_quality_50.py](../tools/evaluate_quality_50.py)', 'Actual runtime and scenarios; automated guard checks are not semantic review'],
            ['Eight-case service demonstration', '[medge_eight_demo.py](../tools/medge_eight_demo.py)', 'Running service; selected examples; writes fresh IDs and outputs'],
            ['CPU model smoke', '[smoke_models.py](../tools/smoke_models.py)', 'Five selected cases; CPU only; not Hailo or Llama validation'],
            ['Regenerate this evidence view', '[build_results_docs.py](../tools/build_results_docs.py)', 'Python standard library; reads saved evidence only'],
        ]),
        '## 10. Downloads, integrity and missing measurements',
        'Browse [all derived CSVs and JSON](../evidence/metrics). Every CSV row links to its original source path '
        'and JSON pointer. The JSON summary hashes each source file and records derivation formulas. '
        'Original evidence is never overwritten. The [source ledger](EVIDENCE_GUIDE.md) explains experiment scopes '
        'and provides exact reproduction commands.',
        'NOT TESTED: labeled INT8 accuracy delta, healthy-only YOLO specificity, approved-SOP/human semantic '
        'advisory quality, new-product/camera generalization, power/energy, NPU utilization and eight-hour line '
        'endurance. Historical benchmarks, current selected tests and CI are distinct evidence classes.',
    ]
    outputs['docs/RESULTS.md'] = '\n\n'.join(sections) + '\n'
    outputs['docs/assets/cpu_vs_hailo.svg'] = bar_chart(
        'YOLO detector latency: CPU vs Hailo-8', 'Actual Raspberry Pi benchmark | 21 November 2026 | lower is faster',
        [('ONNX CPU', hardware[0]['mean_ms'], '#98a7ff', '35 calls / 20.30 s'),
         ('Hailo-8 INT8', hardware[1]['mean_ms'], '#48d9ce', '3,948 calls / 60.01 s')],
        'ms', 600, 'Repeated-image detector path; unequal trials. Not camera FPS or complete line throughput.')
    outputs['docs/assets/llama_latency.svg'] = bar_chart(
        'Llama advisory: historical median elapsed time', 'Actual Arm ExecuTorch paired scenarios | lower is faster',
        [(r['candidate'], r['median_ms']/1000, '#48d9ce' if r['candidate']=='1b_adaptive_v1' else '#b39dff',
          f"38 latency samples; final guard replay {r['final_guard_accepted']}/39") for r in llama],
        's', 40, 'Timings predate final JSON stop boundary. Guard acceptance is not semantic accuracy.')
    outputs['docs/assets/anomaly_f1.svg'] = bar_chart(
        'Anomaly image-level F1 at saved thresholds', 'Original labeled held-out category tests | higher is better',
        [(r['profile'], r['f1']*100, '#f1ba63' if r['profile']=='visa_capsules' else '#48d9ce',
          f"{r['images']} images; recall {r['recall']*100:.2f}%") for r in anomaly_image],
        '%', 100, 'Category-specific models. Selected demos do not replace these full held-out results.')
    outputs['evidence/metrics/README.md'] = (
        '# Metric exports\n\n'
        'Generated deterministically from preserved source evidence; no fresh inference. '
        '[Readable results and interpretation](../../docs/RESULTS.md) · '
        '[Experiment/source ledger](../../docs/EVIDENCE_GUIDE.md).\n\n'
        'Rates are fractions, times milliseconds unless named otherwise, and memory MiB. '
        'CSV `source` / `source_pointer` fields identify each original JSON record. '
        '`summary.json` includes input SHA-256 hashes, formulas, scopes and missing measurements. '
        'Empty CSV cells mean unmeasured/not applicable, never zero.\n\n'
        '```sh\npython tools/build_results_docs.py\npython tools/build_results_docs.py --check\n```\n\n'
        + '\n'.join(f'- [{Path(path).name}]({Path(path).name})' for path in outputs if path.startswith('evidence/metrics/')) + '\n'
    )
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail on stale/missing generated files; do not write')
    args = parser.parse_args()
    outputs = build()
    stale = []
    for relative, content in outputs.items():
        path = ROOT / relative
        encoded = content.encode('utf-8')
        if args.check:
            # Text checkout line endings may differ across platforms.
            if not path.exists() or path.read_text(encoding='utf-8').replace('\r\n', '\n') != content:
                stale.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(encoded)
    if stale:
        print('STALE: ' + '\nSTALE: '.join(stale))
        return 1
    print(f"{'Verified' if args.check else 'Generated'} {len(outputs)} evidence views; historical sources unchanged.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
