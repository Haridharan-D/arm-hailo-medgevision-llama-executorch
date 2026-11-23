import {api} from './api.js?display-sync-v1';
import {displayVerdict} from './verdict.js';
const label=document.querySelector('#verdict'),reason=document.querySelector('#reason'),symbol=document.querySelector('#symbol'),identity=document.querySelector('#identity');
const reduced=matchMedia('(prefers-reduced-motion:reduce)'),link=document.querySelector('#link-state'),lastCheck=document.querySelector('#last-check');let lastKey='';
const glyphs={safe:'<svg viewBox="0 0 48 48"><path d="m12 25 8 8 17-19"/></svg>',warning:'<svg viewBox="0 0 48 48"><path d="M24 8 43 40H5Z"/><path d="M24 19v10m0 5v1"/></svg>',rejected:'<svg viewBox="0 0 48 48"><path d="m24 5 16 7v12c0 10-8 16-16 20C16 40 8 34 8 24V12Z"/><path d="m18 18 12 12m0-12L18 30"/></svg>',idle:'<svg viewBox="0 0 48 48"><circle cx="24" cy="24" r="15"/><path d="M24 14v11l8 4"/></svg>'};
function render(record,overrideReason){const v=displayVerdict(record);if(overrideReason)v.reason=overrideReason;const key=JSON.stringify([v.key,v.label,v.reason,record?.inspection_id]);if(key===lastKey)return;lastKey=key;document.body.dataset.verdict=v.key;label.textContent=v.label;reason.textContent=v.reason;symbol.innerHTML=glyphs[v.key]||glyphs.idle;identity.textContent=record?.inspection_id?'Inspection '+record.inspection_id:'Waiting for an inspection record';const content=document.querySelector('.verdict-content');if(!reduced.matches&&content?.animate)content.animate([{opacity:.5,transform:'translateY(8px)'},{opacity:1,transform:'translateY(0)'}],{duration:320,easing:'cubic-bezier(.2,.8,.2,1)'});}
function connection(ok){if(link){link.dataset.connected=String(ok);const text=link.querySelector('span');if(text)text.textContent=ok?'STATION ONLINE':'RECONNECTING';}if(lastCheck)lastCheck.textContent=ok?'Checked '+new Date().toLocaleTimeString():'Waiting for local station';}
let polling=false,timer;
async function poll(){
 if(polling)return;polling=true;
 try{
  const state=await api.displayStatus();render(state.record);connection(true);
 }catch(error){connection(false);try{render({error:true},'Station disconnected — reconnecting automatically');}catch{}}
 finally{polling=false;clearTimeout(timer);timer=setTimeout(poll,500);}
}
document.addEventListener('visibilitychange',()=>document.body.classList.toggle('display-paused',document.hidden));
render(null);poll();
window.addEventListener('focus',()=>{clearTimeout(timer);poll();});
