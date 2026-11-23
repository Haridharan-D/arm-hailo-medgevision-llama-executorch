# Troubleshooting and recovery

**Readiness versus liveness:** `/api/live` means the HTTP process is alive; `/api/ready` checks usable service, database, disk and Hailo availability. The UI can start while model initialization is pending. A503 during initialization is not a measured inference failure. Benchmark scripts must wait for ready status before starting their load branch.

**Hailo already owned:** stop the competing inspection process; do not instantiate a second VDevice for a concurrent benchmark. Use one running API. No automatic CPU fallback is used for Hailo faults. An explicit CPU reference configuration is a separate documented mode.

```bash
systemctl --user restart blistertrace.service
systemctl --user status blistertrace.service --no-pager
journalctl --user -u blistertrace.service -n 100 --no-pager
```

**Llama fallback:** retain the original result. Inspect fallback reason and native timing/log evidence. Invalid JSON, unsupported claims or ungrounded clauses are rejected. Retrying may restart a damaged native worker; missing files require restoring the verified model/tokenizer/runtime sidecars. A slow3B candidate must not displace1B merely because it loads. Native worker library dependencies must resolve locally; use `ldd native/bin/aarch64/blistertrace_instrumented` when checking an installation.

**Interrupted jobs:** queued/running jobs become interrupted/fallback after restart; original images and decisions remain. Operator can explicitly request new advice. Queue-full responses use immediate bounded fallback/backpressure rather than spawning more Llama workers.

**Database write failure:** spool JSON remains on disk; maintenance retries in order. `/operations` shows spool count/error and offers replay. Never remove a failed spool operation to make the warning disappear; preserve it for investigation. Consistent backup and restore-to-new-directory commands are in DATABASE_AND_AUDIT.md. Replayed operation IDs prevent double application.

**Low disk/thermal warning:** no automatic evidence deletion or overclocking is applied. Verify/copy backups and archive under team retention rules. A critically full evidence disk blocks new inspections. Temperature warnings are visible; ensure active cooling and adequate power. A model absent from a log is not a valid acceptable-product result.

**USB camera:** select USB0 for the connected Lenovo FHD webcam. If another program owns it, close that program before starting capture. Inference waits for a frame acquired after the request; a stale/no frame produces an explicit error. Camera testing establishes acquisition and timing only without labeled blister strips. CSI enumeration/troubleshooting is excluded from this release.

**Return to preserved deployment:** stop the hardened user service, then run `~/BlisterTrace/BlisterTrace_App/.venv/bin/python ~/BlisterTrace/BlisterTrace_App/main.py --desktop` using its preserved original config. Baseline source archive and consistent database backup are retained under `~/BlisterTrace/Backups/hardening_20261121_201140`; never overwrite the hardened data to perform a rollback. Both old/new code can read preserved original decisions, but new migrations are not silently undone.
