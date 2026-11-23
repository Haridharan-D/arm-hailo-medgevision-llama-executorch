"""Exercise real upload, library, async Llama, QA and export in the browser."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
url=os.environ.get('BT_TEST_URL','http://127.0.0.1:8765')
def main():
    output=ROOT/'validation/browser';output.mkdir(parents=True,exist_ok=True)
    checks=[];errors=[];external=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
        context=browser.new_context(viewport={'width':1500,'height':1050},record_video_dir=str(output/'video'))
        page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('request',lambda request:external.append(request.url) if not request.url.startswith((url,'blob:','data:')) else None)
        page.goto(url);expect(page.locator('h1')).to_have_text('Every detail matters.')
        tested_backend=page.request.get(url+'/api/status').json()['vision_backend']
        checks.append('Dashboard loaded')
        sample=next((ROOT/'test_images').glob('*.jpg'))
        page.locator('#image-file').set_input_files(str(sample))
        expect(page.locator('#inspect-button')).to_be_enabled()
        page.locator('#inspect-button').click()
        expect(page.locator('#decision b')).to_have_text('HOLD',timeout=10000)
        checks.append('Actual trained YOLO upload produced HOLD')
        expect(page.locator('#defect-count')).not_to_have_text('0')
        expect(page.locator('#assistant-state')).to_contain_text('Llama response passed',timeout=200000)
        checks.append('Real ExecuTorch model response arrived asynchronously')
        page.screenshot(path=str(output/'dashboard_inspection.png'),full_page=True)
        page.locator('[data-advice="qa"]').click()
        page.locator('#reviewer').fill('Demonstration reviewer')
        page.locator('#review-comment').fill('Evidence reviewed for software demonstration. Production QA sign-off remains separate.')
        page.locator('#save-review').click();expect(page.locator('#toast')).to_contain_text('Review note saved')
        checks.append('QA review note saved without changing HOLD')
        expect(page.locator('#decision b')).to_have_text('HOLD')
        response=page.request.get(url+'/api/export.csv');assert response.ok and 'HOLD' in response.text()
        checks.append('CSV export includes inspection')
        page.locator('[data-mode="library"]').click();expect(page.locator('#library button')).to_have_count(18)
        page.locator('#library button').first.click();expect(page.locator('#decision b')).to_have_text('HOLD')
        checks.append('Stored-image library runs actual inference')
        page.locator('[data-mode="camera"]').click();expect(page.locator('#camera-source')).to_be_visible()
        assert page.locator('#camera-source option').count()==4
        checks.append('USB/CSI camera selectors available')
        if os.environ.get('BT_TEST_PHYSICAL_CAMERA')=='1':
            page.locator('#camera-start').click()
            page.wait_for_function("async () => {const s=await (await fetch('/api/status')).json(); return s.camera.running && s.camera.fps>0}",timeout=30000)
            expect(page.locator('#preview-image')).to_be_visible()
            page.wait_for_function("document.getElementById('preview-image').naturalWidth > 0",timeout=15000)
            page.screenshot(path=str(output/'pi_live_camera.png'),full_page=True)
            page.locator('#camera-stop').click()
            page.wait_for_function("async () => !(await (await fetch('/api/status')).json()).camera.running",timeout=20000)
            checks.append('Physical Pi USB camera stream received and stopped through dashboard')
        page.set_viewport_size({'width':430,'height':900});page.screenshot(path=str(output/'dashboard_mobile.png'),full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        checks.append('Mobile layout has no horizontal overflow')
        context.close();browser.close()
    report={'checks':checks,'page_errors':errors,'external_network_requests':external,
            'physical_camera_verified':os.environ.get('BT_TEST_PHYSICAL_CAMERA')=='1',
            'hailo_hardware_verified':tested_backend=='hailo',
            'vision_backend':tested_backend,'test_url':url}
    report_name='pi_browser_report.json' if os.environ.get('BT_TEST_PHYSICAL_CAMERA')=='1' else 'browser_report.json'
    (ROOT/'validation'/report_name).write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2));assert not errors and not external
if __name__=='__main__':main()
