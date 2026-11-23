"""Stage source and measured evidence in the isolated existing GitHub clone."""
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parent;REPO=PROJECT/'BlisterTrace_GitHub'

def copy_tree(source,target,skip):
    for path in source.rglob('*'):
        rel=path.relative_to(source)
        if path.is_file() and not skip(rel,path):
            dst=target/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst)

def main():
    assert (REPO/'.git').is_dir()
    forbidden={'.git','.venv','__pycache__','build','dist','llama','test_images','run_data','packaged_run_data','browser'}
    copy_tree(ROOT,REPO/'BlisterTrace_App',lambda rel,p:any(part in forbidden or (part.startswith('.') and part!='.gitignore') for part in rel.parts)
              or p.suffix.lower() in {'.onnx','.hef','.zip','.sqlite3','.pyc','.log'}
              or rel.parts[0]=='models')
    for folder in ['Llama_ExecuTorch','YOLO_v2_Annotated','Final_Submission_Training','EfficientAD_Full_Training']:
        def skip(rel,p):
            if any(part in {'.venv','__pycache__','artifacts','bin','host_validation','build','dist'} or (part.startswith('.') and part!='.gitignore') for part in rel.parts):return True
            return p.suffix.lower() in {'.pte','.pt','.pth','.onnx','.hef','.whl','.log','.pyc'} or (p.suffix=='.zip' and p.name!='embedded_source.zip')
        copy_tree(PROJECT/folder,REPO/folder,skip)
    for p in (PROJECT/'Hailo_Compiler').iterdir():
        if p.is_file() and p.name in {'compile_hef.sh','install_dfc334_py311.sh','README.md','compiler_wheel_receipt.json'}:
            target=REPO/'Hailo_Compiler'/p.name;target.parent.mkdir(exist_ok=True);shutil.copy2(p,target)
    results=REPO/'Hailo_Compiler/output';results.mkdir(exist_ok=True)
    shutil.copy2(PROJECT/'Hailo_Compiler/output/compile_receipt.json',results/'compile_receipt.json')
    (REPO/'README.md').write_text('''# BlisterTrace — Arm, Hailo and ExecuTorch\n\nOffline pharmaceutical blister-pack inspection for Bharat AI-SoC PS5.\nThe trained seven-class YOLOv8s runs through HailoRT on the Pi Hailo-8.\nLlama 3.2 1B Instruct runs independently through native ExecuTorch on the Arm CPU.\nVision and deterministic rules decide disposition; Llama drafts SOP-grounded\nactions and QA notes. A single local dashboard handles USB camera, stored images,\nuploads, evidence and inspection history. Terminal inspection is included.\n\n## Working application\n\n- [Application instructions](BlisterTrace_App/README.md)\n- [Technical report](BlisterTrace_App/TECHNICAL_REPORT.md)\n- [Measured target evidence](BlisterTrace_App/validation/)\n- [Hailo compiler workflow and actual receipt](Hailo_Compiler/)\n- [Llama native runtime and strict advisory adapter](Llama_ExecuTorch/)\n- [YOLO training notebook](YOLO_v2_Annotated/)\n- [Optional EfficientAD cloud training](EfficientAD_Full_Training/)\n\nActual checks passed on the Pi: custom HEF load/inference, USB camera stream,\ntrained model image inspection, asynchronous native Llama advice and the browser\nworkflow. One measured live run averaged about 15 application FPS with native\nLlama generating concurrently. An uploaded known-defect sample returned HOLD\nin about 0.15 seconds; advice arrived afterwards. Warm Hailo detector median was\n15.27 ms on 18 demo images. See JSON reports for scope and timings.\n\nThe actual Windows executable was also tested with real trained YOLO and bundled\nLlama through installed local WSL2/Ubuntu 24.04. Keep its entire application\nfolder; it is not a standalone native-Windows Llama runtime.\n\n## Models and releases\n\nLarge model files, compiled application dependencies and the vendor compiler\nwheel are excluded from Git. Use the release assets for the Pi application,\ntrained vision bundle, HEF and demo recording. The Pi handoff reuses the native\nLlama runtime already installed under `~/BlisterTrace/Llama_ExecuTorch`; for a\nfresh device, follow that component's README and pinned downloader. The Llama\nartifact is an upstream-linked community conversion, not team-trained weights.\nThe complete Windows build is prepared locally; model setup and build scripts\nare included in source.\n\n## Evaluation limits\n\nThe source YOLO test results are mAP50 0.992 / mAP50–95 0.892, with no healthy\nnegative test images or physical-strip group IDs. Actual FP32/INT8 comparison on\n18 training-source demonstration images matched 37/38 FP32 detections with two\nextra INT8 detections. This is agreement, not independent accuracy. The CPU-only\ncompiler calibration used 64 of 512 available training-only images, without GPU\naccuracy optimization. Independent labeled camera/SKU quality, healthy false\nholds and longer-run stability remain to be measured. Unvalidated capture\nprofiles default to REVIEW when no configured defect is seen.\n\nThe original Pi Llama v2 development evaluation accepted 33/36 responses under\nautomatic checks and used three fallbacks; all decisions were preserved. The\nshipped v3 guard additionally rejects unobserved anomaly wording identified in\ntwo capture-only review notes. This metric is not general factual accuracy or a\nfresh v3 evaluation. QA must review drafts; output checks are not a semantic\nproof. Optional EfficientAD inference is not bundled pending trained artifacts.\n\nBuilt with Llama. Preserve third-party licenses and dataset attribution included\nwith the components. The vendor DFC wheel is not redistributed here.\n''',encoding='utf8')
    ignore=REPO/'.gitignore'
    exception='!/EfficientAD_Full_Training/embedded_source.zip'
    if exception not in ignore.read_text():
        with ignore.open('a') as stream:
            stream.write('\n# Small source archive required to rebuild the self-contained training notebook\n'+exception+'\n')
    print('Source staged in',REPO)

if __name__=='__main__':main()
