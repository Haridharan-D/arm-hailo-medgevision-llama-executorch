# Direct-launch workstation and status display

**Current visual-result update:** the second screen now uses the same independent visual check as the main banner: clear usable image → SAFE, unusable/incomplete capture → WARNING, detected defect or anomaly → REJECTED. It does not map an unvalidated QA REVIEW directly to WARNING anymore. The unchanged QA disposition is shown separately. See [verified visual test suite](VISUAL_TEST_SUITE.md); the original mapping described below is historical.

The22November kiosk update disables station sign-in at the user's request, including when a saved users file exists. Accounts remain preserved in case the owner later enables authentication. New local actions record `local-operator`; they no longer identify an authenticated individual. Models, thresholds and original inspection decisions are unchanged.

Run on the Pi:

```bash
~/blistertrace
```

This starts the existing service, uses both detected native HDMI resolutions and opens:

- HDMI-A-1, Dell1600×900: the complete inspection dashboard, fullscreen at100% browser scale.
- HDMI-A-2,1024×768: `/display`, a large automatically updating status-only screen.

The second screen maps recorded PASS to SAFE, REVIEW to WARNING, and HOLD to REJECTED. Disconnection, stale camera frames and camera faults show WARNING. SAFE describes only a recorded visual PASS and does not establish pharmaceutical safety. No uncertain profile is promoted to PASS. With a live camera, current frame decisions drive the status; otherwise the latest stored inspection drives it. Llama text never supplies its verdict.

The command automatically enters the modern dashboard. For classic layout use `~/blistertrace-b`. The prior command/config is preserved in `~/BlisterTrace/Backups/kiosk_*`. The loopback service remains at `http://127.0.0.1:8765`; status alone is `http://127.0.0.1:8765/display`.

The launcher uses separate station-owned Chromium profiles/windows and resets their zoom. Other browser profiles are left alone. It detects output size/position using the installed `wlr-randr`, then uses XWayland window placement so each fullscreen window occupies one monitor. Chromium debugging remains loopback-only for recorded placement verification.

Windows: `dist_hardening/BlisterTrace/BlisterTrace.exe --desktop` also starts without station credentials. The documented WSL Llama dependency remains. Its status-only page can be opened separately at `/display`.
