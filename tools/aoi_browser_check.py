"""Exercise the actual AOI UI, model, asynchronous advice and optional Pi camera."""
import argparse
import json
from pathlib import Path
import subprocess
import time
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pi',action='store_true');parser.add_argument('--url',default='http://127.0.0.1:8773')
    args=parser.parse_args();tunnel=None
    if args.pi:
        args.url='http://127.0.0.1:8772'
        tunnel=subprocess.Popen(['ssh','-i',str(Path.home()/'.ssh/blistertrace_pi'),'-o','BatchMode=yes',
            '-o','ExitOnForwardFailure=yes','-N','-L','8772:127.0.0.1:8765','saul@10.217.96.102'],
            stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        time.sleep(1)
        if tunnel.poll() is not None:raise RuntimeError('Owned Pi tunnel did not start')
    output=ROOT/'validation/aoi_browser';output.mkdir(exist_ok=True)
    checks=[];errors=[];external=[]
    try:
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
            context=browser.new_context(viewport={'width':1500,'height':1100},record_video_dir=str(output/'video'))
            page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('request',lambda request:external.append(request.url) if not request.url.startswith((args.url,'data:','blob:')) else None)
            page.goto(args.url)
            expect(page.locator('#boot')).to_be_visible()
            page.screenshot(path=str(output/('pi_boot.png' if args.pi else 'boot.png')))
            expect(page.locator('#boot')).to_be_hidden(timeout=30000)
            expect(page.locator('h1')).to_contain_text('Inspection console');checks.append('Logo splash and AOI console')
            sample=ROOT/'test_images/000000_c7aa17370159.jpg'
            assert sample.is_file()
            page.locator('#image-file').set_input_files(str(sample))
            expect(page.locator('#inspect-button')).to_be_enabled();page.locator('#inspect-button').click()
            expect(page.locator('#result-dialog')).to_be_visible(timeout=15000)
            expect(page.locator('#popup-result')).to_have_text('HOLD')
            popup_began=time.monotonic()
            page.screenshot(path=str(output/('pi_result_popup.png' if args.pi else 'result_popup.png')))
            expect(page.locator('#result-dialog')).not_to_be_visible(timeout=7000)
            popup_seconds=time.monotonic()-popup_began
            assert 4.0<=popup_seconds<=6.8,popup_seconds
            expect(page.locator('#decision b')).to_have_text('HOLD');checks.append('Actual trained model + automatic five-second result dialog')
            page.locator('#toggle-original').click();expect(page.locator('#preview-image')).to_have_attribute('src',__import__('re').compile('original$'))
            page.locator('#zoom-in').click();expect(page.locator('#zoom-value')).to_have_text('150%')
            page.locator('#zoom-fit').click();page.locator('#toggle-original').click();checks.append('Original/annotation toggle and zoom')
            expect(page.locator('#assistant-state')).to_contain_text('Llama response passed',timeout=200000)
            page.locator('[data-intent="rectify"]').click()
            expect(page.locator('.chat.assistant')).to_contain_text('QA')
            page.locator('#question').fill('Why this result?');page.locator('#ask-button').click()
            expect(page.locator('.chat.assistant').last).to_contain_text('HOLD');checks.append('Real asynchronous Llama plus grounded operator question intents')
            page.screenshot(path=str(output/('pi_inspection.png' if args.pi else 'inspection.png')),full_page=True)
            page.locator('[data-advice="qa"]').click();page.locator('#reviewer').fill('AOI demonstration reviewer')
            page.locator('#review-comment').fill('UI and evidence reviewed for the demonstration; product release is not authorized.')
            page.locator('#save-review').click();expect(page.locator('#toast')).to_contain_text('Review note saved')
            expect(page.locator('#decision b')).to_have_text('HOLD');checks.append('QA review appended without changing HOLD')
            assert page.request.get(args.url+'/api/export.csv').ok
            page.locator('[data-mode="library"]').click();page.locator('#library-select').select_option(sample.name)
            page.locator('#inspect-button').click();expect(page.locator('#popup-result')).to_have_text('HOLD')
            page.locator('#popup-dismiss').click();checks.append('Stored image selection + explicit Run inference')
            if args.pi:
                page.locator('[data-mode="camera"]').click();page.locator('#camera-start').click()
                page.wait_for_function("async () => {const s=await (await fetch('/api/status')).json();return s.camera.running && s.camera.fps>0}",timeout=30000)
                page.wait_for_function("document.getElementById('preview-image').naturalWidth>0",timeout=15000)
                page.locator('#inspect-button').click();expect(page.locator('#result-dialog')).to_be_visible(timeout=15000)
                page.locator('#popup-dismiss').click();page.screenshot(path=str(output/'pi_live_camera.png'),full_page=True)
                page.locator('#camera-stop').click();checks.append('Physical USB camera + operator-triggered raw-frame inference')
            page.locator('#system-toggle').click();expect(page.locator('#system-dialog')).to_be_visible();page.locator('#system-close').click()
            page.set_viewport_size({'width':430,'height':900});page.screenshot(path=str(output/('pi_mobile.png' if args.pi else 'mobile.png')),full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth');checks.append('System telemetry and mobile overflow check')
            status=page.request.get(args.url+'/api/status').json()
            context.close();browser.close()
        report={'checks':checks,'page_errors':errors,'external_requests':external,'popup_observed_seconds':round(popup_seconds,2),
                'physical_camera_checked':args.pi,'backend':status['vision_backend'],'llama_platform':status['llama_platform'],
                'application_version':status['version'],'all_passed':not errors and not external}
        (ROOT/'validation'/('aoi_pi_browser.json' if args.pi else 'aoi_pc_browser.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2));assert report['all_passed']
    finally:
        if tunnel is not None:tunnel.terminate();tunnel.wait(timeout=10)


if __name__=='__main__':main()
