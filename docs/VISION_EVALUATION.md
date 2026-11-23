# Frozen vision evaluation

No vision training, weight/HEF compilation, threshold change, preprocessing change or NMS change is part of this release. YOLOv8s uses seven established labels: black_dot, broken, color_mismatch, crack, dual_cap, empty, foreign_particle. RGB640 letterbox, per-class thresholds and classwise IoU0.7 NMS remain frozen. Hailo exposes seven-class NMS output through HailoRT; ORT provides the reference path. Hailo absence does not silently select CPU or yield an acceptable result.

Historical FP32 held-out evaluation:1303 images,2956 boxes, mAP50~0.9922, mAP50:95~0.8919. **Zero healthy test images** prevents false-hold specificity estimation. No physical strip identifiers were supplied. These data do not establish generalization to the connected USB camera, unseen SKU, drug identity, chemical safety or production throughput. Frame-derived grouping does not prove physical independence.

The historical FP32/INT8 comparison of18 demonstration images contains37 matched detections,2 INT8-only and1 FP32-only. It measures reference agreement, not ground-truth accuracy after quantization. No accuracy prediction is substituted for annotated target testing.

EfficientAD-S is an independent ONNX CPU anomaly branch; it is not EfficientNet and is not currently running on Hailo. MVTec pill/capsule and VisA capsules are category-specific. VisA retained image AUROC~0.650 and weak recall make that profile research/demo-only. Auxiliary anomaly flags never clear existing HOLD decisions, and dataset labels are not passed into Llama as observations. Selected20-image demo libraries per category are not substitutes for the retained full evaluation. MVTec data retains noncommercial licensing terms.

USB camera acquisition/inference metrics in the new target report describe the observed scene and hardware path only. Without labeled blister-strip samples they establish functionality and timing, not camera-domain detection accuracy. CSI testing is excluded.
