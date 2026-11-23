"""Check click-gated intro and animated light verdict on physical Pi monitors."""
import argparse,json,socket,subprocess,time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1];out=root/'validation/intro_display_20261122';out.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--host',default='saul@192.168.137.32');a=parser.parse_args();key=Path.home()/'.ssh/blistertrace_pi'
tunnel=subprocess.Popen(['ssh','-i',str(key),'-o','BatchMode=yes','-o','ExitOnForwardFailure=yes','-N','-L','8923:127.0.0.1:9223','-L','8924:127.0.0.1:9224',a.host],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
try:
 for _ in range(60):
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',8923))==0:break
    time.sleep(.2)
 with sync_playwright() as p:
    primary=p.chromium.connect_over_cdp('http://127.0.0.1:8923');secondary=p.chromium.connect_over_cdp('http://127.0.0.1:8924')
    main=next(page for c in primary.contexts for page in c.pages if ':8765/' in page.url)
    display=next(page for c in secondary.contexts for page in c.pages if '/display' in page.url)
    errors=[];main.on('pageerror',lambda e:errors.append(str(e)));display.on('pageerror',lambda e:errors.append(str(e)))
    main.reload();display.reload();main.wait_for_selector('.intro-poster');main.wait_for_function('document.querySelector(".intro-poster").naturalWidth>0')
    main.wait_for_timeout(6000);expect(main.locator('#splash')).to_be_visible();assert main.locator('#app').evaluate('(el)=>el.inert')
    main.screenshot(path=str(out/'intro_monitor.png'));display.screenshot(path=str(out/'light_verdict_monitor.png'))
    main.locator('.intro-poster').click();expect(main.locator('#splash')).to_be_hidden();main.wait_for_function('window.BlisterTraceUI?.getState().initialLoaded',timeout=45000);assert not main.locator('#app').evaluate('(el)=>el.inert')
    main.goto('http://127.0.0.1:8765/classic?kiosk=1');expect(main.locator('#welcome .intro-poster')).to_be_visible();assert main.locator('#control').evaluate('(el)=>el.inert');main.keyboard.press('Enter');expect(main.locator('#welcome')).to_be_hidden()
    bg=display.evaluate('getComputedStyle(document.body).backgroundImage');assert 'gradient' in bg
    motion=display.locator('.orbit-packet').evaluate('(el)=>getComputedStyle(el).animationName');assert motion=='orbit-turn'
    reduced=primary.contexts[0].new_page();reduced.emulate_media(reduced_motion='reduce');reduced.goto('http://127.0.0.1:8765/display');reduced.wait_for_selector('.orbit-packet');assert reduced.locator('.orbit-packet').evaluate('(el)=>getComputedStyle(el).animationName')=='none';reduced.close()
    dims={label:page.evaluate('({w:innerWidth,h:innerHeight,sw:document.documentElement.scrollWidth,sh:document.documentElement.scrollHeight})') for label,page in [('main',main),('display',display)]}
    assert all(d['sw']==d['w'] for d in dims.values())
    report={'passed':not errors,'poster_held_without_click_seconds':6,'click_anywhere_enters':True,'classic_enter_key':True,'light_display':True,'display_orbit_animation':motion,'reduced_motion_verified':True,'physical_monitor_viewports':dims,'errors':errors}
    (out/'browser_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert report['passed']
    # Leave the supplied intro visible for the operator to enter themselves.
    main.goto('http://127.0.0.1:8765/?kiosk=1');expect(main.locator('#splash')).to_be_visible()
finally:
 tunnel.terminate()
 try:tunnel.wait(timeout=5)
 except subprocess.TimeoutExpired:tunnel.kill()
