import {mountIntro,introExitDelay} from './intro.js';
import {api,assetURL,getSop,subscribe} from './api.js';
import './operations-link.js';
import {runtimeTiming} from './runtime-metrics.js';
import {icon,escape as esc,badge} from './icons.js';
import {$,$$,num,when,toast,download,copy,openDialog,closeDialog,setupDialogs,resultDialog,empty,spark,animateNumber,VirtualTable,reviewEntry,digest} from './components.js';
import {Viewer} from './viewer.js';
import {t} from './i18n.js';
import {transition,themeReveal,motionStatus} from './motion.js';
import {enhance,updateOptical,scan,verdict,iris,idle} from './optical.js';
import {mountConsole,updateConsole} from './console.js';
import {inspectionLabel,visualTone,visualReason} from './inspection-label.js';
const version='2026.11.20-studio-v5';
const saved=(k,f)=>{try{return JSON.parse(localStorage.getItem('bt.'+k))??f;}catch{return f;}};
const persist=(k,v)=>{try{localStorage.setItem('bt.'+k,JSON.stringify(v));}catch{}};
const state={route:'inspect',status:null,health:null,sop:null,records:[],library:[],selected:null,source:'local',sourceName:null,file:null,viewer:null,virtual:null,busy:false,connected:false,theme:saved('theme','dark'),sound:saved('sound',false),glove:saved('glove',false),operator:saved('operator','OP-01'),batch:saved('batch','all'),sort:'confidence',descending:true,filters:saved('filters',{}),selectedRows:new Set(),reviewMirror:new Map(),questionAnswers:new Map(),drafts:new Map(),audit:[],bootStarted:performance.now(),lastRefresh:0,previewURL:null,unsub:null};
const routes=[['inspect','Inspect','inspect'],['history','History','history'],['dashboard','Batches','dashboard'],['sop','SOP library','sop'],['audit','Audit log','audit'],['settings','Settings','settings'],['health','Health','health']];
const button=(label,action,name='',cls='',attrs='')=>'<button class="btn '+cls+'" data-action="'+action+'" '+attrs+'>'+(name?icon(name):'')+'<span>'+label+'</span></button>';
const field=(id,label,type='text',value='',attrs='')=>'<div class="field"><label for="'+id+'">'+label+'</label><input id="'+id+'" type="'+type+'" value="'+esc(value)+'" '+attrs+'></div>';
const statusText=()=>state.status?.llama_state||'warming up';
const clsName=s=>s==='ready'||s==='idle'?'ready':s==='unavailable'||s==='fallback'?'fail':'warn';
const knownClasses=['black_dot','broken','color_mismatch','crack','dual_cap','empty','foreign_particle'];
const human=s=>String(s||'').replaceAll('_',' ');
const activeRecord=()=>state.selected;
function applyTheme(){
 document.documentElement.dataset.theme=state.theme==='system'?(matchMedia('(prefers-color-scheme: light)').matches?'light':'dark'):state.theme;
 document.body.classList.toggle('glove',state.glove);persist('theme',state.theme);
}
applyTheme();matchMedia('(prefers-color-scheme: light)').addEventListener('change',()=>{if(state.theme==='system')applyTheme();});
function shell(){
 $('#app').innerHTML='<div class="app-shell"><header class="topbar"><a href="#inspect" class="brand" style="text-decoration:none;color:inherit" aria-label="Medge Vision home"><img src="'+assetURL('logo.svg')+'" alt=""><div><div class="brand-name">Medge Vision<span style="color:var(--accent)">.</span></div><div class="brand-sub">Optical inspection workspace</div></div></a><select class="batch-select" id="batch-select" aria-label="Active batch"><option value="all">All inspections · unassigned</option>'+(api.mode==='mock'?'<option value="BT-261119-A">BT-261119-A · Tablet · Line 01</option><option value="BT-261119-B">BT-261119-B · Capsule · Line 02</option>':'')+'</select><div class="spacer"></div><span class="shift" id="shift-timer">SESSION 00:00:00</span><div class="system-chips" aria-label="Subsystem status">'+[['camera','Camera'],['hailo','Hailo'],['llama','Llama'],['database','DB']].map(([key,label])=>'<span class="system-chip" id="chip-'+key+'" data-state="warn" title="'+label+' pending">'+icon(key==='hailo'?'chip':key)+'<span>'+label+'</span></span>').join('')+'</div><span class="badge accent offline-badge">'+icon('offline')+'OFFLINE DESIGN</span><button class="btn icon-only ghost" data-action="command" aria-label="Open command palette" title="Command palette · Ctrl K">'+icon('search')+'</button><button class="btn icon-only ghost" data-action="theme" aria-label="Toggle light and dark theme">'+icon('sun')+'</button><button class="operator" data-action="operator" id="operator-badge" aria-label="Operator identity">'+esc(state.operator.slice(0,2))+'</button></header><nav class="rail" aria-label="Primary">'+routes.map(([id,label,name])=>'<a href="#'+id+'" data-route="'+id+'" title="'+label+'">'+icon(name)+'<span>'+label+'</span></a>').join('')+'<a class="rail-bottom" href="#shortcuts" data-action="shortcuts" aria-label="Keyboard shortcuts">'+icon('help')+'<span>Shortcuts</span></a></nav><main class="workspace" id="workspace" tabindex="-1"><div id="demo-banner" class="demo-banner" '+(api.mode==='mock'?'':'hidden')+'>'+icon('info')+' DEMO WORKSPACE · Simulated inspections, overlays and telemetry. No hardware inference or QA authorization.</div><div id="connection-banner" class="disconnect-banner" role="status" hidden></div><div id="page"></div></main><footer class="safety-footer"><span class="row">'+icon('shield')+t('safety')+'</span><span id="footer-connection">CONNECTING TO LOCAL STATION</span></footer></div>';
 $('#batch-select').value=state.batch;$('#batch-select').onchange=async e=>{state.batch=e.target.value;persist('batch',state.batch);if(api.mode==='real'&&state.batch!=='all'){try{await api.selectBatch(state.batch);}catch(error){toast(error.message,true);}}renderRoute();};
 setInterval(()=>{const seconds=Math.floor((performance.now()-state.bootStarted)/1000);$('#shift-timer').textContent='SESSION '+[Math.floor(seconds/3600),Math.floor(seconds/60)%60,seconds%60].map(n=>String(n).padStart(2,'0')).join(':');},1000);
 setupDialogs();
}
function heading(title,description,actions=''){return '<div class="page-heading"><div><div class="eyebrow">PHARMA QUALITY CONTROL / '+(api.mode==='mock'?'DEMO STATION':'EDGE STATION')+'</div><h1>'+title+'</h1><p>'+description+'</p></div><div class="row">'+actions+'</div></div>';}
function boot(){
 $('#app').inert=true;mountIntro($('#splash'),{onEnter:hideBoot});
 $('#splash-logo').src=assetURL('logo.svg');
 $('#boot-list').innerHTML=[['camera','Camera'],['hailo','Hailo NPU'],['detector','Detector'],['llama','ExecuTorch Llama'],['sop','SOP index'],['database','Database']].map(([id,label])=>'<div class="boot-item" id="boot-'+id+'" data-state="pending">'+icon('clock')+'<span>'+label+'</span><span>pending</span></div>').join('');

 if(new URLSearchParams(location.search).get('kiosk')==='1')document.body.classList.add('station-kiosk');
 $('#skip-boot').focus();
}
function hideBoot(){const s=$('#splash');if(s.hidden||s.classList.contains('leaving'))return;$('#app').inert=false;s.classList.add('leaving');setTimeout(()=>{s.hidden=true;$('#workspace').focus();},introExitDelay());}
function bootItem(id,value,label){const e=$('#boot-'+id);if(!e)return;e.dataset.state=value;e.innerHTML=icon(value==='ready'?'check':value==='warn'?'REVIEW':'clock')+'<span>'+({camera:'Camera',hailo:'Hailo NPU',detector:'Detector',llama:'ExecuTorch Llama',sop:'SOP index',database:'Database'}[id])+'</span><span>'+esc(label)+'</span>';}
function onStatus({health,status,error}){
 state.health=health;
 state.connected=!!health&&!error;
 if(status)state.status=status;
 const banner=$('#connection-banner');
 banner.hidden=!error&&!health?.startup_error;
 banner.textContent=error?'Local station disconnected. Recorded results stay pinned. Reconnecting automatically…':health?.startup_error?'Station startup needs attention: '+health.startup_error:'';
 $('#footer-connection').textContent=api.mode==='mock'?'DEMO ADAPTER · NO HARDWARE':error?'STATION DISCONNECTED':health?.ready?'LOCAL STATION CONNECTED':'RUNTIME STARTING · SHELL READY';
 const s=status||{},cam=s.camera||{};
 const values={camera:[cam.frame_ready?'ready':'warn',cam.running?(cam.frame_ready?'Live frames available':'Waiting for fresh frame'):'Camera idle · image inspection available'],hailo:[s.ready?(s.vision_backend==='hailo'?'ready':'warn'):'warn',s.vision_backend==='hailo'?'HailoRT vision pipeline active':s.ready?'ONNX CPU fallback':'Detector starting'],llama:[clsName(s.llama_state),s.llama_error||'ExecuTorch advisor: '+statusText()],database:[health?.ready?'ready':'warn',health?.ready?'Inspection database available':'Database pending']};
 for(const [key,[value,label]] of Object.entries(values)){const el=$('#chip-'+key);el.dataset.state=error?'fail':value;el.title=label;el.setAttribute('aria-label',label);}
 bootItem('camera',cam.frame_ready?'ready':'warn',cam.frame_ready?'ready':'idle / optional');bootItem('hailo',s.vision_backend==='hailo'?'ready':'warn',s.vision_backend||'pending');bootItem('detector',s.ready?'ready':'pending',s.ready?'ready':'starting');bootItem('llama',s.llama_state==='ready'?'ready':'warn',s.llama_state||'warming up');bootItem('sop',state.sop?'ready':'pending',state.sop?'revision '+state.sop.revision:'loading');bootItem('database',health?.ready?'ready':'pending',health?.ready?'ready':'pending');
 updatePipeline();updateCameraHint();updateOptical(state.selected,state.status);updateConsole(state);
 if(state.route==='health')updateHealth();
 if(health?.ready&&Date.now()-state.lastRefresh>10000){state.lastRefresh=Date.now();refreshRecords().catch(()=>{});}
}
function updatePipeline(){
 const v=$('#vision-state'),l=$('#llama-state'),s=state.status;
 const heading=v?.closest('.pipeline')?.querySelector('h3');if(heading)heading.textContent=s?.vision_backend==='hailo'?'Vision / Hailo-8':'Vision / Arm CPU';
 if(v)v.innerHTML=badge(!state.connected?'DISCONNECTED':s?.ready?(s.vision_backend==='hailo'?'HAILO ACTIVE':'CPU FALLBACK'):'STARTING',s?.vision_backend==='hailo'?'accent':'');
 if(l)l.innerHTML='<span class="badge '+(clsName(s?.llama_state)==='ready'?'accent':'')+'">'+(s?.llama_state==='generating'?'<span class="spinner"></span>':icon('llama'))+esc(statusText().toUpperCase())+'</span>';
 const meta=$('#llama-meta');if(meta)meta.textContent='Llama 3.2 1B · INT4 · '+(s?.llama_threads||2)+' threads · automatic advice';
}
async function refreshRecords(){
 if(state.refreshInFlight)return;
 state.refreshInFlight=true;
 try{
 const rows=await api.history();
 // Bounded detail hydration supports filters without unbounded API concurrency.
 if(api.mode==='real'){let cursor=0;await Promise.all(Array.from({length:3},async()=>{while(cursor<rows.length){const i=cursor++;try{rows[i]={...rows[i],...await api.get(rows[i].inspection_id)};}catch{}}}));}
 state.records=rows;
 if(state.route==='history')renderHistoryRows();
 }finally{state.refreshInFlight=false;}
}
function inspectHTML(){
 return heading('Inspection station','Precision in every pocket. Evidence behind every decision.',button('Export JSON','export-selected','download')+button('Command','command','search','ghost'))+
 '<div class="pipeline-grid"><div class="card pipeline"><div class="pipeline-symbol">'+icon('chip')+'</div><div><h3>Vision / Hailo NPU</h3><p>YOLOv8s · HailoRT · detector + rules</p></div><div id="vision-state">'+badge('STARTING')+'</div></div><div class="card pipeline"><div class="pipeline-symbol llama">'+icon('llama')+'</div><div><h3>Advisory / Arm CPU</h3><p>ExecuTorch · separate inference pipeline</p></div><div id="llama-state">'+badge('WARMING UP')+'</div></div></div>'+
 '<div class="inspect-grid"><section class="vision-column" aria-label="Vision and inspection results"><div class="card viewer-card"><div class="card-header"><div class="row">'+icon('eye')+'<h2>Inspection viewer</h2></div><span class="badge" id="viewer-pin">'+icon('lock')+'NO SNAPSHOT</span></div><div class="viewer-toolbar"><div class="segmented" aria-label="Image display mode">'+[['original','Original'],['annotated','Annotated'],['split','Side-by-side'],['heatmap','Heatmap']].map(([v,label])=>'<button class="btn '+(v==='annotated'?'active':'')+'" data-view="'+v+'" '+(v==='heatmap'&&!api.capabilities.heatmap?'disabled title="No anomaly heatmap is exposed by this backend"':'')+'>'+label+'</button>').join('')+'</div><label class="row tiny">Opacity <input id="overlay-opacity" type="range" min="10" max="100" value="90" aria-label="Annotation opacity"></label></div><div class="viewer-stage" id="viewer" tabindex="0" aria-label="Inspection image viewer"></div><div class="viewer-controls"><span class="tiny mono" id="image-size">— × — px</span><div class="row">'+button('','zoom-out','minus','icon-only ghost','aria-label="Zoom out"')+'<span class="mono tiny" id="zoom-label">100%</span>'+button('','zoom-in','plus','icon-only ghost','aria-label="Zoom in"')+button('Fit','fit','fit','ghost')+button('Fill','fill','','ghost')+button('1:1','one','','ghost')+'</div></div><div class="source-controls"><div class="source-tabs" aria-label="Inspection source">'+[['upload','Upload','upload'],['local','Local images','folder'],['usb','USB camera','camera'],['csi','CSI camera','chip']].map(([v,label,i])=>'<button class="btn '+(state.source===v?'active':'')+'" data-source="'+v+'">'+icon(i)+label+'</button>').join('')+'</div><div id="source-options"></div><div id="camera-hint" class="source-hint"></div></div></div><div id="result-panel">'+resultHTML()+'</div><div class="card"><div class="card-header"><div class="row"><h2>Detections</h2><span class="badge" id="detection-count">0 REGIONS</span></div><span class="tiny">Hover to locate · click coordinates to copy</span></div><div class="table-scroll" style="max-height:310px"><table class="table"><thead><tr>'+[['type','Defect class'],['confidence','Confidence'],['bbox','BBox x / y / w / h'],['area','Area %'],['severity','Severity']].map(([id,label])=>'<th><button data-sort="'+id+'">'+label+(id==='confidence'?' ↓':'')+'</button></th>').join('')+'</tr></thead><tbody id="detections-body"></tbody></table></div><div id="detections-empty"></div></div></section>'+
 '<aside class="advice-column" aria-label="Advisory assistance"><div class="card"><div class="card-header"><div><div class="row">'+icon('llama')+'<h2>ExecuTorch Llama</h2></div><p class="tiny mt-8" id="llama-meta">Llama 3.2 1B · INT4 · on-device</p></div><span class="badge accent">'+icon('shield')+'ADVISORY ONLY</span></div><div class="card-body" id="advice-content"></div></div><div class="card"><div class="card-header"><div class="row">'+icon('file')+'<h2>QA deviation draft</h2></div><span class="badge REVIEW">DRAFT</span></div><div class="card-body"><p class="tiny mb-16">An editable working note. QA review and sign-off are required.</p>'+button('Draft deviation report','draft','file','','id="draft-button"')+'<textarea id="qa-draft" class="qa-draft mt-16" aria-label="Editable QA draft" placeholder="Generate a draft grounded in this inspection’s recorded advisory." hidden></textarea><div class="draft-actions" id="draft-actions" hidden>'+button('Copy','copy-draft','copy','small-btn')+button('Export .txt','export-draft','download','small-btn')+'</div></div></div><div class="card"><div class="card-header"><h2>Ask about this inspection</h2>'+icon('lock')+'</div><div class="card-body"><div class="badge mb-16" id="question-context">No inspection selected</div><div class="question-chips">'+button('Why was this flagged?','question-explain')+button('What SOP applies?','question-rectify')+button('Similar past rejects?','question-similar')+'</div><form id="question-form" class="question-entry"><input id="question-text" maxlength="500" aria-label="Question about selected inspection" placeholder="Ask about the selected evidence…"><button class="btn icon-only" aria-label="Send inspection question">'+icon('send')+'</button></form><div id="answer-output" role="status"></div><p class="tiny mt-8">Constrained inspection intents. No free-form repair or release decisions.</p></div></div><div class="card"><div class="card-header"><h2>QA review</h2><span class="badge">'+icon('lock')+'APPEND ONLY</span></div><div class="card-body"><form id="review-form" class="stack">'+field('reviewer','Reviewer ID','text',state.operator,'maxlength="80" required autocomplete="off"')+'<div class="field"><label for="review-note">Disposition note · does not change detector result</label><textarea id="review-note" maxlength="1000" rows="3" required placeholder="Document the review and next step…"></textarea></div><button class="btn" id="review-submit" type="submit">'+icon('check')+'Record QA review</button></form><div class="divider"></div><div id="qa-timeline"></div><p class="tiny mt-16" id="review-scope"></p></div></div><div class="notice">'+icon('shield')+'<span>AI advice is informational. Final disposition rests with QA personnel.</span></div></aside></div>';
}
function renderInspect(){
 $('#page').innerHTML=inspectHTML();state.viewer=new Viewer($('#viewer'),index=>{$$('#detections-body tr').forEach(r=>r.classList.toggle('highlight',Number(r.dataset.index)===index));});
 let dimensions='';state.viewer.onZoom=scale=>{$('#zoom-label').textContent=Math.round(scale*100)+'%';const size=state.viewer.width+' × '+state.viewer.height+' px';if(state.viewer.width&&dimensions!==size){dimensions=size;$('#image-size').textContent=size;renderDetections();}};
 $('#overlay-opacity').oninput=e=>{state.viewer.opacity=e.target.value/100;state.viewer.draw();};
 $('#question-form').onsubmit=e=>{e.preventDefault();askQuestion($('#question-text').value);};
 $('#review-form').onsubmit=submitReview;
 $('#qa-draft').oninput=e=>{if(state.selected)state.drafts.set(state.selected.inspection_id,e.target.value);};
 sourceOptions();renderSelected();updatePipeline();updateCameraHint();
 mountConsole(state,{runAnomaly,error:message=>toast(message,true),preview:previewImage,
   showRecord:record=>{state.selected=record;state.previewing=false;if(!record)state.viewer.clear();renderSelected();if(record)state.viewer.setMode(record.anomaly?'heatmap':'annotated');}});
}
function sourceOptions(){
 const host=$('#source-options');if(!host)return;
 const s=state.source;
 if(s==='upload')host.innerHTML='<div class="source-options"><input id="file-input" type="file" accept="image/*" class="sr-only" aria-label="Upload inspection image"><label class="btn" for="file-input">'+icon('upload')+'Choose image</label><span class="source-name" id="source-file-name">'+esc(state.file?.name||'JPG, PNG, WEBP · up to 20 MB')+'</span>'+button('Run inference','run','play','primary','id="run-button"')+'</div>';
 else if(s==='local'){
  const groups=[...new Set(state.library.map(r=>r.group||'other'))],rows=state.library.filter(r=>!state.libraryGroup||(r.group||'other')===state.libraryGroup);
  host.innerHTML='<div class="source-options"><select id="local-group" aria-label="Defect test folder"><option value="">All test folders</option>'+groups.map(g=>'<option value="'+esc(g)+'" '+(g===state.libraryGroup?'selected':'')+'>'+esc(human(g))+' ('+state.library.filter(r=>(r.group||'other')===g).length+')</option>').join('')+'</select><select id="local-image" aria-label="Local test image">'+(rows.length?rows.map(r=>'<option value="'+esc(r.name)+'" '+(r.name===state.sourceName?'selected':'')+'>'+esc(r.display_name||r.name.split('/').at(-1))+'</option>').join(''):'<option>No local images found</option>')+'</select>'+button('Run detection','run','play','primary','id="run-button"')+'</div><div class="library-scope tiny">'+esc(rows[0]?.label_origin||'Unannotated demonstrations')+' · stored locally</div>';
 }
 else host.innerHTML='<div class="source-options"><select id="camera-device" aria-label="Camera device">'+(s==='csi'?'<option value="picamera2">CSI · Picamera2</option>':['0','1','2'].map(n=>'<option value="'+n+'" '+(saved('camera','0')===n?'selected':'')+'>USB /dev/video'+n+'</option>').join(''))+'</select>'+button('Connect','camera-start','camera')+button('Stop','camera-stop','stop','icon-only','aria-label="Stop camera"')+'</div><div class="source-options mt-8">'+button('Live view','camera-live','eye')+button('Freeze / Snapshot','run','camera','primary','id="run-button"')+'</div>';
 if($('#file-input'))$('#file-input').onchange=e=>{const file=e.target.files[0];if(!file)return;if(file.size>20*1024*1024){toast('Choose an image smaller than 20 MB.',true);return;}state.file=file;if(state.previewURL)URL.revokeObjectURL(state.previewURL);state.previewURL=URL.createObjectURL(file);previewImage(state.previewURL,'UPLOAD PREVIEW · '+file.name+' · NOT INSPECTED');$('#source-file-name').textContent=file.name;};
 if($('#local-group'))$('#local-group').onchange=e=>{state.libraryGroup=e.target.value;state.sourceName=state.library.find(r=>!state.libraryGroup||(r.group||'other')===state.libraryGroup)?.name;sourceOptions();if(state.sourceName)previewLocal(state.sourceName);};
 if($('#local-image'))$('#local-image').onchange=e=>previewLocal(e.target.value);
 updateCameraHint();updateRunButton();
}
function previewImage(url,label){state.previewing=true;state.viewer?.preview(url,label);if($('#viewer-pin'))$('#viewer-pin').innerHTML=icon('eye')+'PREVIEW · NOT INSPECTED';$('#result-panel').innerHTML='<div class="card result-banner"><div class="result-icon">'+icon('eye')+'</div><div><h2>Preview</h2><p>Run '+(state.workspaceMode==='anomaly'?'anomaly inference':'detection')+' to record the result for this image.</p></div></div>';updateConsole(state);}
function previewLocal(name){const image=state.library.find(r=>r.name===name);if(!image)return;state.sourceName=name;state.file=null;previewImage(image.url,'LOCAL PREVIEW · '+name+' · NOT INSPECTED');$('#local-image')&&($('#local-image').value=name);$$('[data-library]').forEach(b=>b.classList.toggle('active',b.dataset.library===name));}
function updateRunButton(){const b=$('#run-button');if(!b)return;b.disabled=state.busy||!state.health?.ready||(state.source==='upload'&&!state.file)||(state.source==='local'&&!state.sourceName)||(['usb','csi'].includes(state.source)&&!state.status?.camera?.frame_ready);b.innerHTML=(state.busy?'<span class="spinner"></span>':icon(['usb','csi'].includes(state.source)?'camera':'play'))+'<span>'+(state.busy?'Inspecting…':['usb','csi'].includes(state.source)?'Freeze / Snapshot':'Run inference')+'</span>';}
function updateCameraHint(){
 updateRunButton();const h=$('#camera-hint');if(!h)return;const cam=state.status?.camera;
 const text=['usb','csi'].includes(state.source)?cam?.error?cam.error:cam?.frame_ready?'Fresh frame available · '+num(cam.fps)+' FPS · '+(cam.frame_age_ms!=null?'frame age '+cam.frame_age_ms+' ms (demo)':'frame age not exposed'):'Waiting for a fresh frame. Connect the camera before snapshotting.':state.source==='local'?'Local device storage · inference and advice remain on-device':'Upload is sent only to this local station.';
 h.innerHTML=icon(cam?.error?'REVIEW':'lock')+esc(text);h.classList.toggle('hold-text',!!cam?.error);
}
function resultHTML(){
 const r=state.selected;if(!r)return '<div class="card result-banner"><div class="result-icon">'+icon('inspect')+'</div><div><h2>Ready for inspection</h2><p>Run inference to record a visual model result.</p></div></div>';
 const times=r.latency||{},tone=visualTone(r);
 return '<div class="card"><div class="result-banner '+tone+'" role="status" aria-live="polite"><div class="result-icon '+tone.toLowerCase()+'-text">'+icon(tone)+'</div><div class="grow"><div class="between"><h2 class="'+tone.toLowerCase()+'-text">'+esc(inspectionLabel(r))+'</h2><span class="mono tiny">'+num(r.vision_ms,2)+' ms</span></div><p>'+esc(visualReason(r))+'</p><div class="decision-lock">'+icon('lock')+'VISUAL MODEL CHECK · QA DECISION PRESERVED · '+esc(r.inspection_id)+'</div></div></div><div class="latency-strip">'+[['Capture',times.capture_ms],['Preprocess',times.preprocess_ms],[r.backend==='hailo'?'Vision / HailoRT':'Vision / CPU',times.inference_ms??r.vision_ms],['Postprocess',times.postprocess_ms]].map(([label,value])=>'<div><label>'+label+'</label><span>'+(value!=null?num(value,2)+' ms':'not exposed')+'</span></div>').join('')+'</div></div>';
}
function renderSelected(){
 if(state.route!=='inspect')return;const r=state.selected;
 $('#result-panel').innerHTML=resultHTML();
 $('#question-context').textContent=r?'Inspection '+r.inspection_id.slice(0,12)+' · pinned context':'No inspection selected';
 $('#question-context').title=r?r.inspection_id:'';
 $('#viewer-pin').innerHTML=icon('lock')+(r?'PINNED SNAPSHOT':'NO SNAPSHOT');
 if(r){state.previewing=false;state.viewer.setRecord({...r,demo_heatmap:api.mode==='mock'});persist('selected',r.inspection_id);}
 renderDetections();renderAdvice();renderReviews();restoreDraft();updateConsole(state);
}
function renderDetections(){
 const detections=(state.selected?.detections||[]).map((d,index)=>({...d,index}));
 const key=state.sort;detections.sort((a,b)=>{const val=d=>key==='type'?d.type:key==='bbox'?d.box_xyxy[0]:key==='area'?(d.box_xyxy[2]-d.box_xyxy[0])*(d.box_xyxy[3]-d.box_xyxy[1]):key==='severity'?(d.severity||'major'):d.confidence;const av=val(a),bv=val(b);return (typeof av==='string'?av.localeCompare(bv):av-bv)*(state.descending?-1:1);});
 $('#detection-count').textContent=detections.length+' REGIONS';$('#detections-empty').innerHTML=detections.length?'':empty(state.selected?'No detections above configured thresholds':'No detections yet',state.selected?'The recorded rule decision also accounts for profile and capture checks.':'Select a source and run inference.','eye');
 $('#detections-body').innerHTML=detections.map(d=>{const [x,y,x2,y2]=d.box_xyxy,coords=[x,y,x2-x,y2-y].map(Math.round).join(' / '),area=state.viewer?.width&&state.viewer?.height?(x2-x)*(y2-y)/(state.viewer.width*state.viewer.height)*100:null;return '<tr data-index="'+d.index+'"><td><strong>'+esc(human(d.type))+'</strong></td><td><div class="confidence mono">'+num(d.confidence*100)+'%<div class="progress"><span style="width:'+Math.min(100,d.confidence*100)+'%"></span></div></div></td><td><button class="copy-coord" data-coords="'+coords+'" title="Copy x y width height in source pixels">'+coords+'</button></td><td class="mono">'+(area==null?'—':num(area,2)+'%')+'</td><td>'+badge(d.severity||state.selected?.severity||'major')+'</td></tr>';}).join('');
 $$('#detections-body tr').forEach(row=>{row.onmouseenter=()=>state.viewer.setHighlight(Number(row.dataset.index));row.onmouseleave=()=>state.viewer.setHighlight(-1);});
}
let adviceToken=0;
function renderAdvice(){
 const host=$('#advice-content');if(!host)return;const r=state.selected;
 if(!r){host.innerHTML=empty('Evidence first. Advice second.','The advisor is pinned to a recorded inspection. Vision runs independently.','llama');return;}
 const a=r.advice;
 if(!a){host.innerHTML='<div class="between"><span class="badge accent"><span class="spinner"></span>ADVISOR PENDING</span><span class="tiny">Vision result is already recorded</span></div><div class="pending-shimmer" style="padding:12px 0"><div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div></div><p class="tiny mt-8">Generating a bounded SOP action on the Arm CPU. This does not block inspections.</p><button class="btn small-btn ghost" data-action="cancel-advice">Cancel advisory</button>';return;}
 const accepted=a.status==='llama_validated',v=a.advisory||{};
 host.innerHTML='<div class="between mb-16">'+(accepted?'<span class="badge accent">'+icon('check')+'VALIDATED RESPONSE</span>':'<span class="badge REVIEW">'+icon('REVIEW')+'SAFE FALLBACK</span>')+'<span class="mono tiny">'+num(a.elapsed_ms/1000)+' s</span></div><div class="eyebrow mb-16">Recommended operator action</div><div class="advice-copy" id="advice-text"></div><div class="advice-detail"><label>Probable cause</label><p>Not established by visual evidence. QA investigation is required.</p></div><div class="between mt-16"><span class="tiny">SOP grounding</span><button class="btn small-btn" data-citation="'+esc(v.clause_id||'BT-03')+'">'+icon('sop')+esc(a.sop_document||'BT-DEMO-SOP-01')+' / '+esc(v.clause_id||'BT-03')+'</button></div><div class="between mt-16"><span class="tiny">Priority: '+esc(r.severity)+' · from inspection rules</span>'+button('Retry','retry','refresh','small-btn ghost')+'</div>'+(a.fallback_reason?'<p class="tiny mt-8">Validation fallback: '+esc(a.fallback_reason)+'</p>':'');
 const text=v.operator_message||'No advisory text is available.';
 const metrics=document.createElement('p');metrics.className='mono tiny mt-8';metrics.textContent=runtimeTiming(a);host.append(metrics);
 const approval=document.createElement('p');approval.className='tiny mt-8';approval.textContent='Demonstration SOP · unapproved for operations. Consult an approved procedure.';host.append(approval);
 if(a.cache_hit){
  host.querySelector('.badge').textContent=accepted?'REUSED VALIDATED ADVICE':'REUSED SOP FALLBACK';
  const timing=host.querySelector('.mono');if(timing)timing.textContent=a.elapsed_ms.toFixed(1)+' ms reuse';
  const note=document.createElement('p');note.className='tiny mt-8';note.textContent='Identical observation and SOP facts reused. Original generation '+(a.original_generation_ms/1000).toFixed(1)+' s. Regenerate to request a fresh model response.';host.append(note);
 }
 const retry=host.querySelector('[data-action="retry"]');if(retry){const header=host.closest('.card').querySelector('.card-header');header.querySelector('[data-action="retry"]')?.remove();retry.className='btn icon-only ghost';retry.title='Regenerate a fresh Llama response';retry.setAttribute('aria-label',retry.title);retry.innerHTML=icon('refresh');header.append(retry);}
 if(api.capabilities.tokenStream&&accepted){
  const generation=++adviceToken,el=$('#advice-text');el.setAttribute('aria-busy','true');(async()=>{for await(const chunk of api.streamText(text)){if(generation!==adviceToken||!el.isConnected)return;el.textContent+=chunk;}el.setAttribute('aria-busy','false');})();
 }else $('#advice-text').textContent=text;
}
function restoreDraft(){const id=state.selected?.inspection_id,draft=state.drafts.get(id);if($('#qa-draft')){$('#qa-draft').hidden=!draft;$('#draft-actions').hidden=!draft;$('#qa-draft').value=draft||'';}}
async function renderReviews(){
 const el=$('#qa-timeline');if(!el)return;const id=state.selected?.inspection_id;
 if(!id){el.innerHTML='<p class="tiny">No inspection selected.</p>';return;}
 let entries=state.reviewMirror.get(id)||[];
 const latest=state.selected.qa_review;
 if(latest&&!entries.some(v=>v.reviewed_at===latest.reviewed_at))entries=[...entries,latest];
 if(api.capabilities.qaTimeline)entries=await api.reviewTimeline(id);
 state.reviewMirror.set(id,entries);
 if(state.selected?.inspection_id!==id||!el.isConnected)return;
 el.innerHTML=entries.length?entries.map(v=>reviewEntry(v,v.browser_hash)).join(''):empty('No QA review recorded','Append a review note to this inspection.','lock');
 $('#review-scope').textContent=api.capabilities.qaTimeline?'Append-only server review timeline; original inspection decision is preserved.':'Latest server review + notes submitted in this browser session.';
}
async function submitReview(e){
 e.preventDefault();const r=state.selected;if(!r)return toast('Select an inspection first.',true);
 const id=r.inspection_id,value={reviewer:$('#reviewer').value.trim(),comment:$('#review-note').value.trim()};if(!value.reviewer||!value.comment)return;
 const submit=$('#review-submit');submit.disabled=true;
 try{const response=await api.review(id,value);const review=response.reviewed_at?{...value,...response}:response.qa_review||{...value,reviewed_at:new Date().toISOString()};review.browser_hash=await digest(review);state.reviewMirror.set(id,[...(state.reviewMirror.get(id)||[]),review]);if(state.selected?.inspection_id===id){state.selected.qa_review=review;$('#review-note').value='';await renderReviews();}toast('QA note appended. Detector decision unchanged.');refreshRecords().catch(()=>{});}catch(e){toast(e.message,true);}finally{if(submit.isConnected)submit.disabled=false;}
}
async function selectRecord(id,showInspect=false){const record=await api.get(id);state.selected=record;persist('selected',id);if(showInspect){location.hash='inspect';if(state.route==='inspect')renderSelected();}else if(state.route==='inspect')renderSelected();return record;}
async function runInspection(){
 if(state.workspaceMode==='anomaly')return state.runAnomalyAction?.();
 if(state.busy)return;state.busy=true;updateRunButton();const source=state.source,start=performance.now();
 try{
  const input={kind:source==='upload'?'upload':source==='local'?'local':'camera',file:state.file,name:state.sourceName};
  if(input.kind==='upload'&&!input.file)throw Error('Choose an image first.');if(input.kind==='local'&&!input.name)throw Error('Choose a local image first.');
  scan(state.viewer);const record=await api.inspect(input);state.selected=record;state.previewing=false;state.modeRecords={...state.modeRecords,detection:record};state.selected.client_response_ms=performance.now()-start;persist('selected',record.inspection_id);
  if(state.route!=='inspect')location.hash='inspect';else renderSelected();
  state.consoleCompleted?.();resultDialog(record,()=>openDetail(record.inspection_id),state.sound);verdict(state.viewer,{...record,decision:visualTone(record)});
  refreshRecords().catch(()=>{});
 }catch(e){toast(e.message,true);}finally{state.busy=false;updateRunButton();updateConsole(state);}
}
async function runAnomaly(profile,sample,file=null){
 if(state.busy)return;
 if(state.anomalySource==='upload'&&!file)return toast('Choose an anomaly image first.',true);
 if(!sample&&!file&&!state.selected)return toast('Choose an image or a recorded inspection first.',true);
 state.busy=true;updateRunButton();updateConsole(state);
 try{
  const record=file?await api.anomalyUpload(profile,file):await api.anomalyInspect(sample?{profile,sample}:{profile,inspection_id:state.selected.inspection_id});
  state.selected=record;state.previewing=false;state.modeRecords={...state.modeRecords,anomaly:record};persist('selected',record.inspection_id);renderSelected();
  state.consoleMeasurementTab?.('anomaly');state.viewer.setMode('heatmap');
  $$('[data-view]').forEach(button=>button.classList.toggle('active',button.dataset.view==='heatmap'));
  state.consoleCompleted?.();resultDialog(record,()=>openDetail(record.inspection_id),false);refreshRecords().catch(()=>{});
 }catch(e){toast(e.message,true);}finally{state.busy=false;updateRunButton();updateConsole(state);}
}
async function askQuestion(question,intent){
 const r=state.selected;if(!r)return toast('Select a recorded inspection first.',true);const id=r.inspection_id,el=$('#answer-output');
 if(!question.trim()&&!intent)return;
 el.innerHTML='<div class="answer-box"><span class="spinner"></span> Checking recorded inspection context…</div>';
 try{
  let answer;
  if(intent==='similar'){
   const types=new Set(r.detections?.map(d=>d.type)||[]);const matches=state.records.filter(v=>v.inspection_id!==id&&v.decision==='HOLD'&&v.detections?.some(d=>types.has(d.type)));
   answer={reply:matches.length+' matching HOLD records in the '+(api.capabilities.historyLimit?'recent '+api.capabilities.historyLimit:'demo')+' inspection snapshot. This is a local class-match lookup, not a Llama diagnosis or a complete historical query.'};
  }else answer=await api.ask(id,question,intent);
  if(state.selected?.inspection_id!==id)return;
  state.questionAnswers.set(id,answer);el.innerHTML='<div class="answer-box">'+esc(answer.reply)+(answer.sections||[]).map((section,index)=>'<details class="answer-section" '+(index===0?'open':'')+'><summary>'+esc(section.title)+'</summary><ul>'+section.items.map(item=>'<li>'+esc(item)+'</li>').join('')+'</ul></details>').join('')+(answer.clause_id?'<div class="mt-8"><button class="btn small-btn" data-citation="'+esc(answer.clause_id)+'">'+icon('sop')+esc(answer.clause_id)+'</button></div>':'')+'<span class="answer-source">'+(answer.source==='recorded_llama_advisory'?'Recorded Llama advisory + SOP context. Follow-up reuses the pinned response.':'Inspection facts + local SOP. No new model generation.')+'</span></div>';
 }catch(e){if(el.isConnected)el.innerHTML='<div class="notice error mt-16">'+esc(e.message)+'</div>';}
}
function historyHTML(){
 const f=state.filters;
 const options=(values,current)=>'<option value="">All</option>'+values.map(v=>'<option value="'+esc(v)+'" '+(v===current?'selected':'')+'>'+esc(human(v))+'</option>').join('');
 return heading('Inspection history','A traceable record of every inspection in the loaded snapshot.',button('Export filtered CSV','history-csv','download')+button('Export selected JSON','history-json','file'))+
 '<div class="card mb-16"><div class="card-body"><div class="filter-grid">'+field('filter-search','Search inspection / source','search',f.search||'','placeholder="Search records…" data-filter="search"')+'<div class="field"><label for="filter-result">Result</label><select id="filter-result" data-filter="result">'+options(['PASS','REVIEW','HOLD'],f.result)+'</select></div><div class="field"><label for="filter-class">Defect class</label><select id="filter-class" data-filter="defect">'+options(knownClasses,f.defect)+'</select></div><div class="field"><label for="filter-review">QA review</label><select id="filter-review" data-filter="review">'+options(['reviewed','unreviewed'],f.review)+'</select></div><div class="field"><label for="filter-batch">Batch</label><select id="filter-batch" data-filter="batch"><option value="">All</option>'+(api.capabilities.batches?options(['BT-261119-A','BT-261119-B'],f.batch):'<option value="unassigned" '+(f.batch==='unassigned'?'selected':'')+'>Unassigned</option>')+'</select></div></div><div class="filter-more">'+field('filter-from','From date','date',f.from||'','data-filter="from"')+field('filter-to','To date','date',f.to||'','data-filter="to"')+field('filter-min','Minimum confidence %','number',f.min||'','min="0" max="100" data-filter="min"')+field('filter-max','Maximum confidence %','number',f.max||'','min="0" max="100" data-filter="max"')+'</div><div class="filter-chips" id="filter-chips"></div></div></div><div class="card"><div class="card-header"><div class="row"><h2>Inspection records</h2><span class="badge" id="history-count">LOADING</span></div><span class="tiny">'+(api.capabilities.historyLimit?'API exposes the latest 50 records':'Virtualized demo dataset')+'</span></div><div class="history-table" id="history-table" role="table" aria-label="Inspection history"></div><div id="history-empty"></div><div class="card-body between"><span class="tiny" id="history-foot"></span><span class="tiny" id="history-selection">0 selected</span></div></div>';
}
function filteredRecords(){
 const f=state.filters;
 return batchRecords().filter(r=>{
  const reviewed=!!r.qa_review||r.qa_reviewed;
  const scores=(r.detections||[]).filter(d=>!f.defect||d.type===f.defect).map(d=>d.confidence*100);
  return (!f.search||[r.inspection_id,r.source,r.batch_id].join(' ').toLowerCase().includes(f.search.toLowerCase()))&&(!f.result||r.decision===f.result)&&(!f.defect||r.detections?.some(d=>d.type===f.defect))&&(!f.review||(f.review==='reviewed'?reviewed:!reviewed))&&(!f.batch||(r.batch_id||'unassigned')===f.batch)&&(!f.from||new Date(r.created_at)>=new Date(f.from+'T00:00:00'))&&(!f.to||new Date(r.created_at)<=new Date(f.to+'T23:59:59.999'))&&(!f.min||(scores.length&&scores.some(v=>v>=Number(f.min))))&&(!f.max||(scores.length&&scores.some(v=>v<=Number(f.max))));
 });
}
function renderHistory(){
 $('#page').innerHTML=historyHTML();
 for(const input of $$('[data-filter]'))input.addEventListener('input',()=>{state.filters[input.dataset.filter]=input.value;persist('filters',state.filters);saveFilterHash();renderHistoryRows();});
 renderHistoryRows();
}
function saveFilterHash(){
 const p=new URLSearchParams();for(const [key,value] of Object.entries(state.filters))if(value)p.set(key,value);
 history.replaceState(null,'','#history'+(p.size?'?'+p:''));
}
function renderHistoryRows(){
 if(state.route!=='history'||!$('#history-table'))return;
 const rows=filteredRecords();state.virtual?.destroy();
 $('#history-count').textContent=num(rows.length,0)+' RECORDS';$('#history-foot').textContent=api.capabilities.historyLimit?'Filtered within the latest 50 server records. No claim of full database coverage.':'Demo dataset · '+num(state.records.length,0)+' simulated records.';
 $('#history-empty').innerHTML=rows.length?'':empty('No matching inspections','Clear a filter or inspect another specimen.','history');
 $('#history-table').style.height=rows.length?'550px':'48px';
 $('#filter-chips').innerHTML=Object.entries(state.filters).filter(([,v])=>v).map(([key,value])=>'<button class="btn small-btn" data-clear-filter="'+key+'">'+esc(key)+': '+esc(value)+icon('close')+'</button>').join('')+(Object.values(state.filters).some(Boolean)?button('Clear all','clear-filters','','ghost small-btn'):'');
 state.virtual=new VirtualTable($('#history-table'),rows,r=>'<div class="history-grid history-row" role="row" tabindex="0" data-row="'+esc(r.inspection_id)+'" aria-label="'+esc(r.inspection_id+' '+r.decision)+'"><div><input type="checkbox" '+(state.selectedRows.has(r.inspection_id)?'checked':'')+' aria-label="Select '+esc(r.inspection_id)+'"></div><div><img loading="lazy" src="'+esc(r.original_url||r.image_url||'')+'" alt=""></div><div><strong class="mono">'+esc(r.inspection_id)+'</strong><div class="tiny">'+when(r.created_at)+'</div></div><div title="'+esc(r.source)+'">'+esc(r.batch_id||r.source||'Unassigned')+'</div><div>'+badge(r.decision)+'</div><div>'+esc([...new Set(r.detections?.map(d=>human(d.type))||[])].join(', ')||'—')+'</div><div class="tiny">'+(r.advice?.status==='llama_validated'?'Validated':r.advice?'Fallback':'Pending')+'</div><div class="tiny">'+(r.qa_review||r.qa_reviewed?'Reviewed':'Open')+'</div></div>',id=>openDetail(id), (id,checked)=>{if(checked)state.selectedRows.add(id);else state.selectedRows.delete(id);updateSelection();});
 $('#history-select-all').onchange=e=>{for(const row of rows){if(e.target.checked)state.selectedRows.add(row.inspection_id);else state.selectedRows.delete(row.inspection_id);}state.virtual.start=-1;state.virtual.draw();updateSelection();};
 updateSelection();
}
function updateSelection(){if($('#history-selection'))$('#history-selection').textContent=state.selectedRows.size+' selected';}
function batchRecords(){return state.records.filter(r=>state.batch==='all'||r.batch_id===state.batch);}
function renderDashboard(){
 const rows=batchRecords(),total=rows.length,counts={PASS:0,REVIEW:0,HOLD:0},classes={},hist=Array(10).fill(0);
 for(const r of rows){counts[r.decision]++;for(const d of r.detections||[]){classes[d.type]=(classes[d.type]||0)+1;hist[Math.min(9,Math.floor(d.confidence*10))]++;}}
 const latencies=rows.map(r=>r.vision_ms).filter(v=>typeof v==='number'),avg=latencies.reduce((a,b)=>a+b,0)/Math.max(1,latencies.length);
 const times=rows.map(r=>+new Date(r.created_at)).filter(Number.isFinite),minutes=(Math.max(...times)-Math.min(...times))/60000,rate=minutes>0?Math.max(0,total-1)/minutes:0;
 const series=Array.from({length:12},(_,i)=>rows.slice(i*Math.ceil(total/12),(i+1)*Math.ceil(total/12)).length);
 const metrics=[['Inspections',total,'',series],['PASS rate',total?counts.PASS/total*100:0,'%',series.map((v,i)=>v*(.7+i/50))],['HOLD',counts.HOLD,'',series.map(v=>v*.2)],['REVIEW',counts.REVIEW,'',series.map(v=>v*.1)],['Mean vision',avg,' ms',latencies.slice(0,20)],['Inspections / min',rate,'',series]];
 const colors={PASS:'var(--pass)',REVIEW:'var(--review)',HOLD:'var(--hold)'};
 let cumulative=0;const circles=Object.entries(counts).map(([key,count])=>{const length=total?count/total*100:0,svg='<circle cx="90" cy="90" r="65" fill="none" stroke="'+colors[key]+'" stroke-width="16" pathLength="100" stroke-dasharray="'+length+' '+(100-length)+'" stroke-dashoffset="'+(-cumulative)+'" transform="rotate(-90 90 90)"/>';cumulative+=length;return svg;}).join('');
 $('#page').innerHTML=heading('Batch overview','Operational trends from the loaded inspection snapshot.',button('Summarize this batch','batch-summary','llama','','id="batch-summary-button"'))+
 '<div class="notice mb-16">'+icon('info')+'<span>'+(api.capabilities.batches?'DEMO · Simulated batch and throughput data.':'Batch IDs are not exposed by the backend. Charts describe up to 50 recent images, not validated production units or a complete batch.')+'</span></div><div class="stats-grid">'+metrics.map(([label,v,suffix,values],i)=>'<div class="card metric"><div class="eyebrow">'+label+'</div><div class="value mono" data-counter="'+i+'">—</div>'+spark(values)+'<span class="tiny">Current loaded snapshot</span></div>').join('')+'</div><div class="batch-charts"><div class="card"><div class="card-header"><h2>Result distribution</h2>'+icon('dashboard')+'</div><div class="card-body chart-wrap"><div class="donut-layout"><svg class="donut" viewBox="0 0 180 180" role="img" aria-label="PASS '+counts.PASS+', REVIEW '+counts.REVIEW+', HOLD '+counts.HOLD+'"><circle cx="90" cy="90" r="65" fill="none" stroke="var(--surface-3)" stroke-width="16"/>'+circles+'<text x="90" y="89" fill="var(--text)" text-anchor="middle" font-family="Inter" font-size="28">'+num(total,0)+'</text><text x="90" y="108" fill="var(--muted)" text-anchor="middle" font-family="Inter" font-size="10">INSPECTIONS</text></svg><div class="legend">'+Object.entries(counts).map(([key,count])=>'<div><i style="background:'+colors[key]+'"></i>'+key+'<strong class="mono">'+count+'</strong></div>').join('')+'</div></div></div></div><div class="card"><div class="card-header"><h2>Detected regions by class</h2><span class="tiny">Multiple regions can occur per image</span></div><div class="card-body">'+(Object.keys(classes).length?Object.entries(classes).sort((a,b)=>b[1]-a[1]).map(([key,value])=>'<div class="bar-row"><span>'+esc(human(key))+'</span><div class="chart-bar"><span style="width:'+value/Math.max(...Object.values(classes))*100+'%"></span></div><span class="mono">'+value+'</span></div>').join(''):empty('No defect regions','No detections in the current snapshot.'))+'</div></div><div class="card"><div class="card-header"><h2>Inspection volume over time</h2><span class="tiny">12 equal time intervals</span></div><div class="card-body">'+rateChart(rows)+'</div></div><div class="card"><div class="card-header"><h2>Confidence histogram</h2><span class="tiny">Detection scores · not calibrated probabilities</span></div><div class="card-body"><svg viewBox="0 0 500 180" style="width:100%;height:180px" role="img" aria-label="Confidence histogram">'+hist.map((v,i)=>{const h=v/Math.max(...hist,1)*130;return '<rect x="'+(i*48+12)+'" y="'+(145-h)+'" width="30" height="'+h+'" rx="3" fill="var(--info)"/><text x="'+(i*48+27)+'" y="166" text-anchor="middle" font-size="10" fill="var(--muted)">'+i*10+'%</text>';}).join('')+'</svg></div></div></div><div id="batch-summary-output" class="mt-16" role="status"></div>';
 for(const [i,m] of metrics.entries())animateNumber($('[data-counter="'+i+'"]'),m[1],m[2]);
}
function rateChart(rows){
 const sorted=[...rows].sort((a,b)=>new Date(a.created_at)-new Date(b.created_at)),start=+new Date(sorted[0]?.created_at||Date.now()),end=+new Date(sorted.at(-1)?.created_at||Date.now()),span=Math.max(1,end-start),buckets=Array(12).fill(0);
 sorted.forEach(r=>buckets[Math.min(11,Math.floor((new Date(r.created_at)-start)/span*12))]++);
 const max=Math.max(...buckets,1),points=buckets.map((n,i)=>(12+i*43)+','+(140-n/max*110)).join(' ');
 return '<svg viewBox="0 0 500 180" style="width:100%;height:180px" role="img" aria-label="Inspection count per interval: '+buckets.join(', ')+'"><path d="M12 30H485M12 85H485M12 140H485" stroke="var(--border)" stroke-dasharray="4 4"/><polyline points="'+points+'" fill="none" stroke="var(--accent)" stroke-width="2.5"/>'+buckets.map((n,i)=>'<circle cx="'+(12+i*43)+'" cy="'+(140-n/max*110)+'" r="3" fill="var(--accent)"/>').join('')+'<text x="12" y="169" font-size="11" fill="var(--muted)">'+new Date(start).toLocaleTimeString()+'</text><text x="485" y="169" text-anchor="end" font-size="11" fill="var(--muted)">'+new Date(end).toLocaleTimeString()+'</text></svg>';
}
function renderSop(){
 const sop=state.sop;
 $('#page').innerHTML=heading('SOP library','Versioned instructions, available entirely on this device.',badge('LOCAL DOCUMENT','accent'))+(sop?'<div class="sop-layout"><div class="card"><div class="card-body"><div class="eyebrow">Active document</div><h2 class="mt-8">'+esc(sop.document_id)+'</h2><p class="tiny mt-8">Revision '+esc(sop.revision)+' · '+esc(sop.status)+'</p><input class="mt-16" id="sop-search" type="search" placeholder="Search sections…" aria-label="Search SOP sections" style="width:100%"><nav class="sop-nav" aria-label="SOP sections">'+sop.clauses.map(c=>'<a class="btn" href="#sop" data-scroll-clause="'+c.id+'">'+icon('sop')+c.id+' · '+esc(human(c.tags[0]))+'</a>').join('')+'</nav></div></div><div class="card"><div class="card-header"><h2>Inspection handling procedures</h2><span class="badge REVIEW">DEMO SOP · QA APPROVAL REQUIRED</span></div><div class="card-body" id="sop-sections">'+sop.clauses.map(c=>'<section class="sop-section" id="clause-'+c.id+'" data-clause="'+c.id+'"><div class="between"><h2>'+c.id+'</h2><span class="mono tiny">rev '+sop.revision+'</span></div><div class="tag-list mt-8">'+c.tags.map(tag=>'<span class="badge">'+esc(human(tag))+'</span>').join('')+'</div><p>'+esc(c.text)+'</p><div class="mt-16">'+button('Open citation','citation:'+c.id,'sop','small-btn')+'</div></section>').join('')+'</div></div></div>':empty('SOP is loading','The local document will appear when available.','sop'));
 if($('#sop-search'))$('#sop-search').oninput=e=>{const q=e.target.value.toLowerCase();$$('[data-clause]').forEach(el=>el.hidden=!el.textContent.toLowerCase().includes(q));};
}
async function buildAudit(){
 let previous='0'.repeat(64);state.audit=[];
 for(const r of [...batchRecords()].reverse()){const facts={inspection_id:r.inspection_id,created_at:r.created_at,decision:r.decision,model_sha256:r.model_sha256||null};const hash=await digest({previous,facts});if(!hash)break;state.audit.push({previous,hash,facts});previous=hash;}
}
function renderAudit(){
 if(api.mode==='real'){
  $('#page').innerHTML=heading('Evidence & audit','Append-only server events. Original detector decisions remain immutable.',button('Verify integrity','server-audit-verify','shield'))+'<div class="notice mb-16">Unkeyed SHA-256 chain. Keep external backup hashes; privileged whole-database replacement is outside this guarantee.</div><div id="server-audit-result" role="status"></div><div class="card card-body" id="server-audit-entries">Loading server events…</div>';
  api.audit().then(rows=>{const host=$('#server-audit-entries');if(!host)return;host.innerHTML=rows.map(r=>'<div class="timeline-entry"><strong>'+esc(r.event_type)+'</strong><p class="tiny">'+esc(r.actor)+' · '+when(r.created_at)+'</p><div class="hash">'+esc(r.event_hash)+'</div><span class="hash">Previous '+esc(r.previous_hash)+'</span></div>').join('');}).catch(e=>toast(e.message,true));return;
 }
 $('#page').innerHTML=heading('Evidence & audit','Read-only inspection evidence with immutable detector decisions.',button('Verify integrity','audit-verify','shield','','id="audit-verify"')+button('Export evidence manifest','audit-export','download'))+'<div class="notice '+(api.mode==='mock'?'':'warn')+' mb-16">'+icon('info')+'<span>'+(api.mode==='mock'?'DEMO · A browser-generated hash chain over simulated records. Verify recomputes every link.':'The backend does not expose its QA event chain or an integrity endpoint. This view creates a browser snapshot digest only; it cannot verify database history or prove tamper resistance.')+'</span></div><div id="audit-verification" role="status" class="mb-16"></div><div class="card"><div class="card-header"><h2>'+(api.mode==='mock'?'Demonstration evidence chain':'Inspection snapshot digests')+'</h2><span class="tiny">Read-only · no edit or delete actions</span></div><div class="card-body" id="audit-entries"><div class="skeleton"></div><div class="skeleton"></div></div></div>';
 if(!api.capabilities.auditChain){$('#audit-verify').disabled=true;$('#audit-verify').title='No server audit verification endpoint is available';}
 buildAudit().then(()=>{if(state.route!=='audit')return;$('#audit-entries').innerHTML=state.audit.length?'<div class="timeline">'+state.audit.slice(-100).reverse().map((a,i)=>'<div class="timeline-entry"><div class="between"><strong class="mono">'+esc(a.facts.inspection_id)+'</strong>'+badge(a.facts.decision)+'</div><p class="tiny">'+when(a.facts.created_at)+'</p><div class="hash">SHA-256 '+a.hash+'</div><button class="btn ghost small-btn" data-hash="'+a.previous+'" aria-label="Copy previous chain hash">'+icon('lock')+'Previous '+a.previous.slice(0,16)+'…</button></div>').join('')+'</div>':empty('No inspection evidence','Inspect a specimen to create an evidence record.','audit');});
}
function renderSettings(){
 $('#page').innerHTML=heading('Station settings','Designed for your station. Stored locally in this browser.')+'<div class="settings-layout"><div class="card"><div class="card-header"><h2>Interface & accessibility</h2>'+icon('settings')+'</div><div class="card-body"><div class="list-option"><div><strong>Appearance</strong><p>Dark control room, light high contrast, or system.</p></div><select id="setting-theme" aria-label="Theme">'+['dark','light','system'].map(v=>'<option '+(state.theme===v?'selected':'')+'>'+v+'</option>').join('')+'</select></div><div class="list-option"><div><strong>Glove-friendly controls</strong><p>Increase touch target height to 56 pixels.</p></div><label class="check-label"><input id="setting-glove" type="checkbox" '+(state.glove?'checked':'')+'><span class="sr-only">Glove spacing</span></label></div><div class="list-option"><div><strong>Soft HOLD notification</strong><p>A single quiet tone after operator-triggered inference.</p></div><label class="check-label"><input id="setting-sound" type="checkbox" '+(state.sound?'checked':'')+'><span class="sr-only">HOLD sound</span></label></div><div class="list-option"><div><strong>Reduced motion</strong><p>Follows the operating system preference automatically.</p></div><span class="badge">'+(matchMedia('(prefers-reduced-motion:reduce)').matches?'ON':'SYSTEM')+'</span></div><div class="list-option"><div><strong>Language</strong><p>English available. Translation dictionary: js/i18n.js.</p></div><select aria-label="Language"><option>English</option></select></div><div class="list-option"><div><strong>Kiosk / fullscreen</strong><p>Escape exits the browser fullscreen mode.</p></div>'+button('Fullscreen','fullscreen','fullscreen')+'</div></div></div><div class="stack"><div class="card"><div class="card-header"><h2>Capture & operator</h2>'+icon('camera')+'</div><div class="card-body"><div class="list-option"><div><strong>Preferred camera</strong><p>Manual selection; hardware discovery is not exposed.</p></div><select id="setting-camera" aria-label="Preferred camera">'+[['0','USB video0'],['1','USB video1'],['2','USB video2'],['picamera2','CSI Picamera2']].map(([v,label])=>'<option value="'+v+'" '+(saved('camera','0')===v?'selected':'')+'>'+label+'</option>').join('')+'</select></div><div class="list-option"><div><strong>Operator identity</strong><p>Local display identity · does not authenticate a QA reviewer.</p></div>'+button(esc(state.operator),'operator','lock')+'</div><div class="notice mt-16">'+icon('shield')+'<span>The touch PIN pad is a demo lock only. Real authentication requires a backend identity endpoint.</span></div></div></div><div class="card"><div class="card-header"><h2>Adapter & capabilities</h2><span class="badge '+(api.mode==='mock'?'demo':'accent')+'">'+api.mode.toUpperCase()+'</span></div><div class="card-body"><p class="tiny">The real adapter preserves all detector and advisory behavior. Demo mode simulates missing product capabilities explicitly.</p><div class="row mt-16"><a class="btn" href="?adapter=mock#inspect">Open Demo mode</a><a class="btn" href="?adapter=real#inspect">Use local backend</a></div><p class="tiny mt-16">UI '+version+' · Vanilla ES modules · no remote dependencies</p></div></div></div></div>';
 $('#setting-theme').onchange=e=>{state.theme=e.target.value;applyTheme();};$('#setting-glove').onchange=e=>{state.glove=e.target.checked;persist('glove',state.glove);applyTheme();};$('#setting-sound').onchange=e=>{state.sound=e.target.checked;persist('sound',state.sound);};$('#setting-camera').onchange=e=>persist('camera',e.target.value);
}
function renderHealth(){
 const cards=[['cpu','CPU load','health'],['ram','RAM used','chip'],['temp','SoC temperature','health'],['hailo','Hailo utilization','chip'],['queue','Llama queue depth','llama'],['db','Database size','database'],['latency','Last vision inference','bolt'],['llama','ExecuTorch advisor','llama'],['storage','Available storage','database']];
 $('#page').innerHTML=heading('System health','Live local measurements. Missing instrumentation is shown explicitly.',button('Download health snapshot','health-export','download'))+'<div class="health-grid">'+cards.map(([id,title,name])=>'<div class="card health-card"><div class="between"><div class="row">'+icon(name)+'<h2>'+title+'</h2></div><span class="badge" id="health-state-'+id+'">WAIT</span></div><div class="health-value mono" id="health-value-'+id+'">—</div><p class="tiny" id="health-note-'+id+'">Waiting for station telemetry</p></div>').join('')+'</div><div class="notice mt-16">'+icon('info')+'<span>Metrics are sampled every 2 seconds while visible. Vision and advisory run in separate pipelines. Utilization and performance do not establish model accuracy.</span></div>';
 updateHealth();
}
function updateHealth(){
 const s=state.status||{},cam=s.camera||{};
 const values={cpu:[s.cpu_percent,'%','System CPU · all cores',s.cpu_percent>85?'REVIEW':'OK'],ram:[s.ram_percent,'%','Physical memory used',s.ram_percent>85?'REVIEW':'OK'],temp:[s.temperature_c,' °C','SoC sensor · not ambient temperature',s.temperature_c>=75?'REVIEW':'OK'],hailo:[s.hailo_utilization,'%','No utilization endpoint in live API','OK'],queue:[s.llama_queue_depth,'','Queue depth not exposed in live API','OK'],db:[s.db_size_mb,' MB','Database byte size not exposed in live API','OK'],latency:[cam.vision_ms,' ms','Camera vision stage · not full Llama latency','OK'],llama:[s.llama_state||null,'',s.llama_platform||'Separate Arm CPU pipeline',s.llama_state==='fallback'||s.llama_state==='unavailable'?'REVIEW':'OK'],storage:[s.free_storage_gb,' GB','Available local data volume','OK']};
 for(const [id,[value,suffix,note,status]] of Object.entries(values)){const el=$('#health-value-'+id);if(!el)continue;el.textContent=value==null?'—':typeof value==='number'?num(value)+suffix:human(value);$('#health-state-'+id).outerHTML='<span id="health-state-'+id+'" class="badge '+(value==null?'':status==='OK'?'PASS':'REVIEW')+'">'+(value==null?'NOT EXPOSED':!state.connected?'STALE':status)+'</span>';$('#health-note-'+id).textContent=api.mode==='mock'?'DEMO · simulated measurement':note;}
}
async function openCitation(id){
 const c=state.sop?.clauses.find(v=>v.id===id);if(!c)return toast('The cited clause is not in the local SOP index.',true);
 $('#drawer-title').textContent=state.sop.document_id+' / '+c.id;
 $('#drawer-body').innerHTML='<div class="tag-list mb-16">'+badge('REV '+state.sop.revision)+badge('LOCAL SOP','accent')+'</div><h2 class="mb-16">Referenced operator procedure</h2><div class="clause"><mark style="background:transparent;color:var(--text)">'+esc(c.text)+'</mark></div><div class="tag-list mt-16">'+c.tags.map(v=>badge(human(v))).join('')+'</div><p class="tiny mt-16">'+esc(state.sop.status)+'</p><div class="notice mt-16">'+icon('shield')+'<span>This citation supports operator handling. It cannot change the detector decision.</span></div>';
 openDialog($('#detail-drawer'));
}
async function openDetail(id){
 $('#drawer-title').textContent='Inspection details';$('#drawer-body').innerHTML='<div class="skeleton"></div><div class="skeleton"></div>';openDialog($('#detail-drawer'));
 try{const r=await api.get(id);const a=r.advice?.advisory;$('#drawer-title').textContent=r.inspection_id;$('#drawer-body').innerHTML='<div class="between mb-16">'+badge(r.decision)+'<span class="tiny">'+when(r.created_at)+'</span></div><img class="drawer-image" src="'+esc(r.image_url||r.original_url)+'" alt="Recorded inspection image"><p class="mt-16">'+esc(r.decision_reason||'Recorded detector result')+'</p><dl class="detail-grid"><div><dt>Vision runtime</dt><dd>'+esc(r.backend)+' · '+num(r.vision_ms,2)+' ms</dd></div><div><dt>Source</dt><dd>'+esc(r.source)+'</dd></div><div><dt>Defect regions</dt><dd>'+r.detections.length+'</dd></div><div><dt>Severity</dt><dd>'+esc(r.severity)+'</dd></div></dl><div class="hash">Model SHA-256 · '+esc(r.model_sha256||'not exposed')+'</div><div class="divider"></div><h2>SOP-grounded advisory</h2><p class="advice-copy mt-16">'+esc(a?.operator_message||'Advisor pending')+'</p>'+(a?'<button class="btn mt-16" data-citation="'+esc(a.clause_id)+'">'+icon('sop')+esc(a.clause_id)+'</button>':'')+'<div class="divider"></div><h2>Recorded QA review</h2><div class="timeline mt-16">'+(r.qa_review?reviewEntry(r.qa_review):'<p class="tiny">No review in this record snapshot.</p>')+'</div><p class="tiny mt-16">Backend returns the latest QA review. Review events remain append-only in storage.</p><div class="row mt-16">'+button('Open in Inspect','open-inspect:'+id,'inspect')+button('Download JSON','detail-json:'+id,'download')+'</div><div class="notice mt-16">'+icon('shield')+'<span>AI advice is informational. Final disposition rests with QA personnel.</span></div>';}catch(e){$('#drawer-body').innerHTML=empty('Inspection unavailable',e.message,'REVIEW');}
}
function renderRoute(){
 state.viewer?.destroy();state.viewer=null;state.virtual?.destroy();state.virtual=null;adviceToken++;
 const hash=location.hash.slice(1)||'inspect',route=hash.split('?')[0];state.route=routes.some(r=>r[0]===route)?route:'inspect';
 document.body.classList.toggle('console-inspect',state.route==='inspect');
 $$('[data-route]').forEach(a=>{const active=a.dataset.route===state.route;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 document.title=t(state.route)+' · Medge Vision';
 if(state.route==='history'&&hash.includes('?')){const p=new URLSearchParams(hash.split('?')[1]);state.filters=Object.fromEntries(p);persist('filters',state.filters);}
 ({inspect:renderInspect,history:renderHistory,dashboard:renderDashboard,sop:renderSop,audit:renderAudit,settings:renderSettings,health:renderHealth}[state.route])();enhance(state,{openDetail});updateOptical(state.selected,state.status);
}
function csvExport(){
 const rows=filteredRecords(),keys=['inspection_id','created_at','source','batch_id','decision','severity','vision_ms'];
 const cell=value=>{let text=String(value??'');if(/^[=+\-@\t\r]/.test(text))text="'"+text;return '"'+text.replaceAll('"','""')+'"';};
 download('blistertrace_filtered.csv',[keys.join(','),...rows.map(r=>keys.map(k=>cell(r[k])).join(','))].join('\r\n'),'text/csv');
}
function commandPalette(){
 $('#command-input').value='';renderCommands('');openDialog($('#command-dialog'));
}
function renderCommands(query){
 const actions=[...routes.map(([id,label,name])=>({label:'Go to '+label,action:'navigate:'+id,name})),{label:'Run inspection / snapshot',action:'run',name:'play'},{label:'Toggle theme',action:'theme',name:'sun'},{label:'Fit image',action:'fit',name:'fit'},{label:'Download selected inspection',action:'export-selected',name:'download'},{label:'Fullscreen',action:'fullscreen',name:'fullscreen'}].filter(v=>v.label.toLowerCase().includes(query.toLowerCase()));
 $('#command-list').innerHTML=actions.map(v=>'<button class="btn" data-command="'+v.action+'">'+icon(v.name)+esc(v.label)+'</button>').join('')||'<div class="empty">No matching command.</div>';
}
function operatorDialog(){
 $('#operator-name').value=state.operator;$('#operator-pin').value='';$('#pin-note').textContent='Local display identity only. Demo PIN: 1234. This does not authorize QA sign-off.';openDialog($('#operator-dialog'));
}
async function action(name){
 if(name==='cancel-advice'){if(state.selected)await api.cancelAdvice(state.selected.inspection_id);return;}
 if(name==='server-audit-verify'){const r=await api.verifyAudit();$('#server-audit-result').textContent=(r.valid?'Verified':'Integrity failure')+' · '+r.checked_events+' events · '+r.images_checked+' images · head '+r.head_sha256;return;}
 if(name.startsWith('navigate:')){location.hash=name.split(':')[1];return;}
 if(name.startsWith('citation:'))return openCitation(name.split(':')[1]);
 if(name.startsWith('open-inspect:')){closeDialog($('#detail-drawer'));await selectRecord(name.slice(13),true);return;}
 if(name.startsWith('detail-json:'))return download(name.slice(12)+'.json',await api.get(name.slice(12)));
 const r=state.selected;
 switch(name){
  case 'command':commandPalette();break;
  case 'shortcuts':openDialog($('#shortcuts-dialog'));break;
  case 'theme':themeReveal(()=>{state.theme=document.documentElement.dataset.theme==='dark'?'light':'dark';applyTheme();});break;
  case 'operator':operatorDialog();break;
  case 'fullscreen':if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();break;
  case 'run':await runInspection();break;
  case 'zoom-in':state.viewer?.zoom(1.25);break;case 'zoom-out':state.viewer?.zoom(.8);break;
  case 'fit':state.viewer?.fit();break;case 'fill':state.viewer?.fit(true);break;case 'one':state.viewer?.oneToOne();break;
  case 'export-selected':if(!r)return toast('Select an inspection first.',true);download(r.inspection_id+'.json',await api.get(r.inspection_id));break;
  case 'camera-start':{const source=$('#camera-device').value;persist('camera',source);await api.cameraStart(source);toast('Camera starting. Waiting for a fresh frame.');setTimeout(async()=>{state.status=await api.status();updateCameraHint();state.viewer?.setLive(api.cameraURL());},700);break;}
  case 'camera-stop':await api.cameraStop();state.status=await api.status();updateCameraHint();if(r)state.viewer?.setRecord(r);toast('Camera stopped. Recorded snapshot is retained.');break;
  case 'camera-live':if(!state.status?.camera?.frame_ready)return toast('Connect the camera and wait for a fresh frame.',true);await api.displayLive();state.viewer?.setLive(api.cameraURL());$('#viewer-pin').innerHTML=icon('eye')+'LIVE · ADVICE STAYS PINNED';break;
  case 'retry':if(!r)return;{const response=await api.retry(r.inspection_id);if(response.queued){state.selected.advice=null;renderAdvice();toast('Advisor queued. Detector result unchanged.');}else toast('Advisor is already queued or unavailable.');}break;
  case 'draft':if(!r)return toast('Select an inspection first.',true);{const answer=await api.ask(r.inspection_id,'','qa_note');state.drafts.set(r.inspection_id,answer.reply);restoreDraft();}break;
  case 'copy-draft':await copy($('#qa-draft').value);break;
  case 'export-draft':download('DRAFT_'+r.inspection_id+'.txt',$('#qa-draft').value,'text/plain');break;
  case 'question-explain':await askQuestion('Why was this flagged?','explain');break;
  case 'question-next':await askQuestion('Suggest detailed next steps for this inspection','next_action');break;
  case 'question-evidence':await askQuestion('What evidence should I record?','evidence');break;
  case 'question-rectify':await askQuestion('What SOP applies?','rectify');break;
  case 'question-similar':await askQuestion('Similar past rejects?','similar');break;
  case 'history-csv':csvExport();break;
  case 'history-json':{const rows=filteredRecords().filter(v=>state.selectedRows.has(v.inspection_id));if(!rows.length)return toast('Select at least one filtered record.',true);download('blistertrace_selected.json',rows);}break;
  case 'clear-filters':state.filters={};persist('filters',{});saveFilterHash();renderHistory();break;
  case 'batch-summary':{const el=$('#batch-summary-output');if(!api.capabilities.batchSummary){el.innerHTML='<div class="notice warn">'+icon('info')+'Batch Llama summarization is not exposed by the current API. Individual inspection advice remains available. A demo is available in Demo mode.</div>';break;}el.innerHTML='<div class="card card-body pending-shimmer"><span class="spinner"></span> Generating simulated batch draft…</div>';const text=await api.summarize(batchRecords());if(el.isConnected)el.innerHTML='<div class="card card-body"><span class="badge REVIEW mb-16">DRAFT · DEMO</span><p>'+esc(text)+'</p></div>';break;}
  case 'audit-export':download('blistertrace_browser_snapshot.json',{scope:'Browser-generated snapshot, not server audit-chain proof',adapter:api.mode,created_at:new Date().toISOString(),entries:state.audit});break;
  case 'audit-verify':{if(!api.capabilities.auditChain)return;let previous='0'.repeat(64),ok=true;for(const a of state.audit){if(a.previous!==previous||await digest({previous:a.previous,facts:a.facts})!==a.hash){ok=false;break;}previous=a.hash;}$('#audit-verification').innerHTML='<div class="notice">'+icon(ok?'check':'REVIEW')+(ok?'Demo snapshot hash links verified. This does not verify a production database.':'Snapshot chain verification failed.')+'</div>';break;}
  case 'health-export':download('blistertrace_health.json',{adapter:api.mode,at:new Date().toISOString(),health:state.health,status:state.status});break;
 }
}
document.addEventListener('click',async e=>{
 const close=e.target.closest('[data-close]');if(close)return;
 const citation=e.target.closest('[data-citation]');if(citation)return openCitation(citation.dataset.citation);
 const coord=e.target.closest('[data-coords]');if(coord)return copy(coord.dataset.coords);
 const hash=e.target.closest('[data-hash]');if(hash)return copy(hash.dataset.hash);
 const scroll=e.target.closest('[data-scroll-clause]');if(scroll){e.preventDefault();$('#clause-'+scroll.dataset.scrollClause)?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth'});return;}
 const library=e.target.closest('[data-library]');if(library)return previewLocal(library.dataset.library);
 const source=e.target.closest('[data-source]');if(source){state.source=source.dataset.source;$$('[data-source]').forEach(b=>b.classList.toggle('active',b===source));sourceOptions();if(state.source==='local'&&state.sourceName)previewLocal(state.sourceName);return;}
 const view=e.target.closest('[data-view]');if(view){$$('[data-view]').forEach(b=>b.classList.toggle('active',b===view));state.viewer?.setMode(view.dataset.view);return;}
 const sort=e.target.closest('[data-sort]');if(sort){state.descending=state.sort===sort.dataset.sort?!state.descending:true;state.sort=sort.dataset.sort;renderDetections();return;}
 const filter=e.target.closest('[data-clear-filter]');if(filter){delete state.filters[filter.dataset.clearFilter];persist('filters',state.filters);saveFilterHash();renderHistory();return;}
 const command=e.target.closest('[data-command]');const target=e.target.closest('[data-action]');
 if(command){closeDialog($('#command-dialog'));try{await action(command.dataset.command);}catch(error){toast(error.message,true);}return;}
 if(target){e.preventDefault();try{await action(target.dataset.action);}catch(error){toast(error.message,true);}}
});
document.addEventListener('keydown',e=>{
 if(e.target.closest('dialog[open]')?.getAttribute('aria-label')==='Local station sign-in')return;
 if(!$('#splash').hidden){if(e.key==='Enter'){e.preventDefault();hideBoot();}else if(e.key==='Tab'){e.preventDefault();$('#skip-boot').focus();}return;}
 const editing=e.target.matches('input,textarea,select,[contenteditable]'),inDialog=!!e.target.closest('dialog[open]');
 if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();commandPalette();return;}
 if(inDialog||editing)return;
 if(e.key==='?'){e.preventDefault();openDialog($('#shortcuts-dialog'));}
 if(e.key==='+'||e.key==='='){e.preventDefault();state.viewer?.zoom(1.25);}
 if(e.key==='-'){e.preventDefault();state.viewer?.zoom(.8);}
 if(e.key.toLowerCase()==='f'){e.preventDefault();state.viewer?.fit();}
 if(e.key==='1')state.viewer?.oneToOne();
 if(e.key.toLowerCase()==='i'){location.hash='inspect';}
 if(e.key.toLowerCase()==='h'){location.hash='history';}
 // Inference is deliberately triggered only by Ctrl/Cmd+Enter.
 if((e.ctrlKey||e.metaKey)&&e.key==='Enter'&&state.route==='inspect'){e.preventDefault();runInspection();}
});
async function init(){
 shell();boot();renderRoute();idle(state);
 $('#command-input').oninput=e=>renderCommands(e.target.value);
 $('#command-input').onkeydown=e=>{if(e.key==='ArrowDown'){e.preventDefault();$('#command-list button')?.focus();}if(e.key==='Enter'){e.preventDefault();$('#command-list button')?.click();}};
 $('#command-list').onkeydown=e=>{if(!['ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();const buttons=$$('button',$('#command-list')),i=buttons.indexOf(document.activeElement),next=i+(e.key==='ArrowDown'?1:-1);if(next<0)$('#command-input').focus();else buttons[Math.min(next,buttons.length-1)]?.focus();};
 $('#pin-grid').innerHTML=['1','2','3','4','5','6','7','8','9','Clear','0','⌫'].map(v=>'<button type="button" class="btn" data-pin="'+v+'">'+v+'</button>').join('');
 $('#pin-grid').onclick=e=>{const v=e.target.closest('[data-pin]')?.dataset.pin;if(!v)return;const input=$('#operator-pin');input.value=v==='Clear'?'':v==='⌫'?input.value.slice(0,-1):(input.value+v).slice(0,8);};
 $('#operator-form').onsubmit=e=>{e.preventDefault();if($('#operator-pin').value!=='1234'){$('#pin-note').textContent='Demo PIN not accepted. Use 1234. This PIN changes display identity only; account permissions are enforced by the server.';return;}state.operator=$('#operator-name').value.trim().slice(0,80)||'OP-01';persist('operator',state.operator);$('#operator-badge').textContent=state.operator.slice(0,2);if($('#reviewer'))$('#reviewer').value=state.operator;closeDialog($('#operator-dialog'));toast('Local display identity updated. This is not QA authentication.');};
 state.unsub=subscribe(onStatus);
 getSop().then(sop=>{state.sop=sop;bootItem('sop','ready','revision '+sop.revision);if(state.route==='sop')renderSop();}).catch(e=>toast('Local SOP could not be loaded: '+e.message,true));
 async function loadInitial(){
  if(!state.health?.ready){setTimeout(loadInitial,800);return;}
  try{
   if(api.mode==='real'){
    state.batches=await api.batches();const selector=$('#batch-select');selector.innerHTML='<option value="all">All recent inspections</option>'+state.batches.map(b=>'<option value="'+esc(b.batch_id)+'">'+esc(b.batch_id+' · '+b.sku+' · '+b.status)+'</option>').join('');if(!state.batches.some(b=>b.batch_id===state.batch))state.batch='all';selector.value=state.batch;
   }
   state.library=await api.library();
   const firstDemo=state.library.find(r=>r.group==='demo_safe');
   if(firstDemo)state.libraryGroup='demo_safe';
   state.sourceName=firstDemo?.name||state.library[0]?.name||null;
   if(state.previewing||state.busy){state.initialLoaded=true;return;}
   const id=saved('selected',null);try{if(id)state.selected=await api.get(id);}catch{}
   if(!state.selected){const recent=await api.history();if(recent.length)state.selected=await api.get(recent[0].inspection_id);}
   if(state.selected)state.workspaceMode=state.selected.anomaly?'anomaly':'detection';
   state.initialLoaded=true;renderRoute();
  }catch(e){toast('Could not load station data: '+e.message,true);setTimeout(loadInitial,5000);}
 }
 loadInitial();
 setInterval(async()=>{
  const id=state.selected?.inspection_id;if(!id||state.selected.advice||!state.health?.ready||document.hidden)return;
  try{const record=await api.get(id);if(state.selected?.inspection_id!==id)return;state.selected=record;if(record.advice&&state.route==='inspect'){renderAdvice();restoreDraft();}}catch{}
 },2000);
 window.addEventListener('hashchange',()=>{if(location.hash==='#shortcuts'){openDialog($('#shortcuts-dialog'));history.replaceState(null,'','#'+state.route);}else transition(renderRoute);});
 window.addEventListener('pagehide',()=>{state.unsub?.();state.viewer?.destroy();if(state.previewURL)URL.revokeObjectURL(state.previewURL);});
 // Test instrumentation reports frontend rendering only, never target inference speed.
 window.BlisterTraceUI={version,adapter:api.mode,getSelected:()=>structuredClone(state.selected),getViewer:()=>state.viewer,getState:()=>({route:state.route,recordCount:state.records.length,connected:state.connected,initialLoaded:state.initialLoaded}),async benchmarkFrames(count=120){const v=state.viewer;if(!v?.loaded)throw Error('Load an inspection image first');const times=[];let last=performance.now();await new Promise(resolve=>{let i=0;function frame(now){if(i)times.push(now-last);last=now;v.x+=i%2?1:-1;v.schedule();if(++i<count)requestAnimationFrame(frame);else resolve();}requestAnimationFrame(frame);});times.sort((a,b)=>a-b);v.fit();return {scope:'This browser rendering only; not a Pi hardware guarantee',frames:times.length,median_ms:times[Math.floor(times.length*.5)],p95_ms:times[Math.floor(times.length*.95)],over_33_ms:times.filter(v=>v>33).length};}};
}
init().catch(e=>{console.error(e);$('#app').innerHTML='<main class="card card-body" style="margin:40px"><h1>Workspace could not start</h1><p class="mt-16">'+esc(e.message)+'</p><p>Serve the folder over HTTP so the browser can load ES modules. See README_UI.md.</p></main>';$('#splash').hidden=true;});
