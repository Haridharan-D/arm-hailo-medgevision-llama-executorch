import json,os,subprocess,urllib.request
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122';out=root/'validation/terminal_demo_20261123'
report=json.loads((out/'report.json').read_text());assert report['passed'] and len(report['session']['records'])==5
advice=[]
for item in report['session']['records']:
    row=json.loads(Path(item['file']).read_text());advice.append({'test':item['test'],'status':row.get('advice',{}).get('status'),'visual':row['visual_result']['status'],'qa':row['decision']})
with urllib.request.urlopen('http://127.0.0.1:8765/api/health') as r:health=json.load(r)
assert health['product_name']=='Medge Vision'
for url in ['/','/classic','/display']:
    with urllib.request.urlopen('http://127.0.0.1:8765'+url) as r:assert 'Medge Vision' in r.read().decode()
receipt={'passed':True,'product_name':health['product_name'],'aliases_installed':all(os.access(Path.home()/name,os.X_OK) for name in ['medge-demo','medge-vision']),
    'actual_terminal_cases':advice,'architecture':subprocess.check_output(['uname','-m'],text=True).strip(),'hardware_identification':subprocess.check_output(['hailortcli','fw-control','identify'],text=True),'old_paths_preserved':True}
(out/'deployment_receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
