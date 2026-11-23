export function runtimeTiming(advice){
 if(advice?.cache_hit)return 'Cached advisory · no new token generation';
 const m=advice?.runtime_metrics;if(!m||!Number.isFinite(m.prompt_tokens))return 'Native stage timing unavailable for this record';
 const decode=m.inference_end_ms-m.first_token_ms,rate=decode>0&&m.generated_tokens>1?(m.generated_tokens-1)*1000/decode:null;
 return ['TTFT '+(m.callback_ttft_ms/1000).toFixed(2)+' s','Prefill '+(m.prefill_ms/1000).toFixed(2)+' s',rate==null?'Decode unavailable':'Decode '+rate.toFixed(1)+' tok/s',m.generated_tokens+' tokens'].join(' · ');
}
