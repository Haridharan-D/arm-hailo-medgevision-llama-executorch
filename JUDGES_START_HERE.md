# MEDGE VISION — judges' evidence guide

**Bharat AI-SoC Challenge 2026–27 · Team Medge Vision**  
Haridharan D (Team leader), Priyadharsan D, Jayaraj M

## Assess the project in three minutes

1. **Understand the system:** open the [architecture image](docs/architecture.svg). YOLO uses Hailo-8; category anomaly models use ONNX CPU; ExecuTorch Llama is a separate Arm advisory process. Llama cannot override the recorded QA decision.
2. **See actual output:** open the [Hailo crack inspection](evidence/gallery/dashboard/02_yolo_defective.png), [anomaly heatmap and advice](evidence/gallery/dashboard/04_anomaly_defective.png), then the [complete 47-screenshot gallery](evidence/gallery/README.md).
3. **Inspect measured results:** read [full accuracy and comparison tables](docs/RESULTS.md). Every table points to original records; [CSV/JSON exports](evidence/metrics/README.md) preserve full precision.
4. **Check actual target execution:** the [eight-case report](evidence/target_20261124/eight_test_report.json) contains original inspection IDs, detections/scores, advice, native token statistics and resource samples. The [summary](evidence/target_20261124/summary.json) reports eight selected outcomes matched and eight fresh validated advisory responses, with zero cache reuse.
5. **Review methodology:** read the [project PDF](docs/MEDGE_VISION_Final_Project_Report.pdf), [model cards](docs/MODEL_CARDS.md) and [engineering acceptance](SUBMISSION_REPORT.md).

## Why these engineering choices?

Read the [decision ledger](docs/ENGINEERING_DECISIONS.md) for Hailo preprocessing, adaptive-v1 selection, persistent advisory, model limitations and reproducible recovery. The [evidence workflow](docs/assets/evidence-path.svg) shows why visual findings, advice and authorized QA remain separate.

## Evidence at a glance

| Question | Direct evidence | Boundary |
| --- | --- | --- |
| How accurate is detection? | [YOLO evaluator and class F1](docs/RESULTS.md#1-yolov8s-original-fp32-held-out-evaluator) | Original FP32 test, 1,303 images / 2,956 boxes; no normal-only images |
| What is deployment-threshold F1? | [Recorded counts and derived F1](docs/RESULTS.md#2-yolo-fixed-class-threshold-operating-point) | Micro F1 97.63%; separate from AP-sweep evaluator |
| How well do anomaly profiles work? | [Image and pixel evaluation](docs/RESULTS.md#3-efficientad-s-labeled-image-level-results) | Pill F1 92.37%; capsule 88.32%; VisA 38.40%, weak research profile |
| What does Hailo improve? | [Actual CPU/Hailo comparison](docs/RESULTS.md#5-actual-pi-detector-benchmark-cpu-versus-hailo-8) | 38.17x mean detector-path latency ratio; unequal repeated-image trials, not line throughput |
| Did quantization preserve accuracy? | [Export/agreement evidence](docs/RESULTS.md#6-quantization-and-export-what-was-verified) | Execution/reference agreement measured; labeled INT8 accuracy delta NOT TESTED |
| Why choose 1B adaptive Llama? | [Candidate comparison](docs/RESULTS.md#7-executorch-llama-candidate-and-prompt-comparison) | Historical median 8.071 s; final guard replay 36/39; not semantic accuracy |
| Was the integrated system executed? | [Final actual target cases](docs/RESULTS.md#8-complete-station-actual-24-november-execution) | Eight selected examples, not unbiased accuracy |
| Is it reproducible? | [Quick start](QUICKSTART.md), [artifact manifest](ARTIFACT_MANIFEST.json), [CI](https://github.com/Haridharan-D/arm-hailo-medgevision-llama-executorch/actions) | CPU CI cannot validate hardware; vendor runtime and external Llama provisioning are explicit |
| Is recovery tested? | [Portable backup guide](backups/README.md), [restored API checks](evidence/gallery/restored_api_verification.json) | Eight published records/images/advice; not a full private station or bootable SD image |

## Reproduce without training

Follow [QUICKSTART.md](QUICKSTART.md). Reassemble and hash-check the included vision models, run the CPU smoke tests, then configure actual Hailo/Arm advisory on compatible hardware. The large Llama PTE/tokenizer use a pinned upstream downloader. No credentials are distributed.

On an installed matching Pi, `~/medge-test` runs eight selected cases with full advisory and summary. `~/medge-vision` opens the dashboard separately. On a fresh source checkout, use the installation instructions first; these aliases do not exist until installed.

## Interpret honestly

- SAFE is a visual model check, not pharmaceutical release approval. QA REVIEW can coexist with a clear model result when product/capture validation is incomplete.
- The actual native advisory messages and validation traces are in the measured records; [advisory CSV](evidence/metrics/target_advisory_outputs.csv) makes them easy to inspect.
- Screenshot terminal pages are labeled replay of the original recorded run; they are not another inference experiment.
- Human semantic advisory review, approved production SOPs, local-camera/product accuracy, healthy-only YOLO specificity, labeled INT8 accuracy delta, power/energy and long-shift endurance remain outstanding.
- MVTec-derived models/samples retain noncommercial restrictions. See [licenses](THIRD_PARTY_NOTICES.md).

[Full README](README.md) · [Documentation index](docs/README.md) · [Where every metric came from](docs/EVIDENCE_GUIDE.md)
