# UltimaAgent 语音产品基线（E3 `src/voice-next/`）

> 工单 0035 v2.0 建立

**本文件只约束 `src/voice-next/`（E3）**：不约束 `src/brain/voice/kws_listener.py`（E1）与 `data/logs/voice-listen-daemon.py`（E2）。

**E1/E2 的取值以 `docs/specs/kws-wakeup-params-baseline.md`（历史实现基线）为准，且该文件取值不约束本文件。**

## E3 产品参数与行为

| 编号 | 项目 | 取值 | 依据 |
|---|---|---|---|
| （a） | 唤醒词 | `你好问问` | `src/voice-next/README.md:3` 说明实际监听固定使用该词。 |
| （b） | `keywords_threshold` | `0.25` | `src/voice-next/README.md:32` 记录新 KWS 阈值为官方默认工作点。 |
| （c） | `keywords_score` | `1` | E3 当前新链路取值；与 E1/E2 历史实现基线互不约束。 |
| （d） | `num_trailing_blanks` | `1` | E3 当前新链路取值；与 E1/E2 历史实现基线互不约束。 |
| （e） | 模型 | `models\voice-next` 独立副本 / chunk-16 | `src/voice-next/README.md:3,44` 记录 chunk16 与独立副本。 |
| （f） | 输入端点 | WASAPI 名字解析（`麦克风 (USBAudio2.0)`） | `src/voice-next/README.md:24` 原文说明按名字和 API 解析，不依赖旧设备索引。 |
| （g） | KWS 增益 | 固定 `input_gain=10`，无自适应 | `src/voice-next/README.md:32` 记录固定软件增益 10 倍且无旧自动增益。 |
| （h） | 指令采集 | 上限 15s / 结束静音 0.8s / 等开口 5s | `src/voice-next/README.md:33` 的回合参数。 |
| （i） | 有效语音门控 | WebRTC VAD ≥5×20ms，无 peak/rms 门 | `src/voice-next/README.md:32-33`：无二次电平门控，VAD 以 20ms 判帧。 |
| （j） | 提示音静置 | 无 `BEEP_SETTLE_SEC`，仅播放后 0.15s sleep | E3 当前实现行为；不得外推为 E1/E2 取值。 |

## 三项待定

- `keywords_score` 2.0→1：**待定，本单不定性**；缺设计意图说明或实测召回对比。
- `num_trailing_blanks` 8→1：**待定，本单不定性**；缺说明是否随官方默认模型参数套用，或词尾延迟实测。
- `BEEP_SETTLE_SEC` 移除：**待定，本单不定性**；缺实测 0.15s 是否足以避免提示音残响被录入 KWS。

## CV3 音色

- 目标：接入 E1 那套 CV3 音色。
- 当前：SAPI（临时）；`src/voice-next/README.md:5` 原文为“新入口临时使用Windows本地SAPI语音：原CV3冷启动联调等待数分钟，因此本轮不启动CV3，原音色配置和源码保留。”
- 规格：见 `docs/specs/voice-next-cv3-tts.md`。本单只出规格不出实现；本单之后 E3 仍未具备 CV3 音色。

## 未验收声明

`src/voice-next/README.md:46` 原文：`合成样本是冒烟证据，不是远场稳定性证明`。

`src/voice-next/README.md:32` 原文：`稳定性仍需真人验收`。

因此，本文件建立的是产品基线与后续验收依据，不宣称 E3 已完成真人稳定性验收。

## 变更记录

| 日期 | 变更 |
|---|---|
| 2026-11-10 | 据 0035 v2.0 改判建立。 |
