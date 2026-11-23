# Judge-facing demonstration

## What the system does

Medge Vision inspects pharmaceutical pack images locally. YOLO localizes seven configured defect classes. Three independent EfficientAD-S category models produce anomaly scores and heatmaps. Vision runs through HailoRT on Hailo-8 when installed, with an explicit ONNX CPU mode for development. ExecuTorch Llama runs separately on the Arm CPU and drafts bounded SOP-grounded advice. It never changes the detector or recorded QA disposition.

## Three-minute walkthrough

1. After setup, run `python run.py`. Explain that installation needs internet, but models, fonts, UI and inference are local.
2. Click the intro. Show independent vision and advisory status lanes. A missing runtime must remain visibly unavailable/fallback.
3. Select YOLO demo crack and run inference. Show box coordinates, confidence, measured latency and DEFECTIVE result. The auto dialog closes after five seconds; the record remains.
4. Select the clear YOLO example. Show SAFE visual check and explain any separate QA REVIEW due to an unvalidated product profile. This is not a drug-safety certification.
5. Switch to anomaly mode, choose a model and demo image, and run the actual model. Show the score, frozen threshold and real heatmap. State that VisA is a weak research candidate.
6. Show genuine Llama advice only if status is `llama_validated`. Explain SOP citations, fallback guards and the inability to override vision. Ask an inspection-scoped question.
7. Open History and a saved record. Show evidence download and append-only QA review. Open `/display` on the second screen and show the current SAFE/WARNING/REJECTED verdict.

## Terminal alternative

Run `python tools/smoke_models.py --output smoke_results.json` for five actual CPU model inferences. Run `python -m pytest tests -q` for the regression suite. The installed station's HTTP demo tool can also request advice; see QUICKSTART.md. Do not run a second Hailo owner while the service owns the NPU.

## Evidence included

- `evidence/clone_cpu_smoke.json`: actual five-case CPU results from the organized checkout.
- `evidence/original_pi/terminal_demo.json`: earlier five-case real-Pi terminal run.
- `evidence/original_pi/display_sync.json`: earlier physical second-monitor synchronization run.
- `evidence/original_pi/station_safe.png`: actual station browser screenshot.
- `docs/REPOSITORY_VERIFICATION.md`: regression-test and backup boundaries.

These are dated observations, not evidence that a new machine or fresh build has been hardware-tested. No Pi was available during repository preparation. Power, long-shift endurance, approved production SOP, new-camera generalization and pharmaceutical release validation remain outside the demonstrated acceptance scope.
