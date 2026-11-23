"""Browser acceptance of real local batch/audit APIs; never invents hardware data."""
import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'validation/hardening/20261122/browser';out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    context=browser.new_context(viewport={'width':1440,'height':1000});page=context.new_page();errors=[];remote=[];bad=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:remote.append(r.url) if not r.url.startswith(('http://127.0.0.1:8770','data:','blob:')) else None)
    page.on('response',lambda r:bad.append([r.status,r.url]) if r.status>=400 else None)
    base='http://127.0.0.1:8770'
    for _ in range(100):
        try:
            if page.request.get(base+'/api/health').json()['ready']:break
        except Exception:pass
        time.sleep(.2)
    page.goto(base+'/operations');expect(page.locator('#vision-state')).to_contain_text('CPU reference',timeout=30000)
    lot='BROWSER-'+str(time.time_ns());page.locator('[name=batch_id]').fill(lot) if page.locator('details').get_attribute('open') is not None else None
    page.locator('summary').click();page.locator('[name=batch_id]').fill(lot);page.locator('[name=sku]').fill('DEMO-SKU');page.locator('[name=description]').fill('Browser verification');page.locator('[name=operator]').fill('Test operator')
    page.locator('#new-batch button').click();expect(page.locator('#batches')).to_have_value(lot)
    page.locator('#select').click();expect(page.locator('#station')).to_contain_text(lot)
    library=page.request.get(base+'/api/library').json();r=page.request.post(base+'/api/library/inspect',data={'name':library[0]['name']});assert r.ok,r.text();inspection=r.json()
    page.locator('#refresh').click();expect(page.locator('#records')).to_contain_text(inspection['inspection_id'])
    page.locator('#records button').first.click();expect(page.locator('#detail')).to_be_visible();expect(page.locator('#evidence-json')).to_contain_text('configuration_revision');page.locator('#dismiss').click()
    page.locator('#verify').click();expect(page.locator('#verification')).to_contain_text('Verified')
    page.screenshot(path=str(out/'operations_1440.png'),full_page=True)
    pdf=page.request.get(base+'/api/batches/'+lot+'/report?format=pdf');assert pdf.ok and pdf.body().startswith(b'%PDF')
    for route,button in [('/','#skip-boot'),('/classic','#enter-station')]:
        page.goto(base+route);page.wait_for_timeout(1500)
        if page.locator(button).count() and page.locator(button).is_visible():page.locator(button).click()
        page.screenshot(path=str(out/('inspect_a.png' if route=='/' else 'inspect_b.png')),full_page=True)
    page.goto(base+'/operations');page.set_viewport_size({'width':1024,'height':768});page.wait_for_timeout(800)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    page.screenshot(path=str(out/'operations_1024.png'),full_page=True)
    report={'checks':['Real batch creation/selection','Actual frozen CPU model inference linked to batch','Evidence detail','SHA-256 chain verification','Batch PDF export','Both preserved inspection dashboards','1024px no horizontal overflow'],'browser_errors':errors,'external_requests':remote,'failed_responses':bad,'scope':'Local browser/CPU reference; target camera and Hailo tested separately.'}
    (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));browser.close()
    assert not errors and not remote and not bad
