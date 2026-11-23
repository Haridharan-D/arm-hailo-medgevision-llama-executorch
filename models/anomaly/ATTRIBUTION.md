# EfficientAD deployment artifacts

These are FP32 CPU ONNX exports of the team's three audited EfficientAD-S checkpoints. Model/source hashes, original thresholds, input ownership and benchmark limits are retained in each profile's `contract.json`. The small PDN teacher/student and feature autoencoder source came from the packaged training implementation, adapted from nelson1425/EfficientAD revision fcab5146f84ae17597044ad5ddf1656ccf805401. Its Apache-2.0 license is retained here.

The pill and capsule checkpoints and selected images derive from MVTec AD. Preserve MVTec AD CC BY-NC-SA 4.0 terms; these artifacts are for non-commercial research. Original dataset: https://www.mvtec.com/company/research/datasets/mvtec-ad

The VisA capsule checkpoint and selected images derive from Amazon Science VisA, CC BY 4.0. Dataset/paper: Zou et al., SPot-the-Difference Self-Supervised Pre-training for Anomaly Detection and Segmentation, ECCV 2022. Original project: https://github.com/amazon-science/spot-diff

Selected files were fetched from public mirrors; each sample manifest records its URL, original held-out path, label and downloaded checksum. They were selected from the existing run's test manifest without looking at new model scores. These small samples do not establish the full benchmark or real blister-camera quality. VisA remains a weak model at its saved threshold and is labeled accordingly.

The ONNX graph consumes RGB float32 in [0,1], resized with Pillow bilinear. ImageNet normalization, teacher normalization, two-map quantile normalization and map alignment are inside the graph. Do not normalize twice. Outputs are a real 256×256 heatmap and its maximum anomaly score. Scores are not probabilities, defect classes, severity or release decisions.
