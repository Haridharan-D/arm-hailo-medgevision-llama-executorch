#!/usr/bin/env bash
# Run in Linux/WSL for host verification or natively on the 64-bit Pi.
# No apt/system configuration changes are performed by this script.
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TASK_STATE="${BT_LLM_BUILD_ROOT:-$HOME/blistertrace_llm_build}"
PIN=8c84780911e7f4e9eb19395181b04761392a4b56
JOBS="${BT_BUILD_JOBS:-2}"
for tool in git python3 cmake g++; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'Missing prerequisite: %s\n' "$tool"
    exit 2
  fi
done
mkdir -p "$TASK_STATE"
if [ ! -d "$TASK_STATE/executorch/.git" ]; then
  git clone --depth 1 --branch v1.0.0 https://github.com/pytorch/executorch.git "$TASK_STATE/executorch"
fi
cd "$TASK_STATE/executorch"
test "$(git rev-parse HEAD)" = "$PIN"
# Native CPU runtime only: avoid CUDA/CUTLASS, mobile GPU and Ethos-U sources.
git submodule update --init --recursive --depth 1 --jobs 4 \
  backends/xnnpack/third-party/FP16 backends/xnnpack/third-party/FXdiv \
  backends/xnnpack/third-party/XNNPACK backends/xnnpack/third-party/cpuinfo \
  backends/xnnpack/third-party/pthreadpool extension/llm/tokenizers \
  kernels/optimized/third-party/eigen third-party/flatbuffers third-party/flatcc \
  third-party/gflags third-party/pocketfft third-party/pybind11 third-party/json \
  third-party/prelude shim
# SDPA includes TorchAO CPU headers even when TORCHAO kernels are disabled.
# Fetch the pinned AO source only; its recursive GPU dependencies are unnecessary.
git -c http.version=HTTP/1.1 submodule update --init --depth 1 -- third-party/ao
test "$(git -C third-party/ao rev-parse HEAD)" = "$(git rev-parse HEAD:third-party/ao)"
test -f third-party/ao/torchao/csrc/cpu/torch_free_kernels/interface/quantized_matmul.h
if [ ! -f "$TASK_STATE/venv/bin/python" ]; then
  python3 -m venv "$TASK_STATE/venv"
fi
source "$TASK_STATE/venv/bin/activate"
python -m pip install --timeout 120 --retries 10 --upgrade 'pip>=25.2,<27'
python -m pip install --timeout 120 --retries 10 --resume-retries 10 'cmake>=3.29,<4' 'PyYAML>=6,<7' 'packaging>=24.2' 'zstd' 'certifi'
# Code generation imports torchgen. Use a CPU PyTorch wheel in this isolated env.
python -m pip install --timeout 120 --retries 10 --resume-retries 10 'torch==2.9.0' --index-url https://download.pytorch.org/whl/cpu
cmake --preset llm -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$TASK_STATE/executorch/cmake-out" -DPYTHON_EXECUTABLE="$TASK_STATE/venv/bin/python"
cmake --build cmake-out --parallel "$JOBS" --target install --config Release
cp "$PROJECT_DIR/native/blistertrace_worker.cpp" examples/models/llama/blistertrace_worker.cpp
python - <<'PY'
from pathlib import Path
p=Path('examples/models/llama/CMakeLists.txt')
s=p.read_text()
marker='# BlisterTrace worker overlay'
if marker not in s:
    s+='''
# BlisterTrace worker overlay
add_executable(blistertrace_worker blistertrace_worker.cpp)
target_include_directories(blistertrace_worker PUBLIC ${_common_include_directories})
target_link_libraries(blistertrace_worker PUBLIC llama_runner ${link_libraries})
target_compile_options(blistertrace_worker PUBLIC ${_common_compile_options})
'''
    p.write_text(s)
PY
cmake -DCMAKE_INSTALL_PREFIX="$TASK_STATE/executorch/cmake-out" -DCMAKE_BUILD_TYPE=Release -DEXECUTORCH_BUILD_KERNELS_OPTIMIZED=ON -DPYTHON_EXECUTABLE="$TASK_STATE/venv/bin/python" -B cmake-out/examples/models/llama examples/models/llama
cmake --build cmake-out/examples/models/llama --parallel "$JOBS" --config Release --target llama_main blistertrace_worker
mkdir -p "$PROJECT_DIR/bin/$(uname -m)"
cp cmake-out/examples/models/llama/llama_main "$PROJECT_DIR/bin/$(uname -m)/"
cp cmake-out/examples/models/llama/blistertrace_worker "$PROJECT_DIR/bin/$(uname -m)/"
cp cmake-out/examples/models/llama/runner/libllama_runner.so "$PROJECT_DIR/bin/$(uname -m)/"
python - "$PROJECT_DIR" "$PIN" <<'PY'
import hashlib,json,platform,subprocess,sys
from pathlib import Path
root=Path(sys.argv[1]);target=root/'bin'/platform.machine()
data={'executorch_tag':'v1.0.0','executorch_commit':sys.argv[2],
      'architecture':platform.machine(),'platform':platform.platform(),
      'compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0],
      'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in target.iterdir() if p.is_file()},
      'pi_inference_verified':False}
(target/'build_receipt.json').write_text(json.dumps(data,indent=2))
print('Built native runtime:',target)
PY
