"""Resident microphone -> official WeKws -> audible acknowledgement -> voice turn."""
from __future__ import annotations
import json
import math
import os
from pathlib import Path
import queue
import subprocess
import shutil
import sys
import threading
import time
import uuid
import wave
from datetime import datetime, timezone

from live_core import PCMFramer, SpeechCapture, resolve_endpoint
from kws_backend import ROOT, build_kws

DATA=ROOT/'data/voice-next'
FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)

class VoiceWorker:
    def __init__(self):
        self.events=queue.Queue(maxsize=50)
        self.log=(DATA/'worker.stderr.log').open('ab',buffering=0)
        self.proc=subprocess.Popen([str(ROOT/'tools/venv-asr/Scripts/python.exe'),'-X','utf8',str(Path(__file__).with_name('turn_worker.py'))],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,encoding='utf-8',bufsize=1,creationflags=FLAGS)
        threading.Thread(target=self._read,name='voice-worker-ipc',daemon=True).start()
    def _read(self):
        try:
            for line in self.proc.stdout:
                try:self.events.put(json.loads(line))
                except json.JSONDecodeError:self.events.put({'type':'protocol_error','error':'Non-JSON worker stdout'})
        finally:self.events.put({'type':'exited','code':self.proc.poll()})
    def send(self,message):
        self.proc.stdin.write(json.dumps(message,ensure_ascii=True)+'\n');self.proc.stdin.flush()
    def close(self):
        if self.proc.poll() is None:
            try:self.send({'op':'shutdown'});self.proc.wait(timeout=3)
            except (OSError,subprocess.TimeoutExpired):
                # This Popen handle belongs only to this service's own worker.
                self.proc.terminate();self.proc.wait(timeout=5)
        self.log.close()

