"""Local batch, audit and maintenance endpoints; no changes to vision policy."""
import csv,io,json,sqlite3
from pathlib import Path
from fastapi import APIRouter,HTTPException,Request
from fastapi.responses import Response,FileResponse
from .auth import LocalAuth,actor
from .traceability import storage_health,VERSION
from .pdf_report import batch_pdf

def install(app,config,svc):
    auth=LocalAuth(config['data_dir'],config.get('auth_required'));app.state.auth=auth
    @app.middleware('http')
    async def access(request,call_next):
        path=request.url.path
        public=path in {'/api/health','/api/live','/api/ready','/api/auth/login','/api/auth/me','/api/auth/bootstrap'} or not path.startswith('/api/')
        user=auth.user(request.cookies.get('bt_session'))
        if not public and not user:return Response('{"detail":"Local sign-in required"}',status_code=401,media_type='application/json')
        if not public and not auth.allowed(user,request.method,path):return Response('{"detail":"Role cannot perform this action"}',status_code=403,media_type='application/json')
        request.state.user=user
        token=actor.set(user['name'] if user else 'anonymous')
        try:
            response=await call_next(request)
            if path.startswith('/api/') and request.method not in {'GET','HEAD'} and app.state.service is not None and hasattr(svc(),'store'):
                svc().store.event('api.action',dict(path=path,status=response.status_code),actor.get())
            return response
        finally:actor.reset(token)
    @app.get('/api/live')
    def live():return {'alive':True,'version':VERSION}
    @app.get('/api/ready')
    def ready():
        s=svc();disk=storage_health(config['data_dir'])
        if s.detector.backend=='hailo' and not Path('/dev/hailo0').exists():raise HTTPException(503,'Hailo device unavailable; manual review required')
        if getattr(s,'last_vision_error',None):raise HTTPException(503,'Vision runtime fault; manual review required')
        try:
            with s.store.connection() as db:db.execute('SELECT 1').fetchone()
        except sqlite3.Error:raise HTTPException(503,'Database unavailable; durable spool retained')
        if disk['state']=='critical':raise HTTPException(503,'Evidence disk critically low')
        return {'ready':disk['state']!='critical','vision_backend':s.detector.backend,'database':'ready','storage':disk,'llama':s.llm.state,'camera_validation':'excluded'}
    @app.get('/api/auth/me')
    def me(request:Request):return {'required':auth.required,'needs_setup':auth.required and not auth.file.exists(),'user':auth.user(request.cookies.get('bt_session'))}
    @app.post('/api/auth/bootstrap')
    async def bootstrap(request:Request):
        if request.client.host not in {'127.0.0.1','::1','testclient'}:raise HTTPException(403,'Initial account setup is local-only')
        from .auth import credential
        import os,re
        v=await request.json()
        if not isinstance(v,dict) or set(v)!={'username','password'} or not isinstance(v['username'],str) or not re.fullmatch('[A-Za-z0-9_-]{1,64}',v['username']) or not isinstance(v['password'],str) or len(v['password'])>256:raise HTTPException(400,'Invalid account input')
        try:user=credential(v['password'],'administrator')
        except ValueError as e:raise HTTPException(400,str(e))
        with auth.lock:
            if auth.file.exists():raise HTTPException(409,'Initial setup is already complete')
            with auth.file.open('x',encoding='utf8') as f:os.chmod(auth.file,0o600);json.dump({v['username']:user},f)
            auth.required=True
        return {'created':True,'role':'administrator'}
    @app.post('/api/auth/login')
    async def login(request:Request):
        data=await request.json()
        if not isinstance(data,dict) or set(data)!={'username','password'} or not all(isinstance(v,str) and len(v)<=256 for v in data.values()):raise HTTPException(400,'Invalid login input')
        try:token,user=auth.login(data['username'],data['password'],request.client.host)
        except ValueError as e:raise HTTPException(401,str(e))
        response=Response(json.dumps({'user':user}),media_type='application/json');response.set_cookie('bt_session',token,httponly=True,samesite='strict',max_age=28800);return response
    @app.post('/api/auth/logout')
    def logout(request:Request):
        auth.logout(request.cookies.get('bt_session'));r=Response('{}',media_type='application/json');r.delete_cookie('bt_session');return r
    @app.get('/api/batches')
    def batches():return svc().store.batches()
    @app.post('/api/batches')
    async def create_batch(request:Request):
        value=await request.json()
        try:return svc().store.create_batch(value,actor.get())
        except (ValueError,sqlite3.IntegrityError) as e:raise HTTPException(400,str(e))
    @app.post('/api/batches/{id}/select')
    def select_batch(id:str):
        value=svc().store.batch(id)
        if not value or value['status']!='OPEN':raise HTTPException(400,'Choose an open batch')
        svc().store.select_batch(id,actor.get());config['active_batch']=id;return value
    @app.post('/api/batches/{id}/close')
    def close_batch(id:str):
        try:return svc().store.close_batch(id,actor.get())
        except ValueError as e:raise HTTPException(400,str(e))
    @app.get('/api/batches/{id}/report')
    def report(id:str,format:str='json'):
        batch=svc().store.batch(id)
        if not batch:raise HTTPException(404,'Batch unavailable')
        with svc().store.connection() as db:ids=[r[0] for r in db.execute('SELECT id FROM inspections WHERE batch_id=? ORDER BY created_at',(id,))]
        rows=[svc().store.get(i) for i in ids];head=svc().store.verify_integrity()['head_sha256']
        if format=='pdf':return Response(batch_pdf(batch,rows,head),media_type='application/pdf',headers={'Content-Disposition':'attachment; filename=batch_'+id+'.pdf'})
        if format=='csv':
            stream=io.StringIO();w=csv.writer(stream);keys=['inspection_id','created_at','source','decision','severity','original_image_sha256','model_sha256','configuration_revision'];w.writerow(keys)
            for r in rows:w.writerow([("'"+str(r.get(k,''))) if str(r.get(k,''))[:1] in '=+-@' else r.get(k,'') for k in keys])
            return Response(stream.getvalue(),media_type='text/csv')
        if format!='json':raise HTTPException(400,'Choose json, csv or pdf')
        return {'batch':batch,'inspections':rows,'audit_head':head}
    @app.get('/api/audit')
    def audit():return svc().store.audit()
    @app.get('/api/audit/verify')
    def verify():return svc().store.verify_integrity(verify_images=True)
    @app.get('/api/inspections/{id}/reviews')
    def reviews(id:str):return svc().store.reviews(id)
    @app.get('/api/inspections/{id}/advice-history')
    def advice_history(id:str):return svc().store.advice_history(id)
    @app.post('/api/inspections/{id}/cancel-advice')
    def cancel(id:str):return {'cancelled':svc().llm.cancel(id)}
    @app.post('/api/database/backup')
    def backup():return svc().store.backup()
    @app.post('/api/database/replay')
    def replay():return {'replayed':svc().store.replay()}
    @app.get('/api/operations/health')
    def health():
        s=svc()
        import psutil,time
        temp_path=Path('/sys/class/thermal/thermal_zone0/temp');temp=float(temp_path.read_text())/1000 if temp_path.exists() else None
        return {'version':VERSION,'active_batch':config.get('active_batch','LEGACY'),'storage':storage_health(config['data_dir']),
            'spooled_operations':len(list((config['data_dir']/'spool').glob('*.json'))),'database_error':s.store.last_error,
            'database_bytes':s.store.path.stat().st_size,'llama_queue_depth':s.llm.jobs.qsize(),'llama_active_id':s.llm.active_id,
            'llama_model_sha256':s.llm.model_hash,'npu_utilization':None,'npu_utilization_note':'No supported device utilization sampler installed',
            'authentication_required':auth.required,'retention':'Manual verified archival only; no automatic deletion',
            'hailo_device_present':Path('/dev/hailo0').exists() if s.detector.backend=='hailo' else None,
            'vision_error':getattr(s,'last_vision_error',None),'system_uptime_seconds':round(time.time()-psutil.boot_time()),
            'available_ram_mib':round(psutil.virtual_memory().available/1024**2),'swap_used_bytes':psutil.swap_memory().used,
            'temperature_state':'unavailable' if temp is None else 'critical' if temp>=85 else 'warning' if temp>=80 else 'ok'}
    @app.get('/operations')
    def operations():return FileResponse(Path(__file__).resolve().parents[1]/'web/operations.html')
