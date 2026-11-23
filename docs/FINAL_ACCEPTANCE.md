# Executed acceptance — 22 November 2026

The hardened release is installed alongside the preserved original on the Pi. Source, SQLite snapshots, original launchers, old native worker and historical benchmark evidence remain recoverable. Run `~/blistertrace`; classic design uses `~/blistertrace-b`.

| Requirement | Executed evidence / boundary |
|---|---|
| Frozen Hailo vision remains functional | Final real HEF image API inspection; eight target artifact hashes matched. No training, quantization, threshold, preprocessing or NMS changes. |
| USB camera | Lenovo FHD Webcam on video0; actual fresh-frame capture/snapshot passed. Scene was unlabeled, so this is not an accuracy test. |
| Local Llama | Original1B SpinQuant PTE with adaptive-v1 prompt selected; persistent native Arm ExecuTorch,3threads,128 output tokens,2048 exported context. Final application returned `llama_validated`. |
| Challenger comparison | Same50 scenarios evaluated on1B baseline,1B adaptive and3B.3B remains optional because latency is substantially higher; no human semantic endorsement claimed. |
| Delegation and kernels | PTE metadata:180 XNNPACK delegate calls and490 remaining kernel calls. Compiled XNNPACK/KleidiAI and Arm dot-product symbols inspected. Per-kernel execution profiling not performed. |
| Structured advice / deterministic decisions | Python guard/recovery tests plus actual target inspection; native JSON boundary5tests. Invalid output explicitly falls back. Llama cannot overwrite stored disposition. |
| Grounding | Available versioned demo SOP used with cited clause and approval-state metadata. No approved manufacturing SOP supplied. |
| Batch / reports / audit | Real batch create/select, concurrent unique inspections, append-only QA review/advice history, image/source hashes, audit verification, PDF report and consistent SQLite backup passed. |
| Storage/restart faults | SQLite writer-lock/spool replay and abrupt process-group restart recovery actually executed. No silent retry presented as a committed record. |
| Browser | A/B/operations exercised locally and against real Pi service through SSH;1366×768 target screenshots. No external frontend requests. No measured60fps Pi claim. |
| Windows | Rebuilt executable exercised with CPU vision and actual WSL ExecuTorch; validated advice and verified audit. WSL remains a dependency. |
| Tests |52Python tests passed, zero failures/skips; one dependency deprecation warning. Five native C++ tests passed. |
| Stability | Actual60-second camera-free API health soak plus separate repeated timing matrices. This does not establish an8-hour factory endurance qualification. |
| Security | Local role accounts required, loopback service, bounded session/rate limits, append-only review interfaces. Hash chain is unkeyed; privileged whole-database replacement is outside its guarantee. |

Raw reports, original failed trials and exact benchmark scopes are retained. Automated acceptance rates are not pharmaceutical accuracy. Human semantic review, approved SOPs, healthy-strip specificity, local product/camera validation, power/energy and NPU utilization measurements remain outstanding. The final runtime JSON boundary was installed after paired timing experiments; final application checks are identified separately.

## Recovery

```bash
systemctl --user restart blistertrace.service
systemctl --user status blistertrace.service --no-pager
journalctl --user -u blistertrace.service -n 100 --no-pager
```

Stop the service before a separate terminal program acquires Hailo. Source backup: `~/BlisterTrace/Backups/promotion_20261122`; original installation: `~/BlisterTrace/BlisterTrace_App`. Do not replace the production database from a snapshot without also restoring its corresponding image evidence and preserving newer records.
