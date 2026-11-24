"""Capture actual Pi Chromium UI using already measured inspection IDs. No new inference."""
import json,subprocess,time,socket
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'evidence/gallery/dashboard';out.mkdir(parents=True,exist_ok=True)
records=json.loads((ROOT/'evidence/target_20261124/eight_test_report.json').read_text())['records']
tunnel=subprocess.Popen(['ssh','-i',str(Path.home()/'.ssh/blistertrace_pi'),'-o','ExitOnForwardFailure=yes','-N','-L','8933:127.0.0.1:9223','-L','8934:127.0.0.1:9224','saul@192.168.137.32'],creationflags=subprocess.CREATE_NO_WINDOW)
manifest=[]
try:
 for _ in range(80):
  with socket.socket() as s:
   if s.connect_ex(('127.0.0.1',8933))==0:break
  time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.connect_over_cdp('http://127.0.0.1:8933');main=next(pg for c in browser.contexts for pg in c.pages if ':8765/' in pg.url)
  main.reload();main.wait_for_selector('.intro-poster');main.wait_for_function('document.querySelector(".intro-poster").naturalWidth>0');main.screenshot(path=str(out/'00_intro.png'))
  for i,row in enumerate(records,1):
   id=row['inspection_id'];main.evaluate('(id)=>localStorage.setItem("bt.selected",JSON.stringify(id))',id);main.goto('http://127.0.0.1:8765/?kiosk=1')
   main.wait_for_selector('#skip-boot');main.locator('#skip-boot').click()
   main.wait_for_function('(id)=>window.BlisterTraceUI?.getSelected()?.inspection_id===id',arg=id,timeout=60000)
   main.wait_for_function('window.BlisterTraceUI?.getViewer()?.loaded',timeout=30000)
   main.wait_for_timeout(700)
   mode='heatmap' if row.get('anomaly') else 'annotated'
   button=main.locator('[data-view="'+mode+'"]')
   if button.count() and button.first.is_visible() and button.first.is_enabled():button.first.click()
   main.wait_for_timeout(400)
   name=f'{i:02}_{"anomaly" if row.get("anomaly") else "yolo"}_{row["visual_result"]["status"].lower()}'
   main.screenshot(path=str(out/(name+'.png')))
   (out/(name+'.txt')).write_text(main.locator('body').inner_text(),encoding='utf8')
   manifest.append(dict(file=name+'.png',inspection_id=id,visual=row['visual_result']['status'],advice_status=row['advice']['status'],scope='Actual Pi Chromium showing the selected original measured inspection'))
   # Scroll existing scrollable advisory panels to reveal lower evidence/SOP text.
   main.locator('.advice-column').evaluate('(root)=>{for(const e of [root,...root.querySelectorAll("*")])if(e.scrollHeight>e.clientHeight+20&&["auto","scroll"].includes(getComputedStyle(e).overflowY))e.scrollTop=e.scrollHeight;}')
   main.wait_for_timeout(250);main.screenshot(path=str(out/(name+'_advice_bottom.png')))
   print(name,flush=True)
  for route in ['history','batch','sop','audit','health']:
   link=main.locator('a[href="#'+route+'"]')
   if link.count():
    link.first.click();main.wait_for_timeout(1000);main.screenshot(path=str(out/('screen_'+route+'.png')))
  secondary=p.chromium.connect_over_cdp('http://127.0.0.1:8934');display=next(pg for c in secondary.contexts for pg in c.pages if '/display' in pg.url)
  display.screenshot(path=str(out/'secondary_actual_current_verdict.png'))
  (out/'capture_manifest.json').write_text(json.dumps(dict(scope='Screenshots from actual Pi Chromium through loopback SSH CDP; original measured records loaded read-only, no model outputs edited',cases=manifest),indent=2))
finally:tunnel.terminate();tunnel.wait(timeout=10)
