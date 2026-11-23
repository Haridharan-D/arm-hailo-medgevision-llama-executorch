# Visual results and29-case demonstration suite

The main result banner,5-second dialog, classic layout and second monitor now show the same visual observation: **SAFE**, **WARNING**, or **DEFECTIVE** (second display uses **REJECTED** for DEFECTIVE). No model weights, detection confidence thresholds, anomaly thresholds, NMS or prior QA records were changed. Llama does not choose these results.

SAFE means a usable image with no configured YOLO detections or a below-threshold anomaly score. WARNING means unusable capture, incomplete assessment or a runtime/disconnection condition. DEFECTIVE means a configured YOLO detection, retained HOLD evidence or an above-threshold anomaly flag in a usable image. An anomaly flag is not a classified defect identity. These are model observations, not proof of pharmaceutical safety. The independent unvalidated QA disposition remains REVIEW; the record includes `visual_result` with policy`visual-check-v1` and explicitly preserves `qa_decision`.

## Files on the Pi

```text
/home/saul/BlisterTrace_TestSuite_20261122/
  YOLO/
    safe/                 2 distinct visually reviewed SCOA images
    warning/              2 simulated unusable captures
    defective/
      black_dot/          1 image
      broken/             1 image
      color_mismatch/     1 image
      crack/              1 image
      dual_cap/           1 image
      empty/              1 image
      foreign_particle/   1 image
  Anomaly/
    mvtec_pill/            safe/2, warning/2, defective/2
    mvtec_capsule/         safe/2, warning/2, defective/2
    visa_capsules/         safe/2, warning/2, defective/2
  verification.json
  results.csv
  manifest_candidates.json
```

PC copy: `C:\arm_bharath_soc_2027\BlisterTrace_TestSuite_20261122`.

Run `~/blistertrace`. Under **Defect detection → Change image → Local images**, select **Demo safe**, **Demo warning**, or the appropriate **Demo [defect]** folder. Under **Anomaly heatmap → Change image → Stored test folder**, choose the model profile and a named **DEMO SAFE / WARNING / DEFECTIVE** case. The original examples remain available. New defaults favor the verified safe examples for simple operator testing.

## Actual verification and selection limits

All29final images were run through the real Pi application: Hailo-8 for the11YOLO cases and ONNX CPU for the18anomaly cases. The final verification matched29/29requested outcomes, including the correct class appearing in every YOLO defect image. Browser-driven checks separately exercise all3visual outcomes in both modes, the popup colors and the live second HDMI status.

These are selected demonstrations, not an unbiased accuracy evaluation. The original dual-cap CASE-001 was missed; CASE-005 was selected after testing5candidates. The missed outputs are retained in `dualcap_selection_trials.json` and raw test logs. The old20-example VisA subset detected none of its10defects. Two different labeled defects were selected from previously recorded true-positive predictions, downloaded from the public dataset mirror and actually rerun at the unchanged threshold. This does not improve VisA's original24%held-out recall or support a reliability claim.

WARNING inputs explicitly simulate very dark exposure or loss of all spatial detail with1×1resampling. They are derived test challenges, not naturally captured failures or additional independent samples. YOLO SAFE SCOA photos show12apparently occupied cavities on visual review, but their release has no formal defect annotations. Basler defect examples were selected by detector behavior, not independently relabeled as human truth. Model misses remain possible on arbitrary images.

MVTec images retain noncommercial CC BY-NC-SA4.0 dataset conditions; VisA, Basler and SCOA retain their source attribution. Filename/folder/expected labels are never inputs to inference or the visual-result policy. No chemical, microbiological or product-release conclusion follows from SAFE.
