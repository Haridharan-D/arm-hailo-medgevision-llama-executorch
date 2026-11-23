"""Download the upstream-linked SpinQuant artifact at a fixed HF revision.

No token is needed for this particular public conversion repository. The user's
approved Meta access does not make this a newly exported team checkpoint.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import sys
import time
import urllib.request

REPO = 'executorch-community/Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8-ET'
REVISION = '911221e0f49d3354cbd4697a9c09feee25cadec7'
FILES = {
    'Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte':
        ('8715cdba9e91f6bede00cc5f2d6b12397b95225da5630c4972a8da03001cda3b', 1135951488),
    'tokenizer.model':
        ('82e9d31979e92ab929cd544440f129d9ecd797b69e327f80f17e1c50d5551b55', 2183982),
    'params.json': (None, 273),
    'README.md': (None, 40241),
    'Export_Recipe_Llama_3_2_1B_Instruct_SpinQuant_INT4_EO8.ipynb': (None, 83165),
}


def parallel_ranges(url,partial,size):
    """Bounded, resumable ranges for the large public model artifact."""
    begin=partial.stat().st_size if partial.exists() else 0
    directory=partial.with_name(partial.name+'.ranges')
    directory.mkdir(exist_ok=True)
    ranges=[(start,min(start+16*1024*1024,size)-1) for start in range(begin,size,16*1024*1024)]
    def fetch(bounds):
        start,end=bounds
        path=directory/f'{start}-{end}.part'
        expected=end-start+1
        for attempt in range(20):
            received=path.stat().st_size if path.exists() else 0
            if received==expected:return path
            if received>expected:raise ValueError('Oversized range file')
            request=urllib.request.Request(url,headers={'Range':f'bytes={start+received}-{end}'})
            try:
                with urllib.request.urlopen(request,timeout=60) as response:
                    if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start+received}-{end}/{size}':
                        raise ValueError('Server did not honor the exact download range')
                    with path.open('ab') as stream:
                        while True:
                            block=response.read(1024*1024)
                            if not block:break
                            stream.write(block)
            except (OSError,TimeoutError):
                time.sleep(min(5,attempt+1))
        raise ValueError('Range download did not complete')
    with ThreadPoolExecutor(max_workers=4) as pool:
        paths=[]
        for i,path in enumerate(pool.map(fetch,ranges),1):
            paths.append(path)
            print(f'{partial.name}: {begin+sum(p.stat().st_size for p in paths):,}/{size:,} bytes ready',flush=True)
    with partial.open('ab') as output:
        for path in paths:
            with path.open('rb') as source:
                for block in iter(lambda:source.read(1024*1024),b''):output.write(block)
    # Retain range files until the model's published checksum has been checked.
    return paths


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def download(destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    receipt = {}
    for name, (expected, size) in FILES.items():
        target = destination / name
        if target.is_file() and target.stat().st_size == size:
            if expected is None or sha256(target) == expected:
                receipt[name] = {'sha256': sha256(target), 'bytes': size}
                print('Verified existing:', name, flush=True)
                continue
        partial = target.with_name(name + '.partial')
        offset = partial.stat().st_size if partial.exists() else 0
        if offset >= size:
            if offset == size and (expected is None or sha256(partial) == expected):
                partial.replace(target)
                receipt[name] = {'sha256': sha256(target), 'bytes': size}
                continue
            raise ValueError('Invalid partial file; retain it for diagnosis: ' + str(partial))
        range_paths=[]
        if size>=256*1024*1024:
            range_paths=parallel_ranges(f'https://huggingface.co/{REPO}/resolve/{REVISION}/{name}',partial,size)
        tick = time.monotonic()
        # Some proxies terminate long responses early without raising an error.
        # Reopen a verified byte range rather than discarding received bytes.
        for attempt in range(100):
            offset = partial.stat().st_size if partial.exists() else 0
            if offset == size:
                break
            request = urllib.request.Request(
                f'https://huggingface.co/{REPO}/resolve/{REVISION}/{name}',
                headers={'Range': f'bytes={offset}-'} if offset else {})
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    if offset and response.status != 206:
                        offset = 0
                    if offset and not response.headers.get('Content-Range', '').startswith(f'bytes {offset}-'):
                        raise ValueError('Unexpected download range')
                    with partial.open('ab' if offset else 'wb') as stream:
                        count = offset
                        while True:
                            block = response.read(1024 * 1024)
                            if not block:
                                break
                            stream.write(block)
                            count += len(block)
                            if count > size:
                                raise ValueError('Response exceeds pinned size')
                            if time.monotonic() - tick >= 10:
                                print(f'{name}: {count/size:.1%}', flush=True)
                                tick = time.monotonic()
                if count == offset:
                    raise ValueError('Download made no progress')
            except (TimeoutError, OSError):
                if attempt == 99:
                    raise
                time.sleep(min(5, attempt + 1))
        if partial.stat().st_size != size:
            raise ValueError('Download size differs from pinned source: ' + name)
        actual = sha256(partial)
        if expected is not None and actual != expected:
            raise ValueError('Published checksum mismatch: ' + name)
        partial.replace(target)
        for path in range_paths:
            path.unlink()  # Exact task-owned byte ranges, after checksum success.
        receipt[name] = {'sha256': actual, 'bytes': size}
        print('Downloaded and verified:', name, flush=True)
    record = {
        'repo': REPO, 'revision': REVISION, 'files': receipt,
        'model_family': 'Llama 3.2', 'model': '1B Instruct SpinQuant INT4 EO8',
        'artifact_type': 'pre-exported ExecuTorch XNNPACK .pte',
        'model_context_tokens': 2048, 'application_context_limit': 1024,
        'license': 'Llama 3.2 Community License; retain source README',
        'exported_by_team': False, 'pi_runtime_verified': False,
        'upstream_reference': 'https://github.com/pytorch/executorch/blob/v1.0.0/examples/models/llama/README.md',
        'runtime_version_to_validate': 'ExecuTorch v1.0.0',
        'note': 'Publisher recipe mentions ExecuTorch 0.6 release candidate. Compatibility with the selected runtime must be measured, not inferred from the .pte extension.'}
    (destination / 'artifact_receipt.json').write_text(json.dumps(record, indent=2), encoding='utf8')
    return record


if __name__ == '__main__':
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / 'artifacts'
    try:
        download(output)
    except Exception as error:
        print('Download failed:', type(error).__name__, file=sys.stderr)
        raise SystemExit(1)
