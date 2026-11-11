"""Lifecycle and audio contract for the unmodified native streaming KWS API."""
import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent))
from kws_backend import NativeKws, verify_files

# 唤醒词唯一源是 config/voice-next/live.json；测试不再写死具体词。
KEYWORD = json.loads(
    (Path(__file__).parents[2] / "config" / "voice-next" / "live.json").read_text(encoding="utf-8")
)["keyword"]


class Stream:
    def __init__(self):
        self.audio=[]
        self.pending=0
        self.result=''
    def accept_waveform(self, rate, samples):
        self.audio.append((rate, samples.copy()))
        self.pending=3


class OfficialApi:
    def __init__(self):
        self.streams=[]
        self.decoded=0
        self.resets=0
    def create_stream(self):
        stream=Stream();self.streams.append(stream);return stream
    def is_ready(self, stream):return stream.pending>0
    def decode_stream(self, stream):
        stream.pending-=1;self.decoded+=1
        stream.result=KEYWORD if stream.pending==1 else ''
    def get_result(self, stream):return stream.result
    def reset_stream(self, stream):
        self.resets+=1;stream.result=''


def test_native_api_receives_each_sample_once_without_eos_or_padding():
    import numpy as np
    api=OfficialApi();backend=NativeKws(api,KEYWORD)
    pcm=np.array([-32768,0,32767],dtype='<i2').tobytes()
    event=backend.forward(pcm)
    rate,samples=api.streams[0].audio[0]
    assert rate==16000
    assert samples.tolist()==[-1,0,32767/32768]
    assert event['keyword']==KEYWORD and event['state']==1
    assert api.decoded==3 and api.resets==1
    assert len(api.streams[0].audio)==1


def test_reset_creates_fresh_stream_and_clears_sticky_result():
    api=OfficialApi();backend=NativeKws(api,KEYWORD)
    backend.forward(bytes(640));old=backend.stream
    old.result=KEYWORD
    backend.reset_all()
    assert backend.stream is not old
    assert backend.forward(b'')=={}
    assert backend.stream.audio==[]
    assert backend.samples_consumed==0


def test_invalid_pcm_is_rejected_before_native_calls():
    api=OfficialApi();backend=NativeKws(api,KEYWORD)
    with pytest.raises(ValueError):backend.forward(bytes(3))
    assert api.decoded==0 and not backend.stream.audio


def test_model_manifest_checks_content_and_blocks_path_escape(tmp_path):
    import hashlib
    model=tmp_path/'model';model.mkdir();(model/'encoder.onnx').write_bytes(b'known')
    digest=hashlib.sha256(b'known').hexdigest()
    verify_files(model,{'encoder.onnx':digest})
    (model/'encoder.onnx').write_bytes(b'changed')
    with pytest.raises(ValueError,match='checksum'):verify_files(model,{'encoder.onnx':digest})
    with pytest.raises(ValueError,match='escapes'):verify_files(model,{'../outside':digest})
