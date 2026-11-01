"""Small input framing and turn boundaries; model/VAD algorithms stay upstream."""
from collections import deque

class PCMFramer:
    def __init__(self,samples):
        if samples<=0:raise ValueError('positive frame size required')
        self.size=samples*2
        self.pending=bytearray()
    def feed(self,data):
        self.pending.extend(data)
        frames=[]
        while len(self.pending)>=self.size:
            frames.append(bytes(self.pending[:self.size]));del self.pending[:self.size]
        return frames
    def reset(self):self.pending.clear()

class SpeechCapture:
    def __init__(self,is_speech,end_silence=.8,wait_seconds=5,max_seconds=15):
        self.is_speech=is_speech
        self.end_frames=max(1,round(end_silence/.02))
        self.wait_frames=max(1,round(wait_seconds/.02))
        self.max_frames=max(1,round(max_seconds/.02))
        self.pre=deque(maxlen=15);self.frames=[];self.started=False
        self.count=0;self.run=0;self.quiet=0;self.speech_frames=0
    def feed(self,pcm):
        if len(pcm)!=640:raise ValueError('VAD requires exactly 20ms PCM16 at16k')
        voiced=self.is_speech(pcm)
        self.count+=1;self.pre.append(pcm)
        self.run=self.run+1 if voiced else 0
        self.speech_frames+=int(voiced)
        if self.started:
            self.frames.append(pcm);self.quiet=0 if voiced else self.quiet+1
        elif self.run>=3:
            self.started=True;self.frames=list(self.pre);self.quiet=0
        if self.started and (self.quiet>=self.end_frames or self.count>=self.max_frames):
            return ('complete',b''.join(self.frames)) if self.speech_frames>=5 else ('empty',b'')
        if not self.started and self.count>=min(self.wait_frames,self.max_frames):return ('empty',b'')
        return None

def resolve_endpoint(devices,hostapis,spec,direction):
    key='max_input_channels' if direction=='input' else 'max_output_channels'
    found=[i for i,d in enumerate(devices) if d.get(key,0)>0 and
           spec['name_contains'].casefold() in d['name'].casefold() and
           hostapis[d['hostapi']]['name']==spec['hostapi']]
    if len(found)!=1:raise ValueError(f'Expected one {direction} endpoint for {spec}, found {found}')
    return found[0]
