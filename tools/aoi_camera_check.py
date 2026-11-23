"""Focused real-device browser check for the operator-triggered camera button."""
import json
from pathlib import Path
import subprocess
import time
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]


def main():
    tunnel=subprocess.Popen(['ssh','-i',str(Path.home()/'.ssh/blistertrace_pi'),'-o','BatchMode=yes',
        '-N','-L','8774:127.0.0.1:8765','saul@10.217.96.102'],stderr=subprocess.PIPE)
    time.sleep(.5);url='http://127.0.0.1:8774';events=[];errors=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
            page=browser.new_page(viewport={'width':1500,'height':1100})
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('response',lambda response:events.append({'url':response.url,'status':response.status}) if '/api/camera/' in response.url or response.status>=400 else None)
            page.goto(url);expect(page.locator('#boot')).to_be_hidden(timeout=20000)
            page.locator('[data-mode="camera"]').click();page.locator('#camera-start').click()
            page.wait_for_function("async () => {const s=await (await fetch('/api/status')).json();return s.camera.running&&s.camera.fps>0}",timeout=15000)
            expect(page.locator('#inspect-button')).to_be_enabled()
            print('Before click:',page.evaluate('({mode,busy,ready,hasFrame:lastStatus.camera.running})'),flush=True)
            page.locator('#inspect-button').click()
            try:
                expect(page.locator('#result-dialog')).to_be_visible(timeout=10000)
                print('Popup:',page.locator('#popup-result').inner_text(),flush=True)
                page.locator('#popup-dismiss').click()
            finally:
                print('After click:',page.evaluate('({mode,busy,ready,pinned:cameraPinned,toast:document.getElementById("toast").textContent})'),flush=True)
                print('Events:',json.dumps(events),flush=True);print('Page errors:',json.dumps(errors),flush=True)
                page.request.post(url+'/api/camera/stop')
            page.close();browser.close()
    finally:tunnel.terminate();tunnel.wait(timeout=10)


if __name__=='__main__':main()
