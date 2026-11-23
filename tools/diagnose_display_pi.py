import json,urllib.request
def get(path):
    with urllib.request.urlopen('http://127.0.0.1:8765'+path,timeout=10) as r:return json.load(r)
s=get('/api/status');rows=get('/api/inspections?limit=3');print(json.dumps({'camera':s['camera'],'llama':s['llama_state'],'latest':rows},indent=2))
