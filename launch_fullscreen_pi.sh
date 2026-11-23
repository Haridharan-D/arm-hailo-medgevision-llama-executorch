#!/usr/bin/env bash
set -euo pipefail
APP="$HOME/BlisterTrace/BlisterTrace_App"
URL="http://127.0.0.1:8765"
cd "$APP"
if ! curl -fsS "$URL/api/health" >/dev/null 2>&1; then
  nohup "$APP/.venv/bin/python" "$APP/main.py" --no-browser > /tmp/blistertrace-dashboard.log 2>&1 < /dev/null &
fi
for attempt in $(seq 1 60); do
  if curl -fsS "$URL/api/health" >/dev/null 2>&1; then
    exec chromium --user-data-dir="$HOME/.local/share/blistertrace-browser" --password-store=basic --app="$URL" --start-fullscreen --no-first-run
  fi
  sleep 0.5
done
printf '%s\n' 'Dashboard did not start. Read /tmp/blistertrace-dashboard.log.' >&2
exit 1
