import os,json,subprocess
from pathlib import Path
report={'session_env':{k:v for k,v in os.environ.items() if k in ['DISPLAY','WAYLAND_DISPLAY','XDG_SESSION_TYPE','XDG_RUNTIME_DIR']},'drm':{},'framebuffers':{},'tools':{}}
for p in Path('/sys/class/drm').glob('card*-*'):
    if (p/'status').exists():report['drm'][p.name]={'status':(p/'status').read_text().strip(),'modes':(p/'modes').read_text().splitlines()}
for p in Path('/sys/class/graphics').glob('fb*'):
    report['framebuffers'][p.name]={n:(p/n).read_text().strip() for n in ['name','virtual_size'] if (p/n).exists()}
env=dict(os.environ,XDG_RUNTIME_DIR=f'/run/user/{os.getuid()}',WAYLAND_DISPLAY='wayland-0',DISPLAY=':0')
for cmd in [['wlr-randr'],['xrandr','--query'],['systemctl','--user','show-environment'],['pgrep','-a','labwc'],['pgrep','-a','chromium'],['ls','/dev/i2c-1']]:
    try:r=subprocess.run(cmd,capture_output=True,text=True,timeout=10,env=env);report['tools'][' '.join(cmd)]=r.stdout[:7000] or r.stderr[:500]
    except Exception as e:report['tools'][' '.join(cmd)]=str(e)
print(json.dumps(report,indent=2))
