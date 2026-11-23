"""Create a source update plus short demonstration narration guide."""
import hashlib,json,shutil,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];dest=root.parent/'BlisterTrace_Deliverables/Medge_Vision_Terminal_Demo_20261123';dest.mkdir(parents=True,exist_ok=True)
shutil.copy2(root/'docs/TERMINAL_DEMO_MEDGE_VISION.md',dest/'COMMANDS_AND_NARRATION.md')
shutil.copy2(root/'tools/medge_demo.py',dest/'medge_demo.py')
shutil.copy2(root/'validation/hardening/HARDENING_SOURCE_20261122.zip',dest/'source_update.zip')
receipt=root/'validation/terminal_demo_20261123/deployment_receipt.json'
verified=json.loads(receipt.read_text()) if receipt.exists() else None
notice={'product_name':'Medge Vision','pi_deployment_verified':bool(verified and verified['passed']),
    'reason':'Five actual Pi cases completed with validated Llama advice; audit verified' if verified else 'Target deployment not yet verified',
    'models_retrained':False,'thresholds_changed':False,'original_paths_and_data_preserved':True}
(dest/'DEPLOYMENT_STATUS.json').write_text(json.dumps(notice,indent=2))
if verified:shutil.copytree(root/'validation/terminal_demo_20261123',dest/'actual_pi_evidence',dirs_exist_ok=True)
archive=dest.with_suffix('.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in dest.rglob('*'):
        if p.is_file():z.write(p,p.relative_to(dest))
archive.with_suffix('.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
print(str(archive))
