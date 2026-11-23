"""Build reproducible local JSON/CSV/charts from saved target evidence only."""
import csv,json,statistics,math,hashlib,tarfile,shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];evidence=ROOT/'validation/hardening/20261122'
OUT=ROOT.parent/'BlisterTrace_Deliverables/Hardening_20261122';OUT.mkdir(parents=True,exist_ok=True)
def jsonfile(p):return json.loads(p.read_text()) if p.is_file() else None
def rows(p):
    if not p.is_file():return []
    result=[]
    for line in p.read_text().splitlines():
        try:result.append(json.loads(line))
        except json.JSONDecodeError:break
    return result
def stats(values):
    values=sorted(float(v) for v in values if v is not None and math.isfinite(v))
    if not values:return None
    def percentile(q):
        x=(len(values)-1)*q;lo=int(x);hi=min(lo+1,len(values)-1);return values[lo]+(values[hi]-values[lo])*(x-lo)
    return dict(n=len(values),mean=statistics.mean(values),median=statistics.median(values),p95=percentile(.95),p99=percentile(.99),std=statistics.pstdev(values))
qualities={}
for name,path in [('1b_baseline',ROOT/'validation/hardening/quality_1b_baseline/cases.jsonl'),('3b_baseline',evidence/'quality_3b/cases.jsonl'),('1b_adaptive_v1',evidence/'quality_1b_adaptive_v1/cases.jsonl')]:
    rr=rows(path)
    if not rr:continue
    valid=[r for r in rr if r['expected']=='bounded_advice'];warm=[r for r in valid if r['case_id']!=1];stages={}
    for key in ['callback_ttft_ms','prefill_ms','tokenization_ms','request_total_ms']:
        stages[key]=stats([r.get('result',{}).get('runtime_metrics',{}).get(key) for r in warm])
    decode=[];rss=[];cpu=[];temp=[];swap=[]
    for r in valid:
        m=r.get('result',{}).get('runtime_metrics',{});duration=m.get('inference_end_ms',0)-m.get('first_token_ms',0)
        if duration>0 and m.get('generated_tokens',0)>1:decode.append((m['generated_tokens']-1)*1000/duration)
        for sample in r.get('resources',[]):
            rss.append(sample['rss_mib']);cpu.append(sample['process_cpu_percent']);temp.append(sample['temperature_c']);swap.append(sample.get('swap_bytes',0))
    qualities[name]=dict(complete=len(rr)==50,total_scenarios=len(rr),bounded_cases=len(valid),validated=sum(r.get('result',{}).get('status')=='llama_validated' for r in valid),fallbacks=sum(r.get('result',{}).get('status')=='fallback' for r in valid),
        decision_preserved=all(r.get('decision_preserved',True) for r in rr),elapsed_ms=stats([r['elapsed_ms'] for r in warm]),stages=stages,decode_tps=stats(decode),peak_rss_mib=max(rss) if rss else None,process_cpu_percent=stats(cpu),temperature_c=stats(temp),peak_swap_bytes=max(swap) if swap else None,human_review_complete=False,
        scope='Automated schema/evidence/SOP guard acceptance, NOT human-judged recommendation accuracy. Warm advisory cases vary by scenario.')
matrices={}
for name,path in [('1b_idle',ROOT/'validation/hardening/matrix/trials.jsonl'),('1b_concurrent',evidence/'matrix_concurrent_validated/trials.jsonl'),('3b_pilot',evidence/'matrix_3b_pilot/trials.jsonl')]:
    rr=rows(path);matrix=[]
    for active in [False,True]:
      for threads in [1,2,3,4]:
       for length in ['short','medium']:
        selected=[r for r in rr if r['concurrent_hailo_db']==active and r['threads']==threads and r['prompt_size']==length]
        if name=='1b_idle':selected=[r for r in selected if not active]
        if not selected:continue
        valid_load=not active or all(not r['load_errors'] and r['load_calls']>0 for r in selected)
        matrix.append(dict(threads=threads,active_hailo=active,prompt_size=length,load_valid=valid_load,failures=sum(bool(r['error']) for r in selected),**(stats([r['elapsed_ms'] for r in selected if not r['error']]) or {})))
    matrices[name]=matrix
