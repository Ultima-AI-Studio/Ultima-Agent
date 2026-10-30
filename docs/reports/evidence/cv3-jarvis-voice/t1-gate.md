# T1 Gate 证据

## 逻辑与同源

- RED：T1 新测试首次运行 6 failed，原因是 `resolve_prompt_wav` / `resolve_prompt_text` 尚不存在。
- GREEN：T0+T1 累计 `12 passed`。
- 默认动态解析：`data/voice/jarvis-ref/jarvis_voice_ref_pcm16.wav`。
- 缺失配置回退：`COSYVOICE_SOURCE/asset/zero_shot_prompt.wav`。
- daemon 与冷启动脚本均在渲染时调用同一解析函数。

## 本地资源探测

- torch：`2.3.1+cu121`
- CUDA：`true`
- GPU：`NVIDIA GeForce RTX 3080 Ti`
- CV3 模型目录：存在
- prompt_wav：`H:\UltimaAI\UltimaAgent\data\voice\jarvis-ref\jarvis_voice_ref_pcm16.wav`，存在
- prompt_text（T4 最终校正）：默认 profile 仍为 `null`；内置贾维斯英文参考解析为与该 WAV 配对的英文内置文字稿，CosyVoice 回退 asset 仍使用原中文文字稿，显式 L2 非空值仍优先。

## 真机离线合成

- 通过样本：`t1-jarvis-probe-zh.wav`
- 文本：`先生，有什么可以为您效劳？`
- 结果：10.4 秒 / 24000 Hz / 单声道 PCM16 / RMS 0.070516 / 峰值 0.850032 / CUDA
- 样本 SHA256：`485532C69B391F7DC013BF1F2CB6FF4EF6F9F11EBF355C1D679EA473808DE597`
- 参考音频 SHA256：`67D7826A6C4A2ACF277F8F61E3871D43E72A00107EE8678FAA579C29AD52297F`

诊断样本 `t1-jarvis-probe-en.wav` 为 0.24 秒 / RMS 0.000690，判近静音并保留，不计入通过证据。

T4 可懂度复核发现，T1 初版把英文贾维斯 WAV 与 CosyVoice 中文文字稿配对，虽然非静音但内容不可验收；已用 RED→GREEN 回归纠正，最终可懂度证据以 `t4-gate.md` 和 `t4-transcript.json` 为准。
