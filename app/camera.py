import json
import threading
import time
from collections import deque
from pathlib import Path
import cv2
from .vision import annotate

class Camera:
    def __init__(self,service):
        self.service=service;self.thread=None;self.stop_event=threading.Event();self.lock=threading.Lock()
        self.condition=threading.Condition(self.lock)
        self.jpeg=None;self.frame=None;self.frame_at=0
        self.status={'running':False,'error':None,'fps':0,'decision':None,'last_inspection_id':None}

    def start(self,source):
        if self.thread is not None and self.thread.is_alive():raise RuntimeError('Stop the current camera before changing source')
        if source not in {'0','1','2','picamera2'}:raise ValueError('Select USB camera 0/1/2 or Pi CSI camera')
        with self.lock:self.jpeg=None;self.frame=None;self.frame_at=0
        self.stop_event.clear();self.status.update(running=True,error=None,source=source,
            fps=0,decision=None,last_inspection_id=None,vision_ms=None,frame_ready=False)
        if hasattr(self.service,'llm'):self.service.llm.camera_active=True
        self.thread=threading.Thread(target=self._run,args=(source,),daemon=True);self.thread.start()

    def _run(self,source):
        capture=None;pi=None;last_saved=0;last_signature=None;intervals=deque(maxlen=30)
        try:
            if source=='picamera2':
                from picamera2 import Picamera2
                pi=Picamera2();pi.configure(pi.create_video_configuration(main={'size':(1280,720),'format':'RGB888'}));pi.start()
            else:
                capture=cv2.VideoCapture(int(source))
                capture.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*'MJPG'))
                capture.set(cv2.CAP_PROP_FRAME_WIDTH,1280);capture.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
                capture.set(cv2.CAP_PROP_FPS,30)
                capture.set(cv2.CAP_PROP_BUFFERSIZE,1)
                if not capture.isOpened():raise RuntimeError('Camera unavailable. Check connection and camera permissions.')
            while not self.stop_event.is_set():
                start=time.monotonic()
                if pi is not None:frame=pi.capture_array()
                else:
                    ok,frame=capture.read()
                    if not ok:raise RuntimeError('Camera stopped returning frames')
                with self.condition:
                    self.frame=frame.copy();self.frame_at=time.monotonic();self.condition.notify_all()
                self.status['frame_ready']=True
                analysis=self.service.analyze(frame)
                detections,decision,severity,quality,latency=analysis
                signature=json.dumps([(d['type'],round(d['confidence'],1)) for d in detections])+decision
                now=time.monotonic()
                # Bound image logging/LLM requests while preserving a live alert every frame.
                if now-last_saved>15 or (signature!=last_signature and now-last_saved>2):
                    record=self.service.inspect(frame,'camera:'+source,analysis)
                    self.status['last_inspection_id']=record['inspection_id'];last_saved=now;last_signature=signature
                ok,encoded=cv2.imencode('.jpg',annotate(frame,detections,decision),[cv2.IMWRITE_JPEG_QUALITY,80])
                if ok:
                    with self.lock:self.jpeg=encoded.tobytes()
                self.status.update(decision=decision,detections=len(detections),vision_ms=latency,capture=quality)
                # Include acquisition, inference, JPEG and pacing in measured
                # application FPS. Processing-only speed would overstate it.
                self.stop_event.wait(max(0,1/30-(time.monotonic()-start)))
                intervals.append(time.monotonic()-start)
                self.status['fps']=round(len(intervals)/max(sum(intervals),.001),2)
        except Exception as error:self.status['error']=str(error)
        finally:
            if capture is not None:capture.release()
            if pi is not None:pi.stop();pi.close()
            self.status['running']=False;self.status['frame_ready']=False
            if hasattr(self.service,'llm'):self.service.llm.camera_active=False

    def stop(self):
        self.stop_event.set()
        if self.thread is not None:self.thread.join(timeout=10)

    def snapshot(self):
        with self.lock:return self.jpeg

    def original(self):
        with self.lock:
            if not self.status['running'] or self.frame is None or time.monotonic()-self.frame_at>3:return None
            return self.frame.copy()

    def frame_age_ms(self):
        with self.lock:return round((time.monotonic()-self.frame_at)*1000,1) if self.frame_at else None

    def fresh_original(self,timeout=2):
        requested=time.monotonic()
        with self.condition:
            while self.status['running'] and self.frame_at<=requested:
                remaining=timeout-(time.monotonic()-requested)
                if remaining<=0:return None
                self.condition.wait(remaining)
            if not self.status['running'] or self.frame is None:return None
            return self.frame.copy()
