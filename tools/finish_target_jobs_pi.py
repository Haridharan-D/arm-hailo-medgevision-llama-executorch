"""Validate isolated candidate completely before starting the production service."""
import subprocess,json,time,sys,os,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1];py=root/'.venv/bin/python';out=root/'validation/hardening/20261122'
while not (out/'matrix_3b_job.json').exists():time.sleep(10)
assert json.loads((out/'matrix_3b_job.json').read_text())['exit_code']==0
for name in ['matrix_concurrent_validated','matrix_3b_pilot']:
    summary=json.loads((out/name/'summary.json').read_text());assert all(r['concurrent_load_valid'] for r in summary['rows'])
commands=[['tools/build_instrumented_pi.py'],['tools/probe_context_pi.py'],['tools/validate_storage_fault_pi.py'],['tools/verify_frozen_target_pi.py'],
          ['tools/staged_server_pi.py','start','--advice'],['tools/validate_hardening_target.py'],['tools/restart_recovery_pi.py'],['tools/validate_usb_target.py']]
for i,args in enumerate(commands):
    print('VALIDATING',args,flush=True)
    result=subprocess.run([str(py),*args],cwd=root)
    (out/f'final_step_{i}.json').write_text(json.dumps({'command':args,'exit_code':result.returncode}))
    if result.returncode:raise SystemExit(result.returncode)
for name in ['context','storage_fault','target','restart','usb']:
    data=json.loads((out/name/'report.json').read_text());assert data['passed'],name
(out/'staging_acceptance.json').write_text(json.dumps({'passed':True,'scope':'Isolated-data application with real Hailo and USB, native Llama, audit and restart recovery; no accuracy or certification claim.'},indent=2))
shutil.copy2(out/'target/report.json',out/'target/staging_report.json')
shutil.copy2(out/'target/batch_report.pdf',out/'target/staging_batch_report.pdf')
print('Candidate target acceptance passed. Promoting preserved release.',flush=True)
subprocess.run([str(py),'tools/promote_hardening_pi.py'],cwd=root,check=True)
subprocess.run([str(py),'tools/validate_hardening_target.py'],cwd=root,check=True)
(out/'deployment_complete.json').write_text(json.dumps({'complete':True,'production_service':'blistertrace.service','auth_required':True},indent=2))
