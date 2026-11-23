# BlisterTrace — The Optical Instrument

Complete buildless frontend. The v4 console adds auxiliary EfficientAD endpoints
and explicit advisory reuse while preserving detector disposition and QA rules.
See [the current guide](../CONSOLE_ANOMALY_V4.md) for real heatmap tests and limitations.

## Run

Configured Pi: run ~/blistertrace, then Ctrl+Shift+R in its browser. URL: http://127.0.0.1:8765/
Windows: run dist_v4/BlisterTrace/BlisterTrace.exe with its complete companion folder.
Standalone demo: from this web directory run python -m http.server 8780 --bind 127.0.0.1
and open http://127.0.0.1:8780/?adapter=mock. Use HTTP rather than file:// for ES modules.
Demo mode is visibly labeled. It performs no hardware inference; boxes and results are simulated.
Real mode is the default and never silently substitutes simulated data.

## Files

- index.html: standalone entry; aoi.html: existing FastAPI entry with /static paths.
- css/tokens.css: fonts/colors/type; components.css: controls/dialogs; app.css: screens;
  motion.css: capsule identity, optical effects and motion tokens.
- js/api.js: every fetch call and REST subscription, typed JSDoc contracts.
- js/mock.js: explicit simulated adapter.
- js/motion.js: spring solver, frame-time governor, transition helpers.
- js/optical.js: atlas, replay, pipeline strip, scan, verdict and idle canvas.
- js/viewer.js: canvas annotations/minimap, zoom/pan/pinch/split/loupe.
- js/app.js: application state, routes and screens.
- js/console.js and css/console.css: fixed viewport workspace, measurement/assistant
  tabs and real model profile/sample controls.
- js/components.js: virtual table, countdown, dialogs, exports.
- js/icons.js: inline SVG; js/i18n.js: translation dictionary.
- assets: local fonts/licenses, logo, actual SOP and demo photograph.

Old top-level aoi.js/aoi.css/app.js/style.css are retained for rollback but are not loaded.
No framework, frontend dependency installation, analytics, CDN or remote font request.

## API and capability map

All network calls are in api.js. Change that module to remap endpoints.

| Endpoint | Use |
| --- | --- |
| GET /api/health, /api/status | readiness, runtime and available telemetry |
| POST /api/inspect | multipart file upload |
| GET /api/library | up to 200 local images |
| POST /api/library/inspect | JSON name |
| GET /api/inspections | latest 50 summaries |
| GET /api/inspections/{id} | immutable facts + advice/latest review |
| GET …/{id}/image, …/{id}/original, …/{id}/report | recorded evidence |
| POST …/{id}/advice | queue retry |
| POST …/{id}/ask | bounded question or intent |
| POST …/{id}/qa | reviewer + comment, append-only |
| POST /api/camera/start | source 0/1/2 or picamera2 |
| POST /api/camera/stop, /api/camera/inspect | stop / inspect fresh frame |
| GET /api/camera/stream | annotated MJPEG |
| GET /api/export.csv | server latest500; filtered UI CSV is generated locally |
| GET /api/anomaly/profiles, /api/anomaly/samples/{profile} | real model contracts and held-out sample list |
| POST /api/anomaly/inspect | profile + sample or pinned inspection_id |
| GET /api/inspections/{id}/heatmap | actual stored EfficientAD transparent overlay |

Existing backend has REST polling and MJPEG, not SSE/WS/token events. TODO integration
contracts: inspection-ID + sequence-number token events; per-stage timing; measured token
rate; NPU utilization; queue depth; DB bytes; batch IDs/targets; paginated
QA events; server audit proof/verification; bounded batch summary; authenticated operators;
device discovery and capture timestamps. These are simulated only in Demo mode or shown
unavailable in Real mode. Real model heatmaps are now available through the v4
anomaly endpoints. They are not fabricated from bounding boxes.

History filters cover the latest 50 records, hydrated with at most three detail requests
concurrently. Filtered CSV and bulk JSON cover the loaded snapshot, not the entire DB.
Similar past rejects is a labeled local class-match lookup, not Llama text-to-SQL.

Real advice appears when the existing server returns validated JSON or fallback.
Only Demo mode simulates token-by-token output. Unknown causes stay unestablished.
SOP chips open exact BT-01…BT-04 passages from local BT-DEMO-SOP-01 revision1.
The SOP requires QA approval. Drafts are working text, not sign-off.
QA notes append through the unchanged API and do not modify detector disposition.
Live review timeline shows the latest server review plus this browser session's writes.
Browser digests are not server-signed audit proofs. Live integrity verification is disabled
because there is no verification endpoint. The demo hash-chain verification is operational.
PIN1234 changes local display identity only; it is not authentication or QA authorization.

## Controls

Ctrl/Cmd+K commands, ? shortcuts, I inspect, H history, +/- zoom, F fit, 1 pixel scale,
Ctrl/Cmd+Enter inference. Wheel/pinch zoom and drag pan. Arrow keys move the split;
pointer release snaps near 25/50/75%. Loupe follows pointer/touch at 4x, wheel adjusts
2–10x, double-click locks/unlocks. Replay uses recorded annotations, no new inference.
Atlas pockets represent image records, not physical cavities. No batch completion
percentage is invented; the gauge is labeled loaded-snapshot coverage.

Motion Full/Calm/Off settings persist. Off means Minimal. Reduced-motion caps at Calm
or quieter. Automatic governor reduces Full → Calm → Minimal after sustained >20ms
frame EMA. No decorative effect delays or changes a detector result. Timing packets
use recorded timings clamped for readability; they are not real-time execution traces.
Fonts/licenses bundled: Inter and JetBrains Mono under assets/fonts.
