"""Frozen deployment identities; never infer compatibility from a file extension."""
import hashlib
import platform
from pathlib import Path

HASHES = {
 'blistertrace_yolov8s.onnx':'114bddd21ff853747036591cf7d76c5523a7d8dc95d770221795de8f36691db0',
 'blistertrace.hef':'43abc3f520b97894504d7d99f209846c9f0cc73542eb7b29e9546e7b6def8018',
 'thresholds.json':'f6d92ab69317404610867347eb6268f493569ad908eeb02fc6eb7bc906331c27',
 'Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte':'8715cdba9e91f6bede00cc5f2d6b12397b95225da5630c4972a8da03001cda3b',
 'tokenizer.model':'82e9d31979e92ab929cd544440f129d9ecd797b69e327f80f17e1c50d5551b55'}

def verify(path):
    path=Path(path)
    if path.name not in HASHES:raise ValueError('Unregistered frozen artifact: '+path.name)
    with path.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if actual!=HASHES[path.name]:raise ValueError('Artifact checksum mismatch: '+path.name)
    return actual

def verify_runtime(path, machine=None):
    path=Path(path)
    with path.open('rb') as stream:header=stream.read(20)
    machine=machine or platform.machine().lower()
    expected=183 if machine in {'aarch64','arm64'} else 62 if machine in {'amd64','x86_64'} else None
    if expected is None or len(header)<20 or header[:6]!=b'\x7fELF\x02\x01' or int.from_bytes(header[18:20],'little')!=expected:
        raise ValueError('Native worker architecture mismatch: '+str(path))
    library=path.parent/'libllama_runner.so'
    if not library.is_file():raise FileNotFoundError('Missing runtime sidecar: '+str(library))
    with library.open('rb') as stream:lh=stream.read(20)
    if len(lh)<20 or lh[:6]!=b'\x7fELF\x02\x01' or int.from_bytes(lh[18:20],'little')!=expected:
        raise ValueError('Runtime library architecture mismatch')
