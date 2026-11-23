import {createMock} from './mock.js';
/**
 * @typedef {'PASS'|'REVIEW'|'HOLD'} Decision
 * @typedef {{class_id:number,type:string,confidence:number,box_xyxy:number[]}} Detection
 * @typedef {{inspection_id:string,created_at:string,source:string,decision:Decision,severity:string,detections:Detection[],vision_ms:number,decision_reason:string,original_url:string,image_url:string,advice:object|null,qa_review:object|null,batch_id?:string}} Inspection
 *
 * All network requests live in this module. Real mode NEVER silently switches to demo.
 * TODO endpoint map is in API_MAP.md. Unsupported real capabilities remain unavailable.
 * Existing server has REST + MJPEG; subscribe() polls, without inventing SSE/token events.
 */
const moduleRoot=new URL('../',import.meta.url);
export const assetURL=name=>new URL('assets/'+name,moduleRoot).href;
export class ApiError extends Error{constructor(message,status){super(message);this.status=status;}}
let loginPromise=null;
async function signIn(){
 if(loginPromise)return loginPromise;
 loginPromise=new Promise(resolve=>{
  const dialog=document.createElement('dialog');dialog.setAttribute('aria-label','Local station sign-in');
  dialog.innerHTML='<form><h2>Station sign-in</h2><p>Use your locally provisioned account.</p><label>Username<input name="username" autocomplete="username" required></label><label>Password<input name="password" type="password" autocomplete="current-password" required></label><p role="alert"></p><button type="submit">Sign in</button></form>';
  dialog.style.cssText='max-width:380px;padding:32px;border:1px solid #64748b;border-radius:16px;background:#101b29;color:#f1f5f9';
  dialog.querySelectorAll('input').forEach(e=>e.style.cssText='display:block;padding:12px;margin:8px 0 16px;width:100%;box-sizing:border-box');
  fetch('/api/auth/me').then(r=>r.json()).then(me=>{dialog.dataset.setup=String(me.needs_setup);if(me.needs_setup){dialog.querySelector('h2').textContent='Create station administrator';dialog.querySelector('p').textContent='First local setup. Choose a password of at least 10 characters.';dialog.querySelector('button').textContent='Create account & sign in';}});
  dialog.addEventListener('cancel',e=>e.preventDefault());document.body.append(dialog);dialog.showModal();
  dialog.querySelector('form').onsubmit=async e=>{e.preventDefault();const f=new FormData(e.target);
   try{const payload=JSON.stringify(Object.fromEntries(f));if(dialog.dataset.setup==='true'){const setup=await fetch('/api/auth/bootstrap',{method:'POST',headers:{'Content-Type':'application/json'},body:payload});if(!setup.ok)throw Error((await setup.json()).detail);dialog.dataset.setup='false';}const response=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:payload});const data=await response.json();if(!response.ok)throw Error(data.detail);dialog.close();dialog.remove();resolve(data.user);}catch(error){dialog.querySelector('[role=alert]').textContent=error.message;}
  };
 }).finally(()=>loginPromise=null);return loginPromise;
}
async function request(path,options={}){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),options.timeout||30000);
 try{
  const response=await fetch(path,{...options,signal:controller.signal,headers:options.body instanceof FormData?{}:{'Content-Type':'application/json',...options.headers}});
  if(response.status===401&&!options.authRetried){clearTimeout(timer);await signIn();return request(path,{...options,authRetried:true});}
  if(!response.ok){const value=await response.json().catch(()=>({detail:'Request failed: '+response.status}));throw new ApiError(typeof value.detail==='string'?value.detail:JSON.stringify(value.detail),response.status);}
  return response.json();
 }catch(error){if(error.name==='AbortError')throw new ApiError('Request timed out. The station may still be processing; check history before retrying.',408);throw error;}
 finally{clearTimeout(timer);}
}
const post=(path,value)=>request(path,{method:'POST',body:value===undefined?undefined:JSON.stringify(value)});
const encoded=encodeURIComponent;
const real={
 mode:'real',capabilities:{historyLimit:50,batches:false,tokenStream:false,auditChain:false,batchSummary:false,heatmap:false,qaTimeline:true,operatorAuth:true,telemetryDetails:false},
 health:()=>request('/api/health',{timeout:4500}),
 status:()=>request('/api/status',{timeout:5000}),
 displayStatus:()=>request('/api/display',{timeout:3500,cache:'no-store'}),
 displayLive:()=>post('/api/display/live',{}),
 /** @returns {Promise<Inspection[]>} */history:()=>request('/api/inspections'),
 latestInspection:()=>request('/api/inspections?limit=1'),
 operationsHistory:batch=>request('/api/inspections?limit=500&batch_id='+encoded(batch)),
 /** @param {string} id @returns {Promise<Inspection>} */get:id=>request('/api/inspections/'+encoded(id)),
 library:()=>request('/api/library'),
 anomalyProfiles:()=>request('/api/anomaly/profiles'),
 anomalySamples:profile=>request('/api/anomaly/samples/'+encoded(profile)),
 anomalyInspect:value=>request('/api/anomaly/inspect',{method:'POST',body:JSON.stringify(value),timeout:90000}),
 anomalyUpload:(profile,file)=>{const body=new FormData();body.set('file',file);return request('/api/anomaly/inspect-upload?profile='+encoded(profile),{method:'POST',body,timeout:90000});},
 /** @param {{kind:string,file?:File,name?:string}} input */
 inspect:input=>{
  if(input.kind==='upload'){const form=new FormData();form.set('file',input.file);return request('/api/inspect',{method:'POST',body:form,timeout:90000});}
  if(input.kind==='local')return post('/api/library/inspect',{name:input.name});
  return post('/api/camera/inspect');
 },
 retry:id=>post('/api/inspections/'+encoded(id)+'/advice'),
 cancelAdvice:id=>post('/api/inspections/'+encoded(id)+'/cancel-advice'),
 ask:(id,question,intent)=>post('/api/inspections/'+encoded(id)+'/ask',intent?{intent}:{question}),
 review:(id,value)=>post('/api/inspections/'+encoded(id)+'/qa',value),
 cameraStart:source=>post('/api/camera/start',{source}),
 cameraStop:()=>post('/api/camera/stop',{}),
 cameraURL:()=>'/api/camera/stream',
 reviewTimeline:id=>request('/api/inspections/'+encoded(id)+'/reviews'),
 batches:()=>request('/api/batches'),createBatch:value=>post('/api/batches',value),
 selectBatch:id=>post('/api/batches/'+encoded(id)+'/select'),closeBatch:id=>post('/api/batches/'+encoded(id)+'/close'),
 audit:()=>request('/api/audit'),verifyAudit:()=>request('/api/audit/verify'),
 operationsHealth:()=>request('/api/operations/health'),backup:()=>post('/api/database/backup'),
 replay:()=>post('/api/database/replay'),me:()=>request('/api/auth/me'),logout:()=>post('/api/auth/logout')
};
export const api=new URLSearchParams(location.search).get('adapter')==='mock'?createMock(assetURL):real;
export async function getSop(){return request(assetURL('sop.json'));}
/**
 * Non-overlapping, visibility-aware REST subscription. SSE/WS can replace this
 * function when the backend exposes versioned events. One error never invents health.
 * @param {(data:{health:object,status:object|null,error:Error|null})=>void} onUpdate
 * @returns {()=>void}
 */
export function subscribe(onUpdate){
 let stopped=false,timer;
 async function tick(){
  let health=null,status=null,error=null;
  try{health=await api.health();if(health.ready)status=await api.status();}catch(e){error=e;}
  if(!stopped){onUpdate({health,status,error});timer=setTimeout(tick,document.hidden?8000:2000);}
 }
 tick();return ()=>{stopped=true;clearTimeout(timer);};
}
