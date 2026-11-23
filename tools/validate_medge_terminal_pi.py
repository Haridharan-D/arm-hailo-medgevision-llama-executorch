"""Run the exact short terminal commands and retain unedited output."""
import json,subprocess,time
from pathlib import Path
root=Path.home()/'BlisterTrace/releases/hardening_20261122';out=root/'validation/terminal_demo_20261123';out.mkdir(exist_ok=True)
commands=[['start'],['models'],*(["test",str(i)] for i in range(1,6)),['summary']]
results=[]
for index,args in enumerate(commands):
    began=time.monotonic();command=[str(Path.home()/'medge-demo'),*args]
    with (out/f'{index:02d}_{args[0]}.txt').open('w') as f:
        child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        for line in child.stdout:print(line,end='',flush=True);f.write(line);f.flush()
        code=child.wait()
    results.append({'command':'~/medge-demo '+' '.join(args),'exit_code':code,'elapsed_s':round(time.monotonic()-began,2)})
    (out/'command_receipts.json').write_text(json.dumps(results,indent=2))
    if code:raise SystemExit(code)
session=json.loads((Path.home()/'BlisterTrace_Data/terminal_demo_state.json').read_text())
report={'passed':all(r['exit_code']==0 for r in results),'commands':results,'session':session,'scope':'Actual Pi Hailo/ONNX/ExecuTorch CLI demonstration; selected five images, not accuracy benchmark.'}
(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({'passed':report['passed'],'cases':len(session['records']),'report':str(out/'report.json')}))
