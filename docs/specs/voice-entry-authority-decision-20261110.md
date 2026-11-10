# 语音入口权威裁决记录 2026-11-10（工单 0035 v2.0 改判版）

## 推翻前提

Owner 原话：`E3 的测试我是测过的，好用。但是没有使用我们 E1 训练的声音。`

这句话否证了工单 v1.1 所依据的“E1 是唯一被真机验收过的链路”前提：E3 链路已有 Owner 实测好用的结论，实际缺口是没有使用 E1 已训练的 CV3 目标音色。

## 两路残缺对照

| 对照项 | E1 `src/brain/voice/kws_listener.py` | E3 `src/voice-next/` |
|---|---|---|
| 链路 | 旧链路 | 新链路，Owner 实测好用 |
| 音色 | CV3（对） | SAPI 系统语音（非目标音色） |
| 设备 | `PLAY_DEVICE=26` 指向 Steam 虚拟声卡（播不出去） | 名字解析已解耦（对） |

## 改判结论

- 产品主线 = E3。
- 产品音色 = E1 的 CV3。
- 目标形态 = E3 链路 + CV3 音色。
- E1/E2 不删、不停用、不归档，降为历史实现。

## Q3 拍板：CV3 不可用时的失败语义

CV3 不可用时降级 SAPI 并上报：照常出声，但 `data/voice-next/status.json` 的 `tts_backend` 写 `sapi_fallback`，同时记录日志告警。禁止静默降级。

## Q5 拍板：E1 输出设备最小修

`PLAY_DEVICE` 只做 `26`→`24` 的最小修复，仅改常量值与同行注释；L106 的 `sd.query_devices(PLAY_DEVICE)` 与 L111 的 `sd.play(audio, rate, device=PLAY_DEVICE)` 调用点不动。“设备应记端点身份而非整数”登记进历史实现基线的待办。

## 机检证据

机检时间：2026-11-10。命令说明：使用 `tools\venv-voice-next` 解释器执行 `sd.query_devices()` + `query_hostapis()`。

    idx=24  OUT  Windows WASAPI       44100  耳机 (POISON M@LOFREE)
    idx=26  OUT  Windows WASAPI       48000  扬声器 (Steam Streaming Microphone)
    idx=4   OUT  Windows MME          44100  耳机 (POISON M@LOFREE)
    idx=15  OUT  Windows DirectSound  44100  耳机 (POISON M@LOFREE)

## 边界声明

本单只出规格、未实现 TTS。CV3 实际接入实现属后续单；本单不宣称 E3 已具备 CV3 音色。
