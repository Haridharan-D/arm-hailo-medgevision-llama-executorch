> Historical 23 November audit. Current target validation, backups and screenshot acceptance supersede pending items in [SUBMISSION_REPORT.md](SUBMISSION_REPORT.md).

# Final reproducibility audit — 23 November 2026

## Acceptance status

PASS — 73 Python regression tests after fixes; original 67 plus six integrity/preprocessing/QA tests. PASS — five real CPU model demo cases on the Windows workstation. PASS — native C++ JSON boundary test (previous release execution, unchanged source). PASS — trained deployment model hashes preserved. PASS — conservative HOLD/REVIEW decisions preserved with additive severity explanations. PASS — app defaults now adaptive-v1, three threads, 128 output tokens, 1536 prompt budget under the 2048 graph capacity. PASS — architecture-specific worker selection and model/tokenizer/runtime-sidecar checks. PASS — shared YOLO letterbox path for CPU and Hailo; input contracts and non-finite HEF outputs now rejected.

NOT TESTED — new Pi Hailo/USB/CSI inference, Pi Llama latency/RAM/CPU after this change, and fresh native build: SSH to the last known Pi address timed out. NOT TESTED — optional Drive upload/download. NOT TESTED — fresh Windows executable build. NOT TESTED — long-shift endurance, production camera/product generalization, clinical severity, approved production SOP and regulatory release validation. FAIL — complete SD-card backup clearance: the original root filesystem and final Pi-only binaries/data have not been backed up here. Keep the card intact.

## Critical changes and boundaries

Frozen identities now fail closed at detector/advisor preparation. Native worker and library must both be 64-bit little-endian ELF of the host architecture. This checks architecture, not reproducible binary authenticity; official original native hashes remain in historical final_runtime_manifest.json. A legitimate rebuild can differ in binary hash. Anomaly models already validate against their own frozen contracts. A runtime mismatch gives explicit unavailable/fallback status; it does not invent advice or switch NPU results to CPU silently.

The existing decision policy is retained: any localized configured defect is HOLD/major; unusable capture or unvalidated profile remains REVIEW. New severity_explanation records the rule and evidence before audit sealing. A clear visual check can display SAFE while QA REVIEW remains separate. No per-class medical severity or defect-free production claim is introduced. Advice and QA reviews remain append-only; Llama cannot authorize disposition. Authentication remains disabled for the owner's loopback kiosk; this is not an authenticated multi-user deployment.

## Historical performance, not rerun measurements

Historical CPU mean vision latency: 580.115 ms; historical Hailo-8 mean: 15.197 ms, ratio 38.17x. These are repeated-image backend timings from different sample counts, not end-to-end production throughput or camera FPS.

Historical Llama baseline median: 15.156 s. Adaptive-v1 median: 8.071 s. Adaptive peak RSS: 1598.55 MiB; sampled process CPU mean: 297.34% (100% is one logical core; more than 100% is normal for a multithreaded process). These paired experiments precede final JSON-boundary changes. They do not predict exact current release latency. Preserve separate n, warm/cold, concurrency and temperature scopes in BENCHMARKS.json; do not mix trials.

INT8-vs-FP32 agreement precision 0.9487, agreement recall 0.9737, on unannotated training-source demo samples. These are matching statistics, NOT defect precision/recall. Quantized held-out ground-truth mAP/accuracy delta: NOT TESTED. No quantization accuracy has been predicted or fabricated. Original FP32 export parity is recorded on eight validation images in export_status.json; full original labeled metrics are retained separately.

New host-only smoke/resource results are in evidence/final_cpu_smoke.json and final_cpu_resources.json. They are Windows CPU observations, not Pi or Llama measurements. The frozen thresholds were not tuned to force demo outcomes. VisA remains a low-recall research candidate.

## Reproduce from beginning to end

Read QUICKSTART.md first for CPU installation and real local inspection. Install licensed HailoRT/driver for Hailo-8, select --backend hailo, and verify actual device results before enabling a deployment. Download the pinned Llama artifact, build ExecuTorch v1.0.0 on Arm, and configure the instrumented worker. Follow docs/HACKATHON_DEMO.md and docs/WINDOWS_BUILD.md. Store inspection data outside the checkout and back it up consistently using the SQLite backup interface and associated image evidence.

The reproduction folder contains original YOLO training helpers/notebook with outputs stripped in the copy, EfficientAD export source/audit, and Hailo compilation recipe. These are provenance/rebuild references, not commands to rerun during installation. Training datasets, licensed vendor compiler wheel and the original 512-image training-only calibration set are external prerequisites. Set MEDGE_CALIBRATION to that exact set; its manifest is checked before compilation. Rebuilding is not guaranteed bit-identical across vendor/compiler versions. Use the already compiled frozen HEF for exact inference reproduction. Original source folders and weights under C:/arm_bharath_soc_2027 were not modified.

## Release readiness

The research demo is reproducible on CPU with documented native/hardware prerequisites. A claim of complete industrial/production acceptance would be false until the NOT TESTED items are executed. Historical measurements, deployment identities and failure evidence remain visible rather than being relabeled as fresh release passes.


New host resource sample: 78.72 s cold five-case window; aggregate peak RSS 427.56 MiB; peak summed CPU 340.9%. Includes loading and multiple models. Shared RSS pages can be counted more than once. The bootstrap-only sample is explicitly retained as INVALID_parent_only_resources.json.
