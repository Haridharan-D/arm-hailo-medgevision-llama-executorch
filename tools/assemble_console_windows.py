"""Assemble the v4 build from prepared assets, without overwriting the reviewed adviser."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist_v4/BlisterTrace'
assert (DIST/'BlisterTrace.exe').is_file(),'Run PyInstaller with dist_v4 first'
for folder in ('llama','test_images','models'):
    for source in (ROOT/folder).rglob('*'):
        if source.is_file() and '__pycache__' not in source.parts:
            target=DIST/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
for name in ('config.json','README.md','CONSOLE_ANOMALY_V4.md','TECHNICAL_REPORT.md','SUBMISSION_CHECKLIST.md','asset_hashes.json'):
    if (ROOT/name).exists():shutil.copy2(ROOT/name,DIST/name)
report={'executable':str(DIST/'BlisterTrace.exe'),'sha256':hashlib.sha256((DIST/'BlisterTrace.exe').read_bytes()).hexdigest(),
    'anomaly_models':3,'offline_sidecars_included':True,'windows_llama_requires_wsl':True,
    'pi_uses_native_arm_runtime':True,'prior_dist_preserved':True}
(ROOT/'validation/v4_windows_build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
