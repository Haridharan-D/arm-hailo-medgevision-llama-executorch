import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];audit=json.loads((root/'validation/hardening/pi_audit.json').read_text());rows=[]
for row in audit['files']:
    p=Path(row['path'])
    if p.suffix not in {'.onnx','.hef','.pte'} and p.name!='thresholds.json':continue
    with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    rows.append({'path':str(p),'expected':row['sha256'],'actual':sha,'matched':row['sha256']==sha})
report={'passed':bool(rows) and all(r['matched'] for r in rows),'checks':rows}
extra={Path.home()/'BlisterTrace/Llama_ExecuTorch/artifacts/Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte':'8715cdba9e91f6bede00cc5f2d6b12397b95225da5630c4972a8da03001cda3b',
       Path.home()/'BlisterTrace/Llama_ExecuTorch/bin/aarch64/blistertrace_worker':'212ca6ceaa62f3179217f6f3db6e663a53ea31467c2a22359449f3bdca871f2b'}
anomaly={'mvtec_capsule':'c8110349b6c52a148be7da5442445a32031911ebf64d8d1fbcad2afb0902a157','mvtec_pill':'4670cd45c0d465bfbcdbdea2ca2711dd21e0b1eb026beb308e484b4f2e99c220','visa_capsules':'ff414f1e16b12f5a9eac9ac0b12886773645279eae61e2123c0a45ac70dcccbf'}
for p in (Path.home()/'BlisterTrace/BlisterTrace_App/models/anomaly').rglob('*.onnx'):
    for name,sha in anomaly.items():
        if name in str(p):extra[p]=sha
for p,expected in extra.items():
    with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    rows.append({'path':str(p),'expected':expected,'actual':sha,'matched':expected==sha})
report['passed']=all(r['matched'] for r in rows)
out=root/'validation/hardening/20261122';out.mkdir(parents=True,exist_ok=True);(out/'frozen_target.json').write_text(json.dumps(report,indent=2));print(json.dumps({'passed':report['passed'],'files':len(rows)}))
if not report['passed']:raise SystemExit(1)
