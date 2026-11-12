# voice-kws-wake 验收证据

- 验收人：主脑（豆包直做）
- 验收时间：2026-10-27
- 依据：用户既定音声方案（KWS 关键词唤醒「贾维斯」才应答，非常驻监听）；sherpa-onnx 2.0 KWS API

## 实现范围（增量，不推倒语音全链路内核）

新建 `src/brain/voice/kws_listener.py`：
- sherpa-onnx `KeywordSpotter`（zipformer-zh-en-3M KWS 模型，chunk-16 int8）流式唤醒检测；
- 唤醒词：`models/sherpa/kws/keywords.txt`（贾维斯 / ULTIMA）；
- 常驻待唤醒 → 命中「贾维斯」→ VAD 录音对话回合（asr_transcribe → VoiceInteractionLoop.handle_audio → TTS 回放）→ 回到待唤醒；
- 灵敏度 `KWS_THRESHOLD`（环境变量，默认 0.25，可调）；
- 单实例原子锁 `%TEMP%\ultima-kws-listener.pid`，残留死锁自动清理；
- 设备/链路参数复用 live_mic 真机已验证值（MIC_DEVICE=1 USB 麦 / PLAY_DEVICE=26 LOFREE 耳机 / GAIN=30 / 能量 VAD 阈值校准）。

## 验收项逐条

| 项 | 判定 | 证据 |
|---|---|---|
| ACCEPT-1 KWS 模型加载与流式检测可用 | 通过 | venv-asr 下 `KeywordSpotter` 加载成功、`create_stream()` 返回 stream；keywords.txt 含「贾维斯/ULTIMA」 |
| ACCEPT-2 唤醒后对话回合链路完整 | 通过 | 代码路径：WAKE_HIT → 录音 → asr_transcribe → handle_audio → reply_wav 回放（复用 live_mic 已验证组件）；进程启动 WARMUP_DONE asr_ok=True |
| ACCEPT-3 未命中保持待唤醒不常驻应答 | 通过 | 主循环仅 KWS 命中才进入对话；日志态 KWS_READY 待唤醒 |
| ACCEPT-4 单实例锁防双开、死锁清理 | 通过 | 原子 O_EXCL 创建 + 旧 PID 存活检测（同 live_mic 已验证模式） |
| ACCEPT-5 回执完整 | 通过 | 本文件 + receipt.json，tasks.json COMPLETED |

## 测试结果

- 语法自检：`py_compile` 通过（SYNTAX_OK）
- 模型加载：venv-asr 下 KWS_MODEL_LOADED stream_ok=True（encoder/decoder/joiner chunk-16 int8 + tokens）
- 进程启动：kws_listener（PID 20188）存活，WARMUP_DONE asr_ok=True text='查询任务状态。'，KWS_READY 待唤醒，err 日志为空
- **缺陷修复（验收中发现）**：sounddevice 返回 (N,1) 二维数组而 sherpa `accept_waveform` 需一维——初版 feed 未展平导致连续 ERR（唤醒检测空转）。修复：`feed()` 入口 `block.flatten()` 展平；修复后重启无 ERR、检测实际工作。
- **缺陷修复（完整审计中发现）**：单实例锁 atexit 退出清理无条件删除共享锁文件，会误删持锁者锁。修复：仅当锁内容==本进程 PID 才删除；并增加主循环心跳刷新（锁内容恒为存活 worker PID）。验证：第二实例 0.3s 内 EXIT_ALREADY_RUNNING，拦截生效；venv-asr pythonw 为 launcher 结构（父=stub/子=执行），成对进程属正常，非双开。
- 真机听测：**登记为统一真机回归项**（用户指示：所有任务流程跑完后统一一点点测，本轮不测）

## 边界确认

- 未唤醒不进入对话（非常驻全量应答）；
- 唤醒灵敏度由 KWS_THRESHOLD 调节（调低更灵敏/易误报），统一真机回归时实测校准；
- ASR/TTS/桥接内核未改动（仅前置唤醒闸门）。
