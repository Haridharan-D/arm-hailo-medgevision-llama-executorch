import {inspectionLabel,visualReason} from './inspection-label.js';
/** Pure visual display mapping; never changes a stored QA disposition. */
export function displayVerdict(record){
 if(!record)return {key:'idle',label:'WAITING',symbol:'—',reason:'Run an inspection on the main monitor'};
 if(record.system_fault||record.error)return {key:'warning',label:'WARNING',symbol:'!',reason:'Station fault — inspection required'};
 const label=inspectionLabel(record);
 if(label==='DEFECTIVE')return {key:'rejected',label:'REJECTED',symbol:'✕',reason:visualReason(record)};
 if(label==='SAFE')return {key:'safe',label:'SAFE',symbol:'✓',reason:visualReason(record)};
 return {key:'warning',label:'WARNING',symbol:'!',reason:visualReason(record)};
}
