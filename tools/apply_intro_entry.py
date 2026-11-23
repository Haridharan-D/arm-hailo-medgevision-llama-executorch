"""Integrate the user's exact poster in both frontends; preserve inference code."""
import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=root.parent/'Intro_entry/MEDGE SoC_ Pharmaceutical Quality at the Edge.png'
target=root/'web/assets/intro/medge-intro.png';target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
receipt={'source':str(source),'deployed_asset':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'image_pixels_changed':False}
out=root/'validation/intro_display_20261122';out.mkdir(exist_ok=True);(out/'poster.json').write_text(json.dumps(receipt,indent=2))
for name in ['aoi.html','index.html','classic.html']:
    p=root/'web'/name;s=p.read_text(encoding='utf8')
    href='/static/css/intro.css' if name!='index.html' else './css/intro.css'
    if 'css/intro.css' not in s:s=s.replace('</head>','<link rel="stylesheet" href="'+href+'"></head>')
    p.write_text(s,encoding='utf8')
p=root/'web/js/app.js';s=p.read_text(encoding='utf8')
if "from './intro.js'" not in s:s="import {mountIntro,introExitDelay} from './intro.js';\n"+s
s=s.replace(" $('#app').inert=true;$('#splash').setAttribute('role','dialog');$('#splash').setAttribute('aria-modal','true');", " $('#app').inert=true;mountIntro($('#splash'),{onEnter:hideBoot});")
s=s.replace(" $('#skip-boot').onclick=hideBoot;",'')
s=s.replace(" if(new URLSearchParams(location.search).get('kiosk')==='1'){document.body.classList.add('station-kiosk');hideBoot();}"," if(new URLSearchParams(location.search).get('kiosk')==='1')document.body.classList.add('station-kiosk');")
s=s.replace(" $('#skip-boot').textContent='Enter inspection workspace';$('#skip-boot').className='btn primary enter-workspace';$('#skip-boot').focus();", " $('#skip-boot').focus();")
s=s.replace("function hideBoot(){const s=$('#splash');if(s.hidden)return;$('#app').inert=false;s.classList.add('leaving');setTimeout(()=>{s.hidden=true;$('#workspace').focus();},180);}","function hideBoot(){const s=$('#splash');if(s.hidden||s.classList.contains('leaving'))return;$('#app').inert=false;s.classList.add('leaving');setTimeout(()=>{s.hidden=true;$('#workspace').focus();},introExitDelay());}")
s=s.replace('shell();boot();iris();renderRoute();idle(state);','shell();boot();renderRoute();idle(state);')
p.write_text(s,encoding='utf8')
p=root/'web/js/classic.js';s=p.read_text(encoding='utf8')
if "from './intro.js'" not in s:s="import {mountIntro,introExitDelay} from './intro.js';\n"+s
s=s.replace("function enter(){if(entered)return;entered=true;$('#welcome').hidden=true;$('#control').inert=false;$('#method').focus();}","function enter(){if(entered)return;entered=true;$('#welcome').classList.add('leaving');$('#control').inert=false;setTimeout(()=>{$('#welcome').hidden=true;$('#method').focus();},introExitDelay());}")
s=s.replace("$('#enter').onclick=enter;$('#enter').focus();", "mountIntro($('#welcome'),{classic:true,onEnter:enter});$('#enter').focus();")
s=s.replace("if(new URLSearchParams(location.search).get('kiosk')==='1')enter();",'')
p.write_text(s,encoding='utf8');print(json.dumps(receipt))
