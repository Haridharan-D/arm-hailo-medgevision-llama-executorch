"""Consistent backup or restore into a NEW directory; no destructive overwrite."""
import argparse,json,sqlite3,sys,shutil,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.store import Store
from app.config import settings
p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
sub.add_parser('backup');r=sub.add_parser('restore');r.add_argument('snapshot',type=Path);r.add_argument('destination',type=Path);r.add_argument('--images',type=Path)
a=p.parse_args()
if a.action=='backup':print(json.dumps(Store(settings()['data_dir']).backup(),indent=2))
else:
    if a.destination.exists():raise SystemExit('Choose a new destination; original evidence will not be overwritten')
    with sqlite3.connect(a.snapshot) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise SystemExit('Snapshot integrity check failed')
    a.destination.mkdir(parents=True);shutil.copy2(a.snapshot,a.destination/'inspections.sqlite3')
    if a.images:shutil.copytree(a.images,a.destination/'images')
    result=Store(a.destination).verify_integrity();result['images_restored']=a.images is not None
    print(json.dumps(result,indent=2))
