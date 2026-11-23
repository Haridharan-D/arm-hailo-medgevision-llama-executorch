import json
import os
import platform
import sys
from pathlib import Path

ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1]))
INSTALL=Path(sys.executable).parent if getattr(sys,'frozen',False) else ROOT

def settings():
    state=Path(os.environ.get('BLISTERTRACE_DATA',str(Path.home()/'BlisterTrace_Data'))).expanduser().resolve()
    state.mkdir(parents=True,exist_ok=True)
    config_path=Path(os.environ.get('BLISTERTRACE_CONFIG',str(INSTALL/'config.json')))
    value=json.loads(config_path.read_text()) if config_path.is_file() else {}
    defaults={'vision_backend':'onnx','profile_validated':False,'camera_source':'0',
              'llama_threads':3,'llama_prompt_mode':'adaptive-v1','llama_output_tokens':128,'llama_prompt_budget':1536,'advice_enabled':True,'port':8765,
              'test_images':str(INSTALL/'test_images'),'hef':str(INSTALL/'models/blistertrace.hef'),
              'anomaly_models':str(INSTALL/'models/anomaly'),
              'llama_artifacts':str(INSTALL/'llama/artifacts')}
    defaults.update(value)
    # A fresh Pi install reuses the already built and verified model/runtime.
    pi_llm=Path.home()/'BlisterTrace/Llama_ExecuTorch'
    if platform.machine() in {'aarch64','arm64'} and pi_llm.is_dir():
        defaults.setdefault('llama_runtime',str(pi_llm/'bin/aarch64/blistertrace_worker'))
        if not Path(defaults['llama_artifacts']).is_dir(): defaults['llama_artifacts']=str(pi_llm/'artifacts')
    elif os.name=='nt':
        defaults.setdefault('llama_runtime',str(INSTALL/'llama/bin/x86_64/blistertrace_worker'))
    defaults['data_dir']=state
    defaults['asset_dir']=ROOT/'assets'
    return defaults
