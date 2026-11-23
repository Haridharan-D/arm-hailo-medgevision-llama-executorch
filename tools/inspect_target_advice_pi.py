import json
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122';p=root/'validation/hardening/20261122/target/report.json'
r=json.loads(p.read_text());a=r['advisory']
print(json.dumps({'status':a['status'],'fallback_reason':a.get('fallback_reason'),'tokens':a.get('prompt_tokens'),'metrics':a.get('runtime_metrics'),'snapshot':r['inspection']['defects'],'latest_error':r['stability_samples'][-1].get('llama_error')},indent=2))
