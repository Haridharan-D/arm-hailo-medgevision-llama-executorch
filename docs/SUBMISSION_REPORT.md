# MEDGE VISION — final submission engineering report

24 November 2026. Authoritative current target acceptance; earlier reports retain their original dates and are not rewritten as fresh measurements.

## Current acceptance

PASS: original project-specific private recovery archive transferred to laptop, archive SHA256 and all 1,862 unique files verified; post-validation delta of 49 changed/new files independently verified. PASS: frozen deployment models preserved; no retraining or requantization. PASS: exact original aarch64 worker and library are now included in verified Git parts. PASS: audited release runs on actual Pi, Hailo backend active. PASS: 73 regression tests on target. PASS: all eight selected demo outcomes matched. PASS: eight genuine llama_validated responses, no cached response reuse. Authentication remains disabled by owner request, loopback-only kiosk; this is not authenticated multi-user deployment.

NOT TESTED: new USB/CSI camera acquisition in this run, monitor placement after this release, long-shift endurance, production camera/product generalization, approved production SOP, clinical severity and regulatory release readiness. NOT TESTED: Drive publication (no upload connector/file IDs) and fresh Windows EXE packaging. The private backup is project recovery, not a complete sector image or a guarantee of bit-identical OS restoration.

## Actual eight-case target execution

- Case 1: hailo; SAFE; no configured defect; vision 36.98 ms; QA REVIEW; advisory llama_validated in 11727.8 ms; no cache reuse.
- Case 2: hailo; DEFECTIVE; crack; vision 15.04 ms; QA HOLD; advisory llama_validated in 9970.1 ms; no cache reuse.
- Case 3: anomaly_onnx_cpu; SAFE; anomaly score 0.07296938449144363 vs 0.35005301237106323; vision 2086.81 ms; QA REVIEW; advisory llama_validated in 7551.8 ms; no cache reuse.
- Case 4: anomaly_onnx_cpu; DEFECTIVE; anomaly score 0.6374081373214722 vs 0.35005301237106323; vision 1321.32 ms; QA REVIEW; advisory llama_validated in 8828.1 ms; no cache reuse.
- Case 5: anomaly_onnx_cpu; SAFE; anomaly score 0.04846011474728584 vs 0.2682838439941406; vision 1726.36 ms; QA REVIEW; advisory llama_validated in 7599.4 ms; no cache reuse.
- Case 6: anomaly_onnx_cpu; DEFECTIVE; anomaly score 3.637528657913208 vs 0.2682838439941406; vision 1327.58 ms; QA REVIEW; advisory llama_validated in 9105.7 ms; no cache reuse.
- Case 7: anomaly_onnx_cpu; SAFE; anomaly score 0.12400093674659729 vs 0.20281894505023956; vision 1736.21 ms; QA REVIEW; advisory llama_validated in 8221.1 ms; no cache reuse.
- Case 8: anomaly_onnx_cpu; DEFECTIVE; anomaly score 2.262270212173462 vs 0.20281894505023956; vision 1410.25 ms; QA REVIEW; advisory llama_validated in 9830.6 ms; no cache reuse.

Fresh advisory median 8966.9 ms; range 7551.8–11727.8 ms. Aggregate service-tree peak RSS 1977.1 MiB and peak summed CPU 302.6% (100% = one logical core). Shared memory may be counted twice in summed RSS. These are full service-tree measurements, not Llama-only memory. Regression/dependency validation overlapped this run; timing is therefore an observed demo result, not a controlled optimal performance benchmark. Full samples and source inspection JSON are in evidence/target_20261124/eight_test_report.json.

## Frozen decisions and deployment changes

CPU and Hailo share letterbox geometry, RGB channel handling and reverse coordinate mapping. CPU divides float input by 255; Hailo consumes uint8 RGB with compiled normalization. Input/output contracts, model/tokenizer hashes and native worker/library architecture now fail closed. Advisory defaults are adaptive-v1, three threads, 128 output tokens and 1536-token prompt budget under the actual 2048 graph capacity. Severity explanations name the conservative rule without inventing medical severity. QA decisions, fixed thresholds, SQLite evidence and append-only QA/advice histories remain separate from advisory text.

## Historical comparisons retained without fabrication

