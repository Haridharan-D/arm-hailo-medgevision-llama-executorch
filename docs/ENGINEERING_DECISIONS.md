# Engineering decisions: performance with boundaries

Medge Vision combines a specialized detector, category-specific anomaly models and a separate language-model assistant. This ledger explains the deployed choices using preserved measurements. It is not a new benchmark or a claim of superiority over systems evaluated on different datasets.

## What changed, why it stayed, and what it costs

| Decision | Evidence supporting the choice | Tradeoff / boundary | Inspect it |
| --- | --- | --- | --- |
| Deploy YOLO on Hailo-8 | Historical mean detector-path latency: CPU 580.115 ms, Hailo 15.197 ms; derived ratio 38.17x | Unequal repeated-image trial counts; not camera FPS or production throughput | [Benchmark methodology](RESULTS.md#5-actual-pi-detector-benchmark-cpu-versus-hailo-8), [adapter](../app/hailo_backend.py) |
| Preserve preprocessing across CPU and NPU | RGB, 640-pixel letterbox, padding 114 and reverse coordinate mapping; backend-specific tensor layout/normalization | Hailo normalization is in the graph; applying CPU normalization again changes inputs | [Model contracts](MODEL_CARDS.md), [vision implementation](../app/vision.py) |
| Keep the frozen INT8 HEF | Actual Hailo execution and an 18-image FP32-reference agreement experiment are recorded | Agreement is not labeled accuracy. INT8 mAP/F1 loss remains NOT TESTED | [Quantization evidence](RESULTS.md#6-quantization-and-export-what-was-verified) |
| Keep three independent anomaly profiles | Labeled image F1: pill 92.37%, capsule 88.32%, VisA 38.40% | Anomaly scores are not class probabilities. VisA is a weak research profile; do not average away its misses | [Full confusion matrices](RESULTS.md), [anomaly adapter](../app/anomaly.py) |
| Select 1B adaptive-v1 advisory | Historical median 8.071 s versus baseline 15.156 s; final-guard replay 36/39 versus 26/39 | Acceptance measures bounded-output guards, not semantic correctness. Timings predate the final JSON stop change | [Candidate experiment](RESULTS.md#7-executorch-llama-candidate-and-prompt-comparison) |
| Retain 3B as a comparison, not default | Historical 39/39 acceptance, median 39.275 s, peak RSS 3,223.77 MiB | Better guard acceptance in this experiment costs latency and memory; no claim that every 3B response is correct | [Llama engineering](LLAMA_EXECUTORCH_OPTIMIZATION.md) |
| Bound native generation | Three threads, 128 output tokens, 1,536 prompt-token budget within 2,048 exported context; first-JSON-object stop | A shorter output is not automatically better advice; schema, claim and SOP checks still apply | [Native boundary tests](../tests/json_boundary_test.cpp), [worker sources](../native/) |
| Use an independent persistent advisory worker | Inspection stays usable while advisory runs; bounded jobs and cache avoid redundant work | Final eight-case demo explicitly used fresh generation, zero cache reuse; cache gains are not substituted for those timings | [Actual target report](../evidence/target_20261124/eight_test_report.json), [LLM adapter](../app/llm.py) |
| Separate visual outcome from QA disposition | A clear model result can coexist with QA REVIEW for an unvalidated capture/product profile | This is intentional uncertainty handling, not a threshold adjusted to produce more green results | [Workflow](INDUSTRIAL_WORKFLOW.md), [visual result mapping](../app/visual_result.py) |
| Preserve evidence and verify restore | Hash-checked artifacts, generated source-linked metrics, original records and tested portable demo restore | Unkeyed audit hashes cannot resist privileged database replacement; portable demo backup is not a full SD image | [Recovery](../backups/README.md), [integrity code](../app/integrity.py) |

## The actual complete-station observation

On 24 November, eight selected cases exercised YOLO plus all three anomaly profiles and produced eight fresh validated advisory responses. Advisory median was **8.9669 s**, observed service-tree peak RSS **1,977.06 MiB**, and summed CPU peak **302.6%** (100% means one logical core). Validation work overlapped this run. These figures describe that demonstration, not isolated Llama memory, a saturation benchmark or an unbiased accuracy evaluation.

The separate historical CPU/Hailo experiment and historical Llama comparison answer different questions. Their denominators and measurement scopes must remain separate. [Read all original-source links and formulas](EVIDENCE_GUIDE.md).

## Experiments that did not justify deployment claims

- Compact-v1/v2 prompting did not provide reliable bounded responses; adaptive-v1 was selected instead. See the recorded account in [Llama engineering](LLAMA_EXECUTORCH_OPTIMIZATION.md).
- VisA training completed, but its held-out recall was only 24%. Completing training did not establish readiness.
- FP32 export checks and NPU agreement did not establish labeled post-quantization accuracy.
- Eight selected demonstrations did not establish healthy specificity, camera generalization or pharmaceutical release safety.
- Compiled XNNPACK/KleidiAI support is not proof that every compiled kernel executed on the Pi. No SME/SME2 execution is claimed for Cortex-A76.

## What a stronger next release must measure

1. Run the same labeled held-out images through FP32 and INT8, with identical matching and reporting.
2. Add independently labeled healthy blister images and report false-reject rate.
3. Validate fixed capture conditions on local products, including focus and illumination failure cases.
4. Run an isolated, cooled endurance workload with external power measurement.
5. Obtain authorized semantic review and approved SOPs before operational advisory use.

These are **NOT TESTED / pending**, not hidden achievements. No models were retrained or thresholds changed for this presentation update.

[Results](RESULTS.md) · [Model cards](MODEL_CARDS.md) · [Judge guide](JUDGES_START_HERE.md)
