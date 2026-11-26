# Software and evaluation upgrade — 26 November 2026

**Baseline:** commit `90302af`. **Environment:** Windows x86-64, Python 3.11, ONNX Runtime CPU. No CUDA device available. The last known Pi address timed out over SSH. No new hardware was requested, no Hailo result was simulated, and no original evidence was overwritten.

**Outcome:** a measured CPU post-processing optimization, corrected anomaly configuration traceability, fail-closed anomaly input validation, a reproducible retained-data audit and expanded evaluation tooling. **No model-accuracy improvement is claimed.** Trained weights, model contracts, deployment thresholds and QA policy remain unchanged.

## Repository audit

This is a repository-wide component inventory with targeted review of deployment and evidence-critical code, not a formal exhaustive security certification.

| Area | Finding | Implemented action / remaining boundary |
| --- | --- | --- |
| Data and labels | Checkout contains selected demos and synthetic warning images, not the complete raw training corpus | Read-only sample/hash audit; historical manifests restored from backup ZIPs with receipts. No demo data used for fitting |
| Train/validation/test | Preserved manifests have no repeated path identities across splits | Full byte/perceptual or physical-strip leakage cannot be ruled out without original images and group IDs |
| YOLO class balance | Historical test support ranges from 111 dual-cap to 634 empty instances (5.71x); training labels unavailable | Test imbalance reported, not used to select a training sampler. New dataset auditor checks missing/invalid/duplicate boxes and decoded cross-split duplicates |
| YOLO runtime | Per-frame threshold selection performed 8,400 Python dictionary lookups | Seven-entry vector lookup, retaining float64 comparison semantics and exact output parity in paired execution |
| EfficientAD | Independent profile contracts; normalization correctly remains inside ONNX | Input validation and stage timing added. No unvalidated crop/resize or normalization change |
| VisA | Held-out recall 24%, F1 38.40%, AUROC 0.65017; normal and defect score distributions overlap strongly | Frozen threshold retained. No post-hoc test tuning or claim that balanced demos fix the model |
| Hailo | Frozen seven-class NMS HEF, uint8 RGB input, no silent fallback | Model hash verified; new hardware execution NOT TESTED |
| ExecuTorch | Adaptive-v1, bounded prompt/output, independent worker, guarded SOP advice | Policy unchanged. Native generation NOT TESTED on this Windows run; historical Arm evidence remains separate |
| Dashboard | Real/mock adapters separated; asynchronous advice pinned to an inspection; status polling | Existing UI retained. No claimed browser FPS or rendering improvement in this change |
| Traceability | Anomaly configuration revision previously described YOLO preprocessing and did not bind anomaly thresholds | New anomaly records include profile/model/image threshold/pixel threshold/preprocessing in the configuration hash; existing records untouched |
| QA workflow | Clear visual result can coexist with QA REVIEW; Llama cannot override verdict | Preserved and regression-tested. Demo labels do not change model observations |
| Offline/recovery | Local inference with explicit external provisioning; hash-checked portable backup | Model materialization, CPU inference and fresh-destination restore executed |

## Data audit and independent metric recomputation

The [audit JSON](../evidence/engineering_20261126/data_audit.json) is generated from retained manifests, byte-preserved historical score files and the shipped sample libraries. [Archive receipts](../evidence/engineering_20261126/archive_receipts.json) bind extracted member bytes to original archive hashes. Re-running the audit does not need the private ZIPs.

| Profile | Train / normal-val / calibration / test | Exact decoded duplicate groups in demo library | Historical test specificity | Historical test FNR | Historical test F1 |
| --- | --- | --- | --- | --- | --- |
| MVTec pill | 187 / 40 / 40 / 167 | 4 | 100.00% (26 normals) | 14.18% | 92.37% |
| MVTec capsule | 153 / 33 / 33 / 132 | 4 | 95.65% (23 normals) | 20.18% | 88.32% |
| VisA capsules | 380 / 81 / 81 / 160 | 2 | 98.33% (60 normals) | 76.00% | 38.40% |

