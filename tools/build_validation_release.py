"""Package source, measured evidence and existing compiled artifact without inventing acceptance."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parent
OUTPUT=PROJECT/'BlisterTrace_Deliverables/v3_20261120'

def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    original=read(ROOT/'validation/20261120_cpu_csi/summary.json')
    cooled=read(ROOT/'validation/20261120_cpu_csi_cooled/summary.json')
    advisory=read(ROOT/'validation/20261120_advisory_v3/summary.json')
    browser=read(ROOT/'validation/20261120_browser/report.json')
    demo=read(ROOT/'validation/20261120_demo/report.json')
    emulator=read(PROJECT/'Hailo_Compiler/output/quantized_emulator_20261120/report.json')
    receipt=read(PROJECT/'Hailo_Compiler/output/compile_receipt.json')
    hef=ROOT/'models/blistertrace.hef'
    assert sha(hef)==receipt['hef_sha256']==emulator['hef_sha256']
    assert cooled['passed_checks']==cooled['total_checks'] and not cooled.get('error')
    assert advisory['complete'] and advisory['cases']==36
    assert browser['all_passed']
    assert demo['all_passed']
    OUTPUT.mkdir(parents=True,exist_ok=True)
    evidence=OUTPUT/'evidence';evidence.mkdir(exist_ok=True)
    for name in ['20261120_cpu_csi','20261120_cpu_csi_cooled','20261120_advisory_v3','20261120_browser','20261120_demo','20261120_terminal']:
        shutil.copytree(ROOT/'validation'/name,evidence/name,dirs_exist_ok=True,
            ignore=shutil.ignore_patterns('video') if name=='20261120_demo' else None)
    video=max((ROOT/'validation/20261120_demo/video').glob('*.webm'),key=lambda path:path.stat().st_mtime)
    shutil.copy2(video,OUTPUT/'BlisterTrace_Actual_CPU_CSI_Demo.webm')
    if (ROOT/'validation/20261120_unit_tests.json').exists():
        shutil.copy2(ROOT/'validation/20261120_unit_tests.json',evidence/'unit_tests.json')
    emuout=evidence/'quantized_emulator';emuout.mkdir(exist_ok=True)
    shutil.copy2(PROJECT/'Hailo_Compiler/output/quantized_emulator_20261120/report.json',emuout/'report.json')
    shutil.copy2(hef,OUTPUT/'blistertrace.hef')
    shutil.copy2(PROJECT/'Hailo_Compiler/output/compile_receipt.json',OUTPUT/'compile_receipt.json')
    shutil.copy2(ROOT/'SUBMISSION_RUNBOOK.md',OUTPUT/'SUBMISSION_RUNBOOK.md')
    if (PROJECT/'EffNet_Kaggle/MODEL_AUDIT.md').exists():
        shutil.copy2(PROJECT/'EffNet_Kaggle/MODEL_AUDIT.md',OUTPUT/'OPTIONAL_ANOMALY_AUDIT.md')
    # Retain the frozen benchmark metadata, not a new evaluation or a modified test split.
    with zipfile.ZipFile(PROJECT/'BlisterTrace_Deliverables/BlisterTrace_Frozen_Vision.zip') as archive:
        frozen=evidence/'frozen_yolo_source';frozen.mkdir(exist_ok=True)
        for name in ['test_metrics.json','frozen_evaluation.json','readiness.json','source_attribution.json','training_complete.json']:
            (frozen/name).write_bytes(archive.read('YOLO_Model/v2/'+name))
    package=OUTPUT/'BlisterTrace_Pi_Source_20261120.zip'
    files=[]
    for name in ['main.py','config.json','README.md','SUBMISSION_RUNBOOK.md',
                 'TERMINAL_TESTS.md','deploy/install_pi.sh','deploy/launch_pi.sh','deploy/install_hailo_pi.sh','requirements.txt','asset_hashes.json']:
        path=ROOT/name
        if path.is_file():files.append(path)
    for folder in ['app','web','advisor_src','assets','models','test_images','tools','tests']:
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    m=cooled['phases'];resource=cooled['resource_summary']['csi_camera_concurrent_llama']
    readiness={'created_utc':datetime.now(timezone.utc).isoformat(),
        'cpu_csi_checks_passed':cooled['passed_checks'],'cpu_csi_checks_total':cooled['total_checks'],
        'browser_checks_passed':sum(browser['checks'].values()),'browser_no_external_requests':not browser['external_requests'],
        'recorded_demo_checks_passed':sum(demo['checks'].values()),
        'recorded_image_advice_status':demo['image_record']['advice']['status'],
        'compiled_hef_verified':True,'hef_sha256':sha(hef),'current_hailo_attached':False,
        'current_hailo_target_quality_verified':False,'camera_accuracy_verified':False,
        'quantized_accuracy_prediction':None,'emulator_agreement_recall':emulator['agreement_recall'],
        'emulator_agreement_precision':emulator['agreement_precision'],
        'llama_evaluation':advisory,'full_target_acceptance_complete':False,
        'software_handoff_prepared':True,'llama_model_and_runtime':'Reuse verified native artifacts already installed on Pi',
        'optional_anomaly_installed':False,'github_published_this_run':False,
        'physical_blister_in_camera_test':False,
        'remaining_acceptance':['Attach Hailo and run ~/blistertrace-hailo',
            'Labeled independent FP32/INT8 camera product evaluation with healthy packs',
            'Authorized QA semantic review of generated drafts']}
    terminal=read(ROOT/'validation/20261120_terminal/report.json')
    readiness['terminal_inspection_passed']=terminal['inspection'].get('advisory_status')=='llama_validated' and terminal['inspection'].get('backend')=='onnx'
    (OUTPUT/'READINESS.json').write_text(json.dumps(readiness,indent=2)+'\n')
    text=f'''# BlisterTrace measured target report — 20 November 2026

The current Pi 5 has 16 GB RAM and an IMX219 CSI camera. Vision runs through ONNX Runtime CPU today because Hailo is disconnected. Llama 3.2 1B Instruct SpinQuant INT4 EO8 runs through the native Arm ExecuTorch worker, independently of vision. The seven-class Hailo-8 HEF is already compiled and checksum-matched. The configured profile remains unvalidated; Llama cannot change disposition.

## Actual current-board results

| Measurement | Result | Scope |
|---|---:|---|
| Pipeline checks | {cooled['passed_checks']}/{cooled['total_checks']} | Actual image/CSI/API/Llama/export/review checks |
| Browser checks | {sum(browser['checks'].values())}/{len(browser['checks'])} | Live Pi API, browser rendered on laptop |
| Recorded end-to-end demo checks | {sum(demo['checks'].values())}/{len(demo['checks'])} | Actual image inference, advisory and CSI snapshot |
| Warm CPU detector median | {m['cpu_detector']['vision_ms']['p50']:.2f} ms | 18 unannotated training-source demo images |
| Warm CPU detector p95 | {m['cpu_detector']['vision_ms']['p95']:.2f} ms | Stage latency, not full inspection |
| Image API median | {m['image_api_llama']['image_response_ms']['p50']:.2f} ms | 3 real requests, before advice |
| CSI application FPS mean | {m['csi_camera']['rolling_application_fps']['mean']:.3f} | Warm rolling estimates, concurrent Llama |
| CSI detector median | {m['csi_camera']['detector_ms']['p50']:.2f} ms | Includes detector lock contention |
| App mean PSS | {resource['app_pss_mib']['mean']:.2f} MiB | CSI/concurrent phase |
| Llama mean PSS | {resource['llama_pss_mib']['mean']:.2f} MiB | CSI/concurrent phase |
| Peak temperature, cooled run | {resource['temperature_c']['max']:.2f} C | Actual SoC sensor |
| Current adviser accepted | {advisory['validated_llama_responses']}/{advisory['cases']} | Automatic schema/SOP/content checks |
| Explicit adviser fallbacks | {advisory['fallbacks']} | Rejected generation replaced by SOP fallback |
| Detector decisions preserved | {advisory['decision_preserved']} | 36 synthetic advisory fixtures |
| Terminal diagnostic inspection | {terminal['inspection']['advisory_status']} | Real stored-image HOLD, {terminal['inspection']['vision_ms']} ms CPU vision |

The initial pre-cooling concurrent run reached 84.8 C and about 0.928 rolling application FPS. The user then connected a running active fan. Raw evidence preserves both runs, rather than mixing their resource measurements. The inspected CSI snapshot showed a mug rather than a blister pack, and the user confirmed a strip could not be positioned for this run. CSI results therefore establish capture/integration and performance only, not actual blister defect recognition or healthy-pack specificity. Process CPU uses 100% per logical core; system CPU uses 0–100%. Electrical watts, per-stage NPU counters and true token throughput were not measured.

## Quantization and quality

DFC SDK_QUANTIZED software emulation matched {emulator['agreement_matches']} of {emulator['agreement_matches']+emulator['fp32_only']} FP32 detections at same-class IoU 0.5 on 18 demo images. There were {emulator['int8_only']} INT8-only detections and {emulator['fp32_only']} FP32-only detections. Agreement precision was {emulator['agreement_precision']:.3%}; agreement recall was {emulator['agreement_recall']:.3%}. These are not ground-truth accuracy, defect recall or mAP. Software emulation is not a current NPU execution test or a guaranteed bit-exact forecast of hardware behavior.

The retained historical actual-Hailo demo agreement was 37/38 FP32 matches with two additional detections; that older result is separate from today's software emulator. The frozen source test reported mAP50 0.992 and mAP50–95 0.892. It had no healthy negative test images and no physical-strip group IDs. Neither source scores nor demo agreement predict independent local-camera INT8 accuracy. No numeric accuracy forecast is supplied.

The compiled HEF uses DFC {receipt['compiler']}, Model Zoo {receipt['model_zoo']}, Hailo-8, and {receipt['actual_calibration_entries']} actual calibration entries from 512 available training-only images, at optimization level zero. SHA256: `{sha(hef)}`. The target activation command checks the checksum, actual device and inference before switching configuration. It refuses safely when Hailo is absent and records failures.

`tools/evaluate_labeled.py` supplies matched frozen-threshold precision/recall and healthy-image false-hold evaluation for FP32 and Hailo. It requires explicit YOLO box labels for every image, including empty files for labeled healthy images. Results are operating-point metrics, not an mAP sweep. Test independence remains a data/protocol requirement.

## Advisory and course process

The 36-case evaluation uses the application's actual adviser version `{advisory['advisor_version']}` and records model/runtime/SOP/source hashes. Cases are synthetic observation records, not images. Automatic validation checks JSON, cited clauses/actions and bounded claims; it does not establish unrestricted factual correctness. Drafts still need authorized QA review. The vision alert and persisted disposition arrive before advice.

The saved Arm course's workflow is applied: freeze input/output contracts; preserve preprocessing; retain model/export provenance; transfer verified artifacts; benchmark on the target; compare quality before and after quantization; integrate asynchronous application handling. ExecuTorch `.pte` advisory remains separate from HailoRT/HEF vision. Ethos-U/Vela/FVP course material is not presented as a Hailo conversion mechanism. Module references are in `web/COURSE_ALIGNMENT.md` and `SUBMISSION_RUNBOOK.md`.

## Delivery and remaining acceptance

Application source, compiled HEF, measured JSON/CSV, browser recording/screenshots, frozen source benchmark metadata and this report are staged together. The source package reuses the native Llama artifact/runtime already on this Pi. Windows continues to use its existing `.exe` plus local WSL runtime; this release does not claim a new native Windows Llama build.

The optional EfficientAD category models are audited separately and are not installed in the camera pipeline. No AnomalyCLIP validation/deployment is claimed. No GitHub push was performed.

Run `~/blistertrace` now. After powering off, attaching Hailo and booting with cooling, run `~/blistertrace-hailo`. Full target acceptance remains pending actual connected-Hailo evaluation, independent labeled camera/product quality, and QA review. `READINESS.json` retains those pending states explicitly.
'''
    (OUTPUT/'TECHNICAL_REPORT.md').write_text(text,encoding='utf8')
    (ROOT/'validation/20261120_FINAL_REPORT.md').write_text(text,encoding='utf8')
    (ROOT/'validation/20261120_readiness.json').write_text(json.dumps(readiness,indent=2)+'\n')
    for folder in ['20261120_cpu_csi','20261120_cpu_csi_cooled','20261120_advisory_v3','20261120_browser','20261120_demo','20261120_terminal']:
        files.extend(p for p in (ROOT/'validation'/folder).rglob('*') if p.is_file() and p.suffix in {'.json','.csv'})
    with zipfile.ZipFile(package,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as archive:
        for path in sorted(set(files)):archive.write(path,'BlisterTrace_App/'+path.relative_to(ROOT).as_posix())
        archive.writestr('BlisterTrace_App/TECHNICAL_REPORT.md',text)
        archive.writestr('BlisterTrace_App/validation/20261120_FINAL_REPORT.md',text)
        archive.writestr('BlisterTrace_App/validation/20261120_readiness.json',json.dumps(readiness,indent=2))
    with zipfile.ZipFile(package) as archive:assert archive.testzip() is None
    recipes=OUTPUT/'YOLO_Training_Recipe.zip'
    with zipfile.ZipFile(recipes,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in (PROJECT/'YOLO_v2_Annotated').iterdir():
            if path.is_file() and path.suffix in {'.ipynb','.py','.md','.json'}:
                archive.write(path,'YOLO_v2_Annotated/'+path.name)
    manifest={str(p.relative_to(OUTPUT)).replace('\\','/'):{'bytes':p.stat().st_size,'sha256':sha(p)}
        for p in sorted(OUTPUT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'}
    (OUTPUT/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'output':str(OUTPUT),'files':len(manifest),'source_package_bytes':package.stat().st_size,'readiness':readiness},indent=2))

if __name__=='__main__':main()
