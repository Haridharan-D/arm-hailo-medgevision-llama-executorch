"""Local candidate HTTP host for browser/API tests, separate from production."""
import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.config import settings
from app.server import create_app
import uvicorn
cfg=settings();cfg.update(advice_enabled=False,auth_required=False,vision_backend='onnx',port=8770)
cfg['data_dir']=ROOT/'validation/hardening/local_test_data';cfg['data_dir'].mkdir(parents=True,exist_ok=True)
if os.environ.get('BT_TEST_AUTH')=='1':
    cfg['data_dir']=ROOT/'validation/hardening/local_auth_test_data';cfg['data_dir'].mkdir(parents=True,exist_ok=True);cfg['auth_required']=True;cfg['port']=8772
uvicorn.run(create_app(cfg),host='127.0.0.1',port=cfg['port'],log_level='warning')
