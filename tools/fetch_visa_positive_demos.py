"""Fetch labeled VisA positives selected from saved predictions; demo selection only."""
import hashlib,json,zipfile
from pathlib import Path
import requests
root=Path(__file__).resolve().parents[1];out=root/'validation/visual_suite_20261122/extra_visa';out.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(root.parent/'EffNet_Kaggle/New folder/visa_capsules_Submission.zip') as z:
    rows=json.loads(z.read(next(n for n in z.namelist() if n.endswith('/predictions.json'))))
rows=sorted((r for r in rows if r['label']==1 and r['prediction']==1),key=lambda r:r['score'],reverse=True)[:4]
results=[]
for i,row in enumerate(rows,1):
    url='https://huggingface.co/datasets/imaadd05/visa-anomaly-detection/resolve/main/'+row['path'];dest=out/f'candidate_{i:02d}.png'
    if not dest.exists():
        response=requests.get(url,timeout=(15,60));response.raise_for_status()
        from PIL import Image
        import io
        Image.open(io.BytesIO(response.content)).convert('RGB').save(dest)
    value=dict(row,file=dest.name,source_url=url,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),selection='Chosen from saved true-positive predictions for demonstration, not an unbiased test');results.append(value)
    print(row['path'],'saved score',row['score'],flush=True)
(out/'manifest.json').write_text(json.dumps(results,indent=2))
