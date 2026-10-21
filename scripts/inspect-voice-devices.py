"""Read WinMM audio device inventory only; never play or capture audio."""
import ctypes
from ctypes import wintypes as W
from datetime import datetime, timezone
import json
from pathlib import Path

class WaveOutCaps(ctypes.Structure):
    _fields_ = [('mid', W.WORD), ('pid', W.WORD), ('version', W.DWORD), ('name', W.WCHAR * 32),
                ('formats', W.DWORD), ('channels', W.WORD), ('reserved', W.WORD), ('support', W.DWORD)]

class WaveInCaps(ctypes.Structure):
    _fields_ = [('mid', W.WORD), ('pid', W.WORD), ('version', W.DWORD), ('name', W.WCHAR * 32),
                ('formats', W.DWORD), ('channels', W.WORD), ('reserved', W.WORD)]

api = ctypes.WinDLL('winmm')
api.waveOutGetDevCapsW.argtypes = [ctypes.c_size_t, ctypes.POINTER(WaveOutCaps), W.UINT]
api.waveInGetDevCapsW.argtypes = [ctypes.c_size_t, ctypes.POINTER(WaveInCaps), W.UINT]
result = {'at': datetime.now(timezone.utc).isoformat(), 'read_only': True, 'recorded_audio': False, 'played_audio': False,
          'input_devices': [], 'output_devices': []}
for kind, count, cls, query in [('input', api.waveInGetNumDevs(), WaveInCaps, api.waveInGetDevCapsW),
                                ('output', api.waveOutGetNumDevs(), WaveOutCaps, api.waveOutGetDevCapsW)]:
    for index in range(count):
        caps = cls()
        status = query(index, ctypes.byref(caps), ctypes.sizeof(caps))
        result[kind + '_devices'].append({'index': index, 'name': caps.name, 'channels': caps.channels, 'query_status': status})
directory = Path(r'H:\UltimaAI\UltimaAgent\logs\voice-resources-preflight-20261021')
directory.mkdir(exist_ok=False)
(directory / 'devices.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
