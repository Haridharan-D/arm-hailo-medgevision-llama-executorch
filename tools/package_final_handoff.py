"""Package actual saved evidence, source and documentation; exclude state/credentials."""
import hashlib,json,shutil,zipfile,xml.etree.ElementTree as ET,statistics
from pathlib import Path
root=Path(__file__).resolve().parents[1]
ev=root/'validation/hardening/20261122'
dest=root.parent/'BlisterTrace_Deliverables/Hardening_20261122'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf8')
suite=ET.parse(ev/'tests/junit.xml').getroot().find('testsuite')
test={k:int(suite.attrib[k]) for k in ['tests','failures','errors','skipped']}
test.update(seconds=float(suite.attrib['time']),executed=True,physical_csi_tested=False)
write(ev/'tests/summary.json',test)
old=read(root/'validation/hardening/baseline_manifest.json');changes={'added':[],'modified':[],'removed':[]}
for name,entry in old.items():
    p=root/name.replace('\\','/')
    if not p.is_file():changes['removed'].append(name);continue
    if hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:changes['modified'].append(name)
for folder in ['app','advisor_src','web','tools','tests','docs','native','deploy']:
    for p in (root/folder).rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or 'bin' in p.parts:continue
        rel=str(p.relative_to(root))
        if rel not in old and rel.replace('\\','/') not in old:changes['added'].append(rel)
write(dest/'CHANGES.json',changes)
for name in ['frozen_target.json','final_runtime_manifest.json','runtime_inspection.json','model_selection.json']:
    shutil.copy2(ev/name,dest/name)
write(dest/'MODEL_MANIFEST.json',{'frozen_artifacts':read(ev/'frozen_target.json')['checks'],
    'challenger':{'repository':'MediaTek-Research/Llama-3.2-3B-Instruct-SpinQuant_INT4_EO8-executorch',
      'revision':'c2ac31ba586e93aad76b2f72aeaf0ecb7d061661','filename':'llama3_2-2048-spin.pte',
      'bytes':2553367552,'sha256':'55d7f829f13063331c3d421816128553b545847628e1f0c71f44a78cb9229271'},
    'not_in_source_zip':'Large PTE/ONNX/HEF files and raw datasets remain in the preserved installation; retain original licenses and gated access.',
    'selected':'Existing1B SpinQuant PTE, adaptive-v1 prompt; vision thresholds unchanged'})
shutil.copytree(root/'docs',dest/'docs',dirs_exist_ok=True)
for name in ['README.md','SUBMISSION_RUNBOOK.md']:shutil.copy2(root/name,dest/name)
refs=dest/'export_reference';refs.mkdir(exist_ok=True)
for p in (root/'llama/artifacts').iterdir():
    if p.name in {'README.md','params.json'} or p.suffix=='.ipynb':shutil.copy2(p,refs/p.name)
for p in [root/'llama/EXECUTORCH_LICENSE',root/'validation/hardening/baseline_manifest.json']:
    shutil.copy2(p,refs/p.name)
raw=dest/'raw_evidence';raw.mkdir(exist_ok=True)
for p in ev.rglob('*'):
    rel=p.relative_to(ev)
    if not p.is_file() or any(part in {'data','images','backups','spool','__pycache__'} for part in rel.parts):continue
    if p.suffix not in {'.json','.jsonl','.txt','.xml','.png','.jpg','.log','.pdf'}:continue
    if p.name in {'config.json','users.json','validation_account_20261122.json'} or p.stat().st_size>20*1024*1024:continue
    target=raw/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
for folder in ['quality_1b_baseline','matrix']:
    for p in (root/'validation/hardening'/folder).glob('*.json*'):
        target=raw/'historical_or_baseline'/folder/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
source=root/'validation/hardening/HARDENING_SOURCE_20261122.zip';shutil.copy2(source,dest/source.name)
usb=read(ev/'usb/report.json');fps=[r['camera']['fps'] for r in usb['samples'] if r.get('camera',{}).get('running')]
write(dest/'EXECUTED_CHECKS.json',{'python':test,'native_boundary':read(ev/'json_boundary/report.json'),
    'target_passed':read(ev/'target/report.json')['passed'],'usb_passed':usb['passed'],
    'usb_camera_loop_fps':{'n':len(fps),'min':min(fps),'median':statistics.median(fps),'max':max(fps),'scope':'Observed application camera loop, unlabeled scene; not factory throughput.'},
    'browser_real_pi':read(ev/'browser_target/report.json'),'windows_passed':read(ev/'windows/report.json')['passed'],
    'human_semantic_review_complete':False,'camera_product_profile_validated':False})
manifest={str(p.relative_to(dest)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in dest.rglob('*') if p.is_file() and p.name!='MANIFEST.json'}
write(dest/'MANIFEST.json',manifest)
archive=dest.parent/'BlisterTrace_Hardening_Handoff_20261122.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in dest.rglob('*'):
        if p.is_file():z.write(p,Path(dest.name)/p.relative_to(dest))
write(archive.with_suffix('.json'),{'file':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'credentials_included':False,'large_model_binaries_included':False})
print(json.dumps({'archive':str(archive),'files':len(manifest),'bytes':archive.stat().st_size,'tests':test,'observed_usb_fps_median':statistics.median(fps)},indent=2))
