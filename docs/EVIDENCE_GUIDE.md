# Evidence guide: where the numbers came from

This is the source ledger for the [README](../README.md) and [full results](RESULTS.md). Paths are relative to this checkout. Absolute Pi paths inside raw records document the original experiment; they are not installation requirements.

## Five distinct evidence classes

1. **Original labeled evaluation:** model accuracy against held-out annotations. YOLO evaluator/frozen-threshold scores and EfficientAD category metrics belong here.
2. **Historical target experiments:** actual Pi CPU/Hailo latency, reference agreement and Llama candidate comparisons. Each experiment has its own denominator and scope.
3. **24 November target demonstration:** eight selected inspections and fresh native advice, with service-tree resource samples. This establishes selected-case integration, not unbiased accuracy.
4. **Regression/recovery verification:** artifact checks, code behavior, database restore and CPU smoke. Passing CI is not Hailo or camera execution.
5. **Screenshots:** actual Pi Chromium plus explicitly labeled physical-terminal replay of recorded outputs. Loading a saved result is not new inference.

## Source ledger

| Question | Original source | Fields and interpretation |
| --- | --- | --- |
| YOLO precision, recall, F1 and mAP? | [test_metrics.json](../evidence/historical/test_metrics.json) | `/mAP` is evaluator aggregate; `/per_class` stores seven Box-P, Box-R, Box-F1 and AP rows |
| YOLO deployment-threshold F1? | [test_metrics.json](../evidence/historical/test_metrics.json) | `/operating_point/per_class` stores TP/FP/FN. Derive F1 as `2TP/(2TP+FP+FN)`; sum counts before micro rates |
| Frozen thresholds? | [thresholds.json](../assets/thresholds.json) | Validation-selected class thresholds; unchanged for demonstrations |
| Actual completed YOLO epochs? | [Per-epoch CSV](../evidence/historical/yolo_results.csv), [arguments](../evidence/historical/yolo_args.yaml) | 134 completed rows versus configured maximum 150; historical console reported 3.232 hours |
| ONNX export check? | [export_status.json](../evidence/historical/export_status.json) | Eight-image raw-tensor parity; not labeled INT8 accuracy |
| Anomaly F1/confusion matrices? | [METRICS.json](../evidence/historical/METRICS.json) | `/anomaly_historical/<profile>`: original image/pixel rates, TN/FP/FN/TP, AUROC/AUPR/AUPRO |
| Anomaly training/threshold provenance? | [Pill](../models/anomaly/mvtec_pill/contract.json), [capsule](../models/anomaly/mvtec_capsule/contract.json), [VisA](../models/anomaly/visa_capsules/contract.json) | Steps, checkpoint/split fingerprints, calibration, contracts and retained evaluation |
| CPU versus Hailo comparison? | [METRICS.json](../evidence/historical/METRICS.json) | `/hardware/backends/onnx` and `/hailo`: 21 November repeated-image Pi trials; 35 versus 3,948 calls |
| Quantized accuracy before/after? | [METRICS.json](../evidence/historical/METRICS.json) | `/agreement`: 18 unannotated reference comparisons; `ground_truth_accuracy_verified:false` |
| Llama baseline/adaptive/3B comparison? | [BENCHMARKS.json](../evidence/historical/BENCHMARKS.json) | `/quality`: latency, native TTFT/decode, memory, experimental acceptance and final guard replay |
| Why adaptive-v1? | [model_selection.json](../evidence/historical/model_selection.json) | Existing 1B artifact; final replay 36/39 versus baseline 26/39; no expert semantic quality score |
| Exact final target outputs? | [eight_test_report.json](../evidence/target_20261124/eight_test_report.json) | `/selected_tests`, `/records`, `/samples`: eight IDs, detections, scores, actual advice and native/resource statistics |
| Final target resource totals? | [summary.json](../evidence/target_20261124/summary.json) | Full service-tree RSS/CPU; overlapping validation work; not isolated Llama memory |
| Visible model output/advice? | [Gallery](../evidence/gallery/README.md) | 47 captured screenshots linked to unchanged measured IDs |
| Frozen artifact identity? | [ARTIFACT_MANIFEST.json](../ARTIFACT_MANIFEST.json), [part manifest](../models/runtime-parts/manifest.json) | Exact byte lengths and SHA-256 hashes |
| Final evidence-release test count? | [Pi log](../evidence/gallery/target_regression_with_restore.txt), [laptop log](../evidence/gallery/regression_with_restore.txt) | 76 passing tests; older counts describe earlier stages |
| Published recovery actually works? | [Restored API verification](../evidence/gallery/restored_api_verification.json) | Eight records, original/annotated images, six heatmaps and stored advice through the application |

