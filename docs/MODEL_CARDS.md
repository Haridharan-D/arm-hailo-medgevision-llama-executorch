# Deployment model cards

These cards describe frozen deployment artifacts. They do not claim new training. [Full results](RESULTS.md) · [Evidence ledger](EVIDENCE_GUIDE.md) · [Artifact hashes](../ARTIFACT_MANIFEST.json).

## YOLOv8s: configured blister defects

| Property | Contract |
| --- | --- |
| Task | Seven-class supervised object detection; class, confidence and bounding box |
| Classes | `black_dot`, `broken`, `color_mismatch`, `crack`, `dual_cap`, `empty`, `foreign_particle` |
| Historical model summary | 11,128,293 fused parameters; 28.4 GFLOPs |
| Training | 134 completed epochs; configured maximum 150; patience 25; batch 8; AdamW; 640 px; seed 42 |
| CPU artifact | `assets/blistertrace_yolov8s.onnx`; opset 11; FP32 input `[1,3,640,640]`, raw output `[1,11,8400]` |
| NPU artifact | `models/blistertrace.hef`; Hailo-8 INT8; HailoRT NMS |
| Shared geometry | Aspect-preserving OpenCV letterbox 640; padding 114; BGR → RGB; reverse mapping to original image |
| CPU host tensor | RGB NCHW float32 `/255` |
| Hailo host tensor | RGB NHWC uint8; normalization belongs to compiled HEF, not another host `/255` |
| Frozen class thresholds | 0.90 / 0.90 / 0.89 / 0.86 / 0.91 / 0.91 / 0.90, in class order above |
| Postprocessing | Existing classwise NMS policy, IoU 0.7; no silent policy changes |
| Original labeled test | 1,303 images / 2,956 boxes; mAP50 0.992206; mAP50-95 0.891865 |
| Fixed-threshold micro F1 | 0.976271, derived from 2,880 TP / 64 FP / 76 FN |

Saved [training arguments](../evidence/historical/yolo_args.yaml), [epoch CSV](../evidence/historical/yolo_results.csv), [evaluation](../evidence/historical/test_metrics.json) and [notebook/helper](../reproduction/yolo) remain unchanged. Historical console time was 3.232 hours; this documentation release did not retrain.

### Conversion

FP32 ONNX raw-tensor export parity passed on eight validation images. Hailo compilation uses Linux x86-64 licensed DFC 3.34.0 and Model Zoo v2.19.1, seven classes and six YOLO head end nodes. The original training-only calibration collection contains **512 available images**. The [recipe](../reproduction/hailo/compile_hef.sh) separately records actual vendor calibration entries; do not infer all available images were consumed without the receipt.

The included frozen HEF avoids recompilation for inference. A new compile needs the licensed compiler and original calibration manifest/images. Compilation success does not establish labeled INT8 accuracy.

### Limits

The curated test excludes unresolved conflicts/invalid families and uses source-family/perceptual grouping. Physical strip independence was not verified. It has **zero normal-only images**: healthy specificity and false-reject rate cannot be estimated. Confidence is not pharmaceutical safety probability. Local-camera/product generalization and clinical severity are unvalidated. Reference INT8/FP32 agreement is a separate unannotated experiment.

Ultralytics licensing applies; see [third-party notices](../THIRD_PARTY_NOTICES.md).

## EfficientAD-S: three independent anomaly profiles

A pretrained PDN teacher, trainable student and feature autoencoder learn the normal category appearance. This is **EfficientAD-S, not EfficientNet**; it does not predict the YOLO defect taxonomy.

| Property | MVTec pill | MVTec capsule | VisA capsules |
| --- | --- | --- | --- |
| Profile | `mvtec_pill` | `mvtec_capsule` | `visa_capsules` |
| Steps | 70,000 | 70,000 | 70,000 |
| Batch / training precision | 1 / FP32 | 1 / FP32 | 1 / FP32 |
| Saved image threshold | 0.3500530124 | 0.2682838440 | 0.2028189451 |
| Held-out images | 167 | 132 | 160 |
| Image F1 | 0.923664 | 0.883249 | 0.384000 |
| Image recall | 0.858156 | 0.798165 | 0.240000 |
| Deployment | ONNX CPU | ONNX CPU | ONNX CPU, research profile |

Contracts: [pill](../models/anomaly/mvtec_pill/contract.json), [capsule](../models/anomaly/mvtec_capsule/contract.json), [VisA](../models/anomaly/visa_capsules/contract.json). Each retains training/checkpoint/split fingerprints, selected step, calibration metadata and original evaluation.

### Input, output and normalization

