import json,subprocess,urllib.request
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122';out=root/'validation/visual_suite_20261122'
def call(path):
    with urllib.request.urlopen('http://127.0.0.1:8765'+path,timeout=60) as r:return json.load(r)
auth=call('/api/auth/me');status=call('/api/status');audit=call('/api/audit/verify')
assert not auth['required'] and status['vision_backend']=='hailo' and audit['valid']
receipt={'service':subprocess.check_output(['systemctl','--user','is-active','blistertrace.service'],text=True).strip(),
    'authentication_required':auth['required'],'vision_backend':status['vision_backend'],'audit':audit,
    'suite':str(Path.home()/'BlisterTrace_TestSuite_20261122'),'software_version':status['version']}
(out/'final_receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({'service':receipt['service'],'audit_valid':audit['valid'],'sign_in_required':auth['required']}))
