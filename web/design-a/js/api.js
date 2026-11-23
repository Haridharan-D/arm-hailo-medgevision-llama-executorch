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
async function request(path,options={}){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),options.timeout||30000);
 try{
  const response=await fetch(path,{...options,signal:controller.signal,headers:options.body instanceof FormData?{}:{'Content-Type':'application/json',...options.headers}});
  if(!response.ok){const value=await response.json().catch(()=>({detail:'Request failed: '+response.status}));throw new ApiError(typeof value.detail==='string'?value.detail:JSON.stringify(value.detail),response.status);}
  return response.json();
 }catch(error){if(error.name==='AbortError')throw new ApiError('Request timed out. The station may still be processing; check history before retrying.',408);throw error;}
 finally{clearTimeout(timer);}
}
const post=(path,value)=>request(path,{method:'POST',body:value===undefined?undefined:JSON.stringify(value)});
const encoded=encodeURIComponent;
const real={
 mode:'real',capabilities:{historyLimit:50,batches:false,tokenStream:false,auditChain:false,batchSummary:false,heatmap:false,qaTimeline:false,operatorAuth:false,telemetryDetails:false},
 health:()=>request('/api/health',{timeout:4500}),
 status:()=>request('/api/status',{timeout:5000}),
 /** @returns {Promise<Inspection[]>} */history:()=>request('/api/inspections'),
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
 ask:(id,question,intent)=>post('/api/inspections/'+encoded(id)+'/ask',intent?{intent}:{question}),
 review:(id,value)=>post('/api/inspections/'+encoded(id)+'/qa',value),
 cameraStart:source=>post('/api/camera/start',{source}),
 cameraStop:()=>post('/api/camera/stop',{}),
 cameraURL:()=>'/api/camera/stream',
 async reviewTimeline(id){const record=await real.get(id);return record.qa_review?[record.qa_review]:[];}
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