These are **recomputed historical metrics**, not new inference results or improved models. Confusion counts and rank-based AUROC agree with the frozen contracts. Near-duplicate dHash candidates are flagged for review only: similar capsules can look alike without being duplicate photographs.

The 0.995 normal-quantile calibration uses only 33–81 images per profile. Empirical tail resolution is approximately 3.03%–1.23%; this does not establish a 0.5% population false-alarm guarantee. New calibration tooling records sample count and rejects test rows, defect rows and duplicate identities.

### Why retraining, threshold replacement and fusion were not promoted

- Original train/validation/calibration pixels and original YOLO labels are absent from the available retained project data. The recovery archives contain checkpoints, split identities and historical evaluation scores, not the raw training images.
- The local demo subsets were selected after inference and include aliases and synthetic acquisition failures. They are unsuitable for independent tuning or model selection.
- Changing preprocessing without matching calibration would invalidate existing thresholds.
- YOLO blister images and category anomaly images are not a common paired product-domain evaluation set. A fusion advantage cannot be estimated by combining their independent metrics.
- No weights were retrained, no thresholds were changed, and no improved accuracy/fusion result was claimed. Original notebooks remain the training path once the licensed raw datasets are restored.

## Measured software results

[Raw paired execution](../evidence/engineering_20261126/cpu_benchmark.json): two identical selected images, two warmup calls per engine, six repetitions, alternating baseline/candidate order, **12 observations per variant**. Detector sessions coexist in this experiment. All 12 paired detection lists were exactly equal.

| Measurement | Baseline | Candidate | Interpretation |
| --- | --- | --- | --- |
| CPU detector p50 | 608.374 ms | 551.827 ms | Observed local run; not a Pi forecast |
| CPU detector p95 | 878.525 ms | 818.293 ms | Small sample with substantial host variability |
| CPU detector mean | 598.330 ms | 524.470 ms | No statistical superiority claim |
| Threshold lookup p50 | 2.55645 ms | 0.03180 ms | 1,000 iterations on seeded simulated class IDs; isolated stage timing, not inference |
| Threshold lookup p95 | 4.02617 ms | 0.05882 ms | Actual CPU execution of equivalent lookup operations |
| Model / threshold changes | None | None | Frozen artifact hashes unchanged |

Only the isolated lookup cost reduction is directly attributable to the code change; the larger whole-detector difference must not be attributed entirely to it. A preserved [exploratory run](../evidence/engineering_20261126/cpu_benchmark_exploratory_cached.json) used a constructor-cached vector and overlapped regression activity; that candidate was revised to rebuild seven entries per call for compatibility with existing detector fixtures and mutable configuration. It is not the final benchmark.

Anomaly timing now separates preprocessing, queue wait, session preparation, inference, overlay/post-processing and total time. The existing `elapsed_ms` field retains its prior meaning (excluding overlay). Cold loads and three warm samples per profile are recorded in the CPU benchmark. These variable host timings are diagnostic observations, not an anomaly performance improvement.

[Persisted-verdict measurement](../evidence/engineering_20261126/verdict_benchmark.json): six CPU service calls, **p50 275.117 ms / p95 300.818 ms**, including QA rules, annotation, image writes, SQLite and explicit advisory-disabled fallback recording. It excludes capture, HTTP/browser, and native Llama generation. It ran separately with one detector session; **do not subtract it from the dual-session detector experiment to estimate overhead**. No before/after complete-service speedup is claimed.

## Verification

