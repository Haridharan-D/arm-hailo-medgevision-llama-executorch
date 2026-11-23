# Submission limitations

- This is a research/hackathon demonstration, not a validated pharmaceutical production system, certified medical device or regulatory release system.
- No team-approved manufacturing SOP has been supplied. BT-DEMO-SOP-01 is explicitly unapproved demonstration material. All recommendations require an applicable approved procedure and authorized QA review.
- Automated JSON/claim guards do not prove semantic recommendation correctness. Human review of the same50 scenarios remains outstanding; acceptance/fallback rates must not be called clinical or operational accuracy.
- Vision weights/HEF/thresholds remain frozen. The original held-out detector set has zero healthy images and no physical-strip IDs, preventing healthy specificity and full physical independence claims. Target USB scene checks do not establish new-SKU or camera-domain accuracy.
- FP32/INT8 agreement on18 demonstration images is not labeled quantized accuracy. Hailo detector throughput is not camera FPS or factory throughput.
- EfficientAD-S is an auxiliary ONNX CPU branch, with weak VisA capsules retained performance. It does not classify chemical contamination or guarantee unknown-defect coverage. MVTec datasets retain noncommercial licensing restrictions.
- NPU utilization, power and energy remain unavailable without a supported sampler/meter. CPU/RSS/temperature observations must not be substituted for them.
- XNNPACK graph partitions and compiled KleidiAI support are inspected. Per-kernel runtime profiling and Model Explorer rendering were not performed. Unsupported4K context or generic re-quantization flags were not blindly applied.
- The3B SpinQuant PTE is a pinned MediaTek conversion of Meta's checkpoint. Its publisher does not supply a full reproducible export recipe; the exact PTE hash/provenance is retained. A compatible QAT+LoRA PTE was not established, so no QAT+LoRA benchmark is claimed.
- Hash chaining detects local modification but does not prevent a privileged attacker rewriting an entire database. External backup/head-hash anchoring and physical security remain necessary. Historical unhashed images are not retrospectively attested.
- Retention is manual verified archival; no silent deletion exists. Database snapshots require corresponding image evidence for a complete restoration. Disk failure beyond writable local storage cannot be hidden by a spool.
- Windows requires the documented WSL dependency for Llama; the `.exe` alone is not a standalone native Windows Llama runtime. The Pi runs native Arm ExecuTorch.
- CSI-camera enumeration and validation are excluded. The newly authorized USB camera is tested independently.
- Batch closure and human comments preserve findings; they do not constitute electronic signature certification or pharmaceutical batch-release authorization. Free-form chat/text-to-SQL and unsupported batch-summary generation are deliberately bounded/refused.
