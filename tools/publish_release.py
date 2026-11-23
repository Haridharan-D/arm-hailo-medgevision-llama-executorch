"""Publish authorized handoff assets using Git's existing credential helper.

Credentials stay in process memory; no token is printed, saved, or accepted on
the command line. The existing private repository visibility is unchanged.
"""
import json
import os
import subprocess
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
REPOSITORY='PRIY4DH4RS4N-D/arm-hailo-vision-llama-executorch'
TAG='blistertrace-v0.1.0-demo'

def main():
    repo=ROOT.parent/'BlisterTrace_GitHub'
    env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
    credential=subprocess.run(['git','credential','fill'],cwd=repo,env=env,
        input='protocol=https\nhost=github.com\npath='+REPOSITORY+'.git\n\n',
        capture_output=True,text=True,check=True)
    values=dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
    token=values.get('password')
    if not token:raise RuntimeError('Existing Git credential helper did not provide repository access')
    session=requests.Session()
    session.headers.update(Authorization='Bearer '+token,Accept='application/vnd.github+json',
                           **{'X-GitHub-Api-Version':'2022-11-28'})
    api='https://api.github.com/repos/'+REPOSITORY
    remote=session.get(api,timeout=30);remote.raise_for_status()
    if not remote.json()['private']:raise RuntimeError('Expected the existing repository to remain private')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    response=session.get(api+'/releases/tags/'+TAG,timeout=30)
    if response.status_code==404:
        body='''Working PS5 demonstration on the supplied Raspberry Pi 5 and Hailo-8.

- Actual compiled custom seven-class YOLOv8s HEF tested through HailoRT 4.23.0.
- USB camera, image upload, stored images, terminal inspection and SQLite evidence.
- Llama 3.2 1B Instruct through native Arm ExecuTorch, independently of Hailo vision.
- Browser workflow verified on the actual Pi; around 15 observed application FPS during concurrent advice.
- Windows executable is prepared locally; its Llama worker requires installed WSL2/Ubuntu 24.04.

The Pi application archive reuses the existing native Llama folder. On a fresh
device follow Llama_ExecuTorch/README.md and the pinned model downloader. The
frozen vision ZIP includes best.pt, ONNX, thresholds, evidence and training-only
calibration images. It excludes intermediate training checkpoints. The recording
is the actual Pi browser session and uses clearly identified training-source
demonstration images plus the connected camera; it is not independent accuracy
evidence. The report and JSON evidence describe all measurement limits.

Independent labeled local-camera INT8 accuracy, healthy false holds and longer
stability tests remain pending. Optional EfficientAD artifacts are not included.
This prerelease is a working demonstrator, not a production quality acceptance.
SHA256SUMS.json records the release files. Vendor compiler and Llama weights
are not redistributed in these release files; download the latter with approved
publisher access as documented. Built with Llama.'''
        response=session.post(api+'/releases',json={'tag_name':TAG,'target_commitish':revision,
            'name':'BlisterTrace v0.1.0 — tested Pi/Hailo demonstrator',
            'body':body,'draft':False,'prerelease':True},timeout=30)
    response.raise_for_status();release=response.json()
    existing={item['name']:item for item in release['assets']}
    uploaded=[]
    for path in sorted((ROOT.parent/'BlisterTrace_Deliverables').iterdir()):
        if not path.is_file():continue
        if path.name in existing:
            item=existing[path.name]
            if item['size']!=path.stat().st_size:
                raise RuntimeError('Existing asset differs; do not replace silently: '+path.name)
        else:
            with path.open('rb') as stream:
                result=session.post(release['upload_url'].split('{')[0],params={'name':path.name},
                    data=stream,headers={'Content-Type':'application/octet-stream'},timeout=(30,600))
            result.raise_for_status();item=result.json()
        uploaded.append({'name':item['name'],'bytes':item['size'],'url':item['browser_download_url']})
        print('Release asset verified:',item['name'],item['size'],flush=True)
    report={'repository':'https://github.com/'+REPOSITORY,'private':True,
            'source_commit':revision,'release':release['html_url'],'tag':TAG,
            'prerelease':True,'assets':uploaded}
    (ROOT/'validation/github_release.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
