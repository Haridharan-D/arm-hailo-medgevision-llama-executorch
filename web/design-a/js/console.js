import {api} from './api.js';
import {escape as esc,icon} from './icons.js';
const $=s=>document.querySelector(s);
function tabs(host,entries,name,onChange=()=>{}){
 const nav=document.createElement('div');nav.className='console-tabs';nav.setAttribute('role','tablist');nav.setAttribute('aria-label',name);
 const select=id=>{for(const [key,label,pane] of entries){const active=key===id;pane.hidden=!active;pane.classList.add('console-tab-pane');const b=nav.querySelector('[data-tab="'+key+'"]');b.setAttribute('aria-selected',String(active));b.tabIndex=active?0:-1;}onChange(id);};
 for(const [id,label,pane] of entries){const b=document.createElement('button');b.className='btn';b.textContent=label;b.dataset.tab=id;b.setAttribute('role','tab');b.onclick=()=>select(id);b.onkeydown=e=>{if(!['ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();const list=[...nav.children],index=list.indexOf(b),next=list[(index+(e.key==='ArrowRight'?1:list.length-1))%list.length];next.click();next.focus();};nav.append(b);pane.setAttribute('role','tabpanel');}
 host.prepend(nav);select(entries[0][0]);return select;
}
export function mountConsole(state,hooks){
 state.anomalyProfile=state.selected?.anomaly?.profile||state.anomalyProfile||'mvtec_pill';
 state.modeRecords=state.modeRecords||{};
 if(state.selected)state.modeRecords[state.selected.anomaly?'anomaly':'detection']=state.selected;
 state.workspaceMode=state.workspaceMode||(state.selected?.anomaly?'anomaly':'detection');
 const vision=$('.vision-column'),aside=$('.advice-column'),viewer=$('.viewer-card');if(!vision||!aside)return;
 const top=$('.topbar');if(!top.querySelector('.fullscreen-launch')){const full=document.createElement('button');full.className='btn fullscreen-launch';full.dataset.action='fullscreen';full.innerHTML=icon('fit')+'<span>Fullscreen</span>';full.title='Fullscreen / Esc to exit (or press F11)';top.insertBefore(full,$('#operator-badge'));}
 const header=viewer.querySelector('.card-header');header.classList.add('instrument-header');header.innerHTML='<div class="instrument-modes" role="tablist" aria-label="Inspection method"><button class="btn" role="tab" data-mode="detection">'+icon('inspect')+'Defect detection</button><button class="btn" role="tab" data-mode="anomaly">'+icon('eye')+'Anomaly heatmap</button></div><button class="btn icon-only ghost" data-action="export-selected" aria-label="Download inspection evidence">'+icon('download')+'</button>';
 const pin=document.createElement('span');pin.id='viewer-pin';pin.className='sr-only';header.append(pin);
 const change=document.createElement('button');change.id='change-image';change.className='btn change-image';change.innerHTML=icon('folder')+'<span>Change image</span>';header.insertBefore(change,header.querySelector('[data-action]'));
 const collapse=value=>{document.body.classList.toggle('acquisition-collapsed',value);change.setAttribute('aria-expanded',String(!value));};
 change.onclick=()=>collapse(!document.body.classList.contains('acquisition-collapsed'));
 state.consoleCompleted=()=>collapse(true);
 const acquire=document.createElement('div');acquire.className='acquisition-panel';viewer.querySelector('.viewer-toolbar').before(acquire);
 const sources=viewer.querySelector('.source-controls');acquire.append(sources);
 const pane=document.createElement('section');pane.className='anomaly-panel';pane.innerHTML='<div class="anomaly-source-tabs segmented" aria-label="Anomaly image source"><button class="btn active" data-anomaly-source="dataset">Stored test folder</button><button class="btn" data-anomaly-source="upload">Upload image</button><button class="btn" data-anomaly-source="pinned">Selected inspection</button></div><div class="anomaly-controls"><label>Model profile<select id="anomaly-profile" aria-label="Anomaly model profile"><option>Loading…</option></select></label><label id="sample-field">Dataset test image<select id="anomaly-sample" aria-label="Anomaly dataset test sample"></select></label><label id="anomaly-upload-field" hidden>Image file<input type="file" id="anomaly-file" accept="image/*"></label><div id="anomaly-pinned-field" class="tiny" hidden>Uses the last recorded inspection, not an uninspected preview.</div><button class="btn primary" id="run-anomaly-sample">'+icon('play')+'Run anomaly</button></div><p class="anomaly-warning" id="anomaly-warning">Loading category models…</p>';
 const sourceSelect=document.createElement('label');sourceSelect.className='anomaly-source-select';sourceSelect.innerHTML='Image source<select id="anomaly-source-select" aria-label="Anomaly image source"><option value="dataset">Stored test folder</option><option value="upload">Upload image</option><option value="pinned">Selected inspection</option></select>';
 pane.querySelector('.anomaly-controls').prepend(sourceSelect);pane.querySelector('.anomaly-source-tabs').hidden=true;acquire.append(pane);
 const strip=document.createElement('div');strip.className='image-context';strip.id='image-context';viewer.querySelector('.viewer-toolbar').after(strip);
 const detectionCard=$('#detections-body').closest('.card');detectionCard.classList.add('detection-drawer');
 const drawerButton=document.createElement('button');drawerButton.className='btn measurement-toggle';drawerButton.setAttribute('aria-expanded','false');drawerButton.innerHTML=icon('inspect')+'<span id="measurement-label">Detection measurements</span><span>View details</span>';
 vision.append(drawerButton);drawerButton.onclick=()=>{const open=document.body.classList.toggle('measurements-open');drawerButton.setAttribute('aria-expanded',String(open));};
 const reading=document.createElement('div');reading.id='anomaly-result';reading.className='anomaly-reading';$('#result-panel').after(reading);
 const cards=[...aside.children];const work=document.createElement('section');work.className='card assistant-workbench';aside.append(work);
 const notice=cards[cards.length-1];notice.classList.add('advisory-notice');
 for(const card of cards.slice(0,-1))work.append(card);
 cards[0].classList.add('automatic-advice');
 state.consoleAssistantTab=tabs(work,[['advice','Auto advice',cards[0]],['ask','Ask / steps',cards[2]],['draft','QA draft',cards[1]],['review','QA review',cards[3]]],'Assistant workspace');
 work.append(notice);
 const chips=$('.question-chips');chips.innerHTML='<button class="btn" data-action="question-next">Suggested next steps</button><button class="btn" data-action="question-explain">Explain the evidence</button><button class="btn" data-action="question-rectify">SOP / reinspection</button><button class="btn" data-action="question-evidence">Evidence to record</button>';
 const handoff=document.createElement('div');handoff.className='advice-quick-actions';handoff.innerHTML='<button class="btn primary" id="open-suggestions">Ask / suggested next steps</button><span class="tiny">Advice is generated automatically after either inspection mode.</span>';cards[0].append(handoff);
 $('#open-suggestions').onclick=()=>{state.consoleAssistantTab('ask');document.querySelector('[data-action="question-next"]').click();};
 state.anomalySource=state.anomalySource||'dataset';
 const previewSample=()=>{if(state.workspaceMode!=='anomaly'||state.anomalySource!=='dataset')return;const row=state.anomalySamples?.find(r=>r.file===$('#anomaly-sample').value);if(row)hooks.preview(row.url,'DATASET PREVIEW · '+row.source_path+' · NOT YET INSPECTED');};
 let sampleRequest=0;
 const loadSamples=async(preview=true)=>{
  const request=++sampleRequest,profile=$('#anomaly-profile').value;state.anomalyProfile=profile;state.samplesLoading=true;state.anomalySamples=[];$('#anomaly-sample').innerHTML='<option value="">Loading test folder…</option>';updateConsole(state);
  const samples=await api.anomalySamples(profile);if(!pane.isConnected||profile!==$('#anomaly-profile').value||request!==sampleRequest)return;
  state.samplesLoading=false;
  state.anomalySamples=samples;$('#anomaly-sample').innerHTML=samples.map((row,i)=>'<option value="'+esc(row.file)+'">'+String(i+1).padStart(2,'0')+' / '+samples.length+' · '+esc(row.label_name.toUpperCase()+' · '+row.source_path.split('/').slice(-2).join('/'))+'</option>').join('');
  const selected=samples.find(row=>row.source_path===state.selected?.sample_ground_truth?.source_path);if(selected)$('#anomaly-sample').value=selected.file;
  $('#anomaly-warning').textContent=profile==='visa_capsules'?'VisA: low defect recall at saved threshold · research profile.':samples.length+' stored held-out examples · category profile; blister-camera acceptance unvalidated.';
  if(preview)previewSample();updateConsole(state);
 };
 const anomalySource=id=>{state.anomalySource=id;pane.querySelectorAll('[data-anomaly-source]').forEach(b=>b.classList.toggle('active',b.dataset.anomalySource===id));$('#sample-field').hidden=id!=='dataset';$('#anomaly-upload-field').hidden=id!=='upload';$('#anomaly-pinned-field').hidden=id!=='pinned';$('#run-anomaly-sample').textContent=id==='pinned'?'Analyze inspection':'Run anomaly';if(id==='dataset')previewSample();updateConsole(state);};
 $('#anomaly-source-select').onchange=e=>anomalySource(e.target.value);
 pane.querySelectorAll('[data-anomaly-source]').forEach(b=>b.onclick=()=>anomalySource(b.dataset.anomalySource));
 $('#anomaly-file').onchange=e=>{const file=e.target.files[0];if(!file)return;if(file.size>20*1024*1024)return hooks.error('Choose an image under 20 MB');state.anomalyFile=file;if(state.anomalyPreviewURL)URL.revokeObjectURL(state.anomalyPreviewURL);state.anomalyPreviewURL=URL.createObjectURL(file);hooks.preview(state.anomalyPreviewURL,'UPLOAD PREVIEW · '+file.name+' · NOT YET INSPECTED');updateConsole(state);};
 $('#anomaly-profile').onchange=()=>loadSamples().catch(e=>hooks.error(e.message));$('#anomaly-sample').onchange=previewSample;
 state.runAnomalyAction=()=>hooks.runAnomaly($('#anomaly-profile').value,state.anomalySource==='dataset'?$('#anomaly-sample').value:null,state.anomalySource==='upload'?state.anomalyFile:null);
 $('#run-anomaly-sample').onclick=()=>state.runAnomalyAction();
 const selectMode=(mode,restore=true)=>{if(state.busy)return;state.workspaceMode=mode;document.body.dataset.inspectionMode=mode;document.body.classList.remove('measurements-open');drawerButton.setAttribute('aria-expanded','false');header.querySelectorAll('[data-mode]').forEach(b=>{b.setAttribute('aria-selected',String(b.dataset.mode===mode));b.classList.toggle('active',b.dataset.mode===mode);});sources.hidden=mode!=='detection';pane.hidden=mode!=='anomaly';state.viewer.setMode(mode==='anomaly'&&state.selected?.anomaly?'heatmap':'annotated');
   if(restore){hooks.showRecord(state.modeRecords[mode]||null);if(mode==='anomaly'&&!state.modeRecords[mode])previewSample();collapse(Boolean(state.modeRecords[mode]));}updateConsole(state);};
 header.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>selectMode(b.dataset.mode));
 state.consoleMeasurementTab=id=>selectMode(id==='anomaly'?'anomaly':'detection',false);
 selectMode(state.workspaceMode,false);anomalySource(state.anomalySource);collapse(Boolean(state.selected)&&!state.previewing);
 if(api.mode==='real')api.anomalyProfiles().then(async profiles=>{if(!pane.isConnected)return;state.anomalyProfiles=profiles;$('#anomaly-profile').innerHTML=profiles.map(p=>'<option value="'+esc(p.id)+'">'+esc(p.name)+'</option>').join('');if(profiles.some(p=>p.id===state.anomalyProfile))$('#anomaly-profile').value=state.anomalyProfile;if(profiles.length)await loadSamples(!state.selected?.anomaly);else $('#anomaly-warning').textContent='No anomaly models installed.';}).catch(e=>{if(pane.isConnected)$('#anomaly-warning').textContent=e.message;});
 else $('#anomaly-warning').textContent='Dataset heatmaps require the real local model backend.';
 updateConsole(state);
}
export function updateConsole(state){
 const a=state.selected?.anomaly,el=$('#anomaly-result');
 if(el){el.hidden=state.workspaceMode!=='anomaly';el.innerHTML=a&&!state.previewing?'<span class="badge '+(a.flagged?'REVIEW':'accent')+'">'+esc(a.classification)+'</span><span class="mono">Score <b>'+a.score.toFixed(4)+'</b> / '+a.threshold.toFixed(4)+'</span><span>'+a.elapsed_ms.toFixed(0)+' ms · CPU</span>'+(state.selected.sample_ground_truth?'<span>Dataset: '+esc(state.selected.sample_ground_truth.label_name)+'</span>':''):'Preview only · click Run anomaly to compute the score and heatmap.';}
 const context=$('#image-context');if(context){context.innerHTML=state.previewing?icon('eye')+'<strong>PREVIEW — NOT INSPECTED</strong><span>Llama stays pinned to '+esc(state.selected?.inspection_id.slice(0,10)||'no inspection')+'</span>':icon('lock')+'<strong>'+(state.selected?'INSPECTED · '+state.selected.inspection_id.slice(0,12):'READY FOR ACQUISITION')+'</strong><span>'+esc(state.selected?.anomaly?'EfficientAD score + real heatmap':state.selected?'YOLO regions + deterministic rules':'Choose a test image or camera')+'</span>';}
 const button=$('[data-view="heatmap"]');if(button){button.disabled=!a||state.previewing;button.title=a?'Actual EfficientAD output':'Run anomaly inference first';}
 const sample=$('#run-anomaly-sample');if(sample)sample.disabled=state.busy||state.samplesLoading||!state.health?.ready||(state.anomalySource==='upload'&&!state.anomalyFile)||(state.anomalySource==='pinned'&&!state.selected)||!state.anomalyProfiles?.length;
 document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===state.viewer?.mode));
 const label=$('#measurement-label');if(label)label.textContent=state.workspaceMode==='anomaly'?'Assessment details':(state.selected?.detections?.length||0)+' detection regions';
 document.querySelectorAll('[data-mode],[data-anomaly-source]').forEach(b=>b.disabled=state.busy);
}
