import json,time,zipfile
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122';out=Path.home()/('BlisterTrace/Backups/BeforeVisualSuite_'+time.strftime('%Y%m%d_%H%M%S')+'.zip')
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for name in ['app','web','docs','tools']:
        for p in (root/name).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:z.write(p,p.relative_to(root))
    z.write(root/'production_config.json','production_config.json')
print(json.dumps({'source_backup':str(out),'models_unchanged':True}))