report={'quality':qualities,'timing_matrices_ms':matrices,'target':jsonfile(evidence/'target/report.json'),'usb':jsonfile(evidence/'usb/report.json'),
        'restart':jsonfile(evidence/'restart/report.json'),'model_selection':jsonfile(evidence/'model_selection.json'),
        'native_json_boundary':jsonfile(evidence/'json_boundary/report.json'),
        'automated_tests':jsonfile(evidence/'tests/summary.json'),
        'browser_target':jsonfile(evidence/'browser_target/report.json'),
        'windows':jsonfile(evidence/'windows/report.json'),
        'historical_detector_scope':'Previous21Nov detector-only measurements retained separately; no new accuracy or camera-FPS inference.'}
selection=report.get('model_selection') or {}
for name,q in qualities.items():
    if name=='1b_adaptive_v1' and 'selected_accepted' in selection:q['final_guard_accepted']=selection['selected_accepted']
    elif name in selection.get('other_candidate_final_guards',{}):q['final_guard_accepted']=selection['other_candidate_final_guards'][name]['accepted']
(OUT/'BENCHMARKS.json').write_text(json.dumps(report,indent=2))
with (OUT/'BENCHMARKS.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=['candidate','threads','active_hailo','prompt_size','load_valid','failures','n','mean','median','p95','p99','std']);writer.writeheader()
    for name,rr in matrices.items():
        for r in rr:writer.writerow(dict(candidate=name,**r))
fig,axs=plt.subplots(1,2,figsize=(11,4),layout='constrained');names=list(qualities)
axs[0].bar(names,[qualities[n]['elapsed_ms']['median']/1000 if qualities[n]['elapsed_ms'] else 0 for n in names],color=['#168a99','#8162ad','#3f9567'][:len(names)]);axs[0].set_ylabel('Warm advisory median (s)');axs[0].set_title('Same scenario set; timings include validation')
axs[1].bar(names,[qualities[n].get('final_guard_accepted',qualities[n]['validated']) for n in names],color=['#168a99','#8162ad','#3f9567'][:len(names)]);axs[1].set_ylabel('Automated accepted responses');axs[1].set_title('Final guards where revalidated; human review outstanding')
for ax in axs:ax.tick_params(axis='x',rotation=15);ax.spines[['top','right']].set_visible(False)
fig.savefig(OUT/'model_comparison.png',dpi=160);plt.close(fig)
lines=['# Hardening evidence — 22 November 2026','','## Automated advisory comparison','', '| Candidate | Scenarios | Bounded cases | Experiment accepted | Final guard accepted | Warm median seconds |','|---|---:|---:|---:|---:|---:|']
for n,q in qualities.items():
    seconds=f"{q['elapsed_ms']['median']/1000:.3f}" if q['elapsed_ms'] else 'pending'
    lines.append(f"| {n}{'' if q['complete'] else ' (INCOMPLETE)'} | {q['total_scenarios']} | {q['bounded_cases']} | {q['validated']} | {q.get('final_guard_accepted','not replayed')} | {seconds} |")
lines += ['', 'These are schema/evidence/SOP guard results, not pharmaceutical accuracy or completed human semantic review. See BENCHMARKS.json for independent native stages and resource measurements. First process-load request is excluded from warm elapsed summaries.', '', '## Frozen vision evidence', '', 'Previous detector-only results: Hailo15.197ms mean,65.789images/s; ONNX580.115ms mean. These historical measurements are NOT USB camera FPS. Model and threshold hashes are verified separately.', '', '## Timing matrix scope', '', '1B:30trials per thread/load condition, split across short/medium prompts.3B:6trials per condition (3per prompt size),48trials total; this is a bounded pilot. Pilot P95/P99 values are descriptive small-sample statistics, not robust tail estimates. Failed21Nov concurrent trials are preserved but excluded from valid concurrency claims.']
if report['model_selection']:lines+=['','## Model selection','',report['model_selection'].get('reason','See model_selection.json')]
lines+=['','## Final deployed runtime','',
    'The final native worker stops at the first complete top-level JSON object and still applies all schema and evidence/claim checks. Five native boundary tests passed. This change followed the paired50-case benchmark; those acceptance rates are not relabeled as new-worker measurements. The final production integration returned validated advice, retained the detector decision and recorded raw untrusted generation text separately.',
    'Actual final integration: '+str(round((report.get('target') or {}).get('image_api_ms',0),3))+'ms for one image API request; '+str((report.get('target') or {}).get('advisory',{}).get('elapsed_ms'))+'ms for its cold advisory including worker load. These are individual samples, not means or FPS estimates.',
    'USB: Lenovo FHD Webcam on /dev/video0. Acquisition/fresh-frame snapshot was physically exercised. Scene labels were unavailable, so no camera accuracy or validated production PASS claim follows. Existing unvalidated profiles remain WARNING/REVIEW instead of being forced SAFE.',
    'Automated Python tests, local and real-Pi browser checks, Windows packaged integration, abrupt restart recovery and SQLite writer-lock/spool replay evidence are retained under raw_evidence/. Browser screenshots reflect the real Pi service through a laptop browser, not measured Pi rendering FPS.']
for name in ['target','usb','restart']:
    value=report.get(name)
    if value:lines+=['',f'## {name.title()} validation','',f"Recorded pass: {value.get('passed')}. Scope: {value.get('scope','See raw report')}."]
lines += ['', '## Reproduction', '', 'Run the scripts in tools/ against the preserved environment; keep raw JSONL and resource samples. No CSI, vision retraining or threshold tuning is part of this work. Full installation/recovery and demo steps are in docs/. No industrial regulatory certification is claimed.']
lines += ['', '## Delivered architecture and changes', '',
    'USB / stored image -> frozen YOLOv8s HEF through HailoRT -> deterministic decision -> durable inspection record / SQLite WAL / hash-chain audit. A separate bounded asynchronous queue sends immutable evidence plus the selected demo SOP clause to the persistent1B ExecuTorch Arm worker; validated advice or explicit fallback is attached without changing the inspection decision. EfficientAD-S remains an independent ONNX CPU branch with heatmaps.',
    'Both dashboard designs are preserved. The operations workspace adds real batch creation/selection/closure, role-based local accounts, PDF/CSV/JSON reports, verified audit history, immutable QA notes and advice retry history, system health and persistence monitoring. Storage hardening includes exact source-byte retention, consumed-pixel hashes, atomic spool/replay, consistent database snapshots, bounded backpressure and tested restart recovery.',
    'CHANGES.json lists added/modified files against the saved baseline. MODEL_MANIFEST.json records artifact hashes and challenger provenance. final_runtime_manifest.json records the deployed worker, shared library, tokenizer, settings and active service. Export reference, raw JSONL, resource samples, screenshots, diagrams and an unscored human-review worksheet are included. Large model files and credentials are excluded from the handoff ZIP; they remain in the preserved installation.',
    '', '## Start and recover', '', 'On the Pi run `~/blistertrace`, or `~/blistertrace-b` for the classic layout. The service is `blistertrace.service`; use `systemctl --user restart blistertrace.service` to recover it. Local URL: `http://127.0.0.1:8765`. Laptop access: `ssh -L 8765:127.0.0.1:8765 saul@10.217.96.233`, then the same local URL. See docs/INSTALLATION.md for the locally stored administrator credential and interactive password change.',
    '', '## Remaining acceptance work', '', 'Human semantic review and approved manufacturing SOPs are outstanding. The local capture/product profile is unvalidated, so no-defect images remain WARNING/REVIEW rather than being forced SAFE. Healthy specificity, labeled local-camera accuracy, long-shift endurance, power/energy and NPU utilization are not established. Windows Llama requires WSL. Nothing here is regulatory certification.']
(OUT/'REPORT.md').write_text('\n'.join(lines),encoding='utf8');print(str(OUT))