Deployment ONNX input is RGB FP32 `[1,3,256,256]` in `[0,1]`, using Pillow bilinear resizing and host `/255`. **ImageNet normalization and anomaly-map normalization/alignment are inside the exported graph.** Training mean/std metadata does not authorize applying normalization twice. See [exporter](../reproduction/anomaly/export_deployment.py) and [runtime](../app/anomaly.py).

Outputs are a real anomaly map and scalar image score. The score can exceed 1 and is not a probability. Heatmap colors use a fixed saved scale; each image is not independently stretched into a dramatic map. An image-level flag is not a localized physical-defect count. Pixel F1/Dice and image F1 measure different tasks.

Normal validation supports checkpoint selection/map normalization. A separate normal calibration subset sets the fixed 0.995-quantile threshold; held-out test data are excluded from optimization. Small calibration sets cannot guarantee production false-alarm rates.

[Three complete training notebooks](../reproduction/anomaly/notebooks) · [Original checkpoint audit](../reproduction/anomaly/MODEL_AUDIT.md). Small interrupted-run recovery checkpoints are not the final 70,000-step artifacts. Selected demo sample folders are not full evaluation datasets.

### Limits and licensing

VisA misses 76/100 anomalous held-out images at its saved threshold, so it remains a weak research/demo profile. No category model is validated for arbitrary new blister strips, SKUs or cameras. A visually clear result does not authorize QA release.

MVTec-derived data/models retain **CC BY-NC-SA 4.0** noncommercial restrictions; VisA retains **CC BY 4.0**. EfficientAD source attribution/license files are in [models/anomaly](../models/anomaly).

## Llama 3.2 1B Instruct SpinQuant INT4 EO8

| Property | Deployed configuration |
| --- | --- |
| Role | Advisory about recorded inspection facts, with SOP references; no disposition authority |
| Provenance | Upstream pre-exported PTE; not team-trained or team-requantized |
| PTE size | 1,135,951,488 bytes |
| Runtime | Native aarch64 ExecuTorch v1.0.0 on Arm CPU, XNNPACK support |
| Exported capacity | Context/sequence 2,048; vocabulary 128,256 |
| Selected prompt | `adaptive-v1`; bounded inspection/SOP context |
| Limits | 1,536 prompt tokens; 128 output tokens |
| Scheduling | Three CPU threads by default; existing camera/CPU scheduler may reduce advisory use |
| Worker | Persistent process; independent request reset; one active and one waiting job |
| Output checks | First-object JSON boundary; schema/clause/action/observed-evidence guards; explicit fallback |
| Cache identity | Model/SOP hashes, prompt mode/version, output budget and facts; reuse identified |
| Graph evidence | 180 XNNPACK delegate calls and 490 remaining kernel calls |
| Final selected target demo | Eight fresh validated responses; zero cache reuse; median 8.9669 s |

The [pinned downloader](../llama/download_model.py), [native build](../llama/build_runtime.sh) and [instrumented worker](../native/blistertrace_instrumented.cpp) preserve provenance. Matching Arm worker/library are reconstructed from Git parts; other ABIs may need a rebuild and actual generation check. ELF architecture matching alone does not establish ABI compatibility.

Quantization metadata includes groupwise INT4 weights, dynamic INT8 activations, group size 32, 8-bit embeddings and a prequantized output projection. No second quantization, fresh export, LoRA or LLM fine-tuning is claimed. [Full pinned revisions and optimization notes](LLAMA_EXECUTORCH_OPTIMIZATION.md).

### Selection and limits

Historical median advisory time: 15.156 s for 1B baseline, 8.071 s for adaptive-v1 and 39.275 s for 3B. Adaptive uses less recorded peak memory than 3B and has a shorter measured response time. Final guard replay accepts 36/39 adaptive cases versus baseline 26/39; experimental 37/39 is not relabeled as final quality.

Do not assign a detector F1 score to Llama. Automated acceptance is not expert semantic correctness. Demo SOP `BT-DEMO-SOP-01` is unapproved for manufacturing. Text cannot establish root cause, chemical/microbial safety, medical severity or release suitability. Invalid output falls back without overwriting the original QA decision.

Accept upstream Llama community license/use terms before download. The PTE/tokenizer are provisioned separately; never commit tokens or private account files.

## Replication boundary

Run `python tools/verify_repository_artifacts.py` before execution. Hash or architecture failures require investigation, not bypassing. Inference needs no retraining; full training reproduction additionally requires original licensed datasets, split/calibration manifests and supported compiler/build environments. The Git repository is not a raw-dataset or complete private-station mirror.