class Resident:
    def __init__(self,config):
        gain=float(config.get('input_gain',1))
        if not math.isfinite(gain) or not 1<=gain<=32:raise ValueError('input_gain must be a fixed finite value from1to32')
        self.input_gain=gain
        self.config=config;self.run_id=os.environ.get("ULTIMA_VOICE_NEXT_RUN_ID") or uuid.uuid4().hex;self.worker=None
        self.queue=queue.Queue(maxsize=100);self.muted=threading.Event()
        self.counters={'callbacks':0,'input_frames':0,'overflows':0,'live_model_packets':0,'peak':0.0,'rms':0.0}
        self.generation=0;self.seen_generation=0
        self.status={'pid':os.getpid(),'run_id':self.run_id,'keyword':config['keyword'],'state':'warming','ready':False,'model':'sherpa-onnx Zipformer native streaming','threshold':config['threshold'],'input_gain':self.input_gain}
        self.phase='warming';self.collector=None;self.last_heartbeat=0;self.turn_id=None;self.last_audio_at=0
        DATA.mkdir(parents=True,exist_ok=True)
        self.log=(DATA/'events.jsonl').open('a',encoding='utf-8',buffering=1)
    def publish(self,event,**values):
        self.status.update(values);self.status.update(self.counters)
        self.status.update(updated_epoch=time.time(),updated_utc=datetime.now(timezone.utc).isoformat())
        tmp=DATA/f'status.{os.getpid()}.tmp'
        tmp.write_text(json.dumps(self.status,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(tmp,DATA/'status.json')
        self.log.write(json.dumps({'event':event,**self.status},ensure_ascii=False)+'\n')
    def heartbeat(self):
        if time.monotonic()-self.last_heartbeat>=2:
            self.publish('heartbeat');self.last_heartbeat=time.monotonic()
    def callback(self,indata,frames,_timing,status):
        self.last_audio_at=time.monotonic()
        self.counters['callbacks']+=1;self.counters['input_frames']+=frames
        if status:self.generation+=1;self.counters['overflows']+=1
        if self.muted.is_set():return
        block=(time.monotonic(),indata[:,0].copy())
        try:self.queue.put_nowait(block)
        except queue.Full:
            self.generation+=1;self.counters['overflows']+=1
            try:self.queue.get_nowait()
            except queue.Empty:pass
            try:self.queue.put_nowait(block)
            except queue.Full:pass
    def reset_audio(self):
        import soxr
        self.resampler=soxr.ResampleStream(self.input_rate,16000,1,dtype='float32',quality='HQ')
        self.kws_frames=PCMFramer(4800);self.vad_frames=PCMFramer(320)
        self.spotter.reset_all();self.seen_generation=self.generation
    def drain(self):
        while True:
            try:self.queue.get_nowait()
            except queue.Empty:break
    def synthesize(self,text,path):
        request=path.with_suffix('.json');request.write_text(json.dumps({'text':text,'output':str(path)},ensure_ascii=False),encoding='utf-8')
        subprocess.run([shutil.which('pwsh.exe') or 'pwsh.exe','-NoProfile','-NonInteractive','-File',str(Path(__file__).with_name('sapi.ps1')),'-Request',str(request)],check=True,capture_output=True,timeout=20,creationflags=FLAGS)
        return path
    def play(self,path):
        import soundfile as sf
        import soxr
        self.muted.set()
        samples,rate=sf.read(str(path),dtype='float32',always_2d=False)
        if samples.ndim>1:samples=samples.mean(axis=1)
        if rate!=self.output_rate:samples=soxr.resample(samples,rate,self.output_rate)
        self.sd.play(samples,self.output_rate,device=self.output_index,blocking=False)
        deadline=time.monotonic()+len(samples)/self.output_rate+5
        while self.sd.get_stream().active:
            self.heartbeat()
            if time.monotonic()>deadline:
                self.sd.stop()
                raise TimeoutError('Playback did not finish')
            time.sleep(.03)
        self.sd.wait()
        time.sleep(.15)
    def listen(self):
        self.muted.set();self.drain();self.reset_audio();self.collector=None;self.phase='ready'
        self.publish('listening',state='ready',ready=True);self.muted.clear()
    def capture(self):
        import webrtcvad
        vad=webrtcvad.Vad(2)
        self.drain();self.reset_audio()
        self.collector=SpeechCapture(lambda pcm:vad.is_speech(pcm,16000),self.config['command_end_silence_seconds'],self.config['command_wait_seconds'],self.config['command_max_seconds'])
        self.phase='capturing';self.publish('capture_start',state='capturing',ready=False);self.muted.clear()
    def submit(self,pcm):
        self.muted.set();self.drain();self.turn_id=uuid.uuid4().hex
        commands=DATA/'commands';commands.mkdir(exist_ok=True)
        path=commands/f'{self.turn_id}.wav'
        with wave.open(str(path),'wb') as f:f.setparams((1,2,16000,0,'NONE','not compressed'));f.writeframes(pcm)
        self.worker.send({'id':self.turn_id,'wav':str(path)})
        self.turn_deadline=time.monotonic()+self.config['worker_timeout_seconds']
        self.phase='processing';self.publish('command_submitted',state='processing',ready=False,turn_id=self.turn_id,command_seconds=len(pcm)/32000)
    def check_worker(self):
        while True:
            try:message=self.worker.events.get_nowait()
            except queue.Empty:return
            kind=message.get('type')
            if kind in ('error','exited','protocol_error'):raise RuntimeError(f'Voice worker unavailable: {message}')
            if kind!='result' or self.phase!='processing' or message.get('id')!=self.turn_id:continue
            result=message.get('result') or {};response=result.get('response') or {}
            self.publish('turn_result',last_transcript=result.get('text'),last_response=response.get('text'),last_turn_ok=result.get('ok'),last_turn_error=result.get('error'))
            reply=result.get('reply_wav')
            if not reply or not Path(reply).is_file():
                text=response.get('text') or '这次没有识别清楚，请重新唤醒后再说一次。'
                reply=self.synthesize(text,DATA/'reply-fallback.wav')
            self.publish('reply_playing',state='speaking',ready=False)
            self.play(reply);self.listen()
    def run(self):
        import numpy as np
        import sounddevice as sd
        self.sd=sd
        self.publish('loading_model',state='warming')
        self.spotter,meta=build_kws(self.config)
        self.status['model_sha256']=meta['model_sha256'];self.status['kws_runtime']=meta
        self.spotter.forward(bytes(9600));self.spotter.forward(bytes(9600))
        self.spotter.reset_all()
        devices=sd.query_devices();apis=sd.query_hostapis()
        self.input_index=resolve_endpoint(devices,apis,self.config['input'],'input')
        self.output_index=resolve_endpoint(devices,apis,self.config['output'],'output')
        self.input_rate=int(devices[self.input_index]['default_samplerate']);self.output_rate=int(devices[self.output_index]['default_samplerate'])
        sd.check_input_settings(device=self.input_index,channels=1,samplerate=self.input_rate,dtype='float32')
        sd.check_output_settings(device=self.output_index,channels=1,samplerate=self.output_rate,dtype='float32')
        self.status.update(input_device=devices[self.input_index]['name'],input_index=self.input_index,input_rate=self.input_rate,output_device=devices[self.output_index]['name'],output_index=self.output_index)
        self.reset_audio()
        prompts=DATA/'prompts';prompts.mkdir(exist_ok=True)
        self.wake_prompt=prompts/'wake.wav';self.empty_prompt=prompts/'empty.wav'
        for name,text in [('wake','在呢，请说。'),('empty','没听到指令，请重新唤醒。'),('ready','新语音入口已就绪，请说，你好问问。'),('error','语音处理暂时出错，请稍后重试。')]:
            self.synthesize(text,prompts/f'{name}.wav')
        self.publish('loading_asr_worker')
        self.worker=VoiceWorker();deadline=time.monotonic()+60
        while True:
            if time.monotonic()>deadline:raise TimeoutError('ASR worker warmup timed out')
            try:message=self.worker.events.get(timeout=.2)
            except queue.Empty:self.heartbeat();continue
            if message.get('type')=='ready' and message.get('asr_ready'):
                self.status['worker_pid']=message.get('pid');self.status['worker_ready']=True;self.status['tts_backend']=message.get('tts_backend');break
            raise RuntimeError(f'ASR worker startup failed: {message}')
        self.muted.set()
        with sd.InputStream(device=self.input_index,samplerate=self.input_rate,channels=1,dtype='float32',blocksize=0,callback=self.callback) as input_stream:
            time.sleep(.2)
            if not self.counters['callbacks']:raise RuntimeError('No audio callbacks from selected microphone')
            self.publish('announcing',state='announcing',ready=False)
            self.play(prompts/'ready.wav');self.listen()
            while True:
                self.heartbeat();self.check_worker()
                if not input_stream.active or time.monotonic()-self.last_audio_at>2:
                    raise RuntimeError('Microphone callbacks stopped; listener is not ready')
                stop=DATA/'stop.request.json'
                if stop.exists():
                    try:
                        if json.loads(stop.read_text(encoding='utf-8'))['run_id']==self.run_id:break
                    except (ValueError,KeyError,OSError):pass
                if self.phase=='processing':
                    if time.monotonic()>self.turn_deadline:raise TimeoutError('Voice turn timed out')
                    time.sleep(.02);continue
                try:captured_at,audio=self.queue.get(timeout=.2)
                except queue.Empty:continue
                if self.generation!=self.seen_generation or time.monotonic()-captured_at>2:
                    self.publish('input_discontinuity',last_capture_aborted=self.phase=='capturing')
                    self.listen();continue
                self.counters['peak']=float(np.max(np.abs(audio)))
                self.counters['rms']=float(np.sqrt(np.mean(audio*audio)))
                samples=self.resampler.resample_chunk(audio,last=False)
                pcm=(np.clip(samples*self.input_gain,-1,1)*32767).astype('<i2').tobytes()
                if self.phase=='ready':
                    for frame in self.kws_frames.feed(pcm):
                        event=self.spotter.forward(frame)
                        self.counters['live_model_packets']+=1
                        if event and event.get('state')==1:
                            self.publish('wake_detected',state='acknowledging',ready=False,last_wake_utc=datetime.now(timezone.utc).isoformat(),last_wake=event)
                            self.play(self.wake_prompt);self.capture();break
                elif self.phase=='capturing':
                    for frame in self.vad_frames.feed(pcm):
                        completed=self.collector.feed(frame)
                        if completed:
                            if completed[0]=='complete':self.submit(completed[1])
                            else:self.publish('command_timeout');self.play(self.empty_prompt);self.listen()
                            break
    def close(self,error=None):
        self.muted.set()
        if self.worker:self.worker.close()
        self.publish('service_exit',state='error' if error else 'stopped',ready=False,last_error=error)
        self.log.close()

def main():
    sys.path.insert(0,str(ROOT))
    from tasks.queue_engine.dispatcher import DispatchLock
    config=json.loads((ROOT/'config/voice-next/live.json').read_text(encoding='utf-8-sig'))
    DATA.mkdir(parents=True,exist_ok=True)
    with DispatchLock(DATA/'service.lock'):
        service=Resident(config);error=None
        try:service.run()
        except KeyboardInterrupt:pass
        except Exception as exc:
            error=str(exc)
            service.publish('service_error',state='error',ready=False,last_error=error)
            try:
                prompt=DATA/'prompts/error.wav'
                if prompt.is_file() and hasattr(service,'sd'):service.play(prompt)
            except Exception:pass
            raise
        finally:service.close(error)

if __name__=='__main__':main()
