# Medge Vision

**Evidence and backups:** [complete screenshot gallery](evidence/gallery/README.md) · [included portable backup and restore commands](backups/README.md) · [full submission report](SUBMISSION_REPORT.md).


**24 November target release:** [full submission report](SUBMISSION_REPORT.md), [eight-case target evidence](evidence/target_20261124/summary.json), [verified project backup status](BACKUP_STATUS.md). Actual Pi: 76 regressions passed, 8/8 selected outcomes and 8/8 genuine Llama responses; no cache reuse. Exact aarch64 runtime is now shipped as verified parts. Camera/endurance/Drive gaps remain explicit.


Offline pharmaceutical optical-inspection research station: Raspberry Pi 5 + Hailo-8 YOLO, three EfficientAD CPU models, and ExecuTorch Llama advisory. Two dashboard designs, camera/upload/local-image inspection, anomaly heatmaps, SQLite evidence and a synchronized second HDMI verdict screen.

**Current audit:** [PASS / FAIL / NOT TESTED report](SUBMISSION_REPORT.md), [architecture](docs/architecture.svg), [model training-to-deployment dossier](docs/MODEL_LIFECYCLE.md), [historical benchmarks](evidence/historical/BENCHMARKS.json), [Drive mirror status](docs/DRIVE_MIRROR.md).

**Start here: [reproducible setup and demo commands](QUICKSTART.md).** All 76 regression tests passed on the Pi and laptop. The portable demo backup was restored and its images/advice were read through the application API. Fresh Pi installation requires matching vendor packages; the original tested Arm runtime is included, with source build available for other OS/ABI combinations.

![Actual measured Hailo defect and Llama advisory](evidence/gallery/dashboard/02_yolo_defective.png)

After setup, launch with `python run.py`. Read the [three-minute hackathon demo](docs/HACKATHON_DEMO.md), [recorded CPU smoke results](evidence/clone_cpu_smoke.json), and [verification report](docs/REPOSITORY_VERIFICATION.md).

For a distributable desktop folder, follow the [Windows EXE build guide](docs/WINDOWS_BUILD.md). Keep its model/runtime sidecars with the executable.

## Quick start: CPU vision

Python 3.11 is the tested Windows development interpreter. On a 64-bit Pi use the supported system Python and matching Hailo packages.

```sh
python -m venv .venv
# Linux: source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python tools/verify_repository_artifacts.py
python main.py --desktop
```

The dashboard is http://127.0.0.1:8765/ . Alternate design: /classic. Second verdict display: /display. The intro waits for a click. Authentication is disabled in the supplied configuration. Bind locally; use an SSH tunnel for remote access. CPU vision can run without Hailo or Llama. Missing advisory runtime is a fallback, never a successful Llama generation.

## Models and licenses

YOLO ONNX, Hailo-8 HEF and three anomaly ONNX models are included. ONNX files are stored as small Git blobs under model_parts to tolerate interrupted uploads; `python tools/verify_repository_artifacts.py` automatically reassembles and verifies them without internet. ARTIFACT_MANIFEST.json records exact sizes/hashes. The original aarch64 worker/library are also included in verified parts. The 1.14 GB Llama PTE and tokenizer use the pinned external downloader; other native platforms require their own runtime build. Accept upstream Llama 3.2 license conditions before downloading. See llama/artifacts/README.md and llama/download_model.py. The tested PTE must match the manifest; another export is not interchangeable. Do not redistribute credentials.

MVTec-derived models/samples retain CC BY-NC-SA 4.0 restrictions: this bundle is not licensed for unrestricted commercial use. VisA is CC BY 4.0; EfficientAD source attribution is in models/anomaly/ATTRIBUTION.md. Ultralytics-derived model use requires its applicable license (including AGPL/commercial terms); see THIRD_PARTY_NOTICES.md.

## Native Pi advisory setup

`llama/build_runtime.sh` is the pinned ExecuTorch v1.0.0 baseline build recipe. It requires Linux build tools and network access during installation. The final instrumented worker additionally uses native/blistertrace_instrumented.cpp, native/json_boundary.h and tools/build_instrumented_pi.py. The instrumented build now discovers the checkout and supports explicit --project/--executorch paths. **The original tested Arm binary and shared library are backed up and reconstructed by the artifact verifier.** Use them on the matching aarch64 Debian Trixie setup; a fresh native source build has not been verified on a clean Pi during this release. Configure the runtime with tools/configure_station.py. Windows Llama requires the Linux x86-64 worker under WSL; the EXE alone is not standalone.

## Hailo

The supplied HEF targets Hailo-8, not Hailo-8L. Install compatible vendor driver/HailoRT first. Follow docs/INSTALLATION.md and docs/TROUBLESHOOTING.md. Start on CPU, verify device identity, then activate the Hailo backend. Compilation is not required for the included frozen HEF. Camera and hardware testing require the actual board; do not interpret CPU tests as hardware validation.

## Terminal and tests

```sh
python main.py --inspect test_images/acceptance_demo/safe/safe_01.jpg --output inspection.json
python -m pip install pytest httpx
python -m pytest tests -q
```

For a running installed clone, `~/medge-test` runs eight cases (two per pipeline) with advisory and summary; `~/medge-vision` opens the dashboard separately. See QUICKSTART.md. The older five-case guide is docs/TERMINAL_DEMO_MEDGE_VISION.md. Legacy station-specific automation under tools is retained for traceability; it is not all a portable installer. See docs/DISPLAY_SYNC_FIX.md for the two-monitor synchronization protocol.

## Results and limits

Detector test: 1,303 images, mAP50 0.992, mAP50-95 0.892; no normal-only test images. EfficientAD original held-out recall: pill 85.82%, capsule 79.82%, VisA capsules 24%. VisA is a weak candidate. Selected demo examples are not an unbiased accuracy benchmark. SAFE means configured visual check clear, not pharmaceutical release approval. QA disposition remains separate; Llama cannot override it. Demo SOP is not approved production SOP. See docs/SUBMISSION_LIMITATIONS.md.

## Backup status

See BACKUP_STATUS.md before erasing the original SD card. The repository includes a verified eight-record SQLite/image/advice demo backup with safe restore tooling. The complete private station archive remains on the laptop; neither is a bootable SD-sector image.
