"""Probe official compatible PTE access; never print credentials or signed URLs."""
import hashlib,json,os,shutil,urllib.request,urllib.error,time
from pathlib import Path
out=Path.home()/'BlisterTrace/Llama_Candidates';out.mkdir(exist_ok=True)
tokens=[Path.home()/'.cache/huggingface/token',Path.home()/'.huggingface/token']
token=os.environ.get('HF_TOKEN') or next((p.read_text().strip() for p in tokens if p.is_file()),None)
rows=[]
for suffix in ['SpinQuant_INT4_EO8','QLORA_INT4_EO8']:
    repo='meta-llama/Llama-3.2-3B-Instruct-'+suffix
    row={'repo':repo,'candidate_only':True,'production_unchanged':True}
    try:
        req=urllib.request.Request('https://huggingface.co/api/models/'+repo+'?blobs=true',headers={'Authorization':'Bearer '+token} if token else {})
        meta=json.load(urllib.request.urlopen(req,timeout=30));row['revision']=meta['sha']
        row['files']=[{k:v for k,v in f.items() if k in ['rfilename','size','lfs']} for f in meta['siblings']]
        target=next(f for f in meta['siblings'] if f['rfilename'].endswith('.pte'))
        req=urllib.request.Request('https://huggingface.co/'+repo+'/resolve/'+meta['sha']+'/'+target['rfilename'],method='HEAD',headers={'Authorization':'Bearer '+token} if token else {})
        with urllib.request.urlopen(req,timeout=30) as r:row['access_status']=r.status
        row['expected_sha256']=target.get('lfs',{}).get('sha256');row['size_bytes']=target.get('size')
        row['download_ready']=True
    except Exception as e:
        row.update(download_ready=False,error_type=type(e).__name__,http_status=getattr(e,'code',None),reason='Official gated artifact could not be accessed with credentials currently available on Pi; existing 1B access does not grant every repository.')
    rows.append(row)
(out/'candidate_access.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
