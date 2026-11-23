"""Package reviewed v4 source and evidence; leave v3 evidence and licensed Llama assets in place."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent/'BlisterTrace_Deliverables/v4_20261120'
OUT.mkdir(parents=True,exist_ok=True)
folders=('app','web','advisor_src','tools','tests','assets','models','test_images')
files=[p for d in folders for p in (ROOT/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
files += [p for p in ROOT.iterdir() if p.is_file() and p.suffix in {'.py','.sh','.txt','.json','.md','.spec'}]
for name in ('check_console_v4.py','check_pipeline_v4.py','check_windows_v4.py','collect_deployment_v4.py','verify_deployment_v4.py'):
    files.append(ROOT/'validation'/name)
for directory in ('v4_anomaly_host','v4_anomaly_pi','v4_llama_threads','v4_console_pi','v4_console_final','v4_pipeline_pi','v4_windows','v4_deployment'):
    source=ROOT/'validation'/directory
    if source.exists():shutil.copytree(source,OUT/'evidence'/directory,dirs_exist_ok=True)
for name in ('v4_windows_build.json','v4_deployed_hashes.json','v4_code_parity.json'):
    if (ROOT/'validation'/name).exists():shutil.copy2(ROOT/'validation'/name,OUT/'evidence'/name)
guide=ROOT/'CONSOLE_ANOMALY_V4.md';shutil.copy2(guide,OUT/guide.name)
checks={name:json.loads((ROOT/'validation'/name/'report.json').read_text()).get('all_passed')
        for name in ('v4_console_pi','v4_console_final','v4_pipeline_pi','v4_windows')}
assert all(checks.values()),checks
manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(OUT/'SOURCE_HASHES.json').write_text(json.dumps(manifest,indent=2))
report={'date':'2026-11-20','checks':checks,'unit_tests':{'command':'python -m pytest tests -q','passed':21},
    'whole_page_scroll':False,'long_content':'Internal tab panes may scroll',
    'models':'Three complete EfficientAD-S profiles exported to ONNX CPU; YOLO weights and disposition rules preserved',
    'sample_checks':{'mvtec_pill':'6/6','mvtec_capsule':'5/6','visa_capsules':'3/6, all three selected defects missed'},
    'sample_scope':'18 selected held-out examples, not a full benchmark or blister camera accuracy',
    'fresh_llama_two_case_mean_seconds':{'threads_2':17.706,'threads_3':14.549,'threads_4':13.304},
    'selected_threads':3,'cpu_camera_target_threads':2,'advice_reuse':'Explicit cache label, new generation bypass via Regenerate',
    'pi_backend':'ONNX CPU; Hailo physically disconnected','anomaly_hailo_compilation':False,
    'independent_local_blister_camera_accuracy':'pending','qa_semantic_review':'pending',
    'submission_readiness':'Working measured project update, not industrial/regulatory acceptance',
    'windows_executable':str(ROOT/'dist_v4/BlisterTrace/BlisterTrace.exe'),'windows_llama':'Verified locally via WSL, not native Windows'}
(OUT/'VALIDATION_SUMMARY.json').write_text(json.dumps(report,indent=2))
archive=OUT/'BlisterTrace_Console_Anomaly_v4_Source.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
    for p in files:z.write(p,'BlisterTrace_App/'+p.relative_to(ROOT).as_posix())
    for p in (OUT/'evidence').rglob('*'):
        if p.is_file():z.write(p,'evidence/'+p.relative_to(OUT/'evidence').as_posix())
    for name in ('SOURCE_HASHES.json','VALIDATION_SUMMARY.json'):z.write(OUT/name,name)
    for name in ('export_deployment.py','download_test_samples.py','MODEL_AUDIT.json'):
        p=ROOT.parent/'EffNet_Kaggle'/name
        if p.exists():z.write(p,'training_provenance/'+name)
    for p in (ROOT.parent/'EffNet_Kaggle/deployment_src').rglob('*.py'):
        z.write(p,'training_provenance/deployment_src/'+p.relative_to(ROOT.parent/'EffNet_Kaggle/deployment_src').as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
receipt={'source_archive':str(archive),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
    'llama_weights_in_archive':False,'llama_reuse':'Pi reuses existing verified Llama_ExecuTorch artifacts; Windows dist_v4 includes sidecars',
    'guide':str(OUT/'CONSOLE_ANOMALY_V4.md')}
(OUT/'PACKAGE.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
