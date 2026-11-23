"""Capture the real Pi UI over an owned SSH tunnel; credentials stay in memory."""
import json,os,subprocess,time,socket
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'validation/hardening/20261122/browser_target';out.mkdir(parents=True,exist_ok=True)
key=Path.home()/'.ssh/blistertrace_pi';host='saul@10.217.96.233';port=8876;base=f'http://127.0.0.1:{port}'
remote='''import json,urllib.request
from pathlib import Path
v=json.loads((Path.home()/'BlisterTrace/Backups/validation_account_20261122.json').read_text())
r=urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8765/api/auth/login',data=json.dumps(v).encode(),headers={'Content-Type':'application/json'}))
cookie=r.headers['Set-Cookie'].split(';')[0].split('=',1)[1]
p=Path.home()/'BlisterTrace/releases/hardening_20261122/validation/hardening/20261122/target/report.json'
print(json.dumps({'cookie':cookie,'inspection_id':json.loads(p.read_text())['inspection']['inspection_id']}))
'''
auth=json.loads(subprocess.check_output(['ssh','-i',str(key),host,'python3','-'],input=remote.encode()))
tunnel=subprocess.Popen(['ssh','-i',str(key),'-N','-L',f'{port}:127.0.0.1:8765','-o','ExitOnForwardFailure=yes',host],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
try:
 for _ in range(80):
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',port))==0:break
    time.sleep(.1)
 with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True);context=browser.new_context(viewport={'width':1366,'height':768});context.add_cookies([{'name':'bt_session','value':auth['cookie'],'url':base,'httpOnly':True,'sameSite':'Strict'}]);page=context.new_page();errors=[];remote_requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:remote_requests.append(r.url) if not r.url.startswith((base,'blob:','data:')) else None)
    context.add_init_script("localStorage.setItem('bt.selected',JSON.stringify("+json.dumps(auth['inspection_id'])+"));")
    page.goto(base+'/');page.locator('#skip-boot').click();page.wait_for_function('window.BlisterTraceUI?.getState().initialLoaded',timeout=30000)
    expect(page.locator('#advice-content')).to_contain_text('Recommended operator action');page.screenshot(path=str(out/'pi_inspection_a_1366.png'),full_page=True)
    page.goto(base+'/classic');page.locator('#enter').click();page.locator('[data-screen=history]').click();page.wait_for_selector('#history-rows tr',timeout=20000);page.locator('#history-rows tr').first.click();page.wait_for_timeout(1200);page.screenshot(path=str(out/'pi_inspection_b_1366.png'),full_page=True)
    page.goto(base+'/operations');expect(page.locator('#vision-state')).to_contain_text('Hailo NPU ready');page.locator('#verify').click();expect(page.locator('#verification')).to_contain_text('Verified',timeout=20000);page.screenshot(path=str(out/'pi_operations_1366.png'),full_page=True)
    report={'passed':not errors and not remote_requests,'checks':['Actual Pi Hailo dashboard A with recorded advice','Actual Pi classic dashboard B','Real batch/audit/health workspace','Server image+audit verification','Zero external frontend requests'],'errors':errors,'external_requests':remote_requests,'scope':'Headless laptop browser rendering the real Pi service via SSH loopback tunnel; not a claim about Pi browser frame rate.'};(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));browser.close();assert report['passed']
finally:
    tunnel.terminate()
    try:tunnel.wait(timeout=10)
    except subprocess.TimeoutExpired:tunnel.kill()
