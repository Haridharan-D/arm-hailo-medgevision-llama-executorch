"""Package verified images and raw evidence; never market selection as accuracy."""
import collections,csv,hashlib,json,shutil,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];suite=root.parent/'BlisterTrace_TestSuite_20261122';ev=root/'validation/visual_suite_20261122'
report=json.loads((suite/'verification.json').read_text());assert report['passed'] and report['checked']==29
browser=json.loads((ev/'browser/report.json').read_text());assert browser['passed']
counts=collections.defaultdict(collections.Counter)
for row in report['results']:
    assert row['matched'] and hashlib.sha256((suite/row['file']).read_bytes()).hexdigest()==row['sha256']
    counts[row.get('profile','yolo')][row['actual_visual']]+=1
assert counts['yolo']=={'SAFE':2,'WARNING':2,'DEFECTIVE':7}
for name in ['mvtec_pill','mvtec_capsule','visa_capsules']:assert counts[name]=={'SAFE':2,'WARNING':2,'DEFECTIVE':2}
shutil.copy2(root/'docs/VISUAL_TEST_SUITE.md',suite/'TEST_GUIDE.md')
shutil.copy2(root/'test_images/SCOA_LICENSE.txt',suite/'SCOA_LICENSE.txt')
evidence=suite/'verification_evidence';evidence.mkdir(exist_ok=True)
for name in ['target_results.jsonl','tests.txt','tests.xml','screened_anomaly_outputs.json','frozen_models.json','windows_report.json','final_receipt.json']:
    if (ev/name).exists():shutil.copy2(ev/name,evidence/name)
shutil.copytree(ev/'browser',evidence/'browser',dirs_exist_ok=True)
for model in ['mvtec_pill','mvtec_capsule','visa_capsules']:shutil.copy2(root/'models/anomaly'/model/'contract.json',evidence/(model+'_contract.json'))
source=root/'validation/hardening/HARDENING_SOURCE_20261122.zip';shutil.copy2(source,evidence/'source.zip')
summary={'actual_pi_cases':29,'matched':29,'counts':{k:dict(v) for k,v in counts.items()},'browser_checks':len(browser['cases']),'visual_policy':'visual-check-v1',
    'models_and_thresholds_unchanged':True,'independent_accuracy_claim':False,'warning_examples':'Synthetic unusable-capture challenges',
    'known_limits':'Selected after inference; original dual-cap misses retained; VisA remains low-recall research profile; SAFE is visual observation only.'}
(suite/'SUMMARY.json').write_text(json.dumps(summary,indent=2))
manifest={p.relative_to(suite).as_posix():{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in suite.rglob('*') if p.is_file() and p.name!='PACKAGE_MANIFEST.json'}
(suite/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
archive=root.parent/'BlisterTrace_Deliverables/BlisterTrace_Visual_TestSuite_20261122.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in suite.rglob('*'):
        if p.is_file():z.write(p,Path(suite.name)/p.relative_to(suite))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
archive.with_suffix('.json').write_text(json.dumps({'file':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'models_included':False},indent=2))
print(json.dumps(dict(archive=str(archive),**summary),indent=2))
