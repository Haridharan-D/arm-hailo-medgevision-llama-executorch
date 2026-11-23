import {inspectionLabel,visualTone,visualReason} from './inspection-label.js';
import {icon,escape,badge} from './icons.js';
export const $=(selector,root=document)=>root.querySelector(selector);
export const $$=(selector,root=document)=>[...root.querySelectorAll(selector)];
export const num=(n,d=1)=>n==null?'—':Number(n).toLocaleString(undefined,{maximumFractionDigits:d});
export const when=value=>value?new Date(value).toLocaleString(undefined,{month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit'}):'—';
export function toast(message,error=false){
 const node=document.createElement('div');node.className='toast'+(error?' error':'');node.innerHTML=icon(error?'REVIEW':'check')+'<span>'+escape(message)+'</span><button aria-label="Dismiss notification">'+icon('close')+'</button>';
 $('#toasts').append(node);$('button',node).onclick=()=>node.remove();setTimeout(()=>node.remove(),7000);
}
export function download(name,value,type='application/json'){
 const blob=new Blob([typeof value==='string'?value:JSON.stringify(value,null,2)],{type});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);
}
export async function copy(text){try{await navigator.clipboard.writeText(String(text));toast('Copied to clipboard');}catch{toast('Clipboard unavailable. Select the text and use Copy.',true);}}
let lastFocus=new WeakMap();
export function openDialog(dialog){lastFocus.set(dialog,document.activeElement);if(!dialog.open)dialog.showModal();requestAnimationFrame(()=>dialog.querySelector('[autofocus],input,button,textarea')?.focus());}
export function closeDialog(dialog){dialog.close();lastFocus.get(dialog)?.focus();}
export function setupDialogs(){
 document.addEventListener('click',e=>{const b=e.target.closest('[data-close]');if(b)closeDialog(document.getElementById(b.dataset.close));});
 for(const d of $$('dialog')){d.addEventListener('close',()=>lastFocus.get(d)?.focus());d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeDialog(d);}});}
}
let countdownCancel=()=>{};
export function resultDialog(record,onDetails,sound){
 const tone=visualTone(record);countdownCancel();const d=$('#result-dialog');d.className='result-dialog '+tone;
 d.innerHTML='<div class="modal-body"><div class="result-symbol '+tone.toLowerCase()+'-text"><svg viewBox="0 0 88 88" aria-hidden="true"><circle cx="44" cy="44" r="40"/><circle class="count-ring" cx="44" cy="44" r="40"/></svg>'+icon(tone)+'</div><div class="eyebrow">Visual result · QA decision preserved</div><h2 id="result-title" class="'+tone.toLowerCase()+'-text">'+escape(inspectionLabel(record))+'</h2><p class="finding">'+escape(visualReason(record))+'</p><p class="mono tiny">'+escape(record.inspection_id)+'</p><p class="countdown-label">Closes in <span id="count-seconds">5</span>s · press and hold to pause</p><button class="btn ghost" id="pause-count">Pause countdown</button></div><div class="modal-actions"><button class="btn" id="result-details">Open details</button><button class="btn primary" id="result-ack" autofocus>Acknowledge</button></div>';
 let remaining=5000,last=performance.now(),frame,paused=false,held=false;
 const tick=now=>{if(!d.open)return;const dt=now-last;last=now;if(!paused&&!held)remaining-=dt;$('.count-ring',d).style.strokeDashoffset=251.33*(1-remaining/5000);$('#count-seconds').textContent=Math.max(0,Math.ceil(remaining/1000));if(remaining<=0)closeDialog(d);else frame=requestAnimationFrame(tick);};
 $('#pause-count').onclick=()=>{paused=!paused;$('#pause-count').textContent=paused?'Resume countdown':'Pause countdown';};
 d.onpointerdown=e=>{if(!e.target.closest('button'))held=true;};d.onpointerup=d.onpointercancel=()=>{held=false;};
 $('#result-ack').onclick=()=>closeDialog(d);$('#result-details').onclick=()=>{closeDialog(d);onDetails();};
 countdownCancel=()=>{cancelAnimationFrame(frame);if(d.open)closeDialog(d);};
 openDialog(d);frame=requestAnimationFrame(tick);
 if(sound&&record.decision==='HOLD'){try{const ctx=new AudioContext(),osc=ctx.createOscillator(),gain=ctx.createGain();osc.frequency.value=440;gain.gain.setValueAtTime(.035,ctx.currentTime);gain.gain.exponentialRampToValueAtTime(.001,ctx.currentTime+.25);osc.connect(gain).connect(ctx.destination);osc.start();osc.stop(ctx.currentTime+.26);osc.onended=()=>ctx.close();}catch{}}
}
export function empty(title,detail,name='inspect'){return '<div class="empty">'+icon(name)+'<strong>'+escape(title)+'</strong><p>'+escape(detail)+'</p></div>';}
export function spark(values){
 const max=Math.max(...values,1),pts=values.map((v,i)=>i*100/Math.max(1,values.length-1)+','+(33-v/max*28)).join(' ');
 return '<svg class="spark" viewBox="0 0 100 36" preserveAspectRatio="none" aria-hidden="true"><polyline points="'+pts+'"/></svg>';
}
export function animateNumber(el,value,suffix=''){
 if(matchMedia('(prefers-reduced-motion: reduce)').matches){el.textContent=num(value)+suffix;return;}
 const start=performance.now();function tick(now){const t=Math.min(1,(now-start)/350);el.textContent=num(value*(1-Math.pow(1-t,3)))+suffix;if(t<1&&el.isConnected)requestAnimationFrame(tick);}requestAnimationFrame(tick);
}
/** Fixed row heights keep work bounded independently of record count. */
export class VirtualTable{
 constructor(scroller,rows,renderRow,onOpen,onSelect){
  this.el=scroller;this.rows=rows;this.height=64;this.renderRow=renderRow;this.onOpen=onOpen;this.onSelect=onSelect;this.start=-1;
  scroller.innerHTML='<div class="history-grid history-head" role="row"><div><input type="checkbox" aria-label="Select all filtered inspections" id="history-select-all"></div><div>Image</div><div>Inspection / time</div><div>Source / batch</div><div>Result</div><div>Defects</div><div>Advice</div><div>QA</div></div><div class="virtual-space" role="rowgroup"><div class="virtual-content"></div></div>';
  this.space=$('.virtual-space',scroller);this.content=$('.virtual-content',scroller);this.space.style.height=rows.length*this.height+'px';
  this.scroll=()=>{cancelAnimationFrame(this.raf);this.raf=requestAnimationFrame(()=>this.draw());};scroller.addEventListener('scroll',this.scroll,{passive:true});
  this.content.onclick=e=>{const row=e.target.closest('[data-row]');if(!row)return;if(e.target.matches('input'))this.onSelect(row.dataset.row,e.target.checked);else this.onOpen(row.dataset.row);};
  this.content.onkeydown=e=>{if(e.target.matches('input'))return;const row=e.target.closest('[data-row]');if(row&&(e.key==='Enter'||e.key===' ')){e.preventDefault();this.onOpen(row.dataset.row);}if(row&&['ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();const index=this.rows.findIndex(r=>r.inspection_id===row.dataset.row)+(e.key==='ArrowDown'?1:-1);if(index>=0&&index<this.rows.length){this.el.scrollTop=Math.max(0,index*this.height-100);this.start=-1;this.draw();this.content.querySelector('[data-row="'+CSS.escape(this.rows[index].inspection_id)+'"]')?.focus();}}};
  this.resize=new ResizeObserver(()=>{this.start=-1;this.draw();});this.resize.observe(scroller);this.draw();
 }
 draw(){const from=Math.max(0,Math.floor((this.el.scrollTop-48)/this.height)-3),end=Math.min(this.rows.length,from+Math.ceil(this.el.clientHeight/this.height)+8);if(from===this.start&&end===this.end)return;this.start=from;this.end=end;this.content.style.transform='translateY('+from*this.height+'px)';this.content.innerHTML=this.rows.slice(from,end).map(this.renderRow).join('');}
 destroy(){this.el.removeEventListener('scroll',this.scroll);this.resize.disconnect();cancelAnimationFrame(this.raf);}
}
export function reviewEntry(review,hash=''){return '<div class="timeline-entry"><div class="between"><strong>'+escape(review.reviewer)+'</strong>'+icon('lock')+'</div><span class="tiny">'+when(review.reviewed_at)+'</span><p>'+escape(review.comment)+'</p>'+(hash?'<span class="hash">Browser digest · '+escape(hash.slice(0,12))+'</span>':'')+'</div>';}
export async function digest(value){if(!crypto.subtle)return null;const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(typeof value==='string'?value:JSON.stringify(value)));return [...new Uint8Array(bytes)].map(b=>b.toString(16).padStart(2,'0')).join('');}
