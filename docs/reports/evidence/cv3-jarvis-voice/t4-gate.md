# T4 Gate 证据

## 配置与专项单测

- 专用解释器：`tools/venv-openjarvis/Scripts/python.exe`，Python 3.13.16。
- 当前默认读回：`engine=cv3`、`ref_audio=data/voice/jarvis-ref/jarvis_voice_ref_pcm16.wav`、`prompt_text=None`。
- 最终专项单测：`37 passed in 0.70s`；`t3-pytest.xml` 已刷新。
- 新增回归首先 RED：默认贾维斯 WAV 仍配旧中文 prompt_text；最小修复后目标测试 `1 passed`，整文件 `21 passed`。
- 独立终审追加 4 个 Important 边界回归，首次合计 `15 failed / 22 passed`；单次修复后整文件 `37 passed`：daemon 每请求刷新配对、malformed voice fail-safe、损坏音频回退、等价 Jarvis 路径同源。

## 真机本地合成

- 中文：`t4-jarvis-zh.wav`，CV3 daemon/CUDA，24000 Hz、单声道 PCM16、4.20s、RMS 0.029394、peak 0.208771、首次成功。
- 英文：`t4-jarvis-en.wav`，CV3 daemon/CUDA，24000 Hz、单声道 PCM16、3.68s、RMS 0.020806、peak 0.278320、首次成功。
- 两次结果 `engine=cv3`，未进入 Piper/Melo/edge-tts；未录音、未调用麦克风、未播放、未发起外部请求。

## 离线转写

- 解释器：`tools/venv-asr/Scripts/python.exe`；本地 `faster-whisper-large-v3`，自动语言检测，无领域提示。
- 中文：`先生,有什么可以为您效劳?`，language=zh，probability=0.935059，语义逐字命中。
- 英文：`At your service, sir.`，language=en，probability=0.970703，逐字命中。
- 初始 prompt/reference 错配及失败转写保留在 `t4-transcript.json`，未把结构化 `ok=true` 冒充可懂度 PASS。

## 全量回归

- 命令：`tools/venv-openjarvis/Scripts/python.exe -m pytest src -q --disable-warnings --junitxml=docs/reports/evidence/cv3-jarvis-voice/t4-full-regression.xml`
- 最终结果：`786 passed, 36 warnings, 120 subtests passed in 195.09s`；XML 独立读回 `tests=906, failures=0, errors=0, skipped=0`。

## Gate 结论

T4 技术执行 Gate PASS；等待独立审计与 Owner 冻结，本证据不宣称 frozen。
