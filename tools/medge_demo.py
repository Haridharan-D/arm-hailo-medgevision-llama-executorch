"""Short offline terminal demonstration of the one installed model pipeline."""
import argparse,json,os,subprocess,sys,time,urllib.error,urllib.request
from datetime import datetime
from pathlib import Path

BASE='http://127.0.0.1:8765'
CASES={
 '1':('YOLO: crack','yolo','acceptance_demo/defective/crack/crack.jpg','DEFECTIVE'),
 '2':('YOLO: clear SCOA strip','yolo','acceptance_demo/safe/safe_01.jpg','SAFE'),
 '3':('EfficientAD: MVTec pill','mvtec_pill','demo/defective/defective_01.png','DEFECTIVE'),
 '4':('EfficientAD: MVTec capsule','mvtec_capsule','demo/defective/defective_01.png','DEFECTIVE'),
 '5':('EfficientAD: VisA capsules','visa_capsules','demo/defective/defective_01.png','DEFECTIVE'),
 'warning':('YOLO: bad-capture warning','yolo','acceptance_demo/warning/warning_01.png','WARNING'),
}
def call(path,value=None,timeout=120):
    req=urllib.request.Request(BASE+path,data=json.dumps(value).encode() if value is not None else None,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as response:return json.load(response)
def heading(title):print('\nMEDGE VISION | '+title+'\n'+'-'*65,flush=True)
def field(name,value):print(f'{name:19} {value}',flush=True)
def state():
    p=Path.home()/'BlisterTrace_Data/terminal_demo_state.json'
    return p,json.loads(p.read_text()) if p.exists() else {}
def save_state(value):
    p,_=state();p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2));tmp.replace(p)
def ready():
    try:return call('/api/ready',timeout=3)
    except (OSError,urllib.error.URLError):raise RuntimeError('First run: ~/medge-demo start') from None
def start():
    heading('START LOCAL PIPELINE')
    subprocess.run(['systemctl','--user','start','blistertrace.service'],check=True)
    for i in range(90):
        try:
            r=call('/api/ready',timeout=2)
            if r.get('ready'):break
        except Exception:pass
        if i%10==0:print('Loading local model/runtime...',flush=True)
        time.sleep(.5)
    else:raise RuntimeError('Service not ready. Read: journalctl --user -u blistertrace.service -n 40')
    status=call('/api/status')
    if status.get('camera',{}).get('running'):call('/api/camera/stop',{})
    name='TERMINAL-'+datetime.now().strftime('%Y%m%d-%H%M%S')
    call('/api/batches',dict(batch_id=name,sku='SELECTED-DEMO',description='Selected five-image terminal demo; not an accuracy benchmark',category='blister',operator='local-operator'))
    call('/api/batches/'+name+'/select',{})
    folder=Path.home()/'BlisterTrace_Data/terminal_demos'/name;folder.mkdir(parents=True)
    save_state({'batch':name,'folder':str(folder),'records':[]})
    field('Service','READY; local loopback only')
    field('Vision',status['vision_backend']+' / '+status['model'])
    field('Advisory','ExecuTorch Llama / Arm CPU / '+status['llama_state'])
    field('Anomaly profiles',', '.join(p['id'] for p in status['anomaly_profiles']))
    field('Batch',name);field('Reports',folder)
    print('No browser opened. Same persistent runtime; no second Hailo owner.',flush=True)
def models():
    ready();heading('MODEL AND HARDWARE INVENTORY')
    status=call('/api/status');ops=call('/api/operations/health')
    field('Vision backend',status['vision_backend']);field('Detector',status['model'])
    field('Device present',ops.get('hailo_device_present'))
    field('Llama','Llama3.2 1B Instruct SpinQuant INT4 / ExecuTorch v1.0.0')
    field('CPU threads',status['llama_threads']);field('Advisory state',status['llama_state'])
    field('Llama SHA256',str(ops.get('llama_model_sha256','unavailable'))[:24]+'...')
    field('Temperature C',status.get('temperature_c'));field('Available RAM MiB',ops.get('available_ram_mib'))
    for p in status['anomaly_profiles']:
        field(p['id'],f"ONNX CPU | threshold {p['threshold']:.6f}")
    print('Vision/HailoRT, anomaly/ONNX CPU and Llama/ExecuTorch CPU are separate.',flush=True)
    print('VisA is a low-recall research profile; these examples are selected demos.',flush=True)