Original CPU mean vision latency 580.115 ms versus Hailo 15.197 ms, approximately 38.17x backend speed ratio, from differently sized repeated-image trials. This is not production camera FPS. Original Llama baseline median 15.156 s versus adaptive-v1 8.071 s; historical adaptive peak RSS 1598.55 MiB. Preserve the warm/cold, concurrency and sampling boundaries in the raw BENCHMARKS.json. Today's eight-case execution is a separate experiment.

Original YOLO FP32 held-out console mAP50 0.992 / mAP50-95 0.892, with no negative test images. Eight-image FP32 raw-tensor export parity passed. Historical INT8 agreement precision 0.9487 / recall 0.9737 is unannotated model agreement, not defect accuracy. Quantized held-out ground-truth accuracy delta is NOT TESTED; no accuracy-after-quantization prediction is claimed. Original anomaly recalls were pill 85.82%, capsule 79.82%, VisA 24%; VisA remains a weak research candidate despite selected demos matching.

## End-to-end reproduction

Use QUICKSTART.md for installation, verified model reconstruction and download, vendor Hailo prerequisites, exact native artifact or pinned source build, service setup, terminal tests and both dashboard designs. On matching aarch64 Debian Trixie, verification reconstructs the shipped instrumented worker and library; configuration discovers them. Other OS/glibc versions may need the pinned source build. Native ELF matching alone does not prove ABI compatibility; a successful genuine target generation is the execution check.

After setup, run ~/medge-test for all eight demonstrations and summary; ~/medge-vision opens the dashboard separately. These samples are selected demonstrations, not a statistical accuracy benchmark. See docs/MODEL_LIFECYCLE.md for original training/export/conversion references and external datasets/calibration/vendor dependencies. No training is needed to reproduce inference.

## Preservation and limitations

Private backup: C:/Arm_B_PS5/Arm_Hailo_Models/Pi_Recovery_20261124, original archive plus post-validation delta and manifests. Credentials and private inspection databases are deliberately excluded from GitHub. Keep that laptop backup and the original model folder. Project-specific files are now recoverable independently of this SD card; an identical bootable SD image was not made. Any inspections performed after the delta snapshot require another backup before erasure.

Historical documents that say Pi validation or project backup was pending describe the earlier state; this report and target_20261124 evidence supersede those pending items only. Drive, camera/endurance and pharmaceutical approval gaps remain open. This is a measured research demonstrator, not a certified pharmaceutical release system.


## Complete evidence gallery and portable recovery — final addition

The repository now contains 47 actual Pi screenshots, indexed in evidence/gallery/README.md. They cover all eight cases in the real Chromium dashboard, image/heatmap plus validated Llama panel, lower advisory content, intro, history, SOP, audit, health and current secondary verdict. Twenty-five physical-terminal screenshots cover all eight original measured records in three pages each plus the summary. The terminal is explicitly labelled recorded-output replay; these screenshots are not represented as a second model run. Original record IDs and unchanged JSON outputs link images to the measured target run.

The included portable backup consists of BUNDLE_MANIFEST.json and five numbered recovery parts under backups/. Restore with tools/restore_demo_backup.py into a new directory. Verification includes each part hash, full archive hash, all member hashes, SQLite integrity, audit-chain integrity and all eight image identities. It restores eight records, their annotated/original/source images, six heatmap/raw-map pairs and recorded advice. It has a NEW import audit chain; the original full station chain remains in the private archive. No account credentials, passwords or unrelated private history are published. The full private station archives are retained on the laptop with their verified manifests and restoration instructions.

The added recovery regression cases cover a successful verified restore, refusal to overwrite existing data, corrupt-part rejection and traversal rejection. Total regression suite is now 76 passed on the Pi and 76 passed on the laptop. This adds recovery tests to the earlier 73-test evidence; it does not change the eight-case inference results or fabricate new hardware measurements. The actual portable bundle was restored and verified on the laptop, and the CI workflow now repeats restoration plus real CPU smoke inference from the published repository.

For judges, begin at README.md, open the evidence gallery, follow QUICKSTART.md, and inspect the recovery instructions in backups/README.md. Initial downloads/installations require internet; inference after provisioning uses local artifacts. Large Llama artifacts use the pinned verified downloader. Drive publication is still not claimed without working file IDs/upload access.
