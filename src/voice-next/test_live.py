import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).parent))
from live_core import PCMFramer, SpeechCapture, resolve_endpoint


def test_framer_preserves_variable_packet_order_and_reset():
    framer=PCMFramer(320)
    pcm=bytes(range(256))*15
    chunks=[]
    for offset in range(0,len(pcm),154):
        chunks.extend(framer.feed(pcm[offset:offset+154]))
    assert b''.join(chunks)+bytes(framer.pending)==pcm
    assert all(len(x)==640 for x in chunks)
    framer.reset()
    assert framer.pending==b''


def test_capture_keeps_pre_roll_and_stops_on_silence():
    flags=iter([False]*10+[True]*15+[False]*40)
    capture=SpeechCapture(lambda _:next(flags),end_silence=0.8)
    frames=[i.to_bytes(2,'little')*320 for i in range(65)]
    result=None
    for frame in frames:
        result=capture.feed(frame)
    assert result[0]=='complete'
    assert frames[9] in result[1]
    assert frames[10] in result[1]
    assert frames[24] in result[1]
    assert capture.speech_frames==15


def test_capture_without_speech_times_out():
    capture=SpeechCapture(lambda _:False,wait_seconds=0.1)
    result=None
    for _ in range(5):result=capture.feed(bytes(640))
    assert result==('empty',b'')


def test_capture_is_bounded_during_continuous_speech():
    capture=SpeechCapture(lambda _:True,max_seconds=0.2)
    for _ in range(10):result=capture.feed(bytes(640))
    assert result[0]=='complete'
    assert len(result[1])<=6400


def test_endpoint_selection_uses_physical_name_and_api():
    devices=[{'name':'USBAudio2.0','hostapi':0,'max_input_channels':1},
             {'name':'USBAudio2.0','hostapi':1,'max_input_channels':2},
             {'name':'Steam microphone','hostapi':1,'max_input_channels':1}]
    apis=[{'name':'MME'},{'name':'Windows WASAPI'}]
    assert resolve_endpoint(devices,apis,{'name_contains':'USBAudio2.0','hostapi':'Windows WASAPI'},'input')==1
    with pytest.raises(ValueError):resolve_endpoint(devices,apis,{'name_contains':'missing','hostapi':'Windows WASAPI'},'input')
    with pytest.raises(ValueError):resolve_endpoint(devices+devices[1:2],apis,{'name_contains':'USBAudio2.0','hostapi':'Windows WASAPI'},'input')

def test_callback_only_copies_and_queues_without_model_calls():
    import live,queue,threading,numpy as np
    obj=live.Resident.__new__(live.Resident)
    obj.queue=queue.Queue(maxsize=1);obj.muted=threading.Event();obj.generation=0
    obj.counters={'callbacks':0,'input_frames':0,'overflows':0}
    audio=np.ones((100,1),dtype=np.float32)
    obj.callback(audio,100,None,False)
    audio[:]=0
    assert obj.queue.get_nowait()[1].sum()==100
    obj.muted.set();obj.callback(audio,100,None,False)
    assert obj.queue.empty()
    obj.muted.clear();obj.callback(audio,100,None,False);obj.callback(audio,100,None,False)
    assert obj.generation==1 and obj.queue.qsize()==1


def test_discontinuity_reset_clears_framers_and_model_cache():
    import live
    class Spotter:
        def __init__(self):self.resets=0
        def reset_all(self):self.resets+=1
    obj=live.Resident.__new__(live.Resident)
    obj.input_rate=48000;obj.spotter=Spotter();obj.generation=2
    obj.reset_audio();first=obj.resampler
    obj.kws_frames.feed(bytes(100));obj.vad_frames.feed(bytes(100))
    obj.reset_audio()
    assert obj.spotter.resets==2
    assert obj.resampler is not first and obj.seen_generation==2
    assert not obj.kws_frames.pending and not obj.vad_frames.pending

def test_callback_updates_liveness_even_when_muted():
    import live,queue,threading,numpy as np
    obj=live.Resident.__new__(live.Resident)
    obj.queue=queue.Queue(maxsize=1);obj.muted=threading.Event();obj.muted.set();obj.generation=0
    obj.counters={'callbacks':0,'input_frames':0,'overflows':0}
    obj.callback(np.zeros((64,1),dtype=np.float32),64,None,False)
    assert obj.last_audio_at>0
    assert obj.queue.empty()
