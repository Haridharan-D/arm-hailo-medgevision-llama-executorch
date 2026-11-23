# Initial technical audit — 21 November 2026

Audit precedes application modifications. Local source snapshot and SHA-256 inventory: `validation/hardening/baseline_*.zip`, `baseline_manifest.json`. Pi source + consistent SQLite backup: `/home/saul/BlisterTrace/Backups/hardening_20261121_201140`. Detailed tree, device response, model hashes, runner headers and CMake flags: `validation/hardening/pi_audit.json`. These backups are outside the mutable release. No CSI work is included.

## Actual deployment and inventory

`~/blistertrace` is a launcher file, not a directory. Application: `/home/saul/BlisterTrace/BlisterTrace_App`; durable data: `/home/saul/BlisterTrace_Data`. Development source: `C:/arm_bharath_soc_2027/BlisterTrace_App`. `main.py` provides desktop, server and terminal entry points. `app/server.py` exposes FastAPI REST, static assets, MJPEG, asynchronous initialization. `app/service.py` joins detector, immutable rule result, images, SQLite and advisory queue. `app/vision.py` owns frozen RGB letterbox, class mapping, thresholds and classwise NMS. `app/hailo_backend.py` owns HEF/VDevice/InferVStreams with no automatic CPU fallback. `app/anomaly.py` provides category-specific EfficientAD-S ONNX auxiliary assessment. `app/camera.py` exists but is excluded from this workstream.

`app/store.py`: WAL SQLite inspections and QA events. QA notes append, original decisions remain unchanged. Missing: schema versioning, batches, cryptographic audit chain, durable spool and explicit authentication. `app/llm.py`: single daemon worker, queue capacity one, lazy native model load, process persistent between requests, timeout in framed client. Missing: durable job metadata, prompt/model-specific cache identity, granular latency and strong failed-worker recovery. `advisor_src/advisor.py`: strict input/schema/decision/claim guards, deterministic two-clause retrieval, explicit fallback. Prompt includes three demonstrations; output budget 192. SOP is explicitly unapproved demonstration material.

`web/aoi.html`, `classic.html` are two working offline designs; `/design-a` preserves earlier design. `web/js/api.js` centralizes requests. Some optional batch/audit/auth capabilities currently report unavailable and must not be represented as implemented. Local Inter/JetBrains fonts and SVGs avoid runtime internet. Main binds localhost. Existing PIN is presentation identity, not authentication. `tools/*` contains benchmark, deployment, packaging and target checks; scripts which include CSI checks must not run for this audit. `prepare_assets.py` can overwrite the reviewed advisor and must not be used.

## Exact baseline identity and execution

Meta `Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte`, SHA-256 `8715cdba9e91f6bede00cc5f2d6b12397b95225da5630c4972a8da03001cda3b`; BPE tokenizer and Meta params/export recipe accompany it. Dim 2048, layers 16, attention heads 32, KV heads 8, vocabulary 128256, group size 32. Chat uses BOS 128000, role headers 128006/128007, EOT 128009. Native worker is pinned to ExecuTorch v1.0.0 commit `8c84780911e7f4e9eb19395181b04761392a4b56`, aarch64/GCC14.2. Model loads once; `runner.reset()` deliberately resets KV state for independent inspections. Existing worker caps sequence length at 1024. Do not assume 2K/4K support from model family capabilities. Candidates A/B are the same artifact, not independent experiments.

Pi CMake cache proves `EXECUTORCH_BUILD_XNNPACK=ON`, `EXECUTORCH_XNNPACK_ENABLE_KLEIDI=ON`, `XNNPACK_ENABLE_KLEIDIAI=ON`; actual symbol/delegate execution remains to be checked. Setting these flags alone does not prove individual kernels executed. `TextLLMRunner::generate` has a stats callback, allowing instrumentation without a new runtime or model export. A separate instrumented binary should preserve the existing framed protocol and original executable. Build-time PyTorch/torchgen does not imply deployed inference requires PyTorch.

## Proven evidence and resource use

Historical `BlisterTrace_Deliverables/Hailo_Metrics_20261121`: 3948 detector calls/60 s, mean15.197/P95 15.526/P99 15.635 ms,65.789 images/s; CPU average10.85%,RSS206.43MiB,temp41.47°C. ONNX CPU580.115ms; path speedup38.17×. Not camera FPS. HEF10.106MB, ONNX44.738MB. Mean observed advisory19.855s, two accepted/one fallback; no historical TTFT or decode rate. Hailo firmware4.23.0 responds. Current idle available RAM~15.6GB and swap0 from audit. These conditions are not sustained Llama measurements.

Historical seven-class FP32 held-out mAP50~.9922/mAP50:95~.8919 on1303 images; zero healthy test images, no physical group IDs. INT8 comparison on18 demonstration images is agreement with FP32, not ground-truth accuracy. EfficientAD VisA capsules has weak retained evaluation; do not present all anomaly profiles as equally reliable. Current capture profile is unvalidated; no-defect detections cannot silently become release authorization. Old evidence stays unchanged.

Dependencies: FastAPI/Uvicorn, Pillow/OpenCV/NumPy, ORT for CPU/anomaly, HailoRT for detector, native ExecuTorch/tokenizer, tiktoken for budgeting, SQLite. External licensing: Llama3.2 terms, MVTec noncommercial dataset restrictions. Model/HEF/export recipes and runtime manifests must travel with reproducibility materials.

## Critical risks and implementation order

1. Preserve sources, database, binaries, model hashes and historical evidence before changes.
2. Add backward-compatible native stats in separate candidate executable; inspect official3B checkpoint access and compatibility. Preserve 1B selection until controlled comparison.
3. Benchmark persistent workers on fixed prompts, threads1–4, idle/concurrent Hailo; append and flush results each trial. No CSI. Distinguish unsupported contexts and unavailable metrics.
4. Version and strengthen advisory evidence/cache/KB metadata without relaxing decision/claim guards. Approved SOPs and human semantic review are unavailable, and must remain explicit limitations.
5. Migrate SQLite transactionally, preserving legacy rows; add batches, evidence identity, audit chain, spool/replay and tested consistent backup. Never rewrite legacy decisions.
6. Wire real batch/audit/health UI and local role authentication in a separate validated release. Avoid breaking two preserved dashboards or locking out the working deployment.
7. Add failure/concurrency/integrity tests, install/recovery commands and measured submission reports. Avoid claims of regulatory certification or unexecuted tests.
