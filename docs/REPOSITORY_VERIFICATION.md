# Repository preparation verification

23 November 2026: Windows Python 3.11, 67 regression tests passed (one upstream Starlette deprecation warning). All five included ONNX/HEF artifact hashes matched. Missing gated Llama artifacts are explicitly reported. No Pi was available for a fresh clone hardware run. Original target validation reports remain on the laptop; documentation records those measured results separately. A file-content scan found no private-key, GitHub-token or Hugging Face-token patterns; this does not claim exhaustive secret detection.

SD erase remains blocked: root filesystem unreadable in this process; final Arm binaries and full station database/evidence backup not verified.


## Final clean-clone verification

A separate shallow clone of commit `bf147d4c6ca3ba667dd69eaee6f154d6651e9643` was downloaded from the target GitHub repository. Model parts reconstructed to all five original artifact hashes. All 67 Python regression tests passed, and all five selected CPU inference cases matched. GitHub Linux CI independently installed requirements, checked artifacts, passed the regression suite and compiled/ran the native JSON-boundary test. See evidence/FRESH_CLONE_VERIFICATION.json and evidence/fresh_clone_cpu_smoke.json. Llama model download/native build and new Hailo/camera tests remain explicitly separate prerequisites.
