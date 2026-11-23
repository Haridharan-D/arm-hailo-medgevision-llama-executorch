"""Observe actual second-monitor IDs after consecutive real model requests."""
import json,subprocess,time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1];out=root/'validation/display_sync_20261123';out.mkdir(exist_ok=True)
key=Path.home()/'.ssh/blistertrace_pi';host='saul@192.168.137.189'
tunnel=subprocess.Popen(['ssh','-i',str(key),'-o','BatchMode=yes','-o','ExitOnForwardFailure=yes','-N','-L','8923:127.0.0.1:9223','-L','8924:127.0.0.1:9224',host],creationflags=subprocess.CREATE_NO_WINDOW)
try:
 time.sleep(1)
 with sync_playwright() as p:
    a=p.chromium.connect_over_cdp('http://127.0.0.1:8923');b=p.chromium.connect_over_cdp('http://127.0.0.1:8924')
    main=next(page for c in a.contexts for page in c.pages if ':8765/' in page.url);display=next(page for c in b.contexts for page in c.pages if '/display' in page.url)
    errors=[];display.on('pageerror',lambda e:errors.append(str(e)));display.reload()
    results=[]
    cases=[('safe','/api/library/inspect',{'name':'acceptance_demo/safe/safe_01.jpg'},'SAFE'),
           ('crack','/api/library/inspect',{'name':'acceptance_demo/defective/crack/crack.jpg'},'REJECTED'),
           ('warning','/api/library/inspect',{'name':'acceptance_demo/warning/warning_01.png'},'WARNING'),
           ('anomaly','/api/anomaly/inspect',{'profile':'mvtec_capsule','sample':'demo/defective/defective_01.png'},'REJECTED'),
           ('safe_repeat','/api/library/inspect',{'name':'acceptance_demo/safe/safe_02.jpg'},'SAFE')]
    for name,url,payload,label in cases:
        record=main.evaluate('async({url,payload})=>{const r=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});if(!r.ok)throw Error(await r.text());return r.json();}',{'url':url,'payload':payload})
        began=time.monotonic();expect(display.locator('#identity')).to_have_text('Inspection '+record['inspection_id'],timeout=15000);expect(display.locator('#verdict')).to_have_text(label)
        results.append({'case':name,'inspection_id':record['inspection_id'],'display':label,'observed_after_response_ms':round((time.monotonic()-began)*1000,2)})
        display.screenshot(path=str(out/(name+'.png')));print(name,label,record['inspection_id'],flush=True)
    # A single transient failure must not terminate the poll loop.
    def fail_once(route):route.fulfill(status=503,body='{"detail":"Controlled transient display test"}',content_type='application/json')
    display.route('**/api/display',fail_once,times=1)
    expect(display.locator('#link-state')).to_contain_text('RECONNECTING',timeout=10000)
    expect(display.locator('#link-state')).to_contain_text('STATION ONLINE',timeout=12000)
    expect(display.locator('#identity')).to_have_text('Inspection '+record['inspection_id'])
    report={'passed':not errors,'actual_second_monitor':True,'cases':results,'transient_failure_recovered':True,'page_errors':errors}
    (out/'report.json').write_text(json.dumps(report,indent=2));assert report['passed'];print(json.dumps(report,indent=2))
    # Show the last SAFE result on the main UI once the operator enters.
    main.evaluate('(id)=>localStorage.setItem("bt.selected",JSON.stringify(id))',record['inspection_id']);main.reload()
finally:
 tunnel.terminate()
 try:tunnel.wait(timeout=5)
 except subprocess.TimeoutExpired:tunnel.kill()
