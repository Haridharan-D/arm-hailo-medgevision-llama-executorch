# Design and motion reference

Inter UI; JetBrains Mono coordinates/hashes/numbers. 8px grid, 12/16px panels,
capsule controls, 44px targets, 56px glove mode. Darkroom default, clean-room light
and system choice. Colors pair with labels and status-specific icon shapes.

| Token | Dark | Light |
| --- | --- | --- |
| Background | #0b0e13 | #eef2f6 |
| Surface | #121821 | #ffffff |
| Text | #edf3fc | #152337 |
| Secondary text | #a0aec0 | #44556c |
| Vision/info | #83ceff | #125b91 |
| Advisory violet | #bda8ff | #6440a7 |
| PASS | #62dfa4 | #08633e |
| REVIEW | #ffc874 | #775000 |
| HOLD | #ff929b | #a21b35 |

Components: shell/rail, checklist, pipeline cards/strip, canvas viewer/minimap/loupe/split,
source filmstrip, result banner/dialog, detections, advice/SOP/draft/Q&A/review, virtual
history/replay, blister atlas, KPI/spark/donut/bar/histogram, SOP/audit/settings/health,
PIN pad, command palette, toast, skeleton, ambient capsule canvas.

| Motion | Trigger | Duration / easing | Minimal fallback |
| --- | --- | --- | --- |
| Iris / logo beam | once/session boot | 420ms emphasized / one1.9s scan | direct reveal |
| Boot status settle | ready | 420ms emphasized | static labeled tick |
| Screen/card enter | route | 240ms standard, 28ms stagger max16 | immediate |
| Scan beam | inference | 700ms emphasized | none |
| Detections reveal | completed result | 420ms ease-out | static annotations |
| Verdict vignette | recorded PASS/REVIEW/HOLD | 700/2400/700ms ease-in-out | static banner |
| Verdict symbol | dialog | heavy spring | static icon |
| Countdown | result | 5s, rAF ring | label/ring; pause retained |
| Split snap | pointer release | 160ms cubic settle | direct interaction |
| Loupe/zoom/pan | user input | rAF transform + demand canvas | direct controls |
| Llama orb | idle/thinking | 4s breath/orbit | static violet |
| Token text | demo only | 23ms per chunk | complete response |
| Timing packets | measured stage | clamped420–1800ms | labels |
| Atlas pockets | dashboard | 240ms +28ms stagger max16 | static |
| Coverage liquid | dashboard | 7s transform drift | static gauge |
| Replay | Play | 1200ms per recorded image | manual scrub |
| Theme reveal | toggle | 420ms clip, View Transitions | immediate theme |
| Idle capsules | 120s inactivity | rAF40 capsules, Full only | disabled |
| Toast | feedback | 160ms | static text |

Durations90/160/240/420/700ms. Easings standard/emphasized/anticipate/overshoot.
Springs stiffness/damping: snappy360/28, soft170/24, heavy110/21; dt clamped32ms.
Governor: sustained >20ms frame EMA steps down with minimum4s interval. No automatic
step-up in a session. Manual changes reset it. Reduced-motion caps at Calm and suppresses
CSS loops. No rapid red/white flashes or meaning carried only through motion.

Implemented interpretation is restrained: geometric iris, uniform annotation reveal,
live REST advice with demo-only simulated streaming. Independently drawn bbox corners,
magnetic buttons, shared-thumbnail morphs, manufacturing milestones and hardware token
events are not claimed. Instrument interactions remain usable without those effects.
