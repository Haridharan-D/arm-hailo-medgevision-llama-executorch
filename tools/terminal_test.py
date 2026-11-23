"""Observe the actual Pi workstation or time a real inspection via its local API.

No second Hailo owner, synthetic FPS, automatic driver changes or model loading.
"""
import argparse
import csv
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request
import psutil

ROOT=Path(__file__).resolve().parents[1]
BITS={0:'undervoltage_now',1:'frequency_capped_now',2:'throttled_now',3:'soft_temperature_limit_now',
      16:'undervoltage_since_boot',17:'frequency_capped_since_boot',18:'throttled_since_boot',19:'soft_temperature_limit_since_boot'}


def api(base,path,payload=None,timeout=5):
    data=None if payload is None else json.dumps(payload).encode()
    request=urllib.request.Request(base+path,data=data,
        headers={'Content-Type':'application/json'} if data else {},method='POST' if data is not None else 'GET')
    with urllib.request.urlopen(request,timeout=timeout) as response:return json.load(response)


def throttle():
    try:
        text=subprocess.check_output(['vcgencmd','get_throttled'],text=True,timeout=2).strip()
        number=int(text.split('=')[1],16)
        return {'raw':hex(number),'flags':[name for bit,name in BITS.items() if number&(1<<bit)]}
    except (OSError,ValueError,subprocess.SubprocessError):return {'raw':None,'flags':[]}


def temperature():
    try:return float(Path('/sys/class/thermal/thermal_zone0/temp').read_text())/1000
    except (OSError,ValueError):return None


def frequency():
    try:return int(Path('/sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq').read_text())/1000
    except (OSError,ValueError):return None


class ProcessMeter:
    def __init__(self,root=ROOT):self.root=Path(root).resolve();self.cached={}

    def sample(self):
        groups={'app':{'cpu':0.,'rss_mib':0.,'pss_mib':0.,'pids':[]},
                'llama':{'cpu':0.,'rss_mib':0.,'pss_mib':0.,'pids':[]}}
        live=set()
        for process in psutil.process_iter(['pid','cmdline','cwd']):
            try:
                args=process.info['cmdline'] or []
                kind=None
                if len(args)>=2 and any(Path(a).name=='main.py' for a in args[1:3]):
                    if Path(process.info['cwd'] or '/').resolve()==self.root:kind='app'
                if args and Path(args[0]).name=='blistertrace_worker':
                    if 'BlisterTrace' in args[0]:kind='llama'
                if kind is None:continue
                pid=process.pid;live.add(pid)
                if pid not in self.cached:
                    self.cached[pid]=process;process.cpu_percent(interval=None);cpu=None
                else:process=self.cached[pid];cpu=process.cpu_percent(interval=None)
                memory=process.memory_full_info();group=groups[kind]
                if cpu is not None:group['cpu']+=cpu
                group['rss_mib']+=memory.rss/1024**2
                group['pss_mib']+=getattr(memory,'pss',memory.rss)/1024**2
                group['pids'].append(pid)
            except (psutil.Error,OSError,ValueError):continue
        self.cached={pid:process for pid,process in self.cached.items() if pid in live}
        return groups


def summary(values):
    values=[v for v in values if v is not None]
    if not values:return None
    return {'n':len(values),'mean':round(statistics.mean(values),2),
            'min':round(min(values),2),'max':round(max(values),2),'median':round(statistics.median(values),2)}


