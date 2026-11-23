# MEDGE SoC intro and second-display refresh

The exact image from `Intro_entry/MEDGE SoC_ Pharmaceutical Quality at the Edge.png` is bundled offline as `web/assets/intro/medge-intro.png`. Its SHA256 is `2741b500f24b176837016b8e1f3ebf18cc163905dbda5de001cc1f5bb070e4e3`; its pixels were not edited. Contain sizing keeps all logos and text visible.

`~/blistertrace` opens both monitors. The primary monitor stays at the full-screen poster until an explicit click anywhere or Enter. The dashboard loads behind an inert barrier, so startup does not expose or activate inspection controls. The classic launcher has the same gate. No account credentials, timer, hardware-ready event or kiosk parameter bypass it. An entrance fade, slow scan highlight, optical corner marks and capsule accents provide restrained animation; exit fades into the existing inspection UI.

The second display now has a light blue/white background with green, amber or rose accents, an orbiting status dot, floating capsules, a scan accent and a transition only when the displayed inspection/result changes. Online state and last-check time come from actual polling. SAFE/WARNING/REJECTED mapping, underlying models, QA disposition and Llama behavior are unchanged. It continues to show the latest recorded/live-camera result while the primary intro is visible.

Actual Pi browser checks passed: poster still visible after6seconds without interaction; pointer entry and classic Enter entry work; no JavaScript errors; full-width fit on the1600×900 primary and currently detected800×480 second display. `prefers-reduced-motion` was exercised and disables decorative animations. Screenshots and raw report: `validation/intro_display_20261122`. Windows uses the same updated bundled web assets; no model export or retraining is involved.

Current Pi IPv4 is192.168.137.32. Launch on the Pi with `~/blistertrace`, classic with `~/blistertrace-b`. Keep the complete Windows executable directory together. Local URLs remain `http://127.0.0.1:8765` and `/display`.
