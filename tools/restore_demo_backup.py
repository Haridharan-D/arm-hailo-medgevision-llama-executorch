"""Restore the credential-free measured demo into a NEW data directory."""
import argparse,hashlib,io,json,sys,zipfile
from pathlib import Path

def restore(bundle_dir,target):
    target=Path(target)
    if target.exists():raise ValueError('Choose a new directory; existing station data is never overwritten')
    bundle_dir=Path(bundle_dir);spec=json.loads((bundle_dir/'BUNDLE_MANIFEST.json').read_text())
    chunks=[]
    for row in spec['parts']:
        name=row['file']
        if Path(name).name!=name or '\\' in name:raise ValueError('Invalid part name')
        block=(bundle_dir/name).read_bytes()
        if len(block)!=row['bytes'] or hashlib.sha256(block).hexdigest()!=row['sha256']:raise ValueError('Backup part checksum mismatch')
        chunks.append(block)
    raw=b''.join(chunks)
    if len(raw)!=spec['bytes'] or hashlib.sha256(raw).hexdigest()!=spec['sha256']:raise ValueError('Backup archive checksum mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names=archive.namelist()
        if len(set(names))!=len(names) or len(names)>256 or sum(v.file_size for v in archive.infolist())>128*1024**2:raise ValueError('Invalid backup layout')
        for name in names:
            p=Path(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:raise ValueError('Unsafe backup path')
        manifest=json.loads(archive.read('manifest.json'))
        if set(names)!=set(manifest)|{'manifest.json'}:raise ValueError('Backup member mismatch')
        files={name:archive.read(name) for name in names}
        for name,row in manifest.items():
            block=files[name]
            if len(block)!=row['bytes'] or hashlib.sha256(block).hexdigest()!=row['sha256']:raise ValueError('Backup file checksum mismatch')
    target.mkdir(parents=True)
    for name,block in files.items():
        p=target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(block)
    return target

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];target=restore(root/'backups',args.output)
    sys.path.insert(0,str(root));from app.store import Store
    store=Store(target);check=store.verify_integrity(verify_images=True)
    if not check['valid']:raise SystemExit('Restored demo failed integrity verification')
    print(json.dumps(dict(restored=str(target.resolve()),records=len(store.recent(500)),verification=check),indent=2))
