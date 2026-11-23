"""Provision local users interactively; passwords never enter shell history."""
import argparse,getpass,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.auth import credential,ROLES
from app.config import settings
p=argparse.ArgumentParser();p.add_argument('username');p.add_argument('role',choices=sorted(ROLES));a=p.parse_args()
password=getpass.getpass('New password (10+ characters): ')
if password!=getpass.getpass('Confirm password: '):raise SystemExit('Passwords differ')
path=settings()['data_dir']/'users.json';users=json.loads(path.read_text()) if path.exists() else {}
users[a.username]=credential(password,a.role)
tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(users,indent=2));os.chmod(tmp,0o600);tmp.replace(path)
print('Local user saved. Restart service to enable authentication if it was previously disabled.')
