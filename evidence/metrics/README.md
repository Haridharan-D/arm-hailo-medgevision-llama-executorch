# Metric exports

Generated deterministically from preserved source evidence; no fresh inference. [Readable results and interpretation](../../docs/RESULTS.md) · [Experiment/source ledger](../../docs/EVIDENCE_GUIDE.md).

Rates are fractions, times milliseconds unless named otherwise, and memory MiB. CSV `source` / `source_pointer` fields identify each original JSON record. `summary.json` includes input SHA-256 hashes, formulas, scopes and missing measurements. Empty CSV cells mean unmeasured/not applicable, never zero.

```sh
python tools/build_results_docs.py
python tools/build_results_docs.py --check
```

- [summary.json](summary.json)
- [yolo_evaluator.csv](yolo_evaluator.csv)
- [yolo_operating_point.csv](yolo_operating_point.csv)
- [anomaly_image.csv](anomaly_image.csv)
- [anomaly_pixel.csv](anomaly_pixel.csv)
- [cpu_vs_hailo.csv](cpu_vs_hailo.csv)
- [llama_comparison.csv](llama_comparison.csv)
- [target_eight_cases.csv](target_eight_cases.csv)
- [target_advisory_outputs.csv](target_advisory_outputs.csv)
