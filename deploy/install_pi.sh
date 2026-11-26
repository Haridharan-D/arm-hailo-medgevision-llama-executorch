#!/usr/bin/env bash
# Fresh-clone CPU installation. Native advisory and HailoRT are separate.
set -euo pipefail
APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install --timeout 120 --retries 10 -r requirements.txt
.venv/bin/python tools/verify_repository_artifacts.py
.venv/bin/python tools/configure_station.py --backend onnx
printf '\nCPU vision installed. Launch: bash deploy/launch_pi.sh\n'
printf 'Native advisory and dual-monitor service: follow docs/QUICKSTART.md\n'
