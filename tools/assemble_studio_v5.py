"""Assemble the isolated v5 executable with offline model and image sidecars."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist_v5/BlisterTrace'
assert (DIST/'BlisterTrace.exe').exists()
for folder in ('llama','test_images','models'):
    for p in (ROOT/folder).rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            dest=DIST/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
for name in ('config.json','README.md','STUDIO_V5.md','CONSOLE_ANOMALY_V4.md','TECHNICAL_REPORT.md','asset_hashes.json'):
    if (ROOT/name).exists():shutil.copy2(ROOT/name,DIST/name)
report={'exe':str(DIST/'BlisterTrace.exe'),'sha256':hashlib.sha256((DIST/'BlisterTrace.exe').read_bytes()).hexdigest(),
    'anomaly_profiles':3,'dataset_samples':60,'defect_folder_memberships':140,'windows_llama_requires_wsl':True}
(ROOT/'validation/v5_windows_build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
