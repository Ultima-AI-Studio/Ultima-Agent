import importlib.util
import sys
import wave
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('voice_next_runner', Path(__file__).with_name('stream_runner.py'))
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)

class FakeSpotter:
    def __init__(self):
        self.received = []
        self.resets = 0
    def reset_all(self):
        self.resets += 1
    def forward(self, pcm):
        self.received.append(pcm)
        return {'state': int(len(self.received) == 1), 'keyword': '你好问问'}

def make_wav(path, rate=16000, channels=1, samples=16000):
    with wave.open(str(path), 'wb') as f:
        f.setparams((channels, 2, rate, 0, 'NONE', 'not compressed'))
        f.writeframes(b'\x00\x00' * samples * channels)
    return path

def test_each_frame_consumed_once_and_event_before_file_end(tmp_path):
    path = make_wav(tmp_path/'input.wav')
    spotter = FakeSpotter()
    rows = list(runner.replay_wav(spotter, path, chunk_samples=4800))
    assert sum(len(x) for x in spotter.received) == 32000
    assert [len(x) for x in spotter.received] == [9600, 9600, 9600, 3200]
    assert rows[0]['event']['keyword'] == '你好问问'
    assert rows[0]['samples_consumed'] < 16000
    assert rows[0]['before_file_end'] is True
    assert rows[-1]['samples_consumed'] == 16000
    assert spotter.resets == 2

@pytest.mark.parametrize('rate,channels', [(44100,1), (16000,2)])
def test_reject_input_without_silent_resampling(tmp_path, rate, channels):
    spotter = FakeSpotter()
    with pytest.raises(ValueError):
        list(runner.replay_wav(spotter, make_wav(tmp_path/'bad.wav',rate,channels)))
    assert spotter.received == []

def test_reset_on_inference_error(tmp_path):
    class Broken(FakeSpotter):
        def forward(self, pcm):
            raise RuntimeError('inference failed')
    spotter = Broken()
    with pytest.raises(RuntimeError):
        list(runner.replay_wav(spotter, make_wav(tmp_path/'input.wav')))
    assert spotter.resets == 2

def test_empty_audio_rejected(tmp_path):
    with pytest.raises(ValueError):
        list(runner.replay_wav(FakeSpotter(),make_wav(tmp_path/'empty.wav',samples=0)))

def test_keyword_matching_includes_final_legal_offset():
    assert runner.keyword_sublist_index((9,1,2,3,4),(1,2,3,4))==1
    assert runner.keyword_sublist_index((1,2,3,4),(1,2,3,4))==0
    assert runner.keyword_sublist_index((9,9),(1,2,3,4))==-1
    assert runner.keyword_sublist_index((1,2,3,4,9),(1,2,3,4))==0
