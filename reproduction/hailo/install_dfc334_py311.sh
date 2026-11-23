#!/usr/bin/env bash
set -euo pipefail
COMPILER_ROOT="${BT_HAILO_BUILD_ROOT:-$HOME/blistertrace_hailo_compiler}"
WHEEL="${BT_HAILO_WHEEL:-/mnt/c/arm_bharath_soc_2027/Hailo/hailo_dataflow_compiler-3.34.0-py3-none-linux_x86_64.whl}"
if [ ! -x "$COMPILER_ROOT/venv311/bin/python" ]; then
  python3 -m pip install --target "$COMPILER_ROOT/bootstrap" uv
  export UV_PYTHON_INSTALL_DIR="$COMPILER_ROOT/python"
  "$COMPILER_ROOT/bootstrap/bin/uv" venv --python 3.11 --seed "$COMPILER_ROOT/venv311"
fi
"$COMPILER_ROOT/venv311/bin/python" -m pip install --timeout 120 --retries 10 "$WHEEL"
"$COMPILER_ROOT/venv311/bin/python" -c 'import hailo_sdk_client; print("DFC 3.34 import successful")'
if [ ! -d "$COMPILER_ROOT/hailo_model_zoo/.git" ]; then
  git -c http.version=HTTP/1.1 clone --depth 1 --branch v2.19.1 https://github.com/hailo-ai/hailo_model_zoo.git "$COMPILER_ROOT/hailo_model_zoo"
fi
test "$(git -C "$COMPILER_ROOT/hailo_model_zoo" rev-parse HEAD)" = b5aaad19f7353b96fce06905e34effa28a64d03a
"$COMPILER_ROOT/venv311/bin/python" -m pip install --timeout 120 --retries 10 -e "$COMPILER_ROOT/hailo_model_zoo"
"$COMPILER_ROOT/venv311/bin/hailomz" compile --help
