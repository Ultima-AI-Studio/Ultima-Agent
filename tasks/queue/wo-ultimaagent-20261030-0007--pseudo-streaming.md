# Codex 工单 · UltimaAgent｜功能｜双线程伪流式（采集∥识别，边说边出字）

> 版本：v1.0 ｜ 状态：派发中（2026-10-30）｜ 适用工具：Codex（`codex exec`，`-m gpt-5.6-sol`）
> 用法：按 T0→T4 顺序逐条执行，Gate 全绿才过，再进下一条。
> 范围依据：`H:\UltimaAI\INDEX.md` + `H:\UltimaAI\_shared\paradigms\UltimaAI-任务工作流范式.md` + `docs/INDEX.md`
> 任务源：`tasks/cards/voice-136-pseudo-streaming/task.md`（任务卡 v1.0，tasks.json 内 task_id=`voice-136-pseudo-streaming`，state=QUEUED）
> 北极星：**贾维斯**（端到端「问就答」再省一步：采集结束即已有识别中间结果，ASR 用时基本归零到首词延迟）
> 登记：2026-10-30 ｜ 原单 ID：wo-ultimaagent-20261030-0007 ｜ 类型：功能

---

## 0. 范围冻结

**目标**：采集线程持续进队，识别线程在说话中提前开跑（whisper-real-time 路线：新块到达即把累积缓冲送识别，边说边出字），不等说完。采集结束即已有识别中间结果，ASR 用时归零到首词延迟。

