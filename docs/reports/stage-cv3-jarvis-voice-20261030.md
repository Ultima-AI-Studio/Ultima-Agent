# CV3 贾维斯音色阶段报告（2026-10-30）

- 工单：`wo-ultimaagent-20261030-0005`
- 执行端：Codex
- 专用解释器：`tools/venv-openjarvis/Scripts/python.exe`（Python 3.13.16）
- 北极星：贾维斯；语音不出本机，edge-tts 仅保留为可禁用兜底。

## 任务粘贴模板回填

- T0 voice 段入 profile：已完成；Gate T0 为 6 passed，默认值读回为 `engine=cv3`、`ref_audio=data/voice/jarvis-ref/jarvis_voice_ref_pcm16.wav`、`prompt_text=None`。
- T1 PROMPT_WAV 动态装载：已完成；Gate T1 动态解析与 daemon/cold 同源通过；T4 追加默认贾维斯 WAV/文字稿配对回归。
- T2 本地优先链：已完成；Gate T2 为累计 20 passed，真实结果 `engine=cv3` 且 daemon 首次本地合成成功。
- T3 单测：已完成；最终 Gate T3 为 `37 passed`（要求 ≥8）。
- T4 总验收：已完成；真机本地 CV3 中英文合成、离线转写、906 项全量回归全绿；等待独立审计与 Owner 冻结。

## Gate T0

- [x] T0-C1 默认 voice 段存在，默认贾维斯参考音频真实存在。
- [x] T0-C2 L2 `engine/ref_audio/prompt_text` 覆盖生效。
- [x] T0-C3 L2 参考音频缺失时回退 L1 贾维斯参考并记录 warning。
- [x] T0-C4 L3 覆盖 L2。
- [x] T0-C5 损坏 JSON 回退完整 L1 voice 段。
- [x] 非法 engine、空 ref_audio、空 prompt_text 分字段回退。

证据：

- `docs/reports/evidence/cv3-jarvis-voice/t0-gate.md`
- `docs/reports/evidence/cv3-jarvis-voice/t0-pytest.xml`

## Gate T1

- [x] T1-C1 默认 profile 的 `resolve_prompt_wav()` 返回指定贾维斯参考音频。
- [x] T1-C2 缺失配置音频回退 `COSYVOICE_SOURCE/asset/zero_shot_prompt.wav`；绝对路径覆盖生效。
- [x] T1-C3 `prompt_text=null` 使用与解析后内置参考 WAV 配对的内置文本，非空 L2 覆盖生效。
- [x] T1-C4 daemon 脚本与冷启动脚本同源调用 `resolve_prompt_wav/resolve_prompt_text`。
- [x] 动态探测：CUDA=True、RTX 3080 Ti、模型目录与贾维斯 prompt_wav 均存在。
- [x] 真机本地 CV3 中文样本：10.4 秒、24000 Hz、单声道 PCM16、RMS 0.070516、峰值 0.850032，非近静音。

诊断保留：首个英文单次冷启动样本仅 0.24 秒、RMS 0.000690，判近静音；未作为 Gate 通过证据。后续 T4 必须经正式重试链重新生成英文样本。

证据：

- `docs/reports/evidence/cv3-jarvis-voice/t1-gate.md`
- `docs/reports/evidence/cv3-jarvis-voice/t1-pytest.xml`
- `docs/reports/evidence/cv3-jarvis-voice/t1-jarvis-probe-zh.wav`
- `docs/reports/evidence/cv3-jarvis-voice/t1-jarvis-probe-en.wav`（近静音诊断样本，不计 PASS）

## Gate T2

- [x] T2-C1 `engine=cv3` 且 CV3 就绪：daemon 优先、冷启动次之，不调用 edge。
- [x] T2-C2 CV3 不可用：Piper 优先、Melo 次之；均为本地降级。
- [x] T2-C3 仅 `engine=edge` 显式允许最后调用 edge；默认 cv3 在全部本地引擎失败时也不触发 edge。
- [x] 返回值无循环引用，可完整 JSON 序列化。
- [x] 真机本地优先实测：`engine=cv3`、`daemon=true`、CUDA、7.2 秒、RMS 0.0338、首尝试成功。

证据：

- `docs/reports/evidence/cv3-jarvis-voice/t2-gate.md`
- `docs/reports/evidence/cv3-jarvis-voice/t2-result.json`
- `docs/reports/evidence/cv3-jarvis-voice/t2-local-priority.wav`
- `docs/reports/evidence/cv3-jarvis-voice/t2-pytest.xml`

## Gate T3

