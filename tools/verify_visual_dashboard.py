"""Exercise real Pi UI inference, popup colors and second HDMI verdict together."""
import json,subprocess,time,socket
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1];out=root/'validation/visual_suite_20261122/browser';out.mkdir(parents=True,exist_ok=True)
key=Path.home()/'.ssh/blistertrace_pi';host='saul@10.217.96.233'
tunnel=subprocess.Popen(['ssh','-i',str(key),'-o','BatchMode=yes','-o','ExitOnForwardFailure=yes','-N','-L','8923:127.0.0.1:9223','-L','8924:127.0.0.1:9224',host],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
checks=[]
try:
 for _ in range(80):
    with socket.socket() as s:
        if s.connect_ex(('127.0.0.1',8923))==0:break
    time.sleep(.2)
 with sync_playwright() as p:
    primary=p.chromium.connect_over_cdp('http://127.0.0.1:8923');secondary=p.chromium.connect_over_cdp('http://127.0.0.1:8924')
    main=next(page for c in primary.contexts for page in c.pages if ':8765/' in page.url)
    display=next(page for c in secondary.contexts for page in c.pages if '/display' in page.url)
    errors=[];main.on('pageerror',lambda e:errors.append(str(e)));display.on('pageerror',lambda e:errors.append(str(e)))
    main.reload();display.reload();main.locator('#skip-boot').click();main.wait_for_function('window.BlisterTraceUI?.getState().initialLoaded',timeout=45000)
    def acquisition():
        if main.locator('.acquisition-panel').is_hidden():main.locator('#change-image').click()
    for pipeline,kind,label,tone in [('yolo','safe','SAFE','PASS'),('yolo','warning','WARNING','REVIEW'),('yolo','black_dot','DEFECTIVE','HOLD'),('anomaly','safe','SAFE','PASS'),('anomaly','warning','WARNING','REVIEW'),('anomaly','defective','DEFECTIVE','HOLD')]:
        main.locator('[data-mode="'+('detection' if pipeline=='yolo' else 'anomaly')+'"]').click();acquisition()
        if pipeline=='yolo':
            main.locator('[data-source=local]').click();main.locator('#local-group').select_option('demo_'+kind)
            value=main.locator('#local-image option').first.get_attribute('value');main.locator('#local-image').select_option(value)
            main.locator('#run-button').click()
        else:
            main.locator('#anomaly-profile').select_option('mvtec_capsule')
            main.wait_for_function('document.querySelector("#anomaly-sample")?.innerText.includes("DEMO SAFE")',timeout=30000)
            main.locator('#anomaly-sample').select_option('demo/'+kind+'/'+kind+'_01.png')
            main.locator('#run-anomaly-sample').click()
        expect(main.locator('#result-dialog')).to_be_visible(timeout=90000)
        expect(main.locator('#result-title')).to_have_text(label)
        expect(main.locator('#result-panel h2')).to_have_text(label)
        assert tone in main.locator('#result-panel .result-banner').get_attribute('class')
        main.locator('#pause-count').click()
        expect(display.locator('#verdict')).to_have_text('REJECTED' if label=='DEFECTIVE' else label,timeout=20000)
        record=main.evaluate('window.BlisterTraceUI.getSelected()');assert record['visual_result']['status']==label
        if label=='SAFE':assert record['decision']=='REVIEW' and record['profile_validated'] is False
        main.locator('#result-ack').click()
        main.screenshot(path=str(out/f'{pipeline}_{label.lower()}_main.png'));display.screenshot(path=str(out/f'{pipeline}_{label.lower()}_display.png'))
        dims=main.evaluate('({w:innerWidth,h:innerHeight,sw:document.documentElement.scrollWidth,sh:document.documentElement.scrollHeight})');assert dims['w']==dims['sw'] and dims['h']==dims['sh']
        checks.append(dict(pipeline=pipeline,label=label,qa=record['decision'],inspection_id=record['inspection_id'],main_class=tone,second_screen=display.locator('#verdict').inner_text()))
        print(pipeline,label,'verified on both physical screens',flush=True)
    main.goto('http://127.0.0.1:8765/classic?kiosk=1');main.locator('#enter').click();expect(main.locator('#welcome')).to_be_hidden()
    main.locator('#method').select_option('detection');main.locator('#source').select_option('stored')
    main.wait_for_function('document.querySelector("#cases")?.innerText.includes("SAFE")',timeout=30000)
    main.locator('#cases').select_option('acceptance_demo/safe/safe_01.jpg');main.locator('#run').click()
    expect(main.locator('#result-title')).to_have_text('SAFE',timeout=60000);main.locator('#ack').click();expect(main.locator('#verdict strong')).to_have_text('SAFE')
    assert 'PASS' in main.locator('#verdict').get_attribute('class')
    main.screenshot(path=str(out/'classic_safe_main.png'));checks.append({'pipeline':'classic_yolo','label':'SAFE','main_class':'PASS'})
    main.goto('http://127.0.0.1:8765/?kiosk=1');main.locator('#skip-boot').click();main.wait_for_function('window.BlisterTraceUI?.getState().initialLoaded',timeout=45000)
    # Leave the operator on a confirmed green normal example.
    main.locator('[data-mode=detection]').click();acquisition();main.locator('[data-source=local]').click();main.locator('#local-group').select_option('demo_safe');main.locator('#run-button').click();expect(main.locator('#result-title')).to_have_text('SAFE',timeout=60000);main.locator('#result-ack').click();expect(display.locator('#verdict')).to_have_text('SAFE',timeout=15000)
    report={'passed':not errors,'cases':checks,'page_errors':errors,'actual_pi_monitors':True,'scope':'Real browser-driven inference, result dialogs/colors and live second-display checks; selected demonstration, not accuracy.'}
    (out/'report.json').write_text(json.dumps(report,indent=2));assert report['passed']
finally:
 tunnel.terminate()
 try:tunnel.wait(timeout=5)
 except subprocess.TimeoutExpired:tunnel.kill()
