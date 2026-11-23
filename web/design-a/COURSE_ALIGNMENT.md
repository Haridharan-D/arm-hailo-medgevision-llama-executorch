# Course terms and process applied

Source: saved ExecuTorch_Industry4_Study course snapshots, retrieved17Nov2026.

| Lesson/module | Course process | Application |
| --- | --- | --- |
| Module1: export to application testing | prepare → export → lower → inspect graph → transfer artifacts → target benchmark → app → trade-offs | frontend consumes existing deployed artifacts; shows model hash; no new export claimed |
| Module1: runtime paths/lowering/delegation | Portable/XNNPACK delegates, delegated regions, fallback operators, .pte | ExecuTorch CPU advisory remains distinct from HailoRT vision |
| Module1: Raspberry Pi benchmark | target timings and comparable input contracts | vision_ms separate from advisory elapsed_ms; browser FPS not an inference benchmark |
| Module2: FP32 vs INT8 | calibration, matching preprocessing, quality/latency trade-off | thresholds/input preprocessing unchanged; utilization does not establish accuracy |
| Module3: model vs app responsibilities | background execution, layout/dtype contract, postprocess, lifecycle | UI handles interaction while backend runs inference; advice never blocks detector result |
| Module3: validate output | contract and output validation | preserve pending/validated/fallback states |
| Module4: Ethos-U | accelerator-specific lowering/support/Vela/FVP | Hailo HEF/HailoRT is a separate vendor pipeline, not Ethos-U |

References:

- [Export to application testing](https://learn.arm.com/courses/executorch-on-arm/compare-transformer-inference/plan-the-executorch-deployment-workflow/follow-the-workflow-from-model-export-to-application-testing/)
- [Runtime paths](https://learn.arm.com/courses/executorch-on-arm/compare-transformer-inference/before-you-begin/understand-the-runtime-paths-you-will-compare/)
- [Model vs app responsibilities](https://learn.arm.com/courses/executorch-on-arm/android-semantic-segmentation/inspect-the-android-runtime-code/separate-runtime-responsibilities-from-app-responsibilities/)

This dashboard is a project adaptation, not an Arm-prescribed UI. It does not establish
new camera/SKU generalization, quantized accuracy, regulatory validation, or release
authority. Llama advisory uses the existing on-device ExecuTorch runtime and bounded
SOP context; PASS/REVIEW/HOLD comes only from unchanged detector/rule facts.

The 20 November v4 adaptation also follows the export-to-target comparison process
for EfficientAD: strict checkpoint load, fixed RGB/normalization contract, FP32
PyTorch/ONNX output checks, hashed artifacts, retained calibration thresholds and
real held-out examples executed on the Pi. This auxiliary anomaly path uses ONNX
Runtime CPU, not ExecuTorch or Hailo. Mandatory Llama remains native ExecuTorch.
Thread comparisons use the same fixed facts and separate warm-up from timed cases;
cached advice is labeled as reuse rather than fresh generation throughput.
