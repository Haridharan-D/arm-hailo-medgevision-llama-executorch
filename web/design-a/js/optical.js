import {icon,escape as esc,badge} from './icons.js';
import {level,enter,heroMotion,spring,setMotion,motionStatus} from './motion.js';
import {assetURL,api} from './api.js';
let lastActivity=Date.now(),ambientFrame,replayTimer,activeObserver;
export function enhance(state,{openDetail}){
 const page=document.querySelector('#page');clearInterval(replayTimer);enter(page.querySelectorAll(':scope > .card,:scope > .settings-layout > .card,:scope > .health-grid > .card'));
 if(state.route==='inspect'){
  const pipeline=document.querySelector('.pipeline-grid');
  if(pipeline){const strip=document.createElement('div');strip.className='optical-strip';strip.setAttribute('aria-label','Separate vision and advisory pipelines');strip.innerHTML='<span class="optical-node">'+icon('camera')+'Capture <b data-flow="capture">—</b></span><span class="optical-link"><i></i></span><span class="optical-node" style="color:var(--vision)">'+icon('chip')+'Vision <b data-flow="vision">—</b></span><span class="optical-link"><i></i></span><span class="optical-node">'+icon('lock')+'Decision</span><span class="optical-link"><i></i></span><span class="optical-node violet">'+icon('llama')+'Llama <b data-flow="llama">—</b></span>';pipeline.before(strip);}
  const head=document.querySelector('.advice-column .card-header .row');if(head){const orb=document.createElement('i');orb.className='orb';orb.setAttribute('aria-hidden','true');head.prepend(orb);}
  const tools=document.querySelector('.viewer-controls>div');if(tools){const b=document.createElement('button');b.className='btn ghost';b.textContent='Loupe';b.setAttribute('aria-pressed','false');b.onclick=()=>{const enabled=state.viewer?.toggleLoupe();b.setAttribute('aria-pressed',String(enabled));b.textContent=enabled?'Loupe on':'Loupe';};tools.append(b);}
  const result=document.querySelector('#result-panel');const viewer=document.querySelector('.viewer-card');if(result&&viewer)viewer.before(result);
 }
 if(state.route==='settings'){
  const body=document.querySelector('.settings-layout .card-body');if(body){const el=document.createElement('div');el.className='list-option';el.innerHTML='<div><strong>Instrument motion</strong><p>Automatic Full → Calm → Minimal governor. Reduced motion forces Calm or quieter.</p><span class="motion-label" id="motion-status"></span></div><select id="motion-setting" aria-label="Motion level"><option value="full">Full</option><option value="calm">Calm</option><option value="off">Off</option></select>';body.prepend(el);el.querySelector('select').value=motionStatus().manual;el.querySelector('select').onchange=e=>{setMotion(e.target.value);updateMotion();};updateMotion();}
 }
 if(state.route==='dashboard'){
  const rows=state.records.filter(r=>state.batch==='all'||r.batch_id===state.batch).slice(0,120);
  const card=document.createElement('section');card.className='card mt-16';card.innerHTML='<div class="card-header"><div><h2>Blister atlas</h2><p class="tiny">One pocket = one image inspection · latest 120 · not physical pack layout</p></div><select id="atlas-filter" aria-label="Filter atlas by result"><option value="">All results</option><option>PASS</option><option>REVIEW</option><option>HOLD</option></select></div><div class="blister-map" id="blister-map"></div><div class="card-body"><div class="between mb-16"><span class="tiny">Loaded snapshot coverage · batch target not exposed</span><span class="mono tiny">'+rows.length+' / '+state.records.length+'</span></div><div class="completion-gauge" aria-label="Loaded snapshot coverage"><div class="completion-liquid" style="transform:scaleX('+rows.length/Math.max(1,state.records.length)+')"></div></div></div>';
  document.querySelector('.stats-grid')?.after(card);
  function draw(filter=''){const map=card.querySelector('#blister-map');map.innerHTML=rows.filter(r=>!filter||r.decision===filter).map(r=>'<button class="blister-pocket '+r.decision+'" data-pocket="'+r.inspection_id+'" aria-label="'+esc(r.inspection_id+' '+r.decision)+'">'+icon(r.decision)+'</button>').join('');enter(map.children);for(const b of map.children){const r=rows.find(v=>v.inspection_id===b.dataset.pocket);b.onclick=()=>openDetail(r.inspection_id);b.onpointerenter=e=>{const pop=document.createElement('div');pop.className='pocket-preview';pop.innerHTML='<img src="'+esc(r.original_url)+'" alt=""><p class="mono tiny">'+esc(r.inspection_id)+'</p>'+badge(r.decision);pop.style.left=Math.min(innerWidth-210,e.clientX+12)+'px';pop.style.top=Math.min(innerHeight-180,e.clientY+12)+'px';document.body.append(pop);b.onpointerleave=()=>pop.remove();};}}
  draw();card.querySelector('select').onchange=e=>draw(e.target.value);
 }
 if(state.route==='history'){
  const rows=[...state.records].reverse().slice(-120);const card=document.createElement('section');card.className='card mb-16';card.innerHTML='<div class="card-header"><h2>Inspection time-lapse</h2><div class="row"><span class="tiny">Recorded evidence · no new inference</span><button class="btn" id="replay-play">'+icon('play')+'Replay</button></div></div><div class="card-body"><div class="replay-preview" id="replay-preview"></div><input class="replay-playhead" id="replay-range" type="range" min="0" max="'+Math.max(0,rows.length-1)+'" value="0" aria-label="Scrub inspection history"><div class="replay-strip">'+rows.map((r,i)=>'<button data-replay="'+i+'" aria-label="Replay '+esc(r.inspection_id)+'"><img loading="lazy" src="'+esc(r.original_url)+'" alt=""></button>').join('')+'</div></div>';
  document.querySelector('#history-table')?.closest('.card').before(card);let index=0;
  function show(n){index=n;const r=rows[n];if(!r)return;card.querySelector('#replay-preview').innerHTML='<img src="'+esc(r.image_url||r.original_url)+'" alt="Recorded annotation"><div><p class="mono">'+esc(r.inspection_id)+'</p><p class="tiny">'+new Date(r.created_at).toLocaleString()+' · '+r.detections?.length+' regions</p>'+badge(r.decision)+' <button class="btn ghost" id="replay-open">Open details</button></div>';card.querySelector('#replay-open').onclick=()=>openDetail(r.inspection_id);card.querySelector('#replay-range').value=n;card.querySelectorAll('[data-replay]').forEach(b=>b.classList.toggle('active',Number(b.dataset.replay)===n));}
  show(0);card.querySelector('#replay-range').oninput=e=>show(Number(e.target.value));card.querySelectorAll('[data-replay]').forEach(b=>b.onclick=()=>show(Number(b.dataset.replay)));card.querySelector('#replay-play').onclick=()=>{if(replayTimer){clearInterval(replayTimer);replayTimer=null;card.querySelector('#replay-play').textContent='Replay';}else{card.querySelector('#replay-play').textContent='Pause replay';replayTimer=setInterval(()=>{if(index>=rows.length-1){clearInterval(replayTimer);replayTimer=null;card.querySelector('#replay-play').textContent='Replay';}else show(index+1);},1200);}};
 }
}
function updateMotion(){const el=document.querySelector('#motion-status');if(el){const s=motionStatus();el.textContent=s.effective.toUpperCase()+' · '+s.averageFrameMs+' ms frame EMA';}}
document.addEventListener('motionchange',updateMotion);
export function updateOptical(record,status){
 const get=s=>document.querySelector(s);const orb=get('.orb');if(orb)orb.dataset.thinking=String(['loading','generating'].includes(status?.llama_state));
 const values={capture:record?.latency?.capture_ms,vision:record?.vision_ms,llama:record?.advice?.elapsed_ms};
 for(const [key,value] of Object.entries(values)){const e=get('[data-flow="'+key+'"]');if(e)e.textContent=value==null?'—':Math.round(value)+'ms';}
}
export function scan(viewer){
 if(!viewer||level()==='minimal')return;
 const beam=document.createElement('i');beam.className='scan-beam';viewer.host.append(beam);
 const a=heroMotion(beam,[{transform:'translateY(0)',opacity:0},{offset:.1,opacity:1},{offset:.9,opacity:1},{transform:'translateY('+viewer.host.clientHeight+'px)',opacity:0}],{duration:700});a?.finished.catch(()=>{}).finally(()=>beam.remove());
}
export function verdict(viewer,record){
 if(!viewer)return;scan(viewer);updateOptical(record,null);
 if(viewer.loupe)viewer.loupe.hidden=true;viewer.loupeOn=false;viewer.loupeLocked=false;
 const c={PASS:'#62dfa42b',REVIEW:'#ffc87422',HOLD:'#ff929b2b'}[record.decision];
 const edge=document.createElement('div');edge.className='optical-verdict';edge.style.setProperty('--verdict-color',c);viewer.host.append(edge);
 if(level()!=='minimal')edge.animate([{opacity:0},{opacity:1},{opacity:.4}],{duration:record.decision==='REVIEW'?2400:700,easing:'ease-in-out'}).finished.finally(()=>edge.remove());else edge.remove();
 const symbol=document.querySelector('#result-dialog .result-symbol .icon');if(symbol&&level()!=='minimal')spring(v=>symbol.style.transform='scale('+(record.decision==='HOLD'?.75+v*.25:.9+v*.1)+')',0,1,'heavy');
 if(level()!=='minimal')viewer.canvas.animate([{opacity:0,transform:'scale(.995)'},{opacity:1,transform:'scale(1)'}],{duration:420,delay:140,easing:'ease-out'});
 // Packet duration represents recorded stage duration, bounded for readability; no inferred stage timing.
 for(const [i,packet] of [...document.querySelectorAll('.optical-link i')].entries()){const ms=i===2?record.advice?.elapsed_ms:record.vision_ms;packet.title=ms==null?'Timing not exposed':'Recorded '+ms.toFixed(1)+' ms; display duration clamped';if(ms!=null&&level()==='full')packet.animate([{transform:'translateX(0)',opacity:0},{offset:.15,opacity:1},{transform:'translateX(80px)',opacity:0}],{duration:Math.max(420,Math.min(1800,ms)),delay:i*160});}
}
export function iris(){
 const splash=document.querySelector('#splash');if(!splash)return;
 const obs=new MutationObserver(()=>{if(!splash.classList.contains('leaving')||level()!=='full')return;const blade=document.createElement('div');blade.className='iris-blade';document.body.append(blade);blade.animate([{opacity:.65,transform:'rotate(-12deg) scale(1)'},{opacity:0,transform:'rotate(30deg) scale(2)'}],{duration:420,easing:'ease-out'}).finished.finally(()=>blade.remove());obs.disconnect();});obs.observe(splash,{attributes:true,attributeFilter:['class']});
}
export function idle(state){
 const wake=()=>{lastActivity=Date.now();const el=document.querySelector('.ambient');if(el){cancelAnimationFrame(ambientFrame);el.remove();}};
 for(const event of ['pointerdown','pointermove','keydown','wheel'])document.addEventListener(event,wake,{passive:true});
 setInterval(()=>{if(Date.now()-lastActivity<120000||level()!=='full'||document.hidden||document.querySelector('dialog[open],.ambient')||state.busy)return;
  const el=document.createElement('div');el.className='ambient';el.setAttribute('role','button');el.setAttribute('tabindex','0');el.setAttribute('aria-label','Station idle. Touch or press any key to return.');el.innerHTML='<canvas></canvas><div class="ambient-center"><div class="eyebrow">OPTICAL INSTRUMENT / STATION IDLE</div><h2>BlisterTrace.</h2><p>'+state.records.length+' loaded inspections · QA decisions remain pinned</p><p class="tiny">Touch anywhere to resume</p></div>';document.body.append(el);
  const canvas=el.querySelector('canvas'),c=canvas.getContext('2d');canvas.width=innerWidth;canvas.height=innerHeight;const particles=Array.from({length:40},()=>({x:Math.random()*innerWidth,y:Math.random()*innerHeight,r:Math.random()*3,s:20+Math.random()*20}));
  let prev=performance.now();function draw(now){if(!el.isConnected||level()!=='full'){el.remove();return;}const dt=Math.min(40,now-prev);prev=now;c.clearRect(0,0,canvas.width,canvas.height);for(const p of particles){p.y-=dt*.008;if(p.y<-70)p.y=canvas.height+70;c.save();c.translate(p.x,p.y);c.rotate(p.r);c.strokeStyle='#83ceff25';c.fillStyle='#bda8ff05';c.lineWidth=1;c.beginPath();c.roundRect(-p.s/2,-p.s,p.s,p.s*2,p.s/2);c.fill();c.stroke();c.beginPath();c.moveTo(-p.s/2,0);c.lineTo(p.s/2,0);c.stroke();c.restore();}ambientFrame=requestAnimationFrame(draw);}ambientFrame=requestAnimationFrame(draw);
 },10000);
}
