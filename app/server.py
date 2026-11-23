import csv
import asyncio
import io
import json
import os
import platform
import shutil
import time
from contextlib import asynccontextmanager
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from fastapi import FastAPI,File,UploadFile,HTTPException,Request
from fastapi.responses import FileResponse,StreamingResponse,Response,JSONResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from .config import ROOT,settings
from .service import InspectionService
from .camera import Camera
from .operator import answer
from .traceability import VERSION

def create_app(config=None,service=None):
    config=config or settings()
    @asynccontextmanager
    async def lifespan(app):
        app.state.service=None;app.state.camera=None;app.state.startup_error=None
        app.state.started=time.monotonic()
        async def initialize():
            try:
                ready=service or await asyncio.to_thread(InspectionService,config)
                app.state.service=ready;app.state.camera=Camera(ready)
            except Exception as error:app.state.startup_error=str(error)
        task=asyncio.create_task(initialize())
        try:yield
        finally:
            await task
            if app.state.camera is not None:app.state.camera.stop()
            if app.state.service is not None:app.state.service.close()
    app=FastAPI(title='Medge Vision',lifespan=lifespan)
    slots=asyncio.Semaphore(4)
    @app.middleware('http')
    async def bound_inspection_requests(request,call_next):
        heavy=request.method=='POST' and request.url.path in {'/api/inspect','/api/library/inspect','/api/anomaly/inspect','/api/anomaly/inspect-upload','/api/camera/inspect'}
        if not heavy:return await call_next(request)
        try:await asyncio.wait_for(slots.acquire(),timeout=.05)
        except TimeoutError:return JSONResponse({'detail':'Inspection queue full; retry after current requests complete','outcome':'SYSTEM_FAULT'},status_code=429,headers={'Retry-After':'2'})
        try:return await call_next(request)
        finally:slots.release()
    @app.exception_handler(RuntimeError)
    async def runtime_failure(request,error):
        import logging
        logging.exception('Runtime failure at %s',request.url.path,exc_info=error)
        service=getattr(app.state,'service',None)
        if service and hasattr(service,'store'):service.store.event('system.fault',{'path':request.url.path,'error_type':type(error).__name__})
        return JSONResponse({'detail':'Inspection/runtime unavailable. No acceptable disposition issued. See station log.','outcome':'SYSTEM_FAULT'},status_code=503)
    @app.middleware('http')
    async def local_origin(request,call_next):
        origin=request.headers.get('origin')
        if origin and request.method not in {'GET','HEAD'}:
            from urllib.parse import urlsplit
            if urlsplit(origin).netloc!=request.headers.get('host'):
                return Response('This application accepts same-origin requests only.',status_code=403)
        return await call_next(request)
    def svc():
        if app.state.service is None:raise HTTPException(503,app.state.startup_error or 'Inspection runtime is starting')
        return app.state.service
    def record(id):
        result=svc().store.get(id)
        if not result:raise HTTPException(404,'Inspection not found')
        return result

    from .industrial_api import install
    install(app,config,svc)
    @app.get('/api/health')
    def health():
        return {'application':'BlisterTrace','product_name':'Medge Vision','version':VERSION,
                'ready':app.state.service is not None,'startup_error':app.state.startup_error,
                'startup_elapsed_ms':round((time.monotonic()-app.state.started)*1000)}

    @app.get('/api/status')
    def status():
        temp=None
        path=Path('/sys/class/thermal/thermal_zone0/temp')
        if path.is_file():
            try:temp=round(float(path.read_text())/1000,1)
            except ValueError:pass
        cpu=ram=None
        try:
            import psutil
            cpu=psutil.cpu_percent(interval=None);ram=round(psutil.virtual_memory().percent,1)
        except ImportError:pass
        return {'ready':True,'vision_backend':svc().detector.backend,'model':'YOLOv8s · 7 blister defect classes',
                'application':'BlisterTrace','product_name':'Medge Vision','version':VERSION,'packaged':bool(getattr(__import__('sys'),'frozen',False)),
                'llama_state':svc().llm.state,'llama_error':svc().llm.error,
                'llama_threads':svc().llm.active_threads or config['llama_threads'],
                'llama_target_threads':svc().llm.target_threads(),
                'llama_platform':'WSL x86-64 ExecuTorch' if os.name=='nt' else platform.machine()+' ExecuTorch CPU',
                'profile_validated':config['profile_validated'],'camera':dict(app.state.camera.status,frame_age_ms=app.state.camera.frame_age_ms()),
                'stats':svc().store.stats(),'temperature_c':temp,
                'free_storage_gb':round(shutil.disk_usage(config['data_dir']).free/1024**3,2),
                'anomaly_model':'EfficientAD-S ONNX CPU' if svc().anomaly.profiles() else 'not installed',
                'anomaly_profiles':svc().anomaly.profiles(),'offline':True,'cpu_percent':cpu,'ram_percent':ram,
                'uptime_seconds':round(time.monotonic()-app.state.started)}

    @app.get('/api/display')
    def display_status():
        from .display_state import current_display
        state=current_display(svc(),app.state.camera)
        return JSONResponse({**state,'version':VERSION},headers={'Cache-Control':'no-store, max-age=0','Pragma':'no-cache'})
    @app.post('/api/display/live')
    def display_live():
        s=svc()
        if not app.state.camera.status.get('running'):raise HTTPException(409,'Start the camera first')
        s.display_record=None
        return {'mode':'live_camera'}
    @app.post('/api/inspect')
    async def inspect(file:UploadFile=File(...)):
        data=await file.read(20*1024*1024+1)
        if len(data)>20*1024*1024:raise HTTPException(413,'Choose an image smaller than 20 MB')
        try:
            with Image.open(io.BytesIO(data)) as header:
                if header.width*header.height>25_000_000:raise ValueError('Image exceeds 25 megapixels')
            image=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
            if image is None or min(image.shape[:2])<16:raise ValueError('Not a readable inspection image')
        except Exception as error:raise HTTPException(400,str(error)) from None
        return await run_in_threadpool(svc().inspect,image,Path(file.filename or 'upload').name,source_bytes=data)

    @app.get('/api/library')
    def library():
        root=Path(config['test_images'])
        if not root.is_dir():return []
        manifest=root/'defects/manifest.json'
        groups=json.loads(manifest.read_text()) if manifest.is_file() else []
        demo=root/'acceptance_demo/manifest.json'
        if demo.is_file():groups+=json.loads(demo.read_text())
        curated={r['file']:r for r in groups}
        from urllib.parse import quote
        return [{'name':p.relative_to(root).as_posix(),'url':'/api/library/image/'+quote(p.relative_to(root).as_posix()),
                 'display_name':curated.get(p.relative_to(root).as_posix(),{}).get('case_id','CASE-'+str(index+1).zfill(3)),
                 'group':curated.get(p.relative_to(root).as_posix(),{}).get('group','other'),
                 'label_origin':curated.get(p.relative_to(root).as_posix(),{}).get('label_origin','Unannotated demonstration image')}
                for index,p in enumerate(sorted(root.rglob('*')))
                if p.is_file() and p.suffix.lower() in {'.jpg','.jpeg','.png','.webp','.bmp'}][:500]

    @app.get('/api/anomaly/profiles')
    def anomaly_profiles():return svc().anomaly.profiles()
    @app.get('/api/anomaly/samples/{profile}')
    def anomaly_samples(profile:str):
        try:
            return [dict(row,url=f'/api/anomaly/samples/{profile}/{row["file"]}') for row in svc().anomaly.samples(profile)]
        except ValueError as error:raise HTTPException(400,str(error)) from None
    @app.get('/api/anomaly/samples/{profile}/{name:path}')
    def anomaly_sample_image(profile:str,name:str):
        try:path,_=svc().anomaly.sample_path(profile,name)
        except ValueError as error:raise HTTPException(404,str(error)) from None
        return FileResponse(path)
    @app.post('/api/anomaly/inspect')
    async def anomaly_inspect(request:Request):
        value=await request.json()
        if not isinstance(value,dict) or set(value)-{'profile','sample','inspection_id'}:
            raise HTTPException(400,'Choose an anomaly profile and a sample or pinned inspection')
        profile=value.get('profile');parent=sample=None
        if bool(value.get('sample'))==bool(value.get('inspection_id')):
            raise HTTPException(400,'Choose exactly one image source')
        try:
            if value.get('sample'):path,sample=svc().anomaly.sample_path(profile,value['sample']);source='anomaly-test:'+sample['source_path']
            else:
                parent=record(str(value['inspection_id']))
                path=config['data_dir']/'images'/(parent['inspection_id']+'_original.jpg');source='anomaly-pinned:'+parent['inspection_id']
            image=cv2.imread(str(path))
            if image is None:raise ValueError('Image unavailable')
            return await run_in_threadpool(svc().inspect_anomaly,image,profile,source,parent,sample)
        except ValueError as error:raise HTTPException(400,str(error)) from None
    @app.post('/api/anomaly/inspect-upload')
    async def anomaly_upload(profile:str,file:UploadFile=File(...)):
        data=await file.read(20*1024*1024+1)
        if len(data)>20*1024*1024:raise HTTPException(413,'Choose an image smaller than 20 MB')
        try:
            with Image.open(io.BytesIO(data)) as header:
                if header.width*header.height>25_000_000:raise ValueError('Image exceeds 25 megapixels')
            image=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
            if image is None or min(image.shape[:2])<16:raise ValueError('Not a readable inspection image')
            return await run_in_threadpool(svc().inspect_anomaly,image,profile,'anomaly-upload:'+Path(file.filename or 'upload').name)
        except (ValueError,OSError) as error:raise HTTPException(400,str(error)) from None
    def library_path(name):
        root=Path(config['test_images']).resolve();target=(root/name).resolve()
        if root not in target.parents or not target.is_file() or target.suffix.lower() not in {'.jpg','.jpeg','.png','.webp','.bmp'}:
            raise HTTPException(404,'Test image not found')
        return target
    @app.get('/api/library/image/{name:path}')
    def library_image(name:str):return FileResponse(library_path(name))
    @app.post('/api/library/inspect')
    async def library_inspect(request:Request):
        data=await request.json();path=library_path(str(data.get('name','')))
        image=cv2.imread(str(path))
        if image is None:raise HTTPException(400,'Image could not be decoded')
        return await run_in_threadpool(svc().inspect,image,'test:'+path.name,source_bytes=path.read_bytes())

    @app.get('/api/inspections')
    def history(limit:int=50,batch_id:str|None=None):return svc().store.recent(limit,batch_id)
    @app.get('/api/inspections/{id}')
    def get_record(id:str):return record(id)
    @app.get('/api/inspections/{id}/image')
    def annotated(id:str):
        record(id);return FileResponse(config['data_dir']/'images'/(id+'.jpg'))
    @app.get('/api/inspections/{id}/original')
    def original(id:str):
        record(id);return FileResponse(config['data_dir']/'images'/(id+'_original.jpg'))
    @app.get('/api/inspections/{id}/source')
    def source_file(id:str):
        if not record(id).get('source_image_sha256'):raise HTTPException(404,'No original input file; camera used a decoded frame')
        return FileResponse(config['data_dir']/'images'/(id+'_source.bin'),media_type='application/octet-stream',filename=id+'_source.bin')
    @app.get('/api/inspections/{id}/heatmap')
    def heatmap(id:str):
        if not record(id).get('anomaly'):raise HTTPException(404,'No anomaly inference has been recorded for this image')
        return FileResponse(config['data_dir']/'images'/(id+'_heatmap.png'),media_type='image/png')
    @app.post('/api/inspections/{id}/advice')
    def advice(id:str):
        record(id);return {'queued':svc().request_advice(id)}
    @app.post('/api/inspections/{id}/ask')
    async def ask(id:str,request:Request):
        value=await request.json()
        if not isinstance(value,dict) or set(value)-{'question','intent'}:
            raise HTTPException(400,'Use an inspection question or supported intent')
        try:return answer(record(id),value.get('question',''),value.get('intent'))
        except ValueError as error:raise HTTPException(400,str(error)) from None
    @app.get('/api/inspections/{id}/report')
    def report(id:str):
        return Response(json.dumps(record(id),indent=2),media_type='application/json',
            headers={'Content-Disposition':'attachment; filename=inspection_'+id+'.json'})
    @app.post('/api/inspections/{id}/qa')
    async def qa(id:str,request:Request):
        record(id);value=await request.json()
        if set(value)!={'reviewer','comment'} or not isinstance(value['reviewer'],str) or not 1<=len(value['reviewer'].strip())<=80:
            raise HTTPException(400,'Enter a reviewer name, up to 80 characters')
        if not isinstance(value['comment'],str) or not 1<=len(value['comment'].strip())<=1000:
            raise HTTPException(400,'Enter a review comment, up to 1000 characters')
        from .auth import actor
        if app.state.auth.required:value=dict(value,reviewer=actor.get(),entered_reviewer=value['reviewer'])
        return svc().store.review(id,value)
    @app.get('/api/export.csv')
    def export_csv():
        stream=io.StringIO();writer=csv.writer(stream);writer.writerow(['id','created_at','source','decision','severity','advice_status','qa_reviewed'])
        for row in svc().store.recent(500):
            values=[row[k] for k in ('inspection_id','created_at','source','decision','severity','advice_status','qa_reviewed')]
            # Prevent spreadsheet formula execution from uploaded filenames/comments.
            writer.writerow(["'"+v if isinstance(v,str) and v[:1] in '=+-@' else v for v in values])
        return Response(stream.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=blistertrace_inspections.csv'})

    @app.post('/api/camera/start')
    async def camera_start(request:Request):
        svc()
        data=await request.json()
        try:app.state.camera.start(str(data.get('source','0')));svc().display_record=None
        except (ValueError,RuntimeError) as error:raise HTTPException(400,str(error)) from None
        return {'started':True}
    @app.post('/api/camera/stop')
    def camera_stop():svc();app.state.camera.stop();return {'stopped':True}
    @app.post('/api/camera/inspect')
    async def camera_inspect():
        svc()
        image=await run_in_threadpool(app.state.camera.fresh_original)
        if image is None:raise HTTPException(409,'Start the camera and wait for a live frame before inspecting')
        return await run_in_threadpool(svc().inspect,image,'camera:operator-trigger')
    @app.post('/api/shutdown')
    def shutdown():
        callback=getattr(app.state,'shutdown_callback',None)
        if callback is None:raise HTTPException(409,'Shutdown is managed by the test host')
        callback();return {'shutting_down':True}
    @app.get('/api/camera/stream')
    def stream(request:Request):
        svc()
        def frames():
            while app.state.camera.status['running']:
                jpeg=app.state.camera.snapshot()
                if jpeg:yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'+jpeg+b'\r\n'
                time.sleep(.1)
        return StreamingResponse(frames(),media_type='multipart/x-mixed-replace; boundary=frame')
    @app.get('/')
    def index():return FileResponse(ROOT/'web/aoi.html')
    @app.get('/classic')
    def classic():return FileResponse(ROOT/'web/classic.html')
    @app.get('/display')
    def verdict_display():return FileResponse(ROOT/'web/display.html')
    @app.get('/design-a')
    def saved_design(request:Request):
        if app.state.auth.user(request.cookies.get('bt_session')) is None:return RedirectResponse('/operations?next=/design-a')
        return FileResponse(ROOT/'web/design-a/aoi.html')
    app.mount('/static',StaticFiles(directory=ROOT/'web'),name='static')
    return app