Historical documents retain their original dates, external paths and pending statements. The current [engineering report](SUBMISSION_REPORT.md) and actual target/recovery logs supersede those pending items only where execution is recorded. No old benchmark is relabeled as a fresh measurement.

## Regenerate the evidence tables

```sh
python tools/build_results_docs.py
python tools/build_results_docs.py --check
```

This standard-library generator builds [RESULTS.md](RESULTS.md), three local SVG charts and [eight CSVs plus summary JSON](../evidence/metrics/README.md). It never executes models or edits historical sources. Every CSV row includes `source` and `source_pointer`. The summary hashes input evidence and records derivation formulas. CSV rates are fractions; readable tables use percentages. Blank CSV cells mean unmeasured/not applicable, never zero.

Anomaly precision/recall/F1 are cross-checked against original confusion counts. CI verifies that published outputs agree with the sources. Original JSON remains authoritative over rounded headline values.

## Execute fresh selected-model tests

After [installation](QUICKSTART.md):

```sh
python tools/verify_repository_artifacts.py
python tools/smoke_models.py --output smoke_results.json
```

This executes two selected YOLO examples and one anomalous image from each EfficientAD profile on CPU. It is not an accuracy evaluation. A new laptop's runtime is not directly comparable to the original Pi benchmark.

For an installed Pi service with actual Hailo and native advisory:

```sh
~/medge-test
```

The source entry point is `python tools/medge_eight_demo.py`. It invokes the active service and writes new inspection IDs/outputs. Inspect `advice.status`, fallback reason and cache provenance before describing advice as fresh validated generation.

## Obtain a new labeled CPU / Hailo quality comparison

Supply the **same explicit image/YOLO-label pairs** to both backends. Every healthy image needs an explicitly empty `.txt` label; missing labels are not assumed normal. Stop the dashboard before acquiring Hailo in a separate process.

```sh
python tools/evaluate_labeled.py --images /path/to/images --labels /path/to/labels --backend onnx --dataset-note "Origin, fixed split and physical grouping limits" --output cpu_labeled.json
python tools/evaluate_labeled.py --images /path/to/images --labels /path/to/labels --backend hailo --dataset-note "Same fixed image/label pairs as CPU" --output hailo_labeled.json
```

This records image/label/model hashes and box counts at frozen thresholds and IoU 0.5. It is **not an mAP sweep**. Preserve the data manifest, hardware/software inventory, sampling scope and complete outputs. Only a completed labeled comparison supports a quantitative accuracy-before/after claim.

The original AP-sweep evaluator is retained in the [YOLO helper](../reproduction/yolo/blistertrace_final.py) and notebook. Reproducing it requires its original curated data/split; the selected demo library cannot substitute for those data.

## Measurement entry points

| Purpose | Tool | Requirement |
| --- | --- | --- |
| Native thread/load matrix | [benchmark_native_matrix.py](../tools/benchmark_native_matrix.py) | Actual model/runtime; fixed prompt, sampling and load configuration |
| Paired advisory scenarios | [evaluate_quality_50.py](../tools/evaluate_quality_50.py) | Actual runtime; automated guards do not replace semantic review |
| Original training/export | [reproduction](../reproduction/README.md) | Licensed original datasets, split/checkpoint/calibration metadata |
| Hailo recompilation | [compile_hef.sh](../reproduction/hailo/compile_hef.sh) | Licensed Linux x86-64 DFC and original training-only calibration collection |
| Eight-case service demo | [medge_eight_demo.py](../tools/medge_eight_demo.py) | Ready service and selected samples; not an accuracy estimate |
| CPU model smoke | [smoke_models.py](../tools/smoke_models.py) | Five selected cases; no Hailo or Llama claim |

Use each tool's `--help` and inspect its workload before a new benchmark. Record new experiments separately; never overwrite historical results with incompatible scopes.

## Definitions and interpretation

- **TTFT:** native callback time to first token; not browser time to receive a fully guarded response.
- **Decode tokens/s:** tokens after the first divided by decode interval, not total request duration.
- **RSS:** candidate-process memory and full service-tree memory have different scopes; tree sums may double-count shared pages.
- **CPU:** native/tree values use 100% per logical core and can exceed 100%. Historical detector percentages retain their original sampler convention.
- **Warm/cold:** a process cold start does not imply a cold filesystem page cache. A persistent worker removes repeated loading.
- **Guard acceptance:** JSON/schema/fact/SOP acceptance is not expert semantic or clinical accuracy. Adaptive 37/39 experimental acceptance becomes 36/39 with final guards.
- **Thermals:** the final status snapshot reached 80.4 C. Active cooling does not establish sustained thermal/endurance qualification.

**NOT TESTED:** labeled INT8 mAP delta, healthy-only YOLO specificity, local-camera/product accuracy, human semantic advisory quality, approved SOPs, power/energy, NPU utilization and eight-hour line endurance.
