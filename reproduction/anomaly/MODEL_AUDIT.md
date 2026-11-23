# EfficientAD artifact audit — 19 November 2026

All three final Submission archives contain completed EfficientAD-S models: 70,000 training steps each, FP32, batch size 1, RGB input 256 × 256. These are teacher/student/autoencoder anomaly models, not EfficientNet classifiers.

Training completion does not establish inspection quality. Results below are the held-out metrics saved in the supplied model contracts; the complete test datasets were not evaluated again locally.

| Model | Finished steps | Selected best step | Image AUROC | Defect recall at saved threshold | Missed defective images | False alarms on normal images |
|---|---:|---:|---:|---:|---:|---:|
| MVTec pill | 70,000 | 69,000 | 98.34% | 85.82% | 20 / 141 | 0 / 26 |
| MVTec capsule | 70,000 | 69,000 | 94.85% | 79.82% | 22 / 109 | 1 / 23 |
| VisA capsules | 70,000 | 70,000 | 65.02% | 24.00% | 76 / 100 | 1 / 60 |

## Which artifacts to keep

- `model_new_kggle/model/mvtec_pill_Submission.zip`
- `New folder (2)/mvtec_capsule_Submission (1).zip`
- `New folder/visa_capsules_Submission.zip`

Each final archive contains its calibrated `runs/<run_name>/best.pt`, inference/training source, model contract, and evaluation material. The `Weights.zip` archives also report completed training. Pill and VisA Submission files with the `(1)` suffix are byte-identical to their corresponding unsuffixed Submission archives.

Use the calibrated final Submission artifacts. The pill Recovery archive is only at step 10. The capsule and VisA Recovery archives record step 70,000 but `training_complete: false`; finalization is represented by the completed Submission archives. A best checkpoint selected at step 69,000 is compatible with a completed 70,000-step run.

## Local verification

- All 11 inspected Submission, Weights, and Recovery ZIP archives passed CRC integrity checks.
- All three selected final `best.pt` checkpoints loaded with PyTorch `weights_only=True`.
- Final checkpoint hashes match their model contracts and checkpoint-status metadata.
- All 46 state tensors in each final model are finite.
- See `MODEL_AUDIT.json` for strict architecture loading and CPU synthetic forward checks, checkpoint hashes, saved thresholds, full metrics, and archive identities. Synthetic inputs verify execution only; they do not establish accuracy or camera generalization.
- No ONNX, HEF, PTE, or TorchScript deployment exports are present in the three final Submission archives.

## Readiness judgment

MVTec pill and capsule are completed category benchmark candidates. Their saved operating thresholds still miss 20 and 22 defective test images respectively. VisA capsules is completed but currently unsuitable as a dependable anomaly alarm: it misses 76 of 100 defective test images, and its image AUROC is only 65.02%. Its high pixel AUROC does not establish reliable image-level detection.

Do not blindly combine these three models or assume they cover a new blister pack. They learn separate normal appearances. Their output is an anomaly heatmap and score, not a seven-class defect label, calibrated probability, or severity. Local normal and defective images from the intended camera/product are required before routing anomaly results into the existing deterministic inspection rules.

Do not optimize thresholds on the held-out test set and continue describing it as independent evaluation. Investigate preprocessing, normal-data coverage, validation behavior, and representative product data first. VisA's weak ranking means a lower threshold alone is not a demonstrated solution.

This audit does not establish anomaly integration into the dashboard, Hailo compilation, quantized parity, Raspberry Pi latency, or production readiness. Existing YOLO and Llama deployment evidence concerns their own separate pipelines.
