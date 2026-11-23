# Second HDMI live-result synchronization —23November

The display now polls a dedicated lightweight `/api/display` response with no-store headers every500ms, and compares actual inspection IDs. New completed uploaded/local/anomaly inspections publish a display record immediately, independently from Llama. A completed manual image result takes priority over background camera processing; choosing camera Connect or Live view returns the second display to camera mode. Snapshot advice remains pinned separately.

The poll timer is scheduled in a finally block, so a network error or missing decorative element cannot silently stop all later updates. Animation targets/connection labels are optional, and versioned display script URLs avoid an old cached module. Disconnections and stale camera frames show WARNING and recover automatically. The visual result policy, thresholds, model weights, original QA disposition and advisory behavior are unchanged.

Tests cover manual precedence over live camera, stale frames/runtime faults, database restoration after restart, and actual Pi display updates through sequential SAFE/REJECTED/WARNING/anomaly/SAFE requests. Browser verification also injects one transient failed request and checks recovery. Evidence: `validation/display_sync_20261123`.

Run `~/medge-vision` to open both screens. The display updates without reloading after subsequent inspections.