def inspection_job(base,name,result,stop):
    """Exactly one real sample; leaves an explicitly recorded inspection."""
    start=time.monotonic()
    try:
        row=api(base,'/api/library/inspect',{'name':name},timeout=30)
        result.update(inspection_id=row['inspection_id'],decision=row['decision'],
            backend=row['backend'],vision_ms=row['vision_ms'],
            image_api_response_ms=round((time.monotonic()-start)*1000,2),
            source_name=name,advisory_status='pending')
        while not stop.is_set():
            row=api(base,'/api/inspections/'+row['inspection_id'])
            if row['advice'] is not None:
                result.update(advisory_status=row['advice']['status'],
                    advisory_internal_ms=row['advice'].get('elapsed_ms'),
                    client_observed_advice_ms=round((time.monotonic()-start)*1000,2),
                    advisory_status_note='Schema/grounding acceptance, not general factual accuracy')
                return
            stop.wait(.5)
    except Exception as error:result['error']=type(error).__name__+': '+str(error)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds',type=int,default=60)
    parser.add_argument('--mode',choices=['observe','inspect'],default='observe')
    parser.add_argument('--image',default='000000_c7aa17370159.jpg',help='Existing local-image library filename')
    parser.add_argument('--base',default='http://127.0.0.1:8765')
    args=parser.parse_args()
    if not 3<=args.seconds<=3600:parser.error('--seconds must be 3 to 3600')
    try:
        health=api(args.base,'/api/health');assert health['ready'],health.get('startup_error') or 'Runtime starting'
        initial=api(args.base,'/api/status')
    except Exception as error:raise SystemExit('Dashboard is unavailable. First run ~/blistertrace. Detail: '+str(error))
    if args.mode=='inspect':
        if initial['llama_state'] in {'loading','generating'}:
            raise SystemExit('Llama is already busy. Let its current request finish, or use --mode observe.')
        if args.image not in {r['name'] for r in api(args.base,'/api/library')}:
            raise SystemExit('Requested file is absent from the dashboard local-image library.')
    folder=Path.home()/'BlisterTrace_Data/benchmarks'/(
        datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+args.mode+'_'+str(os.getpid()))
    folder.mkdir(parents=True)
    meter=ProcessMeter();meter.sample();psutil.cpu_percent(interval=None)
    first_throttle=throttle();samples=[];inspection={};stop=threading.Event();thread=None
    report={'mode':args.mode,'requested_seconds':args.seconds,'started_at':datetime.now(timezone.utc).isoformat(),
        'backend':initial['vision_backend'],'initial_llama_state':initial['llama_state'],
        'initial_camera_running':initial['camera']['running'],'initial_throttle':first_throttle,
        'scope':['Actual running service; no standalone Hailo benchmark',
                 'Observe mode does not start/stop a camera or run inference',
                 'Inspect mode adds one actual library-image inspection and advisory request',
                 'System CPU is 0-100% across the machine; process CPU is 100% per logical core',
                 'RSS includes shared pages; PSS apportions shared pages (uses RSS only if PSS unavailable)',
                 'Camera FPS is the application rolling estimate; detector ms is a stage timing',
                 'Advisory time can include queue/poll/model-start overhead; this is not tokens/sec',
                 'No independent defect accuracy measurement, whole-board watts or NPU-utilization percent']}
    atomic=folder/'report.json';interrupted=False
    print('\nBlisterTrace actual-device diagnostics | '+args.mode.upper(),flush=True)
    print('CPU(proc): 100% = one core; up to '+str((psutil.cpu_count() or 1)*100)+'% on this Pi.',flush=True)
    print('MiB = 1,048,576 bytes. Process CPU is sampled separately for the app and native Llama worker.',flush=True)
    print('App CPU covers camera/OpenCV/HailoRT/API together; it is not NPU hardware utilization.',flush=True)
    print('Watch results:',folder,flush=True)
    print('\n   s SYS-CPU APP-CPU LLM-CPU APP-PSS LLM-PSS TEMP-C   MHz   FPS VISION-ms LLM-STATE',flush=True)
    began=time.monotonic()
    if args.mode=='inspect':
        thread=threading.Thread(target=inspection_job,args=(args.base,args.image,inspection,stop),daemon=True);thread.start()
    try:
        with (folder/'samples.csv').open('w',newline='') as stream:
            writer=None
            for index in range(args.seconds):
                time.sleep(max(0,began+index+1-time.monotonic()))
                state=api(args.base,'/api/status');groups=meter.sample();memory=psutil.virtual_memory();cam=state['camera']
                frame_running=bool(cam.get('running') and cam.get('frame_ready'))
                item={'elapsed_s':round(time.monotonic()-began,2),'system_cpu_percent':psutil.cpu_percent(interval=None),
                    'app_cpu_one_core_percent':round(groups['app']['cpu'],1),
                    'llama_cpu_one_core_percent':round(groups['llama']['cpu'],1),
                    'app_rss_mib':round(groups['app']['rss_mib'],1),'llama_rss_mib':round(groups['llama']['rss_mib'],1),
                    'app_pss_mib':round(groups['app']['pss_mib'],1),'llama_pss_mib':round(groups['llama']['pss_mib'],1),
                    'system_available_mib':round(memory.available/1024**2,1),'system_memory_percent':memory.percent,
                    'temperature_c':temperature(),'cpu_frequency_mhz':frequency(),
                    'camera_running':frame_running,'camera_fps':cam.get('fps') if frame_running else None,
                    'camera_detector_ms':cam.get('vision_ms') if frame_running else None,
                    'camera_error':cam.get('error'),'llama_state':state['llama_state'],
                    'app_pids':','.join(map(str,groups['app']['pids'])),'llama_pids':','.join(map(str,groups['llama']['pids']))}
                samples.append(item)
                if writer is None:writer=csv.DictWriter(stream,fieldnames=list(item));writer.writeheader()
                writer.writerow(item);stream.flush()
                def show(value,precision=1):return '—' if value is None else f'{value:.{precision}f}'
                print(f"{item['elapsed_s']:4.0f} {item['system_cpu_percent']:7.1f} {item['app_cpu_one_core_percent']:7.1f} "
                    f"{item['llama_cpu_one_core_percent']:7.1f} {item['app_pss_mib']:7.1f} {item['llama_pss_mib']:7.1f} "
                    f"{show(item['temperature_c']):>6} {show(item['cpu_frequency_mhz'],0):>5} "
                    f"{show(item['camera_fps']):>5} {show(item['camera_detector_ms']):>9} {item['llama_state']}",flush=True)
    except KeyboardInterrupt:
        interrupted=True;print('\nObservation stopped; preserving samples. Dashboard remains running.',flush=True)
    finally:
        stop.set()
        if thread is not None:thread.join(timeout=6)
        report.update(elapsed_seconds=round(time.monotonic()-began,2),interrupted=interrupted,
            samples=len(samples),final_throttle=throttle(),inspection=dict(inspection),
            summary={key:summary([row[key] for row in samples]) for key in [
                'system_cpu_percent','app_cpu_one_core_percent','llama_cpu_one_core_percent',
                'app_pss_mib','llama_pss_mib','temperature_c','camera_fps','camera_detector_ms']})
        before=set(first_throttle['flags']);after=set(report['final_throttle']['flags'])
        report['new_throttle_flags_during_run']=sorted(after-before)
        report['camera_accuracy_verified']=False
        atomic.write_text(json.dumps(report,indent=2)+'\n')
        print('\nSAVED REPORT:',atomic,flush=True)
        print('SAVED SAMPLES:',folder/'samples.csv',flush=True)
        if inspection:print('INSPECTION TIMINGS:',json.dumps(inspection,indent=2),flush=True)
        print('THROTTLING:',json.dumps(report['final_throttle']),flush=True)
        print('This test did not measure electrical power in watts or change the model/dashboard configuration.',flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
