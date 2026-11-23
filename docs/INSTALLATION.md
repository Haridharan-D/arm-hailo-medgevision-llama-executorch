# Installation and launch

**Current kiosk configuration:** station sign-in is disabled at the owner's request. `~/blistertrace` opens the fullscreen dashboard on HDMI1 and the verdict-only display on HDMI2, without entering credentials. See [dual-display setup](DUAL_DISPLAY_KIOSK.md). Saved accounts are retained but inactive in this configuration. The account provisioning section below is for optional future authenticated deployments.

The existing environment is reused; installation is not training or model compilation. Tested platform inventory is in the initial audit and target runtime manifests. Python requirements are pinned/ranged in `requirements.txt`; native Llama uses ExecuTorch v1.0.0 and its shipped `libllama_runner.so`. HailoRT and Hailo driver versions must match the installed Hailo-8 system. No CSI commands are required.

## Existing Pi installation

Working source: `~/BlisterTrace/BlisterTrace_App`. Hardened release: `~/BlisterTrace/releases/hardening_20261122`. Models/assets are shared through explicit paths/symlinks and remain frozen. Production data: `~/BlisterTrace_Data`. Source-only ZIPs do not contain gated/model binaries; keep original model/tokenizer/license/provenance files with the installation.

```bash
systemctl --user daemon-reload
systemctl --user enable --now blistertrace.service
systemctl --user status blistertrace.service --no-pager
~/blistertrace
```

Classic dashboard: `~/blistertrace-b`. Browser links: `http://127.0.0.1:8765/`, `/classic`, `/design-a`, `/operations`. For an SSH-connected laptop, use `ssh -L 8765:127.0.0.1:8765 saul@10.217.96.233` then open `http://127.0.0.1:8765`. This keeps the service loopback-bound. Replace the IP if the Pi's address changes.

The installed user service starts after user login; unattended boot before login requires separately configured user lingering. Do not describe a user service as a boot-time system service without that configuration. Dedicated launchers open a local browser; full screen can be toggled in the UI or via the existing fullscreen launcher.

## Local accounts

For a fresh data directory, open the dashboard and create the first administrator when prompted. The validated Pi installation already has `station-admin`. Its generated password is stored only on the Pi in a protected file; read it in your own terminal (do not share its output):

```bash
cat ~/BlisterTrace/Backups/validation_account_20261122.json
```

Change it interactively with `.venv/bin/python tools/manage_users.py station-admin administrator` from the hardened release directory, then restart the user service. Passwords require at least10characters and remain in local PBKDF2-derived form. To provision other roles interactively:

```bash
cd ~/BlisterTrace/releases/hardening_20261122
.venv/bin/python tools/manage_users.py qa-supervisor supervisor
.venv/bin/python tools/manage_users.py line-operator operator
.venv/bin/python tools/manage_users.py evidence-auditor auditor
```

Administrator/supervisor can create/select/close batches and append QA reviews; operators inspect; auditors read/export evidence. The older operator display PIN does not grant server permissions. Avoid exposing the loopback HTTP service directly to an untrusted network.

## Terminal use

```bash
cd ~/BlisterTrace/releases/hardening_20261122
.venv/bin/python main.py --inspect /path/to/image.jpg --wait-advice --output /tmp/inspection.json
```

Stop the service before a separate terminal inspector acquires Hailo, then restart it afterwards. Running two independent Hailo VDevices against a device already owned by the dashboard can fail. For concurrent testing, use the HTTP inspection API of the one active service instead.

## Windows

Launch `dist_hardening/BlisterTrace/BlisterTrace.exe --desktop` from the complete directory. Windows uses CPU vision and its bundled x86-64 ExecuTorch worker through WSL; it does not turn the Pi Hailo into a Windows accelerator. Model/runtime sidecars, assets and the `_internal` directory must remain together. Source use: the existing development Python can run `main.py --desktop`. Do not run `prepare_assets.py` over reviewed advisory sources.
