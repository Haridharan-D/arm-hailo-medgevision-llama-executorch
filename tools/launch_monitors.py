"""One command: fullscreen workstation on monitor1, verdict on monitor2."""
import argparse,json,os,re,signal,subprocess,time,urllib.request
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--classic',action='store_true');args=parser.parse_args()
env=dict(os.environ)
raw=subprocess.run(['systemctl','--user','show-environment'],capture_output=True,text=True,check=True).stdout
for line in raw.splitlines():
    name,sep,value=line.partition('=')
    if sep and name in {'DISPLAY','WAYLAND_DISPLAY','XDG_RUNTIME_DIR','DBUS_SESSION_BUS_ADDRESS','XDG_SESSION_TYPE'}:env[name]=value
subprocess.run(['systemctl','--user','start','blistertrace.service'],check=True)
for _ in range(60):
    try:
        if json.load(urllib.request.urlopen('http://127.0.0.1:8765/api/ready',timeout=2)).get('ready'):break
    except Exception:pass
    time.sleep(.5)
else:raise SystemExit('Station not ready. Run: journalctl --user -u blistertrace.service -n 50')
result=subprocess.run(['wlr-randr'],capture_output=True,text=True,env=env)
outputs=[];current=None
for line in result.stdout.splitlines():
    if line and not line[0].isspace():
        current={'name':line.split()[0],'width':0,'height':0,'x':0,'y':0};outputs.append(current)
    elif current is not None:
        mode=re.search(r'(\d+)x(\d+) px,.*\(.*current.*\)',line)
        pos=re.search(r'Position: (-?\d+),(-?\d+)',line)
        if mode:current.update(width=int(mode[1]),height=int(mode[2]))
        if pos:current.update(x=int(pos[1]),y=int(pos[2]))
outputs=[o for o in outputs if o['width']]
outputs.sort(key=lambda o:(o['name']!='HDMI-A-1',o['x']))
if not outputs:outputs=[dict(name='default',width=1600,height=900,x=0,y=0)]
home=Path.home();profiles=[home/'.config/blistertrace-main',home/'.config/blistertrace-verdict']
owned=profiles+[home/'.config/blistertrace-browser']
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:
        cmd=(p/'cmdline').read_bytes().decode(errors='replace').split('\0')
        if not any('--type=' in a for a in cmd) and any('--user-data-dir='+str(profile) in cmd for profile in owned):os.kill(int(p.name),signal.SIGTERM)
    except (OSError,ProcessLookupError,PermissionError):pass
time.sleep(.5)
jobs=[]
for index,output in enumerate(outputs[:2]):
    profile=profiles[index];profile.mkdir(parents=True,exist_ok=True)
    prefs=profile/'Default/Preferences';prefs.parent.mkdir(parents=True,exist_ok=True)
    try:value=json.loads(prefs.read_text()) if prefs.exists() else {}
    except json.JSONDecodeError:value={}
    value.setdefault('partition',{})['per_host_zoom_levels']={};value['default_zoom_level']=0
    prefs.write_text(json.dumps(value))
    url='http://127.0.0.1:8765'+('/display' if index else ('/classic?kiosk=1' if args.classic else '/?kiosk=1'))
    command=['chromium','--ozone-platform=x11','--password-store=basic','--no-first-run','--no-default-browser-check',
        '--force-device-scale-factor=1','--user-data-dir='+str(profile),'--app='+url,'--kiosk',
        f'--window-position={output["x"]},{output["y"]}',f'--window-size={output["width"]},{output["height"]}',
        f'--remote-debugging-port={9223+index}']
    log=home/'BlisterTrace_Data'/f'browser_monitor_{index+1}.log';log.parent.mkdir(exist_ok=True)
    with log.open('ab') as f:child=subprocess.Popen(command,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=f,start_new_session=True)
    jobs.append(dict(output=output,url=url,pid=child.pid,debug_port=9223+index))
    time.sleep(.5)
receipt=home/'BlisterTrace_Data/monitor_launch.json';receipt.write_text(json.dumps(jobs,indent=2));print(json.dumps(jobs,indent=2))