**写域（fail-closed，越界即停）**：仅 `H:\UltimaAI\UltimaAgent\`：
- 代码：`data/logs/voice-listen-daemon.py`（T1-T3 全部改造在此文件）
- 真机验证：`data/logs/voice-listen.log` + 首字延迟对比报告（`docs/reports/stage-pseudo-streaming-20261030.md`）
- 基线：`docs/specs/kws-wakeup-params-baseline.md` 变更记录表追加 #136 条目（**只追加记录，不改任何参数值**）

**禁止（硬红线）**：
- 禁止引入真流式 ASR 模型（P2 延伸：sherpa streaming transducer / Paraformer 本地版，另立项）；
- 禁止改动 #132/#133/#134 已冻结参数：`keywords_threshold=0.08`、`keywords_score=2.0`、`num_trailing_blanks=8`、`QUIET_AFTER_SPEECH=1.2`（能量兜底）、`BEEP_SETTLE_SEC=1.2`、sinc 重采样（441:160 / 48k 3:1 整数 sinc）、VAD `min_silence=0.5s`、门控 0.4s/0.002（块峰值 0.01）、`MIC_DEVICE/DEV_IN=1`（惠普麦）——零漂移核对；
- 禁止触碰 TTS 链路（CV3 克隆音色强项不动、不云化）；
- 禁止重构 wait_wakeup（唤醒态保持单线程流式 KWS）；
- 伪流式重跑整段须控制频率（如每 1s 一次），不得让识别线程抢占采集线程导致卡顿；
- 越界 fail-closed 写域仅 `H:\UltimaAI\UltimaAgent\`；不做 SFT/换模型/云端调优/W6 UI/KWS·ASR 参数基线改动；仅标准库 json/pathlib（+ 既有依赖）。

**执行环境**：
- 专用解释器：`tools\venv-openjarvis\Scripts\python.exe`（Py 3.13.16，禁系统 Python312）；ASR 链路（T3 回退路径/SenseVoice）用 `tools\venv-asr\Scripts\python.exe`；
- 依赖：voice-listen-daemon.py 现用依赖（sounddevice/numpy/sherpa-onnx/silero-vad 等）以 venv-openjarvis / venv-asr 实际安装为准，缺失时如实登记不静默降级。

---

## 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 基线 | 只读 | 冻结参数零漂移核对通过（diff 基线文档五、六节与 daemon 常量） |
| T1 | `data/logs/voice-listen-daemon.py` | 双线程骨架：采集线程入队 + 识别线程消费，主循环改造不阻塞采集 |
| T2 | `data/logs/voice-listen-daemon.py` | 重跑节流：累积缓冲每 1s 送一次 ASR，取最后一次结果；说完后立即终跑 |
| T3 | `data/logs/voice-listen-daemon.py` | 回退保护：识别线程异常/超时（>600s）回退原"采集完再 ASR"路径，不丢轮次 |
| T4 | 真机验证 | 0.6s 短指令"查天气"与 10-29 停顿场景：首字延迟对比（伪流式 vs 串行 #134 基线）落盘 |

## 任务明细

### T0 · 基线核对（Gate 前置）
**写什么**：只读核对 `docs/specs/kws-wakeup-params-baseline.md` 与 `data/logs/voice-listen-daemon.py` 常量（keywords_threshold/score/num_trailing_blanks/DEV_IN/QUIET_AFTER_SPEECH/BEEP_SETTLE_SEC/VAD min_silence/sinc 重采样/门控 0.4s/0.002 块峰值 0.01）一致，零漂移才开工。**T0 已裁定基线（2026-10-30 主脑）：score=2.0、BEEP_SETTLE_SEC=1.2、门控 0.4s/rms 0.002 块峰值 0.01，基线文档第七节变更记录已追加 #136 前置裁定，以基线文档汇总为准。**
**验收（Gate）**：核对表落盘（T0-gate.md）。

### T1 · 双线程骨架
**文件**：`data/logs/voice-listen-daemon.py`（collect/main）
**写什么**：collect() 改为采集线程（持续读麦克风入 queue.Queue，帧附带时间戳）；新增识别线程（消费缓冲→降采样→VAD 分段→累积）；VAD 段提交后由识别线程触发终跑。主循环等识别线程结果返回。
**验收（Gate）**：双线程无死锁；采集不因识别阻塞（CHUNK=1600 读取间隔 <36ms 可接受）；真机一轮完整对话走通。
**禁止**：不在采集线程内做 ASR 推理。

### T2 · 重跑节流
**文件**：`data/logs/voice-listen-daemon.py`
**写什么**：识别线程累积缓冲，距上次送识 ≥1s 或收到"说完"信号时整段送 ASR；保留最近一次中间结果；采集结束后强制终跑并返回。
**验收（Gate）**：重跑次数受控（8s 指令 ≤8 次）；中间结果不覆盖终跑结果。
**禁止**：每次新块都全量重跑（识别器开销大）。

### T3 · 回退保护
**文件**：`data/logs/voice-listen-daemon.py`
**写什么**：识别线程任何异常/超时（>600s）→ 标记降级，主循环回退"采集完再调 asr_transcribe"原路径，本轮不丢。
**验收（Gate）**：注入异常后本轮仍返回 ASR 结果；日志留痕。
**禁止**：异常吞掉无日志。

### T4 · 真机对比落盘
**文件**：`data/logs/voice-listen.log` + `docs/reports/stage-pseudo-streaming-20261030.md`
**写什么**：真机各 ≥3 轮"贾维斯+查天气"（0.6s 短指令）与"贾维斯+长指令"，记录首字延迟（唤醒命中→TTS 播放）伪流式 vs 串行（#134 基线数据）。
**验收（Gate）**：首字延迟下降量量化落盘；无回归（无新增误唤醒/掐断）。
**禁止**：无数据宣称收益。

---

## 总验收（阶段 DoD）
- [ ] T0-T4 全部过 Gate（T0-gate.md / t1-gate.md / t2-gate.md / t3-gate.md / t4-gate.md + 证据文件）
- [ ] 伪流式 vs 串行首字延迟对比数据落盘
- [ ] 基线文档 `docs/specs/kws-wakeup-params-baseline.md` 变更记录追加 #136（只追加，不改值）
- [ ] 冻结参数零漂移核对

## 验收要点
- [ ] py_compile SYNTAX_OK（专用解释器）
- [ ] 双线程无死锁、无资源竞争（锁/队列正确）
- [ ] 回执含 reviewReason/stdoutText/evidence/acceptance（8 字段 final-message）

## 回执要求（final-message.json，8 字段）
status / reviewReason / stdoutText / evidence（证据路径+关键结论）/ acceptance（Gate 逐项）/ verdict（是否提交/打 tag）/ 越界声明 / nextSteps。**技术执行完成即如实写"技术执行完成，待主脑复核与 Owner 冻结"，不得冒充冻结、不得自行打 tag、不得自行提交。**

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-30 | 初版：双线程伪流式（采集∥识别，1s 重跑节流 + 说完终跑 + 异常回退），源任务卡 voice-136-pseudo-streaming |
