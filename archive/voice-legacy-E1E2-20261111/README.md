# 语音旧入口冻结归档（E1 / E2）

- 冻结日期：2026-11-11
- 判定：旧唤醒入口整条链路停用，物理移出 `src/`、`models/`、`docs/`、`data/logs/`，只在本目录留存。
- 现行入口：`src/voice-next/`（E3），唯一权威参数见 `docs/specs/voice-next-product-baseline.md`。

## 为什么冻结

两套唤醒入口长期并存，导致同一件事实出现两个答案：

1. 启动脚本 `scripts/start-ultima-agent.ps1` 第 3 步拉起的是 E2 daemon，并在末行打印"唤醒词：贾维斯"；实际在跑的是 E3，唤醒词是"你好问问"。
2. 旧词表 `models/sherpa/kws/keywords.txt`（6 个"贾维斯"变体 + 幂幂 + ULTIMA）仍留在仓库主路径上，容易被误读为现行配置。
3. `src/brain/voice/` 是混合包——`daemon / tts / asr / voice_profile / resources` 仍被新入口 `turn_worker.py` 依赖，不能整包搬走，只能搬"入口独占"的部分。

## 归档清单（git mv 保留历史）

| 原路径 | 归档后同路径 | 说明 |
|---|---|---|
| `src/brain/voice/kws_listener.py` | `src/brain/voice/kws_listener.py` | E1 唤醒入口（贾维斯 / 幂幂 / ULTIMA） |
| `data/logs/voice-listen-daemon.py` | `data/logs/voice-listen-daemon.py` | E2 常驻 daemon |
| `models/sherpa/kws/keywords.txt` | `models/sherpa/kws/keywords.txt` | E1 词表 |
| `docs/specs/kws-wakeup-params-baseline.md` | `docs/specs/kws-wakeup-params-baseline.md` | E1/E2 参数基线（阈值 0.08 / score 2.0 / trailing 8） |
| `src/brain/tests/test_voice_wakeword_reload.py` | `src/brain/tests/test_voice_wakeword_reload.py` | 只测 E1 热重载 |
| `src/brain/tests/test_kws_user_entry.py` | `src/brain/tests/test_kws_user_entry.py` | 只测 E1 换词 CLI 路径 |
| `scripts/kws_reconfig.py` | `scripts/kws_reconfig.py` | 旧换词 CLI：写 `models/sherpa/kws/keywords.txt` 并通知 E2 daemon 热重载 |
| `scripts/test_kws_reconfig.py` | `scripts/test_kws_reconfig.py` | 上述 CLI 的测试 |

`src/brain/voice/tests/test_jarvis_p0_voice.py` 中的
`test_kws_listener_refreshes_only_its_stream_and_fuzzy_matches` 与
`src/brain/tests/test_audio_resample.py` 中的
`test_audio_capture_opens_wasapi_stereo_and_reads_mono` 不是删除，而是**原样搬进归档**（断言一字未改，仅把被测文件路径改指归档）：

| 冻结测试（归档内） | 原位置 | 保留的判据 |
|---|---|---|
| `src/brain/voice/tests/test_e1_kws_listener_frozen.py` | `src/brain/voice/tests/test_jarvis_p0_voice.py` | 阈值 0.08 / score 2.0 / trailing 8；"贾维丝"模糊命中；命中后只换 stream 不重建实例 |
| `src/brain/tests/test_e2_audio_capture_frozen.py` | `src/brain/tests/test_audio_resample.py` | 48k 双声道开流参数；两帧混单声道得 `[[2000],[0]]`；溢出标志为 False |

两份冻结测试均已实测可执行（各 1 passed），但不进 CI。
`test_jarvis_p0_voice.py` 原文件保留其余 5 组用例（asr / session_restart / wake_matching / transcription_backends），仅删除这一条并留注释指向归档。

## 未搬走的部分（故意留下）

- `src/brain/voice/` 下的 `daemon.py`、`tts.py`、`asr.py`、`resources.py`、`voice_profile.py`、`_resample.py`、`input_probe.py`、`wake_matching.py`、`session_restart.py`、`transcription_backends.py`、`fullchain.py` 是**新旧共享底座**，新入口 `src/voice-next/turn_worker.py:50-52,69-70,216-217`、`agent_server.py:190`、`interaction.py` 仍在用。搬走会同时打断新旧两条链路。

- 共享底座里属于旧入口的那部分**已就地收口，不再保留第二份词**：
  - `voice_profile.py` 的 `DEFAULT_WAKE_WORDS` 清空为 `[]`（原 6 条「贾维斯」token 即上方 `models/sherpa/kws/keywords.txt` 的内容），`DEFAULT_WAKE_ECHO_ROOTS` 改为只取 `config/voice-next/live.json` 的 `keyword`；
  - `config/voice-profile.json` 的 `wakeword.words` 置空、`wakeword.custom`（原 `幂幂`）置 `null`；
  - `voice_loop.py` 的默认换词事务改为 fail-closed，不再调用本目录的 `scripts/kws_reconfig.py`，也不再有「贾维斯」字面量。
  回滚 E1 时需同时恢复上述三处（本目录内 `src/brain/voice/voice_profile.py` 之外无对应副本，需从 `artifacts/voice-legacy-baseline-20261101/` 取回原值）。
- `models/sherpa/kws/sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20/`（70.2MB / 38 文件）为中立模型资源，留在原路径，不再被任何在跑进程加载。

## 回滚方法

若需临时回到 E1/E2：

1. 把上表六项 `git mv` 回原路径；
2. 还原 `scripts/start-ultima-agent.ps1` 第 3 步（改回拉起 `data\logs\voice-listen-daemon.py`，用 `tools\venv-asr` 解释器）；
3. 旧参数取值以本目录 `docs/specs/kws-wakeup-params-baseline.md` 为准。

回滚前必须先停 `src/voice-next/live.py`，否则两条入口会同时抢麦克风与 WASAPI 输出设备。

## 硬约束

- 本目录文件**不得被现行产品代码 import、运行或引用**，也不得被现行文档当作参数依据；
  仅本目录内的两份冻结回归测试可只读加载自身文件，且不进入 CI；
- 现行参数改动只改 `config/voice-next/live.json`（唯一源）与 `docs/specs/voice-next-product-baseline.md`；
- 不得把本目录的词表 / 参数回填进新链路。
