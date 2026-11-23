"""Keep the kiosk update/evidence separate from earlier authenticated validation."""
import hashlib,json,shutil,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'validation/kiosk_20261122'
windows=json.loads((root/'validation/hardening/20261122/windows/report.json').read_text())
assert windows['passed'] and not windows['authentication']['required']
shutil.copy2(root/'validation/hardening/20261122/windows/report.json',out/'windows_report.json')
report={'sign_in_required':False,'accounts_deleted':False,'production_decision_logic_changed':False,
        'main_monitor':'HDMI-A-1 1600x900 fullscreen','second_monitor':'HDMI-A-2 1024x768 fullscreen',
        'one_command':'~/blistertrace','status_mapping':{'PASS':'SAFE','REVIEW':'WARNING','HOLD':'REJECTED'},
        'python_tests':54,'actual_pi_browser':json.loads((out/'browser_report.json').read_text()),
        'windows_executable_passed':True,'windows_llama_status':windows['record']['advice']['status']}
(out/'summary.json').write_text(json.dumps(report,indent=2))
dest=root.parent/'BlisterTrace_Deliverables/BlisterTrace_Dual_Display_Kiosk_20261122.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for p in out.iterdir():
        if p.is_file() and p.suffix in {'.json','.png','.xml','.txt','.log'}:z.write(p,Path('evidence')/p.name)
    z.write(root/'docs/DUAL_DISPLAY_KIOSK.md','README.md')
    z.write(root/'validation/hardening/HARDENING_SOURCE_20261122.zip','source.zip')
dest.with_suffix('.json').write_text(json.dumps({'archive':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'large_models_included':False,'credentials_included':False},indent=2))
print(json.dumps({'archive':str(dest),'passed':True}))
