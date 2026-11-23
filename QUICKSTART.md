# Reproduce Medge Vision

## CPU vision, Windows or Linux

Clone this repository, open a terminal in the checkout, and use Python 3.11:

```sh
python -m venv .venv
```

Activate with `source .venv/bin/activate` on Linux or `.venv\Scripts\Activate.ps1` in PowerShell, then:

```sh
python -m pip install -r requirements.txt pytest httpx
python tools/verify_repository_artifacts.py
python -m pytest tests -q
python tools/configure_station.py --backend onnx
python main.py --desktop
```

Open http://127.0.0.1:8765/ . Click the intro to enter. Alternate design: `/classic`; verdict-only screen: `/display`. Network access is needed for installation, not local inference. No station login is required. Missing native Llama is explicitly reported as fallback.

## Genuine Llama advisory

Accept upstream Llama 3.2 license conditions. Download the pinned public conversion, then build on Linux/Arm (Pi) or Linux/x86-64 (WSL):

```sh
python llama/download_model.py
bash llama/build_runtime.sh
python tools/build_instrumented_pi.py
python tools/configure_station.py --backend onnx
python tools/verify_repository_artifacts.py
```

Prerequisites: git, cmake, g++, build-essential, python3-venv. The baseline build uses pinned ExecuTorch v1.0.0 and TorchAO headers. The instrumented build now accepts `--project` and `--executorch`, so the original workstation paths are unnecessary. Build output is under `native/bin/<architecture>`. Keep `libllama_runner.so` beside the worker. Set `--runtime /absolute/path/to/worker` if automatic discovery cannot find it.

Windows advisory executes its Linux x86-64 worker through WSL. Build under WSL, copy the worker and shared library into `llama/bin/x86_64`, and run the Windows configuration helper. No native Windows Llama executable is asserted. The portable build integration has not been retested on a fresh Pi after the original device became unavailable.

## Hailo-8 vision

Install matching vendor Hailo driver, HailoRT and Python bindings. On Pi create the virtual environment using `python3 -m venv --system-site-packages .venv`. Confirm `hailortcli fw-control identify`, then:

```sh
python tools/configure_station.py --backend hailo
python main.py --inspect test_images/acceptance_demo/defective/crack/crack.jpg --output crack.json
python main.py --desktop
```

The supplied HEF targets Hailo-8, not Hailo-8L. Configuration does not prove hardware readiness. Stop the desktop service before running an independent Hailo terminal inspector; one process must own the device. The USB/CSI camera and second-monitor procedures are in `docs/DUAL_DISPLAY_KIOSK.md`; historical migration tools assume the old station and should not be blindly executed on a new machine.

## Standalone terminal demonstration

```sh
python main.py --inspect test_images/acceptance_demo/defective/crack/crack.jpg --wait-advice --output crack.json
python main.py --inspect test_images/acceptance_demo/safe/safe_01.jpg --wait-advice --output clear.json
```

With the local server running, `python tools/medge_demo.py test 1` through `test 5` exercise two YOLO cases and all three EfficientAD profiles. Add `--help` to inspect options. The `start` subcommand expects an installed systemd service; source users launch `python main.py --no-browser` instead. Do not call fallback output successful Llama generation.

## Submission boundaries

Selected demonstrations are not unbiased accuracy measurements. SAFE means a configured visual check is clear, not pharmaceutical release approval. QA disposition is separate, and Llama cannot override it. See `BACKUP_STATUS.md`, `THIRD_PARTY_NOTICES.md` and `docs/SUBMISSION_LIMITATIONS.md` before reuse or deployment.
