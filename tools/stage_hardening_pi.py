"""Stage new source alongside working installation, sharing read-only model assets."""
from pathlib import Path
import zipfile,json,shutil,subprocess,os
base=Path.home()/'BlisterTrace/BlisterTrace_App'
dest=Path.home()/'BlisterTrace/releases/hardening_20261122';dest.mkdir(parents=True,exist_ok=True)
archive=Path.home()/'BlisterTrace/Backups/HARDENING_SOURCE_20261122.zip'
with zipfile.ZipFile(archive) as z:
    for name in z.namelist():
        p=(dest/name).resolve()
        if dest.resolve() not in p.parents:raise ValueError('Archive escaped staging root')
    z.extractall(dest)
for name in ['assets','models','test_images','llama','.venv']:
    target=dest/name
    original=base/name
    if name=='llama' and not original.exists():original=Path.home()/'BlisterTrace/Llama_ExecuTorch'
    if target.is_symlink() and not target.exists():target.unlink()
    if not target.exists() and not target.is_symlink():target.symlink_to(original,target_is_directory=True)
runtime=dest/'native/bin/aarch64';runtime.mkdir(parents=True,exist_ok=True)
for p in (base/'native/bin/aarch64').iterdir():
    if p.is_file() and not (runtime/p.name).exists():shutil.copy2(p,runtime/p.name)
cfg=json.loads((base/'config.json').read_text());cfg.update(port=8766,advice_enabled=False,camera_source='0')
(dest/'candidate_config.json').write_text(json.dumps(cfg,indent=2))
print(json.dumps({'staging':str(dest),'models_shared_unchanged':True,'production_launcher_changed':False}))
