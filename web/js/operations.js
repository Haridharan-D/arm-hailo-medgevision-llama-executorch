import {api} from './api.js';
const $=s=>document.querySelector(s),esc=s=>String(s??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let batches=[],selected='LEGACY',records=[];
const showError=e=>{$('#error').hidden=false;$('#error').textContent=e.message||String(e);};
async function guarded(task){try{$('#error').hidden=true;await task();}catch(e){showError(e);}}
function renderBatch(){
 const b=batches.find(b=>b.batch_id===selected);if(!b)return;
 $('#batch-detail').innerHTML='<dl>'+[['SKU',b.sku],['Category',b.category],['Operator',b.operator],['Status',b.status],['Started',b.started_at],['Detector mean',b.mean_detector_ms==null?'Unavailable':b.mean_detector_ms.toFixed(2)+' ms']].map(([k,v])=>'<dt>'+esc(k)+'</dt><dd>'+esc(v)+'</dd>').join('')+'</dl>';
 const distribution=Object.entries(b.defect_distribution),maximum=Math.max(1,...distribution.map(([,v])=>v));
 $('#batch-detail').insertAdjacentHTML('beforeend','<h3>Observed defect distribution</h3><div role="img" aria-label="Observed defect counts">'+(distribution.map(([k,v])=>'<div style="margin:10px 0"><div style="display:flex;justify-content:space-between;font-size:12px"><span>'+esc(k)+'</span><strong>'+v+'</strong></div><div style="height:8px;background:#e5ecf2;border-radius:8px;margin-top:5px"><div style="height:100%;width:'+100*v/maximum+'%;background:#178b96;border-radius:8px"></div></div></div>').join('')||'<p class="hint">No defect observations recorded in this batch.</p>')+'</div>');
 $('#kpis').innerHTML=[['INSPECTED',b.counts.total],['HOLD · DEFECTIVE',b.counts.HOLD],['REVIEW · UNRESOLVED',b.counts.REVIEW],['RECORDED PASS',b.counts.PASS]].map(([k,v])=>'<div class="kpi"><small>'+esc(k)+'</small><strong>'+v+'</strong></div>').join('');
 $('#exports').innerHTML=['pdf','csv','json'].map(f=>'<a href="/api/batches/'+encodeURIComponent(selected)+'/report?format='+f+'" target="_blank" rel="noopener">'+f.toUpperCase()+' report</a>').join('');$('#select').disabled=b.status!=='OPEN';$('#close').disabled=b.status!=='OPEN';
 guarded(async()=>{records=await api.operationsHistory(selected);renderRecords();});
}
function renderRecords(){const q=$('#search').value.toLowerCase();$('#records').innerHTML=records.filter(r=>r.batch_id===selected&&[r.inspection_id,r.source].join(' ').toLowerCase().includes(q)).map(r=>'<tr><td><code>'+esc(r.inspection_id)+'</code></td><td>'+esc(r.created_at)+'</td><td><strong>'+esc(r.decision)+'</strong></td><td>'+esc(r.advice_status)+'</td><td><button data-id="'+esc(r.inspection_id)+'">Open</button></td></tr>').join('')||'<tr><td colspan="5">No inspections in this batch.</td></tr>';}
async function refresh(){
 const [bs,status,health,audit]=await Promise.all([api.batches(),api.status(),api.operationsHealth(),api.audit()]);batches=bs;
 $('#batches').innerHTML=batches.map(b=>'<option value="'+esc(b.batch_id)+'">'+esc(b.batch_id+' · '+b.sku)+'</option>').join('');if(!batches.some(b=>b.batch_id===selected))selected=health.active_batch;$('#batches').value=selected;
 records=await api.operationsHistory(selected);
 $('#station').textContent='Active batch '+health.active_batch+' · '+health.version+' · '+(health.authentication_required?'Local authentication enabled':'Local demo access — provision users to enable roles');
 $('#vision-state').textContent=status.vision_backend==='hailo'?'Hailo NPU ready':'CPU reference · '+status.vision_backend;$('#llama-state').textContent=status.llama_state+' · '+status.llama_threads+' threads';
 document.querySelector('.lane.vision small').textContent=status.vision_backend==='hailo'?'VISION · HAILORT / NPU':'VISION · ONNX / CPU REFERENCE';
 $('#llama-state').textContent+=' · '+status.llama_platform;
 const fields=[['CPU',status.cpu_percent==null?'Unavailable':status.cpu_percent+'%'],['RAM',status.ram_percent+'%'],['Temperature',status.temperature_c==null?'Unavailable':status.temperature_c+' °C'],['Free disk',health.storage.free_gib+' GiB · '+health.storage.state],['Llama queue',health.llama_queue_depth],['Spool',health.spooled_operations],['Database',health.database_error||'Connected'],['NPU utilization','Unavailable · no sampler']];
 $('#health').innerHTML=fields.map(([k,v])=>'<dt>'+esc(k)+'</dt><dd>'+esc(v)+'</dd>').join('');
 $('#audit').innerHTML=audit.map(r=>'<tr><td>'+esc(r.seq+' · '+r.event_type)+'</td><td>'+esc(r.actor)+'</td><td>'+esc(r.created_at)+'</td><td><code title="'+esc(r.event_hash)+'">'+esc(r.event_hash.slice(0,16))+' → '+esc(r.previous_hash.slice(0,16))+'</code></td></tr>').join('');renderBatch();
}
$('#batches').onchange=()=>{selected=$('#batches').value;renderBatch();};$('#search').oninput=renderRecords;
$('#refresh').onclick=()=>guarded(refresh);$('#select').onclick=()=>guarded(async()=>{await api.selectBatch(selected);await refresh();});$('#close').onclick=()=>guarded(async()=>{await api.closeBatch(selected);await refresh();});
$('#new-batch').onsubmit=e=>{e.preventDefault();guarded(async()=>{const b=await api.createBatch(Object.fromEntries(new FormData(e.target)));selected=b.batch_id;e.target.reset();await refresh();});};
$('#verify').onclick=()=>guarded(async()=>{const v=await api.verifyAudit();$('#verification').textContent=(v.valid?'Verified':'Integrity failure')+' · '+v.checked_events+' events · head '+v.head_sha256;});
$('#backup').onclick=()=>guarded(async()=>{$('#maintenance').textContent=JSON.stringify(await api.backup(),null,2);});$('#replay').onclick=()=>guarded(async()=>{$('#maintenance').textContent=JSON.stringify(await api.replay());await refresh();});
$('#records').onclick=e=>{const b=e.target.closest('[data-id]');if(!b)return;guarded(async()=>{const r=await api.get(b.dataset.id);$('#evidence-image').src=r.image_url;$('#evidence-json').textContent=JSON.stringify(r,null,2);$('#detail').showModal();});};
$('#dismiss').onclick=()=>$('#detail').close();$('#fullscreen').onclick=()=>guarded(async()=>document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen());$('#logout').onclick=()=>guarded(async()=>{await api.logout();location.reload();});
guarded(async()=>{await refresh();const next=new URLSearchParams(location.search).get('next');if(['/design-a'].includes(next))location.replace(next);});
