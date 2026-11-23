"""Verify pinned assets and native architecture before executing the model."""
from pathlib import Path
import argparse
import json
import platform
import struct
from download_model import FILES,sha256

ROOT=Path(__file__).resolve().parent
PIN='8c84780911e7f4e9eb19395181b04761392a4b56'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--artifacts',type=Path,default=ROOT/'artifacts')
    args=parser.parse_args()
    checks={}
    for name,(expected,size) in FILES.items():
        path=args.artifacts/name
        checks[name]=path.is_file() and path.stat().st_size==size and (expected is None or sha256(path)==expected)
    receipt_path=args.runtime.parent/'build_receipt.json'
    build=json.loads(receipt_path.read_text()) if receipt_path.is_file() else {}
    checks['runtime_commit']=build.get('executorch_commit')==PIN
    checks['runtime_binary_hash']=args.runtime.is_file() and build.get('files',{}).get(args.runtime.name)==sha256(args.runtime)
    header=args.runtime.read_bytes()[:20] if args.runtime.is_file() else b''
    machine=struct.unpack('<H',header[18:20])[0] if header[:4]==b'\x7fELF' and len(header)==20 else None
    expected_machine={'aarch64':183,'x86_64':62}.get(platform.machine())
    checks['runtime_matches_host_architecture']=expected_machine is not None and machine==expected_machine
    report={'checks':checks,'all_passed':all(checks.values()),'host_architecture':platform.machine(),
            'runtime_build':build,'generation_verified':False,
            'next':'Run advisor.py and require status llama_validated; then perform target evaluation.'}
    print(json.dumps(report,indent=2))
    (ROOT/'installation_verification.json').write_text(json.dumps(report,indent=2))
    return 0 if all(checks.values()) else 1


if __name__=='__main__':raise SystemExit(main())
