# Documentation index

## Reproduce and demonstrate

- [Fresh-clone quick start](../QUICKSTART.md): CPU, matching Pi/Hailo, pinned Llama download and service setup.
- [Model cards](MODEL_CARDS.md): frozen artifacts, training, normalization, outputs and limitations.
- [Model lifecycle](MODEL_LIFECYCLE.md): notebooks, export, Hailo compilation and external prerequisites.
- [Hackathon demonstration](HACKATHON_DEMO.md): operator-facing walkthrough.
- [Windows build](WINDOWS_BUILD.md): EXE sidecars and WSL advisory dependency.
- [Dual-display kiosk](DUAL_DISPLAY_KIOSK.md): main dashboard and verdict-only HDMI display.
- [Troubleshooting](TROUBLESHOOTING.md): runtime, device, storage and configuration failures.

## Assess results

- [26 November software/evaluation upgrade](ENGINEERING_UPGRADE_20261126.md): repository audit, data availability, measured CPU experiment, 95 regressions and exact reproduction commands.

- [Full results](RESULTS.md): YOLO class F1/mAP, anomaly confusion matrices, CPU/Hailo, Llama and final eight-case outputs.
- [Evidence guide](EVIDENCE_GUIDE.md): original source files, exact experiment scopes and rerun commands.
- [CSV/JSON exports](../evidence/metrics/README.md): full-precision values with provenance and source hashes.
- [Actual Pi screenshot gallery](../evidence/gallery/README.md): all eight inspections, heatmaps/advice, terminal replay and application screens.
- [Current engineering acceptance](../SUBMISSION_REPORT.md): final target/recovery checks and unresolved validation.
- [Project PDF](MEDGE_VISION_Final_Project_Report.pdf): methodology, results, hardware and optimization.

## Understand the design

- [Engineering decision ledger](ENGINEERING_DECISIONS.md): deployed choices, evidence, tradeoffs and unmeasured next steps.

- [System architecture](SYSTEM_ARCHITECTURE.md) and [architecture image](architecture.svg).
- [Llama/ExecuTorch optimization](LLAMA_EXECUTORCH_OPTIMIZATION.md): artifacts, native instrumentation and candidate selection.
- [Vision evaluation](VISION_EVALUATION.md): original evaluation and quantization boundaries.
- [QA workflow](INDUSTRIAL_WORKFLOW.md): visual observation versus authorized disposition.
- [Database/audit](DATABASE_AND_AUDIT.md): evidence persistence and append-only review.
- [Portable backup](../backups/README.md) and [private backup status](../BACKUP_STATUS.md).
- [Third-party licenses](../THIRD_PARTY_NOTICES.md) and [submission limitations](SUBMISSION_LIMITATIONS.md).

## Historical engineering records

[Initial audit](INITIAL_TECHNICAL_AUDIT.md), [22 November acceptance](FINAL_ACCEPTANCE.md),
[repository verification](REPOSITORY_VERIFICATION.md), [hardware benchmark notes](HARDWARE_BENCHMARKS.md)
and [original-station installation notes](INSTALLATION.md) preserve their dated scope.
An old test count, path or pending statement is not the current release status. Use the current evidence
guide and final target/recovery logs for later executed work. The historical raw JSON/CSV records are
never rewritten to make them look like fresh measurements.
