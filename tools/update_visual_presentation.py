"""Apply the separate visual-status presentation to preserved dashboard components."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'web/js/app.js';s=p.read_text(encoding='utf8')
start=s.index('function resultHTML(){');end=s.index('function renderSelected(){',start)
s=s[:start]+'''function resultHTML(){
 const r=state.selected;if(!r)return '<div class="card result-banner"><div class="result-icon">'+icon('inspect')+'</div><div><h2>Ready for inspection</h2><p>Run inference to record a visual model result.</p></div></div>';
 const times=r.latency||{},tone=visualTone(r);
 return '<div class="card"><div class="result-banner '+tone+'" role="status" aria-live="polite"><div class="result-icon '+tone.toLowerCase()+'-text">'+icon(tone)+'</div><div class="grow"><div class="between"><h2 class="'+tone.toLowerCase()+'-text">'+esc(inspectionLabel(r))+'</h2><span class="mono tiny">'+num(r.vision_ms,2)+' ms</span></div><p>'+esc(visualReason(r))+'</p><div class="decision-lock">'+icon('lock')+'VISUAL MODEL CHECK · QA DECISION PRESERVED · '+esc(r.inspection_id)+'</div></div></div><div class="latency-strip">'+[['Capture',times.capture_ms],['Preprocess',times.preprocess_ms],[r.backend==='hailo'?'Vision / HailoRT':'Vision / CPU',times.inference_ms??r.vision_ms],['Postprocess',times.postprocess_ms]].map(([label,value])=>'<div><label>'+label+'</label><span>'+(value!=null?num(value,2)+' ms':'not exposed')+'</span></div>').join('')+'</div></div>';
}
''' +s[end:]
s=s.replace('verdict(state.viewer,record);','verdict(state.viewer,{...record,decision:visualTone(record)});')
p.write_text(s,encoding='utf8')
p=root/'web/js/components.js';s=p.read_text(encoding='utf8')
if "from './inspection-label.js'" not in s:s="import {inspectionLabel,visualTone,visualReason} from './inspection-label.js';\n"+s
start=s.index('export function resultDialog(');end=s.index('export function empty(',start);part=s[start:end]
if 'const tone=visualTone(record);' not in part:part=part.replace(' countdownCancel();',' const tone=visualTone(record);countdownCancel();',1)
part=part.replace("d.className='result-dialog '+record.decision","d.className='result-dialog '+tone").replace('record.decision.toLowerCase()','tone.toLowerCase()').replace('icon(record.decision)','icon(tone)').replace('escape(record.decision)','escape(inspectionLabel(record))').replace('escape(record.decision_reason)','escape(visualReason(record))').replace('Detector result · pinned to inspection','Visual result · QA decision preserved')
s=s[:start]+part+s[end:];p.write_text(s,encoding='utf8')
p=root/'web/js/classic.js';s=p.read_text(encoding='utf8')
s=s.replace("$('#verdict').className='verdict '+r.decision","$('#verdict').className='verdict '+visualTone(r)")
s=s.replace('esc(r.decision_reason)','esc(visualReason(r))')
s=s.replace("$('#result-title').textContent=r.decision","$('#result-title').textContent=inspectionLabel(r)")
s=s.replace("r.decision==='HOLD'?'#c93445':r.decision==='PASS'?'#148447':'#9b6208'","visualTone(r)==='HOLD'?'#c93445':visualTone(r)==='PASS'?'#148447':'#9b6208'")
s=s.replace("$('#result-detail').textContent=r.decision_reason","$('#result-detail').textContent=visualReason(r)")
p.write_text(s,encoding='utf8')
p=root/'web/js/console.js';s=p.read_text(encoding='utf8')
s=s.replace("+' · blind test</option>'","+(row.demo_suite?' · verified demo':' · blind test')+'</option>'")
p.write_text(s,encoding='utf8')
print('Updated visual status, color and popup; original QA decision fields untouched.')
