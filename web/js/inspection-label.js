/** Visual model observation, independent from immutable QA disposition. */
export function visualAssessment(record){
 if(!record)return {status:'WARNING',reason:'No inspection available'};
 if(record.system_fault||record.error)return {status:'WARNING',reason:'Station fault — inspection required'};
 if(record.visual_result?.policy==='visual-check-v1')return record.visual_result;
 if(record.detections?.length||record.decision==='HOLD')return {status:'DEFECTIVE',reason:'Configured defect detected by the vision model'};
 if(record.capture_valid!==true)return {status:'WARNING',reason:'Capture quality requires reinspection'};
 if(record.anomaly?.flagged===true)return {status:'DEFECTIVE',reason:'Anomaly score exceeds the saved model threshold'};
 if(record.anomaly&&record.anomaly.flagged!==false)return {status:'WARNING',reason:'Anomaly assessment incomplete'};
 return {status:'SAFE',reason:record.anomaly?'Below the saved anomaly threshold':'No configured defect detected'};
}
export function inspectionLabel(record){return visualAssessment(record).status;}
export function visualTone(record){return {SAFE:'PASS',WARNING:'REVIEW',DEFECTIVE:'HOLD'}[inspectionLabel(record)];}
export function visualReason(record){return visualAssessment(record).reason+' · visual check only · QA: '+(record.decision||'unavailable');}
