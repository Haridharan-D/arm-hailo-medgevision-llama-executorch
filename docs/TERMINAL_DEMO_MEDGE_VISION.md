# Medge Vision — short terminal-first demonstration

New command aliases require `tools/install_medge_terminal_pi.py` to have been installed on the Pi. The original `~/blistertrace` command and service name stay compatible. No cloud, laptop or camera is required once files are installed. USB/CSI is not exercised in these stored-image tests.

Open a Pi terminal (Ctrl+Alt+T). Type one command at a time. Startup does not open a browser or create another Hailo owner. The existing one-process service owns HailoRT; this CLI sends local loopback requests to that same model pipeline. Every test performs actual vision inference, waits for associated local Llama advice or clearly reports fallback/pending, and saves JSON evidence. A cached advisory is explicitly marked reused. Use `--fresh` if fresh token generation is needed, for example `~/medge-demo test 1 --fresh`; this is slower. Do not claim fallback or cached text is new Llama generation.

1. `uname -m`

   Output to identify: `aarch64`. Say: “This is our Arm-based Raspberry Pi execution target.”

2. `hailortcli fw-control identify`

   Output to identify: actual Hailo device and installed firmware. Say: “Hailo is present and its runtime can communicate with the accelerator.”

3. `~/medge-demo start`

   Output: READY, actual model/backend, advisory state, new batch ID and evidence folder. Say: “Medge Vision starts the complete local pipeline without opening a browser. Vision and advice execute independently.”

4. `~/medge-demo models`

   Output: Hailo-backed YOLO,3EfficientAD ONNX CPU profiles, ExecuTorch Llama identity, threads, temperature and available memory. Say: “YOLO uses HailoRT on the NPU. Anomaly models use ONNX on the CPU. Llama uses ExecuTorch on the Arm CPU.”

5. `~/medge-demo test 1`

   Output: actual crack detection, confidence, box coordinates, DEFECTIVE, QA HOLD, Llama action, draft and SOP citation. Say: “The detector localizes a crack. Llama supplies a grounded operator action after the decision; it cannot change the decision.”

6. `~/medge-demo test 2`

   Output: no configured detections, visual SAFE, separate QA REVIEW, associated advice. Say: “This selected SCOA image has no configured visual defect. SAFE is a visual observation; an unvalidated product profile still requires QA review.”

7. `~/medge-demo test 3`

   Output: MVTec pill score, saved threshold, actual anomaly flag, visual DEFECTIVE and advice. Say: “The pill anomaly branch reports an unusual appearance. It provides an image-level anomaly signal, not a named defect class.”

8. `~/medge-demo test 4`

   Output: MVTec capsule score, threshold, visual DEFECTIVE and advice. Say: “A separate capsule-specific model runs on-device and generates its own heatmap and score.”

9. `~/medge-demo test 5`

   Output: VisA capsules score, threshold, actual flag and associated advice. Say: “This is a selected positive demonstration for the VisA model. Its overall recall is limited, so we present it as a research profile.”

10. `~/medge-demo summary`

    Output: recorded5-test results, actual audit verification and evidence path. Say: “Every inspection has a unique ID and preserved model output. We verify the database audit chain and retain the original QA decisions.”

11. `~/medge-demo web`

    Opens the two-monitor web demo, with poster entry waiting for a click. Say: “The operator dashboard now uses the same pipeline and recorded results; it is a separate presentation of the same local execution.”

Optional warning: `~/medge-demo test warning`. Say: “This deliberately degraded capture produces WARNING and requests recapture.” The input is a synthetic acquisition challenge, not a natural defect. Optional whole run: `~/medge-demo all` executes startup, inventory,5tests and summary without opening the web.

All5images are selected demonstrations, not an independent accuracy benchmark. No latency is promised in advance; printed timings are measured on the current run. SOPs remain demonstration material requiring authorized QA approval. If Hailo is absent, the inventory must be described as CPU fallback rather than NPU inference.

## If the aliases are absent and the Pi cannot reach the laptop

The existing deployment can still be started with `systemctl --user start blistertrace.service`. Its runtime inventory is available through `curl -s http://127.0.0.1:8765/api/status | python3 -m json.tool`. Do not claim newly prepared aliases/branding are installed until the update has actually been transferred. Reconnect the Pi and laptop to the same network, obtain `hostname -I`, then transfer and install the source update.
