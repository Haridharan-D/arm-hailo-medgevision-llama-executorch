"""Local PBKDF2 credentials, bounded sessions, no cloud auth dependency."""
import hashlib,hmac,json,secrets,time,threading
from contextvars import ContextVar
actor=ContextVar('actor',default='local-operator')
ROLES={'administrator','supervisor','operator','auditor'}
def password_hash(password,salt):return hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),600000).hex()
def credential(password,role):
    if role not in ROLES or len(password)<10:raise ValueError('Choose a supported role and password of at least 10 characters')
    salt=secrets.token_hex(16);return dict(role=role,salt=salt,password_hash=password_hash(password,salt))
class LocalAuth:
    def __init__(self,root,required=None):
        # Explicit kiosk access overrides saved accounts without deleting them.
        # Omitted settings retain account-based authentication for older installs.
        self.file=root/'users.json';self.required=self.file.exists() if required is None else bool(required);self.sessions={};self.attempts={};self.lock=threading.Lock()
    def login(self,name,password,client):
        with self.lock:
            now=time.monotonic();attempts=[t for t in self.attempts.get(client,[]) if now-t<300]
            if len(attempts)>=10:raise ValueError('Too many login attempts; wait five minutes')
            if len(self.attempts)>1024:self.attempts.clear()
            self.attempts[client]=attempts+[now]
            users=json.loads(self.file.read_text()) if self.file.exists() else {}
            user=users.get(name);salt=user['salt'] if user else '00'*16
            actual=password_hash(password,salt)
            if not user or not hmac.compare_digest(actual,user['password_hash']):raise ValueError('Invalid local credentials')
            self.attempts.pop(client,None)
            self.sessions={k:v for k,v in self.sessions.items() if v['expires']>now}
            if len(self.sessions)>=64:self.sessions.pop(next(iter(self.sessions)))
            token=secrets.token_urlsafe(32);self.sessions[hashlib.sha256(token.encode()).hexdigest()]=dict(name=name,role=user['role'],expires=now+8*3600)
            return token,dict(name=name,role=user['role'])
    def user(self,token):
        if not self.required:return dict(name='local-operator',role='administrator',authentication='disabled-local-demo')
        if not token:return None
        with self.lock:
            key=hashlib.sha256(token.encode()).hexdigest();user=self.sessions.get(key)
            if user and user['expires']>time.monotonic():return user
            self.sessions.pop(key,None);return None
    def logout(self,token):
        with self.lock:self.sessions.pop(hashlib.sha256((token or '').encode()).hexdigest(),None)
    @staticmethod
    def allowed(user,method,path):
        if method in {'GET','HEAD'}:return True
        role=user['role']
        if role=='administrator':return True
        if path.endswith('/qa') or path.startswith('/api/batches') or path.startswith('/api/database'):return role=='supervisor'
        if path=='/api/shutdown':return False
        return role in {'operator','supervisor'}
