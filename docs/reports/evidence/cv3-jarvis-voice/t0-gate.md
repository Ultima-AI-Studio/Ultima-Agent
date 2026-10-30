# T0 Gate 证据

- RED：`test_voice_voice.py` 首次运行 6 failed，统一根因 `KeyError: 'voice'`。
- GREEN：专用解释器运行同一文件，结果 `6 passed in 0.12s`。
- 配置读回：`{'engine': 'cv3', 'ref_audio': 'data/voice/jarvis-ref/jarvis_voice_ref_pcm16.wav', 'prompt_text': None}`。
- 参考音频读回：单声道、24000 Hz、PCM16、7.933 秒。
- CosyVoice 回退音频：`COSYVOICE_SOURCE/asset/zero_shot_prompt.wav`，真实存在。

命令：

```powershell
tools\venv-openjarvis\Scripts\python.exe -m pytest src/brain/tests/test_voice_voice.py -q --disable-warnings
tools\venv-openjarvis\Scripts\python.exe -c "from src.brain.voice.voice_profile import load_profile; p=load_profile(); print(p['voice'])"
```
