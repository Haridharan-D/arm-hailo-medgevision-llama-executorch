# Operator workflow and offline demonstration

1. After the clone installer has been run, start `~/medge-vision` (see [quick start](../QUICKSTART.md)) and enter the workspace deliberately. Show separate Hailo vision and ExecuTorch Arm advisory statuses.
2. Open **Batch records · Audit · Accounts** or `/operations`; the shipped owner-requested configuration opens without a station login. Keep access on loopback or use an SSH tunnel; this is not authenticated multi-user deployment.
3. Create a known demonstration batch with SKU, description, category and operator; select it for new inspections. Historical records stay attached to their original batch.
4. Inspect one of the stored neutral CASE images using local input, or upload an existing image. USB camera0 is optional. No CSI is required.
5. Show boxes, confidences, coordinates and the original HOLD/REVIEW/PASS decision immediately. Capture/profile uncertainty remains visible and cannot be removed to make a nicer demonstration.
6. Show original/annotated views and pinned inspection ID. Zoom/pan never changes model coordinates.
7. Wait for the independent Llama job; show native timing and accepted/fallback status. Vision continues while advisory is pending.
8. Open the cited **demonstration/unapproved** SOP clause. Explain that authorized QA must consult an approved procedure for operations.
9. Show the draft deviation note and constrained inspection questions. No free-form text-to-SQL or replacement product-release decision exists.
10. In operations, show real batch counts, observed defect distribution and inspection timeline.
11. Open individual JSON evidence: source hash, model hash, configuration revision, original decision and advisory.
12. Download PDF/CSV/JSON batch report. Closing a batch is record closure, not pharmaceutical release authorization.
13. Append a QA review with reviewer identity. With authentication disabled, this identity is an entered attribution, not a verified supervisor/administrator role. Show the immutable review timeline and unchanged original decision.
14. Verify audit/hash integrity and create a consistent DB snapshot. Show unavailable NPU utilization explicitly, plus CPU/RAM/temperature/storage/queue.
15. Demonstrate a controlled Llama fallback without changing the original result, then show measured baseline/challenger comparison and its limitations.

Outcomes distinguish DEFECTIVE, NO_VISIBLE_DEFECT_DETECTED, WARNING, MANUAL_REVIEW and SYSTEM_FAULT. These observation labels do not replace frozen QA decisions. A no-defect image with an unvalidated capture profile remains manual review. Anomaly flags are appearance deviations; neither anomaly scores nor Llama text diagnose manufacturing/chemical/microbial causes.