| Check | Result | Evidence |
| --- | --- | --- |
| Full Python regression suite | **PASS — 95 tests**, up from historical 76 | [Run log](../evidence/engineering_20261126/regression.txt) |
| Actual CPU inference, four model paths / five selected cases | **PASS** | [Smoke outputs](../evidence/engineering_20261126/cpu_smoke.json) |
| Paired detector-output parity | **PASS — 12/12** | [Timing and parity rows](../evidence/engineering_20261126/cpu_benchmark.json) |
| Historical anomaly counts and AUROC recomputation | **PASS — all three profiles** | [Audit](../evidence/engineering_20261126/data_audit.json) |
| Existing generated metric views | **PASS — 14 verified**, original records unchanged | `python tools/build_results_docs.py --check` |
| Portable backup restore | **PASS** | [Restore verification](../evidence/engineering_20261126/restore_verification.json) |
| Native C++ JSON-boundary tests | **PASS — compiled and executed locally**, exit 0 | `g++ -std=c++17 tests/json_boundary_test.cpp -o json_boundary_test` followed by execution; no Arm runtime claim |
| New accuracy, independent fusion gain, new AUPRO | **NOT TESTED** | Original full images/masks and paired product data unavailable |
| New Pi/Hailo/Arm Llama execution | **NOT TESTED** | SSH timeout; no local Hailo/Arm target |
| Browser frame time, power, production endurance | **NOT TESTED** | No new measurements |

Synthetic unit fixtures test metric definitions and failure handling; they are never reported as model accuracy. One upstream Starlette/httpx deprecation warning remains. Existing historical Pi results are preserved, not relabeled as this run.

## Exact reproduction commands

From a clone with dependencies installed as in [QUICKSTART](QUICKSTART.md):

```sh
python tools/verify_repository_artifacts.py
python tools/audit_retained_data.py
python -m pytest tests -q
python tools/build_results_docs.py --check
python tools/smoke_models.py --output cpu_smoke.json
python tools/benchmark_cpu_upgrade.py --baseline 90302af --repeats 6 --output cpu_benchmark.json
python tools/benchmark_verdict.py --repeats 3 --output verdict_benchmark.json
python tools/restore_demo_backup.py --output ../medge-restored-new
```

The restore destination must not exist. Timing values will differ by machine and load. The benchmark loads the trusted historical detector source from Git; use a full clone containing baseline `90302af`. CPU benchmarks do not need CUDA or Hailo. The benchmark creates temporary station data and explicitly disables Llama; it never edits the operator database.

For restored full datasets and future independent experiments:

```sh
python tools/audit_yolo_dataset.py --root /path/to/yolo_dataset --output dataset_audit.json
python tools/calibrate_anomaly_scores.py --input calibration_scores.json --quantile 0.995 --output candidate_threshold.json
python tools/compare_scores.py --baseline baseline_scores.json --candidate candidate_scores.json --output paired_comparison.json
python tools/detection_ap.py --predictions low_confidence_predictions.json --output box_ap.json
python tools/evaluate_labeled.py --images /path/to/images/test --labels /path/to/labels/test --backend onnx --dataset-note "Describe source and independent grouping" --output operating_point.json
```

Input schemas are in each tool's module documentation / `--help`. Comparison rejects different image or label identities and calibration/test overlap. AP uses an explicit custom 101-point interpolation protocol over IoU .50:.95, **not a claim of official COCO/Ultralytics equivalence**. It requires low-confidence predictions; deployed high-threshold predictions cannot establish a full PR sweep. Existing historical mAP and AUPRO remain unchanged. The dataset auditor writes only an eligible exact-deduplicated training manifest; it never deletes images, relabels boxes or resplits test data.

## Changed files

- Runtime: `app/vision.py`, `app/anomaly.py`, `app/traceability.py`.
- Evaluation: `tools/evaluation_protocol.py`, `tools/compare_scores.py`, `tools/detection_ap.py`, `tools/evaluate_labeled.py`, `tools/calibrate_anomaly_scores.py`.
- Data audit: `tools/audit_retained_data.py`, `tools/audit_yolo_dataset.py`.
- Measurements: `tools/benchmark_cpu_upgrade.py`, `tools/benchmark_verdict.py`.
- Tests: `tests/test_evaluation_protocol.py`, `tests/test_anomaly_policy.py`.
- Reproducibility: `.gitattributes`, `.github/workflows/tests.yml`, `evidence/engineering_20261126/`.
- Documentation: this report, `README.md`, `docs/README.md`.

The previous checkout's unrelated uncommitted UI changes were preserved by working in a separate Git worktree. This release strengthens measured software efficiency and evaluation integrity; it does not certify industrial readiness or claim superiority over other teams' incomparable benchmarks.
