// Explicit demonstration adapter. No demo data is used by the real adapter.
export function createMock(assetURL){
 const types=['black_dot','broken','color_mismatch','crack','dual_cap','empty','foreign_particle'];
 const image=assetURL('demo-blister.jpg');
 const batches=[{id:'BT-261119-A',product:'Tablet · 10-pocket strip',line:'Line 01'},{id:'BT-261119-B',product:'Capsule · 10-pocket strip',line:'Line 02'}];
 let seq=2048,camera=false,source='0';
 const now=Date.now();
 const records=new Map();
 function record(n){
  const decision=n%13===0?'REVIEW':n%5===0?'HOLD':'PASS', type=types[n%7];
  const det=decision==='PASS'?[]:[{class_id:n%7,type,confidence:.82+(n%15)/100,box_xyxy:[74,64,174,174]},{class_id:n%7,type,confidence:.88,box_xyxy:[270,218,366,326]}];
  const clause=decision==='HOLD'?(types.indexOf(type)===0||type==='foreign_particle'?'BT-01':'BT-02'):decision==='REVIEW'?'BT-03':'BT-04';
  return {inspection_id:'DEMO-'+String(n).padStart(6,'0'),created_at:new Date(now-(2048-n)*8500).toISOString(),source:'demo:simulated-inspection',batch_id:batches[n%2].id,decision,severity:decision==='HOLD'?'major':decision==='REVIEW'?'review':'none',detections:det,defects:det.length?[{type,count:2}]:[],vision_ms:12.3+(n%29)/10,capture_valid:true,profile_validated:true,backend:'hailo',model_name:'YOLOv8s · demo',model_sha256:'demo-not-a-model-hash',image_url:image,original_url:image,image_width:640,image_height:640,decision_reason:decision==='HOLD'?'Simulated known defect exceeds the configured threshold.':decision==='REVIEW'?'Simulated capture quality requires operator review.':'Simulated recipe checks passed.',latency:{capture_ms:3.1,preprocess_ms:1.4,inference_ms:13.8,postprocess_ms:2.2},advice:{status:'llama_validated',sop_document:'BT-DEMO-SOP-01',sop_revision:'1',elapsed_ms:17420,prompt_tokens:650,advisory:{clause_id:clause,action_id:decision==='HOLD'?'ISOLATE_AND_REINSPECT':decision==='REVIEW'?'RECAPTURE_AND_REVIEW':'RECORD_INSPECTION',operator_message:decision==='HOLD'?'Keep this pack on HOLD. Preserve the inspection image and defect record, isolate the pack, and request QA review against the configured recipe.':decision==='REVIEW'?'Check the camera alignment and lighting, recapture the pack, and request human review.': 'Record the existing PASS and retain its evidence. Product release remains an authorized QA responsibility.',qa_note:'DRAFT · Demo inspection '+n+'. '+decision+' recorded by inspection rules. Evidence retained; QA review pending.'}},qa_review:n%9===0?{reviewer:'QA-DEMO-01',comment:'Demonstration evidence reviewed; disposition remains unchanged.',reviewed_at:new Date(now-(2048-n)*8500+2000).toISOString()}:null};
 }
 for(let n=1;n<=2048;n++){const r=record(n);records.set(r.inspection_id,r);}
 const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
 const clone=x=>structuredClone(x);
 const reviews=new Map();
 const adapter={
  mode:'mock',capabilities:{historyLimit:null,batches:true,tokenStream:true,auditChain:true,batchSummary:true,heatmap:true,qaTimeline:true,operatorAuth:false,telemetryDetails:true},
  async health(){await delay(120);return {ready:true,application:'BlisterTrace DEMO',startup_error:null};},
  async status(){return {ready:true,vision_backend:'hailo',model:'YOLOv8s · 7 classes (simulated)',llama_state:'ready',llama_platform:'Arm CPU (simulated)',stats:{total:records.size,PASS:1512,HOLD:378,REVIEW:158},cpu_percent:24.8,ram_percent:32.1,temperature_c:54.2,free_storage_gb:18.6,offline:true,profile_validated:true,uptime_seconds:4821,hailo_utilization:38,llama_queue_depth:0,db_size_mb:12.4,tokens_per_second:16.2,camera:{running:camera,frame_ready:camera,source,fps:camera?27.4:0,error:null,vision_ms:14.1,frame_age_ms:48},anomaly_model:'demo heatmap only'};},
  async history(){return [...records.values()].reverse().map(r=>clone(r));},
  async get(id){await delay(80);const r=records.get(id);if(!r)throw Error('Demo inspection not found');return clone(r);},
  async library(){return Array.from({length:12},(_,i)=>({name:'Demo specimen '+String(i+1).padStart(2,'0'),url:image}));},
  async inspect(input){await delay(650);const r=record(++seq);r.created_at=new Date().toISOString();r.source='demo:'+input.kind;r.advice=null;records.set(r.inspection_id,r);setTimeout(()=>{records.get(r.inspection_id).advice=record(seq).advice;},2600);return clone(r);},
  async retry(id){records.get(id).advice=null;setTimeout(()=>{records.get(id).advice=record(Number(id.split('-')[1])).advice;},2000);return {queued:true};},
  async ask(id,question,intent){await delay(450);const r=records.get(id);if(!r)throw Error('Select an inspection');
   const replies={explain:r.decision_reason,next_action:r.advice?.advisory.operator_message||'Advice is pending.',rectify:r.advice?.advisory.operator_message||'Advice is pending.',qa_note:r.advice?.advisory.qa_note||'Draft is pending.',evidence:'Image, detector class scores, bounding boxes, model identifier and rule decision are linked to '+id+'.'};
   return {inspection_id:id,intent:intent||'unsupported',reply:replies[intent]||'This question is outside the selected inspection. Ask about the flag, evidence, SOP action or QA draft. I cannot provide treatment advice, manufacturing root cause, or release approval.',clause_id:r.advice?.advisory.clause_id,source:'demo_simulated_advisory'};
  },
  async review(id,value){await delay(250);const r=records.get(id);const v={...value,reviewed_at:new Date().toISOString()};r.qa_review=v;reviews.set(id,[...(reviews.get(id)||[]),v]);return clone(v);},
  async reviewTimeline(id){const r=records.get(id);return clone(reviews.get(id)||(r?.qa_review?[r.qa_review]:[]));},
  async cameraStart(value){source=value;camera=true;return {started:true};},async cameraStop(){camera=false;return {stopped:true};},
  cameraURL(){return image;},
  async summarize(rows){await delay(700);return 'DRAFT · Simulated Llama summary: '+rows.length+' demo inspections in the current view. '+rows.filter(r=>r.decision==='HOLD').length+' HOLD and '+rows.filter(r=>r.decision==='REVIEW').length+' REVIEW records require QA attention. This summary does not authorize release.';},
  async *streamText(text){for(const chunk of text.match(/\S+\s*/g)||[]){await delay(23);yield chunk;}}
 };
 return adapter;
}
