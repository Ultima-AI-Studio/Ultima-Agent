"""Replay an existing synthetic WAV to an offline ASR probe; no audio device I/O."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import wave

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / 'Topo Backup/C_Guixu/source/guixu-v1.04.00-phase6.3.02-cross-platform-matrix/apps/desktop-host-winui/qa/VOICE_041_V0_20261010_R1'
source = ROOT / 'logs/host-shell-repair-20261021T061613/tts-smoke.wav'
out = ROOT / 'logs/voice-existing-audio-replay-20261021'
out.mkdir(exist_ok=False)
pin = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
expected = '30597bab8f2ac365bae3ac7c50d334532f6903dfa3e3da71d0d27e323508b661'
assert pin(source) == expected
with wave.open(str(source), 'rb') as wav:
    rate, channels, width, count = wav.getframerate(), wav.getnchannels(), wav.getsampwidth(), wav.getnframes()
    assert channels == 1 and width == 2 and rate == 24000
    raw = wav.readframes(count)
samples = struct.unpack('<' + 'h' * count, raw)
target_count = count * 16000 // rate
converted = []
for index in range(target_count):
    position = index * rate / 16000
    left = int(position)
    fraction = position - left
    converted.append(round(samples[left] * (1-fraction) + samples[min(left+1, count-1)] * fraction))
resampled = out / 'existing-synthetic-16khz.wav'
with wave.open(str(resampled), 'wb') as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(16000)
    wav.writeframes(struct.pack('<' + 'h' * len(converted), *converted))
model = LEGACY / 'models/sensevoice-20240717'
assert pin(model / 'model.int8.onnx') == 'c71f0ce00bec95b07744e116345e33d8cbbe08cef896382cf907bf4b51a2cd51'
assert pin(model / 'tokens.txt') == 'f449eb28dc567533d7fa59be34e2abca8784f771850c78a47fb731a31429a1dc'
probe = LEGACY / 'AudioProbe/bin/Release/net8.0-windows/win-x64/AudioProbe.dll'
assert probe.is_file()
report = out / 'asr.json'
env = os.environ.copy()
env['DOTNET_ROOT'] = r'C:\Users\Administrator\.dotnet'
command = [str(Path(env['DOTNET_ROOT']) / 'dotnet.exe'), str(probe), 'asr', 'sensevoice', str(model), str(resampled), str(report), 'cpu', '2']
with (out / 'out.log').open('wb') as stdout, (out / 'err.log').open('wb') as stderr:
    process = subprocess.run(command, cwd=out, env=env, stdout=stdout, stderr=stderr, creationflags=0x08000000, timeout=90)
data = json.loads(report.read_text(encoding='utf-8')) if report.exists() else {}
recognized = data.get('text', '')
reference = '这是离线语音合成环境测试'
normalized = ''.join(c for c in recognized if '\u4e00' <= c <= '\u9fff')
result = {'at': datetime.now(timezone.utc).isoformat(), 'scope': '已有合成音频离线ASR复验；不是语音工单验收',
          'source': str(source), 'source_sha256': expected, 'source_unchanged': pin(source) == expected,
          'resample': '24kHz PCM16 mono -> 16kHz linear interpolation, file only',
          'probe': str(probe), 'probe_sha256': pin(probe), 'exit_code': process.returncode,
          'asr_status': data.get('status'), 'text': recognized,
          'reference_text': reference, 'reference_exact_match_after_punctuation': normalized == reference,
          'recorded_audio': False, 'played_audio': False, 'requested_provider': 'cpu',
          'gpu_execution_claimed': False, 'voice_order_pass_claimed': False}
with (out / 'result.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False))
raise SystemExit(0 if process.returncode == 0 and normalized == reference else 2)
