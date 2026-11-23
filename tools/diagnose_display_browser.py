import json,socket,subprocess,time
from pathlib import Path
from playwright.sync_api import sync_playwright
host='saul@192.168.137.189';key=Path.home()/'.ssh/blistertrace_pi'
t=subprocess.Popen(['ssh','-i',str(key),'-o','BatchMode=yes','-o','ExitOnForwardFailure=yes','-N','-L','8923:127.0.0.1:9223','-L','8924:127.0.0.1:9224',host],creationflags=subprocess.CREATE_NO_WINDOW)
try:
 time.sleep(1)
 with sync_playwright() as p:
  for port in [8923,8924]:
   b=p.chromium.connect_over_cdp('http://127.0.0.1:'+str(port))
   for c in b.contexts:
    for page in c.pages:
     print(json.dumps({'port':port,'url':page.url,'state':page.evaluate('({hidden:document.hidden,selected:window.BlisterTraceUI?.getSelected()?.inspection_id,visual:window.BlisterTraceUI?.getSelected()?.visual_result,verdict:document.querySelector("#verdict")?.innerText,identity:document.querySelector("#identity")?.innerText,lastCheck:document.querySelector("#last-check")?.innerText,connection:document.querySelector("#link-state")?.innerText})')},indent=2))
finally:t.terminate();t.wait(timeout=5)
