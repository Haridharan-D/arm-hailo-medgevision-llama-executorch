#!/usr/bin/env bash
# Run explicitly on the Pi; installs drivers/runtime and requires a reboot.
set -euo pipefail
test "$(uname -m)" = aarch64
sudo apt update
sudo apt install -y dkms hailo-all
printf '\nReboot the Pi, then run: hailortcli fw-control identify\n'
printf 'Do not enable the Hailo application backend until the custom HEF is verified.\n'
