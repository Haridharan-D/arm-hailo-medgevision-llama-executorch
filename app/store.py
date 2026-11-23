import json
import sqlite3
from datetime import datetime,timezone
from contextlib import contextmanager

class Store:
    def __init__(self,root):
        self.root=root;self.path=root/'inspections.sqlite3'
        (root/'images').mkdir(exist_ok=True)
        with self.connection() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''CREATE TABLE IF NOT EXISTS inspections(
              id TEXT PRIMARY KEY, created_at TEXT NOT NULL, source TEXT NOT NULL,
              decision TEXT NOT NULL, severity TEXT NOT NULL, record_json TEXT NOT NULL,
              advice_json TEXT, qa_json TEXT);
              CREATE TABLE IF NOT EXISTS qa_events(
              seq INTEGER PRIMARY KEY AUTOINCREMENT, inspection_id TEXT NOT NULL,
              created_at TEXT NOT NULL, payload_json TEXT NOT NULL);
              CREATE INDEX IF NOT EXISTS inspection_time ON inspections(created_at);''')

    @contextmanager
    def connection(self):
        db=sqlite3.connect(self.path,timeout=10)
        try:
            with db:yield db
        finally:db.close()

    def add(self,record):
        with self.connection() as db:
            db.execute('INSERT INTO inspections(id,created_at,source,decision,severity,record_json) VALUES(?,?,?,?,?,?)',
                       (record['inspection_id'],record['created_at'],record['source'],record['decision'],record['severity'],json.dumps(record)))

    def advice(self,id,value):
        with self.connection() as db:db.execute('UPDATE inspections SET advice_json=? WHERE id=?',(json.dumps(value),id))

    def get(self,id):
        with self.connection() as db:row=db.execute('SELECT record_json,advice_json,qa_json FROM inspections WHERE id=?',(id,)).fetchone()
        if row is None:return None
        record=json.loads(row[0]);record['advice']=json.loads(row[1]) if row[1] else None
        record['qa_review']=json.loads(row[2]) if row[2] else None
        return record

    def recent(self,limit=50):
        with self.connection() as db:
            rows=db.execute('SELECT id,created_at,source,decision,severity,advice_json,qa_json FROM inspections ORDER BY created_at DESC LIMIT ?',
                            (min(max(limit,1),500),)).fetchall()
        return [dict(inspection_id=r[0],created_at=r[1],source=r[2],decision=r[3],severity=r[4],
                     advice_status=json.loads(r[5])['status'] if r[5] else 'pending',qa_reviewed=bool(r[6])) for r in rows]

    def stats(self):
        with self.connection() as db:
            counts=dict(db.execute('SELECT decision,count(*) FROM inspections GROUP BY decision').fetchall())
            total=db.execute('SELECT count(*) FROM inspections').fetchone()[0]
        return {'total':total,'HOLD':counts.get('HOLD',0),'REVIEW':counts.get('REVIEW',0),'PASS':counts.get('PASS',0)}

    def review(self,id,review):
        if self.get(id) is None:raise KeyError(id)
        review=dict(review,reviewed_at=datetime.now(timezone.utc).isoformat(),
                    note='Operator-entered review; inspection decision is preserved. Not product-release authorization.')
        with self.connection() as db:
            db.execute('INSERT INTO qa_events(inspection_id,created_at,payload_json) VALUES(?,?,?)',(id,review['reviewed_at'],json.dumps(review)))
            db.execute('UPDATE inspections SET qa_json=? WHERE id=?',(json.dumps(review),id))
        return review

# Keep the v6 implementation above readable; new migrations extend its contract.
from .industrial_store import Store