- [x] 新增 `src/brain/tests/test_voice_voice.py`。
- [x] 覆盖 voice 段 L1/L2/L3、损坏 JSON、缺失引用回退。
- [x] 覆盖 prompt_wav/prompt_text 动态解析与 daemon 同源。
- [x] 覆盖 daemon→冷启动 CV3→Piper→Melo→edge 顺序、默认禁用 edge。
- [x] 覆盖结果 JSON 可序列化回归。
- [x] 专用解释器最终运行结果：`37 passed in 0.70s`，测试未真实加载 CV3。

证据：`docs/reports/evidence/cv3-jarvis-voice/t3-pytest.xml`。

## Gate T4

- [x] 专用解释器全量回归：`786 passed + 120 subtests`；JUnit XML 独立读回 `906 tests / 0 failures / 0 errors / 0 skipped`。
- [x] 中文真机本地 CV3：4.20s、24000 Hz、单声道 PCM16、RMS 0.029394、`engine=cv3`、daemon/CUDA、首次成功。
- [x] 英文真机本地 CV3：3.68s、24000 Hz、单声道 PCM16、RMS 0.020806、`engine=cv3`、daemon/CUDA、首次成功。
- [x] 离线转写：中文 `先生,有什么可以为您效劳?`（zh 0.935059）；英文 `At your service, sir.`（en 0.970703）。
- [x] 默认链未调用 edge-tts；无录音、无麦克风、无播放、无外部语音请求。
- [x] 证据目录含专项 XML、全量 XML、结果 JSON、转写 JSON、正式中英文 WAV 与逐 Gate 摘要。
- [x] fresh-context 只读终审的 4 个 Important 已在一次有界修复中 RED→GREEN：daemon profile 热刷新、malformed voice 回退、损坏音频回退、等价 Jarvis 路径配对。

证据：

- `docs/reports/evidence/cv3-jarvis-voice/t4-gate.md`
- `docs/reports/evidence/cv3-jarvis-voice/t4-result.json`
- `docs/reports/evidence/cv3-jarvis-voice/t4-transcript.json`
- `docs/reports/evidence/cv3-jarvis-voice/t4-jarvis-zh.wav`
- `docs/reports/evidence/cv3-jarvis-voice/t4-jarvis-en.wav`
- `docs/reports/evidence/cv3-jarvis-voice/t4-full-regression.xml`

## 根因与裁决

默认 7.93s 贾维斯参考 WAV 是英文，而初版 `prompt_text=null` 仍解析为 CosyVoice asset 的中文文字稿；零样本克隆的音频/文字稿错配导致目标内容不可懂。保持工单冻结的 `prompt_text=null` 与默认 Jarvis WAV 不变，只在解析层让内置 Jarvis WAV 选取与其配对的内置英文稿；显式 L2 prompt_text 与 CosyVoice 缺失回退语义不变。该修复由新增回归先 RED、后 GREEN 证明。

## 标准回执

| 字段 | 回执 |
|---|---|
| 工单号 | `wo-ultimaagent-20261030-0005` |
| 执行端 | Codex（`codex exec`，项目内原地执行） |
| 完成状态 | T0→T4 技术执行已完成；Gate 全绿；待独立审计与 Owner 冻结，未宣称 frozen |
| 根因结论 | 旧实现固定 CosyVoice prompt 且 edge-tts 在线通道优先；切换英文 Jarvis WAV 后还存在音频/文字稿错配，现已改为 profile 动态配对与本地优先链 |
| 产出路径 | `config/voice-profile.json`；`src/brain/voice/{voice_profile.py,tts.py,daemon.py}`；`src/brain/tests/test_voice_voice.py`；本报告与 `docs/reports/evidence/cv3-jarvis-voice/` |
| 验收证据 | 37 项专项单测；真机 RTX 3080 Ti/CUDA 的 CV3 中英 WAV；本地离线转写逐字命中；全量 XML 906/906、0 failure、0 error |
| 越界声明 | 无；未动 SFT、模型版本、云端调优、W6 UI、KWS/ASR 参数基线、ASR 通道；未停止/重启后台 Agent、KWS/ASR、watchdog；未改项目/全局队列聚合状态 |
| 环境声明 | 真机实测（Windows、RTX 3080 Ti、CUDA、本地 CV3、本地 ASR）；无录音/麦克风/播放；结果与默认 cv3 分支证明 edge-tts 未调用，未做独立抓包审计 |

## 越界声明（执行完成）

无。未动 SFT、模型版本、云端调优、W6 UI、KWS/ASR 参数基线、ASR 通道；未停止或重启现有语音/Agent 后台进程。

