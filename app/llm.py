import os
import platform
import queue
import threading
import hashlib
from .advisory_cache import AdvisoryCache
from pathlib import Path
from advisor_src.advisor import Advisor,NativeWorker,token_counter,ADVISOR_VERSION

class Unavailable:
    def __init__(self,reason):self.reason=reason
    def generate(self,*args):raise RuntimeError(self.reason)
    def close(self):pass

def wsl_path(path):
    path=Path(path).resolve()
    if not path.drive or len(path.drive)!=2:raise ValueError('WSL bridge requires a local Windows drive path')
    return '/mnt/'+path.drive[0].lower()+'/'+path.as_posix()[3:]

class LlamaManager:
    def __init__(self,config,store):
        self.config=config;self.store=store;self.jobs=queue.Queue(maxsize=1)
        self.state='idle';self.error=None;self.worker=None;self.advisor=None
        self.camera_active=False;self.active_threads=None
        self.guard=threading.Lock();self.stop=threading.Event()
        self.pending=set();self.cancelled=set();self.active_id=None
        model=Path(config['llama_artifacts'])/config.get('llama_model','Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte')
        if model.is_file():
            with model.open('rb') as f:self.model_hash=hashlib.file_digest(f,'sha256').hexdigest()
        else:self.model_hash='missing'
        identity={'sop_sha256':hashlib.sha256((Path(__file__).resolve().parents[1]/'advisor_src/sop.json').read_bytes()).hexdigest(),
                  'prompt_version':ADVISOR_VERSION,'prompt_mode':config.get('llama_prompt_mode','baseline'),'prompt_budget':config.get('llama_prompt_budget',768),'model_sha256':self.model_hash,'output_tokens':config.get('llama_output_tokens',192)}
        self.cache=AdvisoryCache(identity)
        self.thread=threading.Thread(target=self._loop,daemon=True);self.thread.start()

    def target_threads(self):
        return 2 if self.camera_active and self.config['vision_backend']=='onnx' else self.config['llama_threads']

    def _prepare(self):
        artifacts=Path(self.config['llama_artifacts'])
        model=artifacts/self.config.get('llama_model','Llama-3.2-1B-Instruct-SpinQuant_INT4_EO8.pte')
        tokenizer=artifacts/'tokenizer.model'
        binary=Path(self.config.get('llama_runtime',''))
        for p in (model,tokenizer,binary):
            if not p.is_file():raise FileNotFoundError(f'LLM asset/runtime missing: {p}')
        counter=token_counter(tokenizer)
        threads=self.target_threads()
        worker=NativeWorker(binary,model,tokenizer,threads)
        if os.name=='nt':
            worker.command=['wsl.exe','--exec','env','LD_LIBRARY_PATH='+wsl_path(binary.parent),
                            wsl_path(binary),wsl_path(model),wsl_path(tokenizer),str(threads)]
        self.worker=worker;self.advisor=Advisor(worker,counter,max_new_tokens=self.config.get('llama_output_tokens',192),prompt_mode=self.config.get('llama_prompt_mode','baseline'),prompt_budget=self.config.get('llama_prompt_budget',768))
        self.active_threads=threads

    def _fallback(self,facts,reason):
        result=Advisor(Unavailable(reason),lambda _:0).advise(facts)
        result['service_note']=reason
        return result

    def submit(self,facts,force=False):
        with self.guard:
            if facts['inspection_id'] in self.pending:return True
        if not self.config['advice_enabled']:
            self.store.advice(facts['inspection_id'],self._fallback(facts,'Llama disabled in configuration'))
            self.store.job(facts['inspection_id'],'fallback','Llama disabled in configuration')
            return False
        if not force:
            with self.guard:cached=self.cache.get(facts)
            if cached is not None:
                self.store.advice(facts['inspection_id'],cached);self.store.job(facts['inspection_id'],'cache_hit');return True
        try:
            with self.guard:
                if facts['inspection_id'] in self.pending:return True
                self.jobs.put_nowait(facts);self.pending.add(facts['inspection_id'])
                self.store.job(facts['inspection_id'],'pending')
            return True
        except queue.Full:
            self.store.advice(facts['inspection_id'],self._fallback(facts,'Advisor queue full; immediate SOP fallback'))
            self.store.job(facts['inspection_id'],'fallback','Queue full')
            return False

    def cancel(self,id):
        with self.guard:
            if id not in self.pending:return False
            self.cancelled.add(id)
            if id==self.active_id and self.worker is not None:self.worker.close()
        return True

    def _loop(self):
        while not self.stop.is_set():
            try:facts=self.jobs.get(timeout=.5)
            except queue.Empty:continue
            try:
                self.active_id=facts['inspection_id'];self.store.job(self.active_id,'running')
                if self.active_id in self.cancelled:raise RuntimeError('Advisory cancelled by operator')
                if self.advisor is not None and self.active_threads!=self.target_threads():
                    self.worker.close();self.worker=None;self.advisor=None
                self.state='loading' if self.advisor is None else 'generating'
                if self.advisor is None:self._prepare()
                self.state='generating'
                self.error=None
                result=self.advisor.advise(facts)
                self.error=self.advisor.last_diagnostics.get('fallback_detail')
                result['validation_trace']={'trusted_recommendation':False,
                    'raw_response':self.advisor.last_diagnostics.get('raw_response'),
                    'rejection_detail':self.error,
                    'scope':'Untrusted model text for engineering audit only; UI advice uses only the validated advisory object or explicit fallback.'}
                self.state='ready' if result['status']=='llama_validated' else 'fallback'
            except Exception as error:
                self.error=str(error);self.state='unavailable'
                result=self._fallback(facts,str(error))
            try:
                if self.active_id in self.cancelled:result=self._fallback(facts,'Advisory cancelled by operator')
                result['model_sha256']=self.model_hash
                with self.guard:self.cache.put(facts,result)
                self.store.advice(facts['inspection_id'],result)
                self.store.job(facts['inspection_id'],'cancelled' if self.active_id in self.cancelled else result['status'],self.error)
                if result.get('fallback_reason') in {'RuntimeError','TimeoutError'} and self.worker is not None:
                    self.worker.close();self.worker=None;self.advisor=None
            except Exception as error:
                self.error='Advisory persistence failure: '+str(error);self.state='fallback'
            finally:
                with self.guard:
                    self.pending.discard(facts['inspection_id']);self.cancelled.discard(facts['inspection_id']);self.active_id=None
                self.jobs.task_done()

    def close(self):
        self.stop.set()
        if self.worker is not None:self.worker.close()
        self.thread.join(timeout=3)
        while True:
            try:facts=self.jobs.get_nowait()
            except queue.Empty:break
            try:
                self.store.advice(facts['inspection_id'],self._fallback(facts,'Application stopped before generation'))
                self.store.job(facts['inspection_id'],'interrupted')
            finally:self.jobs.task_done()
