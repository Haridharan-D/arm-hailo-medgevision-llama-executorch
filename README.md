# Medge Vision

Offline pharmaceutical optical-inspection research station: Raspberry Pi 5 + Hailo-8 YOLO, three EfficientAD CPU models, and ExecuTorch Llama advisory. Two dashboard designs, camera/upload/local-image inspection, anomaly heatmaps, SQLite evidence and a synchronized second HDMI verdict screen.

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

YOLO ONNX, Hailo-8 HEF and three anomaly ONNX files are included. ARTIFACT_MANIFEST.json records exact sizes/hashes. The 1.14 GB gated Llama PTE, tokenizer and platform binaries are intentionally separate. Accept the upstream Llama 3.2 license/access conditions before downloading. See llama/artifacts/README.md and llama/download_model.py. The tested PTE must match the manifest; another export is not interchangeable. Do not redistribute credentials.

MVTec-derived models/samples retain CC BY-NC-SA 4.0 restrictions: this bundle is not licensed for unrestricted commercial use. VisA is CC BY 4.0; EfficientAD source attribution is in models/anomaly/ATTRIBUTION.md. Ultralytics-derived model use requires its applicable license (including AGPL/commercial terms); see THIRD_PARTY_NOTICES.md.

## Native Pi advisory setup

`llama/build_runtime.sh` is the pinned ExecuTorch v1.0.0 baseline build recipe. It requires Linux/Arm build tools and network access during installation. The final instrumented worker additionally uses native/blistertrace_instrumented.cpp, native/json_boundary.h and tools/build_instrumented_pi.py. That historical tool assumes the original station paths; inspect and adapt those paths for a clean machine. **The original station's final Arm binary is not backed up here. A fresh native build has not been verified from this clone.** Set llama_runtime and llama_artifacts in config.json to real absolute paths. Windows Llama requires the Linux x86-64 worker under WSL; the EXE alone is not standalone.

## Hailo

The supplied HEF targets Hailo-8, not Hailo-8L. Install compatible vendor driver/HailoRT first. Follow docs/INSTALLATION.md and docs/TROUBLESHOOTING.md. Start on CPU, verify device identity, then activate the Hailo backend. Compilation is not required for the included frozen HEF. Camera and hardware testing require the actual board; do not interpret CPU tests as hardware validation.

## Terminal and tests

```sh
python main.py --inspect test_images/acceptance_demo/safe/safe_01.jpg --output inspection.json
python -m pip install pytest httpx
python -m pytest tests -q
```

For a running installed station see docs/TERMINAL_DEMO_MEDGE_VISION.md (five real-model tests with advisory). Legacy station-specific automation under tools is retained for traceability; it is not all a portable installer. See docs/DISPLAY_SYNC_FIX.md for the two-monitor synchronization protocol.

## Results and limits

Detector test: 1,303 images, mAP50 0.992, mAP50-95 0.892; no normal-only test images. EfficientAD original held-out recall: pill 85.82%, capsule 79.82%, VisA capsules 24%. VisA is a weak candidate. Selected demo examples are not an unbiased accuracy benchmark. SAFE means configured visual check clear, not pharmaceutical release approval. QA disposition remains separate; Llama cannot override it. Demo SOP is not approved production SOP. See docs/SUBMISSION_LIMITATIONS.md.

## Backup status

See BACKUP_STATUS.md before erasing the original SD card. This repository is source/model recovery, not a complete SD-card or evidence-database backup.