def run_case(number,timeout=100,fresh=False):
    ready();_,session=state()
    if not session:raise RuntimeError('First run: ~/medge-demo start')
    title,pipeline,image,expected=CASES[number];heading('TEST '+number+' | '+title)
    start_at=time.monotonic()
    value=call('/api/library/inspect',{'name':image}) if pipeline=='yolo' else call('/api/anomaly/inspect',{'profile':pipeline,'sample':image})
    record_id=value['inspection_id'];visual=value.get('visual_result',{}).get('status','unavailable')
    field('Inspection',record_id);field('Input',image);field('Backend',value['backend'])
    field('Visual result',visual+' | '+('matched selected demo' if visual==expected else 'UNEXPECTED — retain this result'))
    field('QA disposition',value['decision']+' (independent; original decision retained)')
    field('Inference ms',value['vision_ms']);field('Capture usable',value['capture_valid'])
    if value.get('anomaly'):
        a=value['anomaly'];field('Anomaly score',f"{a['score']:.6f} / threshold {a['threshold']:.6f}");field('Flagged',a['flagged'])
        print('Finding: image-level unknown visual anomaly; no classified defect type.',flush=True)
    elif value['detections']:
        for d in value['detections']:print(f"Finding: {d['type']} | confidence {d['confidence']:.3f} | bbox {d['box_xyxy']}",flush=True)
    else:print('Finding: no configured defect detected.' if visual=='SAFE' else 'Finding: unusable capture; recapture required.',flush=True)
    if fresh:call('/api/inspections/'+record_id+'/advice',{})
    print('Waiting for local Llama / SOP advice',end='',flush=True)
    until=time.monotonic()+timeout;next_dot=0
    while time.monotonic()<until:
        value=call('/api/inspections/'+record_id,timeout=10)
        if value.get('advice'):break
        if time.monotonic()>next_dot:print('.',end='',flush=True);next_dot=time.monotonic()+2
        time.sleep(.5)
    print('',flush=True)
    advice=value.get('advice')
    if advice:
        a=advice.get('advisory',{});cached=advice.get('cache_hit') or advice.get('reused') or advice.get('generation_status')=='reused'
        field('Advisory status',advice.get('status'))
        field('Response cache','REUSED prior validated response; no new token generation' if cached else 'Fresh or recorded response; see saved provenance')
        field('Llama action',a.get('operator_message','No validated advice available'))
        field('QA draft',a.get('qa_note','unavailable'))
        field('SOP citation',str(advice.get('sop_document',''))+' / '+str(a.get('clause_id','')))
        field('Advisory ms',advice.get('elapsed_ms','unavailable'))
        if advice.get('fallback_reason'):field('Fallback reason',advice['fallback_reason'])
        print('SOP is demonstration material; QA retains final disposition.',flush=True)
    else:print('Advisory still pending; visual result is already recorded. Check history later.',flush=True)
    field('Client elapsed s',round(time.monotonic()-start_at,2))
    file=Path(session['folder'])/('test_'+number+'_'+record_id+'.json');file.write_text(json.dumps(value,indent=2))
    session['records'].append({'test':number,'title':title,'inspection_id':record_id,'visual':visual,'expected':expected,'matched':visual==expected,'file':str(file)})
    save_state(session);field('Saved evidence',file)
    return visual==expected
def summary():
    ready();_,session=state();heading('SAVED RESULTS AND AUDIT')
    for r in session.get('records',[]):print(f"Test {r['test']:>7} | {r['visual']:<10} | {r['title']} | {r['inspection_id'][:12]}",flush=True)
    audit=call('/api/audit/verify');field('Audit chain','VERIFIED' if audit['valid'] else 'INTEGRITY FAILURE');field('Checked events',audit.get('checked_events'));field('Evidence folder',session.get('folder','not started'))
    print('Selected demonstration outcomes only, not independent accuracy. SAFE = visual check.',flush=True)
def main():
    global BASE
    parser=argparse.ArgumentParser(description='Medge Vision offline terminal demo')
    parser.add_argument('command',choices=['start','models','test','summary','web','all']);parser.add_argument('case',nargs='?',choices=list(CASES));parser.add_argument('--fresh',action='store_true',help='Request new Llama generation instead of permitting cached advice');parser.add_argument('--timeout',type=int,default=100)
    parser.add_argument('--base',default=BASE,help='Existing local HTTP service URL; default127.0.0.1:8765')
    a=parser.parse_args();BASE=a.base.rstrip('/')
    if a.command=='start':start()
    elif a.command=='models':models()
    elif a.command=='test':
        if not a.case:parser.error('Use: test 1 (or2,3,4,5,warning)')
        return 0 if run_case(a.case,a.timeout,a.fresh) else 2
    elif a.command=='summary':summary()
    elif a.command=='web':subprocess.run([str(Path.home()/'medge-vision')],check=True)
    elif a.command=='all':
        start();models()
        for n in ['1','2','3','4','5']:run_case(n,a.timeout,a.fresh)
        summary()
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except KeyboardInterrupt:print('\nStopped waiting; saved inspection remains in the database.');raise SystemExit(130)
    except Exception as e:print('Medge Vision:',str(e),file=sys.stderr);raise SystemExit(1)
