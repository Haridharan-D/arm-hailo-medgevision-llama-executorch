"""Add a distinct executable target; never overwrite baseline worker or model."""
from pathlib import Path
import subprocess,hashlib,json
root=Path.home()/'blistertrace_llm_build/executorch'
project=Path.home()/'BlisterTrace/releases/hardening_20261122'
if not project.exists():project=Path.home()/'BlisterTrace/BlisterTrace_App'
src=project/'native/blistertrace_instrumented.cpp'
target=root/'examples/models/llama/blistertrace_instrumented.cpp';target.write_bytes(src.read_bytes())
(target.parent/'json_boundary.h').write_bytes((src.parent/'json_boundary.h').read_bytes())
runner=(root/'extension/llm/runner/text_llm_runner.cpp').read_text()
runner=runner.replace('int num_prompt_tokens = prompt_tokens.size();','int num_prompt_tokens = prompt_tokens.size();\n  stats_->token_encode_end_ms = time_in_ms();')
runner=runner.replace('auto prefill_res = text_prefiller_->prefill(prompt_tokens, pos_);','stats_->model_execution_start_ms = time_in_ms();\n  auto prefill_res = text_prefiller_->prefill(prompt_tokens, pos_);')
(root/'examples/models/llama/blistertrace_runner_timed.cpp').write_text(runner)
cm=root/'examples/models/llama/CMakeLists.txt';text=cm.read_text()
text=text.replace('add_executable(blistertrace_instrumented blistertrace_instrumented.cpp)','add_executable(blistertrace_instrumented blistertrace_instrumented.cpp blistertrace_runner_timed.cpp)')
marker='# BlisterTrace instrumented candidate'
if marker not in text:
    text=text+'\n'+marker+'''\nadd_executable(blistertrace_instrumented blistertrace_instrumented.cpp blistertrace_runner_timed.cpp)
target_include_directories(blistertrace_instrumented PUBLIC ${_common_include_directories})
target_link_libraries(blistertrace_instrumented PUBLIC llama_runner ${link_libraries})
target_compile_options(blistertrace_instrumented PUBLIC ${_common_compile_options})
'''
cm.write_text(text)
subprocess.run(['cmake','-S','examples/models/llama','-B','cmake-out/examples/models/llama'],cwd=root,check=True)
subprocess.run(['cmake','--build','cmake-out/examples/models/llama','--target','blistertrace_instrumented','--parallel','2'],cwd=root,check=True)
binary=root/'cmake-out/examples/models/llama/blistertrace_instrumented'
dest=src.parent/'bin/aarch64';dest.mkdir(parents=True,exist_ok=True)
(dest/binary.name).write_bytes(binary.read_bytes());(dest/binary.name).chmod(0o755)
library=root/'cmake-out/examples/models/llama/runner/libllama_runner.so'
(dest/library.name).write_bytes(library.read_bytes())
receipt={'baseline_untouched':True,'binary_sha256':hashlib.file_digest(binary.open('rb'),'sha256').hexdigest(),'source_sha256':hashlib.file_digest(src.open('rb'),'sha256').hexdigest()}
receipt['libllama_runner_sha256']=hashlib.file_digest(library.open('rb'),'sha256').hexdigest()
(dest/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
