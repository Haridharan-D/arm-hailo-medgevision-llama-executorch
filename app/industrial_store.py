"""Additive traceability migration, immutable findings and durable DB replay."""
import hashlib,json,os,re,sqlite3,threading,uuid
from pathlib import Path
from datetime import datetime,timezone
from .legacy_store import Store as LegacyStore

def now():return datetime.now(timezone.utc).isoformat()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()

class Store(LegacyStore):
    def __init__(self,root):
        root=Path(root);root.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.last_error=None
        super().__init__(root)
        for name in ['spool','backups']:(root/name).mkdir(exist_ok=True)
        with self.connection() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,sku TEXT NOT NULL,
              description TEXT NOT NULL,category TEXT NOT NULL,operator TEXT NOT NULL,
              started_at TEXT NOT NULL,ended_at TEXT,status TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS audit_events(seq INTEGER PRIMARY KEY AUTOINCREMENT,
              event_id TEXT UNIQUE,actor TEXT,event_type TEXT,created_at TEXT,previous_hash TEXT,
              payload_json TEXT,event_hash TEXT UNIQUE);
              CREATE TABLE IF NOT EXISTS replayed_operations(id TEXT PRIMARY KEY);
              CREATE TABLE IF NOT EXISTS station_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS advisory_events(seq INTEGER PRIMARY KEY AUTOINCREMENT,inspection_id TEXT NOT NULL REFERENCES inspections(id),created_at TEXT NOT NULL,payload_json TEXT NOT NULL);
              CREATE TRIGGER IF NOT EXISTS immutable_advice_update BEFORE UPDATE ON advisory_events BEGIN SELECT RAISE(ABORT,'Advisory history is append-only'); END;
              CREATE TRIGGER IF NOT EXISTS immutable_advice_delete BEFORE DELETE ON advisory_events BEGIN SELECT RAISE(ABORT,'Advisory history is append-only'); END;
              CREATE TABLE IF NOT EXISTS advisory_jobs(inspection_id TEXT PRIMARY KEY REFERENCES inspections(id),state TEXT,updated_at TEXT,detail TEXT);
              CREATE TRIGGER IF NOT EXISTS immutable_decision BEFORE UPDATE OF id,created_at,source,decision,severity,record_json ON inspections BEGIN SELECT RAISE(ABORT,'Original inspection is immutable'); END;
              CREATE TRIGGER IF NOT EXISTS retain_inspection BEFORE DELETE ON inspections BEGIN SELECT RAISE(ABORT,'Evidence retention forbids deletion'); END;
              CREATE TRIGGER IF NOT EXISTS immutable_audit_update BEFORE UPDATE ON audit_events BEGIN SELECT RAISE(ABORT,'Audit is append-only'); END;
              CREATE TRIGGER IF NOT EXISTS immutable_audit_delete BEFORE DELETE ON audit_events BEGIN SELECT RAISE(ABORT,'Audit is append-only'); END;
              CREATE TRIGGER IF NOT EXISTS immutable_qa_update BEFORE UPDATE ON qa_events BEGIN SELECT RAISE(ABORT,'QA events are append-only'); END;
              CREATE TRIGGER IF NOT EXISTS immutable_qa_delete BEFORE DELETE ON qa_events BEGIN SELECT RAISE(ABORT,'QA events are append-only'); END;''')
            cols={r[1] for r in db.execute('PRAGMA table_info(inspections)')}
            for col,typ in [('batch_id',"TEXT NOT NULL DEFAULT 'LEGACY'"),('image_sha256','TEXT')]:
                if col not in cols:db.execute('ALTER TABLE inspections ADD COLUMN '+col+' '+typ)
            db.execute("INSERT OR IGNORE INTO batches VALUES('LEGACY','unspecified','Historical/unassigned evidence','unspecified','legacy',?,NULL,'OPEN')",(now(),))
            db.execute('CREATE INDEX IF NOT EXISTS inspection_batch ON inspections(batch_id,created_at)')
            db.execute('CREATE INDEX IF NOT EXISTS image_hash ON inspections(image_sha256)')
            db.execute("CREATE TRIGGER IF NOT EXISTS immutable_identity BEFORE UPDATE OF batch_id,image_sha256 ON inspections BEGIN SELECT RAISE(ABORT,'Evidence identity is immutable'); END")
            db.execute("CREATE TRIGGER IF NOT EXISTS valid_batch BEFORE INSERT ON inspections WHEN NOT EXISTS(SELECT 1 FROM batches WHERE id=NEW.batch_id) BEGIN SELECT RAISE(ABORT,'Unknown batch'); END")
            db.execute('PRAGMA user_version=2')
            if not db.execute('SELECT 1 FROM audit_events LIMIT 1').fetchone():self._audit(db,'system','migration.v2',{'legacy_count':db.execute('SELECT count(*) FROM inspections').fetchone()[0],'scope':'Historical decisions unchanged; chain starts at migration.'})
        self.replay()

    def connection(self):
        from contextlib import contextmanager
        @contextmanager
        def connect():
            db=sqlite3.connect(self.path,timeout=1)
            try:
                db.execute('PRAGMA foreign_keys=ON');db.execute('PRAGMA synchronous=FULL')
                with db:yield db
            finally:db.close()
        return connect()

    def _audit(self,db,actor,event_type,payload):
        prev=db.execute('SELECT event_hash FROM audit_events ORDER BY seq DESC LIMIT 1').fetchone()
        event=dict(event_id=uuid.uuid4().hex,actor=str(actor)[:80],event_type=event_type,created_at=now(),previous_hash=prev[0] if prev else '0'*64,payload=payload)
        sha=digest(event)
        db.execute('INSERT INTO audit_events(event_id,actor,event_type,created_at,previous_hash,payload_json,event_hash) VALUES(?,?,?,?,?,?,?)',(event['event_id'],event['actor'],event_type,event['created_at'],event['previous_hash'],canonical(payload),sha));return sha

    def _apply(self,op):
        k,v=op['kind'],op['value']
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM replayed_operations WHERE id=?',(op['id'],)).fetchone():return
            if k=='add':
                db.execute('INSERT INTO inspections(id,created_at,source,decision,severity,record_json,batch_id,image_sha256) VALUES(?,?,?,?,?,?,?,?)',(v['inspection_id'],v['created_at'],v['source'],v['decision'],v['severity'],canonical(v),v.get('batch_id','LEGACY'),v.get('original_image_sha256')))
                self._audit(db,v.get('operator','system'),'inspection.created',{'inspection_id':v['inspection_id'],'record_sha256':digest(v),'batch_id':v.get('batch_id','LEGACY')})
            elif k=='advice':
                db.execute('UPDATE inspections SET advice_json=? WHERE id=?',(canonical(v['value']),v['id']))
                seq=db.execute('INSERT INTO advisory_events(inspection_id,created_at,payload_json) VALUES(?,?,?)',(v['id'],now(),canonical(v['value']))).lastrowid
                self._audit(db,'advisor','advisory.recorded',{'inspection_id':v['id'],'value_sha256':digest(v['value']),'advisory_event_seq':seq})
            elif k=='review':
                db.execute('INSERT INTO qa_events(inspection_id,created_at,payload_json) VALUES(?,?,?)',(v['id'],v['review']['reviewed_at'],canonical(v['review'])))
                db.execute('UPDATE inspections SET qa_json=? WHERE id=?',(canonical(v['review']),v['id']))
                self._audit(db,v['review']['reviewer'],'qa.review.appended',{'inspection_id':v['id'],'review':v['review']})
            elif k=='job':db.execute('INSERT INTO advisory_jobs VALUES(?,?,?,?) ON CONFLICT(inspection_id) DO UPDATE SET state=excluded.state,updated_at=excluded.updated_at,detail=excluded.detail',(v['id'],v['state'],now(),v.get('detail')))
            elif k=='event':self._audit(db,v['actor'],v['event_type'],v['payload'])
            else:raise ValueError('Unknown durable operation')
            db.execute('INSERT INTO replayed_operations VALUES(?)',(op['id'],))

    def _write(self,kind,value):
        op=dict(id=uuid.uuid4().hex,kind=kind,value=value,queued_at=now())
        with self.lock:
            try:self._apply(op);self.last_error=None;return True
            except sqlite3.OperationalError as error:
                self.last_error=str(error)
                path=self.root/'spool'/(op['queued_at'].replace(':','-')+'_'+op['id']+'.json');tmp=path.with_suffix('.tmp')
                with tmp.open('x',encoding='utf8') as f:f.write(canonical(op));f.flush();os.fsync(f.fileno())
                tmp.replace(path)
                if os.name!='nt':
                    directory=os.open(str(path.parent),os.O_RDONLY|os.O_DIRECTORY)
                    try:os.fsync(directory)
                    finally:os.close(directory)
                return False

    def replay(self):
        count=0
        with self.lock:
            for p in sorted((self.root/'spool').glob('*.json')):
                try:self._apply(json.loads(p.read_text()));p.unlink();count+=1
                except (sqlite3.Error,ValueError,KeyError) as e:self.last_error=str(e);break
        return count

    def add(self,record):return self._write('add',record)
    def advice(self,id,value):return self._write('advice',{'id':id,'value':value})
    def event(self,event_type,payload,actor='system'):return self._write('event',dict(event_type=event_type,payload=payload,actor=actor))
    def job(self,id,state,detail=None):return self._write('job',dict(id=id,state=state,detail=detail))
    def get(self,id):
        try:value=super().get(id)
        except sqlite3.OperationalError:value=None
        if value:
            with self.connection() as db:value.setdefault('batch_id',db.execute('SELECT batch_id FROM inspections WHERE id=?',(id,)).fetchone()[0])
            return value
        for p in (self.root/'spool').glob('*.json'):
            op=json.loads(p.read_text())
            if op['kind']=='add' and op['value']['inspection_id']==id:return dict(op['value'],advice=None,qa_review=None,persistence_status='spooled')
        return None

    def recent(self,limit=50,batch_id=None):
        with self.connection() as db:rows=db.execute('SELECT id,created_at,source,decision,severity,advice_json,qa_json,batch_id FROM inspections '+('WHERE batch_id=? ' if batch_id else '')+'ORDER BY created_at DESC LIMIT ?',([batch_id] if batch_id else [])+[min(max(limit,1),500)]).fetchall()
        return [dict(inspection_id=r[0],created_at=r[1],source=r[2],decision=r[3],severity=r[4],advice_status=(json.loads(r[5]) or {}).get('status','pending') if r[5] else 'pending',qa_reviewed=bool(r[6]),batch_id=r[7]) for r in rows]

    def review(self,id,review):
        if self.get(id) is None:raise KeyError(id)
        v=dict(review,reviewed_at=now(),note='Operator-entered review; inspection decision is preserved. Not product-release authorization.')
        self._write('review',dict(id=id,review=v));return v
    def reviews(self,id):
        with self.connection() as db:return [json.loads(r[0]) for r in db.execute('SELECT payload_json FROM qa_events WHERE inspection_id=? ORDER BY seq',(id,))]
    def advice_history(self,id):
        with self.connection() as db:return [dict(created_at=r[0],advice=json.loads(r[1])) for r in db.execute('SELECT created_at,payload_json FROM advisory_events WHERE inspection_id=? ORDER BY seq',(id,))]
    def duplicate(self,sha):
        with self.connection() as db:r=db.execute('SELECT id FROM inspections WHERE image_sha256=? ORDER BY created_at LIMIT 1',(sha,)).fetchone()
        return r[0] if r else None

    def create_batch(self,value,actor='operator'):
        if set(value)!={'batch_id','sku','description','category','operator'} or any(not isinstance(v,str) or not 1<=len(v.strip())<=240 for v in value.values()):raise ValueError('Provide bounded batch_id, sku, description, category and operator strings')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',value['batch_id']):raise ValueError('Invalid batch ID')
        if value['category'] not in {'tablet','capsule','blister','unspecified'}:raise ValueError('Choose tablet, capsule, blister or unspecified')
        with self.lock,self.connection() as db:
            db.execute('BEGIN IMMEDIATE');db.execute("INSERT INTO batches VALUES(?,?,?,?,?,?,NULL,'OPEN')",tuple(value[k] for k in ['batch_id','sku','description','category','operator'])+(now(),));self._audit(db,actor,'batch.created',value)
        return self.batch(value['batch_id'])
    def batch(self,id):
        with self.connection() as db:
            row=db.execute('SELECT * FROM batches WHERE id=?',(id,)).fetchone()
            if not row:return None
            counts=dict(db.execute('SELECT decision,count(*) FROM inspections WHERE batch_id=? GROUP BY decision',(id,)));classes={};lat=[]
            for (raw,) in db.execute('SELECT record_json FROM inspections WHERE batch_id=?',(id,)):
                r=json.loads(raw);lat.append(r.get('vision_ms',0))
                for d in r.get('defects',[]):classes[d['type']]=classes.get(d['type'],0)+d['count']
        return dict(zip(['batch_id','sku','description','category','operator','started_at','ended_at','status'],row),counts={'total':sum(counts.values()),**{k:counts.get(k,0) for k in ['PASS','HOLD','REVIEW']}},defect_distribution=classes,mean_detector_ms=sum(lat)/len(lat) if lat else None,warning='Visual inspection only; batch closure is not pharmaceutical release authorization.')
    def batches(self):
        with self.connection() as db:ids=[r[0] for r in db.execute('SELECT id FROM batches ORDER BY started_at DESC')]
        return [self.batch(id) for id in ids]
    def close_batch(self,id,actor):
        with self.lock,self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("UPDATE batches SET status='CLOSED',ended_at=? WHERE id=? AND status='OPEN'",(now(),id)).rowcount!=1:raise ValueError('Batch missing or already closed')
            self._audit(db,actor,'batch.closed',dict(batch_id=id))
        return self.batch(id)
    def active_batch(self):
        with self.connection() as db:row=db.execute("SELECT value FROM station_settings WHERE key='active_batch'").fetchone()
        return row[0] if row else 'LEGACY'
    def select_batch(self,id,actor):
        with self.lock,self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT status FROM batches WHERE id=?',(id,)).fetchone()
            if not row or row[0]!='OPEN':raise ValueError('Choose an open batch')
            db.execute("INSERT INTO station_settings VALUES('active_batch',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(id,))
            self._audit(db,actor,'batch.selected',dict(batch_id=id))
        return self.batch(id)
    def recover_jobs(self):
        with self.lock,self.connection() as db:
            ids=[r[0] for r in db.execute("SELECT inspection_id FROM advisory_jobs WHERE state IN ('pending','running')")]
            if ids:
                db.execute("UPDATE advisory_jobs SET state='interrupted',updated_at=?,detail='Previous process ended; original decision preserved' WHERE state IN ('pending','running')",(now(),))
                self._audit(db,'system','advisory.jobs.recovered',{'inspection_ids':ids})
        return ids
    def audit(self,limit=200):
        with self.connection() as db:return [dict(zip(['seq','event_id','actor','event_type','created_at','previous_hash','payload','event_hash'],r)) for r in db.execute('SELECT * FROM audit_events ORDER BY seq DESC LIMIT ?',(min(max(limit,1),1000),))]
    def verify_integrity(self,verify_images=False):
        prev='0'*64;count=0;errors=[]
        image_errors=[];images_checked=0
        with self.connection() as db:
            for seq,id,actor,kind,at,previous,payload,sha in db.execute('SELECT * FROM audit_events ORDER BY seq'):
                v=dict(event_id=id,actor=actor,event_type=kind,created_at=at,previous_hash=previous,payload=json.loads(payload))
                if previous!=prev or digest(v)!=sha:errors.append(seq)
                if kind=='inspection.created':
                    r=db.execute('SELECT record_json FROM inspections WHERE id=?',(v['payload']['inspection_id'],)).fetchone()
                    if not r or digest(json.loads(r[0]))!=v['payload']['record_sha256']:errors.append(seq)
                    if verify_images and r:
                        record=json.loads(r[0]);image_sha=record.get('original_image_sha256')
                        if image_sha:
                            path=self.root/'images'/(record['inspection_id']+'_original.jpg');images_checked+=1
                            if not path.is_file():image_errors.append(record['inspection_id'])
                            else:
                                with path.open('rb') as f:
                                    if hashlib.file_digest(f,'sha256').hexdigest()!=image_sha:image_errors.append(record['inspection_id'])
                        if record.get('source_image_sha256'):
                            source=self.root/'images'/(record['inspection_id']+'_source.bin')
                            if not source.is_file():image_errors.append(record['inspection_id'])
                            else:
                                with source.open('rb') as f:
                                    if hashlib.file_digest(f,'sha256').hexdigest()!=record['source_image_sha256']:image_errors.append(record['inspection_id'])
                if kind=='advisory.recorded' and v['payload'].get('advisory_event_seq'):
                    item=db.execute('SELECT payload_json FROM advisory_events WHERE seq=?',(v['payload']['advisory_event_seq'],)).fetchone()
                    if not item or digest(json.loads(item[0]))!=v['payload']['value_sha256']:errors.append(seq)
                prev=sha;count+=1
            check=db.execute('PRAGMA integrity_check').fetchone()[0]
        return dict(valid=not errors and not image_errors and check=='ok',checked_events=count,invalid_sequences=sorted(set(errors)),head_sha256=prev,sqlite_integrity=check,images_checked=images_checked,invalid_images=image_errors,limitation='Unkeyed chain; anchor backup hashes externally. Does not prevent privileged whole-DB replacement. Legacy unhashed images are outside image verification.')
    def backup(self):
        dest=self.root/'backups'/('evidence_'+uuid.uuid4().hex+'.sqlite3')
        with self.lock,sqlite3.connect(self.path) as src,sqlite3.connect(dest) as dst:src.backup(dst)
        return dict(path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),scope='SQLite snapshot; retain images separately.')
