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

For the measured Raspberry Pi 5 aarch64 Debian Trixie setup, `python tools/verify_repository_artifacts.py` now reconstructs the original tested Arm worker and shared library as well as the vision models. Download the pinned Llama files, then run `python tools/configure_station.py --backend hailo`. A native rebuild is optional on the matching system; other architecture/OS/glibc combinations require the source-build path below. The PTE/tokenizer download remains separate because of size/licensing.

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

The supplied HEF targets Hailo-8, not Hailo-8L. Configuration does not prove hardware readiness. Stop the desktop service before running an independent Hailo terminal inspector; one process must own the device.

For a new Pi desktop with Chromium, XWayland and wlr-randr installed, run `python tools/install_clone_pi.py --install`, then `~/medge-vision`. This creates a service for the actual checkout and opens the main monitor plus verdict monitor. Existing service/launchers are preserved rather than overwritten. Run from a logged-in desktop session; this does not configure unattended pre-login startup. Historical migration tools assume the old station and should not be blindly executed on a new machine.

## Standalone terminal demonstration

```sh
python main.py --inspect test_images/acceptance_demo/defective/crack/crack.jpg --wait-advice --output crack.json
python main.py --inspect test_images/acceptance_demo/safe/safe_01.jpg --wait-advice --output clear.json
```

With `python main.py --no-browser` running in one terminal, initialize a source demonstration in another:

```sh
python tools/medge_demo.py start --no-service
python tools/medge_demo.py models
python tools/medge_demo.py test 1
python tools/medge_demo.py test 2
python tools/medge_demo.py test 3
python tools/medge_demo.py test 4
python tools/medge_demo.py test 5
python tools/medge_demo.py summary
```

These exercise two YOLO cases and all three EfficientAD profiles. Add `--help` to inspect options. The installed `~/medge-demo start` can start systemd automatically. Do not call fallback output successful Llama generation.

The clone installer also creates `~/medge-test`: two cases per pipeline, eight total, full advisory output and final summary. Run `~/medge-vision` separately to open the dashboard. See SUBMISSION_REPORT.md for the actual 24 November Pi run and snapshot/recovery boundaries.

## Submission boundaries

Selected demonstrations are not unbiased accuracy measurements. SAFE means a configured visual check is clear, not pharmaceutical release approval. QA disposition is separate, and Llama cannot override it. See `BACKUP_STATUS.md`, `THIRD_PARTY_NOTICES.md` and `docs/SUBMISSION_LIMITATIONS.md` before reuse or deployment.
