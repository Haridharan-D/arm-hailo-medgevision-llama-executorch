"""systemd readiness check; never enumerates cameras."""
import json,time,urllib.request
for _ in range(90):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8765/api/ready',timeout=2) as r:value=json.load(r)
        if value.get('ready'):raise SystemExit(0)
    except (OSError,ValueError):pass
    time.sleep(1)
raise SystemExit('Readiness timed out; inspect journal/application log')
