import urllib.request,json,psutil
for path in ['/api/health','/api/status']:
    try:print(path,json.load(urllib.request.urlopen('http://127.0.0.1:8765'+path,timeout=5)))
    except Exception as e:print(path,type(e).__name__)
for p in psutil.process_iter(['pid','cmdline']):
    cmd=p.info.get('cmdline') or []
    if any('main.py' in s or 'uvicorn' in s for s in cmd):print(p.info)
