"""Check actual physical Chromium windows via loopback CDP/SSH, without accounts."""
import json,subprocess,time,socket
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1];out=root/'validation/kiosk_20261122';out.mkdir(exist_ok=True)
key=Path.home()/'.ssh/blistertrace_pi';host='saul@10.217.96.233'
tunnel=subprocess.Popen(['ssh','-i',str(key),'-o','BatchMode=yes','-o','ExitOnForwardFailure=yes','-N','-L','8923:127.0.0.1:9223','-L','8924:127.0.0.1:9224',host],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
try:
 for _ in range(80):
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',8923))==0:break
    time.sleep(.2)
 with sync_playwright() as p:
    primary=p.chromium.connect_over_cdp('http://127.0.0.1:8923');secondary=p.chromium.connect_over_cdp('http://127.0.0.1:8924')
    main=next(page for c in primary.contexts for page in c.pages if ':8765/' in page.url)
    display=next(page for c in secondary.contexts for page in c.pages if '/display' in page.url)
    display.reload()
    if main.locator('#splash').is_visible():main.locator('#skip-boot').click()
    main.wait_for_function('window.BlisterTraceUI?.getState().initialLoaded',timeout=45000)
    auth=main.evaluate('fetch("/api/auth/me").then(r=>r.json())');assert auth['required'] is False
    assert main.locator('#splash').is_hidden()
    rows=main.evaluate('fetch("/api/inspections").then(r=>r.json())');record=next((r for r in rows if r.get('decision')=='HOLD'),rows[0])
    main.evaluate('(id)=>localStorage.setItem("bt.selected",JSON.stringify(id))',record['inspection_id']);main.reload();main.locator('#skip-boot').click()
    main.wait_for_function('window.BlisterTraceUI?.getState().initialLoaded',timeout=45000)
    main.wait_for_function('(id)=>window.BlisterTraceUI.getSelected()?.inspection_id===id',arg=record['inspection_id'],timeout=20000)
    assert main.evaluate('window.BlisterTraceUI.getSelected().decision')==record['decision']
    measurements=[]
    for label,browser,page in [('main',primary,main),('status',secondary,display)]:
        session=browser.new_browser_cdp_session();target=page.context.new_cdp_session(page).send('Target.getTargetInfo')['targetInfo']['targetId']
        bounds=session.send('Browser.getWindowForTarget',{'targetId':target})
        dims=page.evaluate('({width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth,scrollHeight:document.documentElement.scrollHeight,dpr:devicePixelRatio})')
        measurements.append(dict(name=label,url=page.url,bounds=bounds,viewport=dims))
        page.screenshot(path=str(out/(label+'_physical_monitor.png')))
    assert measurements[0]['viewport']['width']==1600,measurements
    assert measurements[0]['viewport']['height']==900,measurements
    assert measurements[1]['viewport']['width']==1024,measurements
    assert measurements[1]['bounds']['bounds']['left']==1600,measurements
    assert all(m['viewport']['scrollWidth']<=m['viewport']['width'] for m in measurements)
    cases=main.evaluate('''async()=>{const {displayVerdict}=await import('/static/js/verdict.js');return [{decision:'REVIEW',capture_valid:true},{decision:'REVIEW',capture_valid:false},{decision:'HOLD',capture_valid:true}].map(record=>displayVerdict(record).label);}''')
    assert cases==['SAFE','WARNING','REJECTED']
    expect(display.locator('#verdict')).not_to_have_text('WAITING',timeout=10000)
    report={'passed':True,'sign_in_required':False,'actual_physical_windows':measurements,'visual_mapping':dict(zip(['CLEAR_USABLE','UNUSABLE_CAPTURE','DETECTED_DEFECT'],cases)),
            'current_status':display.locator('#verdict').inner_text(),'scope':'Actual Pi Chromium windows on both connected HDMI monitors; no threshold or QA decision changes.'}
    (out/'browser_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
finally:
 tunnel.terminate()
 try:tunnel.wait(timeout=5)
 except subprocess.TimeoutExpired:tunnel.kill()
