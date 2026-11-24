"""Reassemble frozen ONNX files from small Git blobs, checking every SHA256."""
from pathlib import Path
import hashlib
import json
import os


def materialize(root):
    for item in json.loads((root/'model_parts/manifest.json').read_text()):
        destination = root/item['path']
        if destination.exists():
            with destination.open('rb') as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() == item['sha256']:
                    if item.get('executable'):destination.chmod(0o755)
                    continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_suffix('.onnx.partial')
        digest = hashlib.sha256()
        with partial.open('wb') as output:
            for part in item['parts']:
                block = (root/part['path']).read_bytes()
                if hashlib.sha256(block).hexdigest() != part['sha256']:
                    raise ValueError('Corrupted model part: '+part['path'])
                digest.update(block)
                output.write(block)
            output.flush()
            os.fsync(output.fileno())
        if digest.hexdigest() != item['sha256'] or partial.stat().st_size != item['bytes']:
            raise ValueError('Reassembled model checksum mismatch: '+item['path'])
        os.replace(partial, destination)
        if item.get('executable'):destination.chmod(0o755)
        print('Reassembled:', item['path'])


if __name__ == '__main__':
    materialize(Path(__file__).resolve().parents[1])
