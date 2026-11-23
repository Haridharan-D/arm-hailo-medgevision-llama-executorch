import json,os,subprocess,time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'validation/hardening/20261122/browser_auth';out.mkdir(parents=True,exist_ok=True)
with (out/'host.log').open('ab') as log:
    process=subprocess.Popen([str(ROOT.parent/'.venv/Scripts/python.exe'),str(ROOT/'tools/start_test_host.py')],cwd=ROOT,env=dict(os.environ,BT_TEST_AUTH='1'),stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
try:
 with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True);context=browser.new_context(viewport={'width':1280,'height':900});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    base='http://127.0.0.1:8772'
    for _ in range(120):
        try:
            if page.request.get(base+'/api/health').json()['ready']:break
        except Exception:pass
        time.sleep(.2)
    page.goto(base+'/operations');dialog=page.get_by_role('dialog',name='Local station sign-in');expect(dialog).to_be_visible(timeout=30000);page.wait_for_timeout(500)
    dialog.locator('[name=username]').fill('browser-admin');dialog.locator('[name=password]').fill('test-password-123');dialog.locator('[name=password]').press('Enter');expect(dialog).not_to_be_visible(timeout=10000)
    expect(page.locator('#station')).to_contain_text('Local authentication enabled');page.screenshot(path=str(out/'signed_in_operations.png'),full_page=True)
    context.close();context=browser.new_context(viewport={'width':1280,'height':900});page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/classic');dialog=page.get_by_role('dialog',name='Local station sign-in');expect(dialog).to_be_visible(timeout=15000)
    dialog.locator('[name=username]').fill('browser-admin');dialog.locator('[name=password]').fill('test-password-123');dialog.locator('[name=password]').press('Enter');expect(dialog).not_to_be_visible(timeout=10000);page.locator('#enter').click();expect(page.locator('#welcome')).not_to_be_visible();page.screenshot(path=str(out/'classic_authenticated.png'),full_page=True)
    report={'passed':not errors,'checks':['One-time local setup or login','Authenticated operations API','Keyboard submit through classic intro','Preserved classic viewer after login'],'errors':errors};(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));browser.close();assert not errors
finally:
    process.terminate()
    try:process.wait(timeout=15)
    except subprocess.TimeoutExpired:process.kill()
