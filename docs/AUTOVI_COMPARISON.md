# Medge Vision and AutoVI benchmark comparison

This comparison uses the AutoVI README from the supplied `ARM_Renault_AUTO_VI_Defect_Detection-main.zip` and the original Medge Vision benchmark records. AutoVI values are project-reported. The projects use different datasets, models, timing boundaries and advisory workloads, so the results support conclusions about each system's own measurements. A cross-project ranking would require a common protocol.

| Dimension | AutoVI reports | Medge Vision evidence |
| --- | --- | --- |
| Compiled detector footprint | **23.4 MB HEF**, down from 99.5 MB ONNX (reported **76.5%** reduction) | **10.11 MB HEF**, down from **44.74 MB** FP32 ONNX (**77.41%** reduction). Exact byte counts are 10,105,866 and 44,738,475. This compares standalone artifacts across distinct models. Total station storage also includes anomaly models and Llama. [Artifact manifest](../ARTIFACT_MANIFEST.json). |
| Pi 5 + Hailo-8 latency | **9.18 ms** for feature extraction and k-NN scoring | **15.197 ms mean / 15.526 ms p95** for YOLO detector calls. On the same repeated-image benchmark protocol, CPU mean was **580.115 ms**, yielding a **38.17x** CPU-to-Hailo mean-latency ratio. There were 35 CPU calls and 3,948 Hailo calls. |
| Power and resources | **2.5 W** under the reported inspection workload | Electrical power and energy **not measured**. Mean detector-process RSS was **254.07 → 206.43 MiB**, about **18.75% lower** in the Hailo trial. RSS measures memory and cannot establish watts. |
| Quantization validation | Reported labeled AUROC **0.9753 → 0.9751** | Actual Hailo-8 INT8 execution and FP32 reference agreement on **18 unannotated images**. **37 matched, 2 INT8-only and 1 FP32-only** detection. Agreement precision **94.87%**, recall **97.37%**. Ground-truth INT8 mAP/F1 delta remains **not tested**. |
| Platform coverage | Five reported targets, including Android | Pi CPU vs Hailo, a separate Windows CPU regression and timing run, and reproducible CPU inference in Ubuntu CI. Android support has **not been tested**. |
| Llama advisory | **1.84 s** reported for its advisory workload | Historical 1B adaptive-v1 median **8.071 s**, down from **15.156 s** on Medge Vision's own workload (**46.75% reduction** from displayed medians). Final guard replay accepted **36/39** vs **26/39** for baseline. Separate actual station run produced **8/8 fresh validated responses**, median **8.967 s**. Guard acceptance verifies application constraints. Human semantic quality remains unmeasured. |

## Evidence judges can reproduce

- **Detection:** original FP32 held-out test of 1,303 images and 2,956 labeled boxes yielded **89.19% mAP50–95** and **99.22% mAP50**. Fixed-threshold micro F1 was **97.63%**. The set contains no healthy-only images, so healthy specificity remains unmeasured. [Evaluation methods and per-class results](RESULTS.md).
- **Integrated inspection:** the Pi report ties each selected case to visual output, runtime measurements and fresh advisory. The review workflow preserves the inspection verdict independently of Llama. [Original eight-case record](../evidence/target_20261124/eight_test_report.json) · [Actual dashboard captures](../evidence/gallery/README.md).
- **Software upgrade:** the Windows experiment matched detections on all **12 paired CPU calls** and reduced the isolated threshold lookup p50 from **2.55645 to 0.03180 ms** using seeded class indices. [Scope, full timings and commands](ENGINEERING_UPGRADE_20261126.md) · [95-test regression run](../evidence/engineering_20261126/regression.txt).

The comparisons above preserve the original benchmarks. The percentages are arithmetic on published Medge Vision measurements. [Raw benchmark records and methodology](RESULTS.md) · [CSV/JSON evidence](../evidence/metrics/README.md) · [Engineering report (PDF)](MEDGE_VISION_PS5_Engineering_Upgrade_Report.pdf).

## Reproduce a paired labeled CPU-to-Hailo accuracy comparison

With the dashboard stopped, run both evaluations on the same matching Pi, from the same checkout, with the frozen host thresholds and an independently labeled set containing healthy and defective images. Supply an explicit empty label file only for a confirmed healthy image. Use the dataset note to record provenance and physical grouping.

```sh
python tools/evaluate_labeled.py --images holdout/images --labels holdout/labels --backend onnx --dataset-note "Independent holdout, record provenance here" --output evaluation/onnx.json
python tools/evaluate_labeled.py --images holdout/images --labels holdout/labels --backend hailo --dataset-note "Independent holdout, record provenance here" --output evaluation/hailo.json
python tools/compare_detector_backends.py --onnx evaluation/onnx.json --hailo evaluation/hailo.json --output evaluation/paired.json
```

The comparison requires identical unique image hashes, label hashes, parsed labels and host threshold hashes. It recomputes per-class and micro precision, recall and F1 at box IoU 0.50, plus image-presence specificity and miss rates. The resulting differences describe the deployed backends, including HEF NMS. AP requires a separate low-score sweep, and identity checks cannot certify physical-strip independence. The comparison logic is covered by regression fixtures. New labeled Hailo results remain pending. [Comparison tool](../tools/compare_detector_backends.py).
