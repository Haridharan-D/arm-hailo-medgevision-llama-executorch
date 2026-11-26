# Deployment models

The five frozen vision models are committed as complete binaries. A regular clone includes them. Run `python tools/verify_repository_artifacts.py` from the repository root to check file sizes and SHA-256 hashes.

| Pipeline | Model | Runtime and configuration |
| --- | --- | --- |
| YOLOv8s | [FP32 ONNX](../assets/blistertrace_yolov8s.onnx) | ONNX Runtime CPU with [class thresholds](../assets/thresholds.json) |
| YOLOv8s | [INT8 HEF](blistertrace.hef) | HailoRT on Hailo-8 with the same host thresholds |
| EfficientAD-S pill | [ONNX](anomaly/mvtec_pill/model.onnx) | CPU with [pill contract](anomaly/mvtec_pill/contract.json) |
| EfficientAD-S capsule | [ONNX](anomaly/mvtec_capsule/model.onnx) | CPU with [capsule contract](anomaly/mvtec_capsule/contract.json) |
| EfficientAD-S VisA capsules | [ONNX](anomaly/visa_capsules/model.onnx) | CPU with [VisA contract](anomaly/visa_capsules/contract.json). Research profile with low held-out recall. |

The anomaly contracts describe preprocessing, score thresholds, and artifact identity. The Hailo HEF is compiled for Hailo-8. The verifier assembles the bundled Arm advisory worker and library from `models/runtime-parts/`. Provision the Llama PTE and tokenizer through the pinned downloader. [Llama setup](../llama/artifacts/README.md)

[Exact artifact sizes and hashes](../ARTIFACT_MANIFEST.json) · [Full setup](../docs/QUICKSTART.md) · [Model cards](../docs/MODEL_CARDS.md) · [Third-party terms](../docs/THIRD_PARTY_NOTICES.md)
