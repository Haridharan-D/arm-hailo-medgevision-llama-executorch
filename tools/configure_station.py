"""Configure a clone using local paths, without changing system services."""
import argparse
import json
import platform
import shutil
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--backend', choices=['onnx', 'hailo'], default='onnx')
parser.add_argument('--runtime', type=Path)
parser.add_argument('--no-advice', action='store_true')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
path = root / 'config.json'
value = json.loads(path.read_text()) if path.exists() else {}
if path.exists():
    shutil.copy2(path, path.with_suffix('.json.before_setup'))
runtime = args.runtime
if runtime is None:
    for candidate in [root/'native/bin'/platform.machine()/'blistertrace_instrumented',
                      root/'llama/bin'/platform.machine()/'blistertrace_worker',
                      root/'llama/bin/x86_64/blistertrace_worker']:
        if candidate.is_file():
            runtime = candidate
            break
value.update(vision_backend=args.backend, auth_required=False,
             profile_validated=False, advice_enabled=not args.no_advice,
             llama_threads=3, llama_prompt_mode='adaptive-v1',
             llama_output_tokens=128, llama_prompt_budget=1536,
             llama_artifacts=str(root/'llama/artifacts'))
if runtime:
    value['llama_runtime'] = str(runtime.resolve())
path.write_text(json.dumps(value, indent=2))
print('Configured:', path, 'backend:', args.backend)
if not runtime and not args.no_advice:
    print('Missing native Llama runtime: advice will explicitly fall back until installed.')
if args.backend == 'hailo':
    print('Requires actual Hailo-8 and matching HailoRT/driver. Configuration is not validation.')
