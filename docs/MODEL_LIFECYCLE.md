# Models: training, export, deployment and interpretation

## Exact deployment, without retraining

Install via QUICKSTART.md. Reassemble ONNX blobs and verify their hashes. Use the supplied Hailo-8 HEF for the original compiled deployment. Download the exact 1B SpinQuant artifact with the pinned recipe. Native build is on the target architecture. Run the model smoke tests, then camera and target-resource validation on actual hardware. Deployment does not retrain or alter thresholds.

## YOLOv8s

Seven classes: black_dot, broken, color_mismatch, crack, dual_cap, empty, foreign_particle. Saved training arguments: 150 maximum epochs, patience 25, batch 8, 640 input, AdamW, seed 42. Original per-epoch results and arguments are retained under evidence/historical/yolo_results.csv and yolo_args.yaml. Maximum epochs are not the number actually executed: count the saved results rows. Historical training console reported 134 epochs / 3.232 hours; this is historical console evidence, not new execution. Training notebook/helper copies are under reproduction/yolo; original training datasets/annotations are not distributed in this Git repository.

FP32 ONNX: static [1,3,640,640], output [1,11,8400], opset 11. Export status records raw-tensor parity on eight validation images. CPU and Hailo use the same OpenCV resize, aspect-preserving 114-padding letterbox, BGR-to-RGB conversion and reverse box mapping. CPU converts RGB uint8 to NCHW float /255. Hailo receives NHWC RGB uint8 because compiled normalization is owned by the HEF. Never apply /255 on the host twice. NMS/quantization can change borderline results; shared preprocessing does not prove equal accuracy.

The saved Hailo recipe uses licensed DFC/Model Zoo on Linux x86-64, seven classes, six YOLO head end nodes, Hailo-8 architecture and the 512-image training-only calibration manifest. Calibration inputs are an external prerequisite; never substitute held-out test samples. Run reproduction/hailo/compile_hef.sh only in a suitable licensed compiler environment with MEDGE_CALIBRATION set. Preserve calibration provenance and log/compiler version. This audit did not compile or requantize the model.

Original labeled FP32 held-out evaluation had 1,303 images / 2,956 defect instances. Console mAP50 0.992 and mAP50-95 0.892; retained test_metrics.json additionally records the class-threshold operating point. No negative images existed in that original test, so specificity and healthy false-reject rate were not established. Int8 hardware matching statistics are in METRICS.json and have different, unannotated data scope. Before/after quantization ground-truth accuracy delta remains NOT TESTED; do not subtract those agreement figures from mAP.

## EfficientAD-S, not EfficientNet

Three independent category models: MVTec pill, MVTec capsule, VisA capsules. Contracts record 70,000 FP32 steps, batch size 1 and fixed thresholds. Each has teacher/student plus autoencoder; normalization and map alignment are inside the ONNX graph. Host supplies resized RGB float [0,1]; do not normalize twice. Output is an actual anomaly map and scalar score, not a probability or a diagnosed defect class. They run on CPU, not in the YOLO Hailo HEF.

Historical recalls: pill 85.82%, capsule 79.82%, VisA 24%. VisA is a weak research candidate. Full metadata and original checkpoint audit are in reproduction/anomaly; small early recovery checkpoints are not the final 70,000-step checkpoints. Selected demonstration cases do not replace the complete held-out evaluation. Do not tune deployment thresholds from those selected examples.

## ExecuTorch Llama

The 1B artifact is an upstream-linked pre-exported SpinQuant INT4 EO8 model, not a newly trained team LLM. Exact identity/export configuration and XNNPACK delegation evidence are described in docs/LLAMA_EXECUTORCH_OPTIMIZATION.md and the pinned artifact recipe. No fresh LLM training, requantization or LoRA fine-tune is claimed. Production defaults are adaptive-v1, three CPU threads, 128 output tokens and a 1536-token prompt budget under the actual 2048 context. Camera+CPU vision reduces advisory thread use through the existing scheduler. Persistent workers avoid repeated model loads; bounded queue/cache retain provenance. This audit adds model/tokenizer and architecture verification without pretending a newly built binary has the old binary hash.

Llama advises only on recorded inspection facts and demo SOP clauses. JSON/schema/evidence guards, explicit fallback and append-only history remain. QA determines disposition. Clinical root cause, approved SOP compliance and production release are not established by a plausible generated explanation.

## What a new replicator must supply

A 64-bit machine, Python environment and disk space; Hailo-8 and matching vendor runtime for NPU execution; licensed native-build prerequisites and Llama license acceptance; camera and lighting for a real capture test. Download/install first, then inference is fully local. Training reproduction additionally needs licensed datasets and original split/calibration manifests. Drive mirror publication is pending; docs/DRIVE_MIRROR.md gives the verified adapter and missing-file-ID boundary.
