# 任务卡：voice-kws-wake

- **task_id**：voice-kws-wake
- **标题**：语音唤醒落地（关键词唤醒「贾维斯」→ 对话回合，替代 MVP 常驻监听）
- **优先级**：90（P0）
- **category**：core　**skill**：engineering
- **依赖**：s3-voice-fullchain（M05/M06 语音全链路已建）、live_mic 真机参数（MVP 验证值）
- **依据**：用户既定音声方案（KWS 关键词唤醒才应答，非常驻监听）；sherpa-onnx KWS zipformer 中英模型

## goal

在既有语音全链路之上落地关键词唤醒（不动 ASR/TTS/桥接内核，前置唤醒闸门）：

1. KWS 唤醒监听 `src/brain/voice/kws_listener.py`：
   - sherpa-onnx `KeywordSpotter`（zipformer 中英 KWS 模型，唤醒词：贾维斯 / ULTIMA）；
   - 常驻待唤醒 → 命中「贾维斯」→ 进入对话回合（VAD 录音 → asr_transcribe → VoiceInteractionLoop.handle_audio → TTS 回放）→ 回到待唤醒；
   - 唤醒灵敏度参数 `KWS_THRESHOLD`（环境变量可调，默认 0.25）。
2. 单实例原子锁（`%TEMP%\ultima-kws-listener.pid`），防双开抢麦。
3. 设备/链路参数复用 live_mic 已验证值：MIC_DEVICE=1（USB 麦）、PLAY_DEVICE=26（LOFREE 耳机）、GAIN=30、VAD 能量阈值校准。

**禁止**：不做常驻全量应答（未唤醒不进入对话）；不预测性结论；不触碰 ASR/TTS/桥接内核。

## acceptance[]

- [ ] ACCEPT-1：KWS 唤醒模型加载与流式检测可用（关键词文件含贾维斯/ULTIMA）
- [ ] ACCEPT-2：唤醒命中后进入对话回合（录音→ASR→桥接→TTS 回放）链路完整
- [ ] ACCEPT-3：未命中时保持待唤醒态，不常驻应答
- [ ] ACCEPT-4：单实例锁防双开；残留死锁自动清理
- [ ] ACCEPT-5：回执完整（ReceiptValidator 0 issues + tasks.json COMPLETED）

## fileDomain[]

- `H:/UltimaAI/UltimaAgent`（src/brain/voice + tasks）
