"""Desktop entry point and terminal inspector. Models always execute locally."""
import argparse
import json
import logging
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from app.config import settings

def main():
    parser=argparse.ArgumentParser(description='Medge Vision offline inspection')
    parser.add_argument('--inspect',type=Path,help='Inspect an image or a folder from the terminal')
    parser.add_argument('--wait-advice',action='store_true',help='Wait for Llama/SOP output before returning')
    parser.add_argument('--output',type=Path,help='Save terminal inspection JSON')
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--desktop',action='store_true',help='Start the local service in the background and open the dashboard')
    parser.add_argument('--port',type=int)
    args=parser.parse_args();config=settings()
    from logging.handlers import RotatingFileHandler
    handler=RotatingFileHandler(config['data_dir']/'application.log',maxBytes=5*1024*1024,backupCount=5,encoding='utf8')
    logging.basicConfig(handlers=[handler],level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    if args.inspect:
        if not args.wait_advice:config['advice_enabled']=False
        import cv2
        from app.service import InspectionService
        paths=sorted(p for p in args.inspect.iterdir() if p.suffix.lower() in {'.jpg','.jpeg','.png','.bmp','.webp'}) if args.inspect.is_dir() else [args.inspect]
        service=InspectionService(config);rows=[]
        try:
            for path in paths:
                image=cv2.imread(str(path))
                if image is None:raise ValueError(f'Cannot read image: {path}')
                row=service.inspect(image,str(path),source_bytes=path.read_bytes())
                if args.wait_advice:
                    until=time.monotonic()+200
                    while time.monotonic()<until:
                        row=service.store.get(row['inspection_id'])
                        if row['advice'] is not None:break
                        time.sleep(.25)
                rows.append(row)
            text=json.dumps(rows,indent=2)
            if sys.stdout is not None:print(text)
            if args.output:
                args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text)
        finally:service.close()
        return 0
    port=args.port or config['port'];url=f'http://127.0.0.1:{port}'
    with socket.socket() as probe:
        occupied=probe.connect_ex(('127.0.0.1',port))==0
    if occupied:
        from urllib.request import urlopen
        try:
            with urlopen(url+'/api/health',timeout=2) as response:
                existing=json.load(response)
            if existing.get('application')=='BlisterTrace':
                if not args.no_browser:webbrowser.open(url)
                return 0
        except Exception:pass
        raise RuntimeError(f'Port {port} is in use. Choose --port with another port.')
    if args.desktop and not args.no_browser:
        command=[sys.executable]
        if not getattr(sys,'frozen',False):command.append(str(Path(__file__).resolve()))
        command.extend(['--no-browser','--port',str(port)])
        options={'start_new_session':True} if os.name!='nt' else {'creationflags':subprocess.CREATE_NO_WINDOW}
        with (config['data_dir']/'launcher.log').open('ab') as log:
            child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,**options)
        from urllib.request import urlopen
        for _ in range(100):
            if child.poll() is not None:raise RuntimeError('Workstation startup failed. Read '+str(config['data_dir']/'launcher.log'))
            try:
                with urlopen(url+'/api/health',timeout=1):pass
                webbrowser.open(url);return 0
            except OSError:time.sleep(.15)
        raise RuntimeError('Workstation is taking longer to start. Open '+url+' and check launcher.log.')
    if not args.no_browser:
        def open_when_ready():
            from urllib.request import urlopen
            for _ in range(60):
                try:
                    with urlopen(url+'/api/health',timeout=1):pass
                    webbrowser.open(url);return
                except Exception:time.sleep(.5)
        threading.Thread(target=open_when_ready,daemon=True).start()
    if sys.stdout is not None:print('BlisterTrace:',url,flush=True)
    import uvicorn
    from app.server import create_app
    application=create_app(config)
    server=uvicorn.Server(uvicorn.Config(application,host='127.0.0.1',port=port,log_config=None))
    application.state.shutdown_callback=lambda:setattr(server,'should_exit',True)
    server.run()
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        logging.exception('Medge Vision startup failed')
        if getattr(sys,'frozen',False) and sys.platform=='win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,str(error),'Medge Vision startup error',0x10)
        raise
