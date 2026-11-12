# 任务卡：voice-136-pseudo-streaming

- **task_id**：voice-136-pseudo-streaming
- **标题**：双线程伪流式（采集∥识别，边说边出字）
- **优先级**：60（P1）
- **reasoningEffort**：medium
- **category**：voice　**skill**：engineering
- **依赖**：#132（参数三处对齐，已验收）、#133（KWS 变体+score，已验收）、#134（VAD 断句，已验收）、#135（ASR GPU A/B：结论不落地，已登记）
- **登记核验**：已查 tasks/tasks.json 无重复；依据 docs/reports/voice-chain-direction-audit-20261030.md 第四步"双线程伪流式——结构改造，独立工单"。

## goal

采集线程持续进队，识别线程在说话中提前开跑（whisper-real-time 路线：新块到达即把累积缓冲送识别，边说边出字），不等说完。目标：端到端「问就答」再省一步（采集结束即已有识别中间结果，ASR 用时基本归零到首词延迟）。

**禁止**：
- 禁止引入真流式 ASR 模型（P2 延伸：sherpa streaming transducer / Paraformer 本地版，另立项）；
- 禁止改动 #132/#133/#134 已冻结参数（threshold 0.08、keywords_score 3.0、QUIET_AFTER_SPEECH 1.2 兜底、BEEP_SETTLE_SEC 1.2、sinc 重采样、VAD min_silence 0.5s）；
- 禁止触碰 TTS 链路（CV3 克隆音色强项不动、不云化）；
- 禁止重构 wait_wakeup（唤醒态保持单线程流式 KWS）；
- 伪流式重跑整段须控制频率（如每 1s 一次），不得让识别线程抢占采集线程导致卡顿。

## 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T1 | `data/logs/voice-listen-daemon.py` | 双线程骨架：采集线程入队 + 识别线程消费，主循环改造不阻塞采集 |
| T2 | `data/logs/voice-listen-daemon.py` | 重跑节流：累积缓冲每 1s 送一次 ASR，取最后一次结果；说完后立即终跑 |
| T3 | `data/logs/voice-listen-daemon.py` | 回退保护：识别线程异常/超时（>600s）回退原"采集完再 ASR"路径，不丢轮次 |
| T4 | 真机验证 | 0.6s 短指令"查天气"与 10-29 停顿场景：首字延迟对比（伪流式 vs 串行）落盘 |

## 任务明细

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
**写什么**：识别线程任何异常/超时 → 标记降级，主循环回退"采集完再调 asr_transcribe"原路径，本轮不丢。
**验收（Gate）**：注入异常后本轮仍返回 ASR 结果；日志留痕。
**禁止**：异常吞掉无日志。

### T4 · 真机对比落盘
**文件**：`data/logs/voice-listen.log` + 报告
**写什么**：真机各 ≥3 轮"贾维斯+查天气"与"贾维斯+长指令"，记录首字延迟（唤醒命中→TTS 播放）伪流式 vs 串行（#134 基线数据）。
**验收（Gate）**：首字延迟下降量量化落盘；无回归（无新增误唤醒/掐断）。
**禁止**：无数据宣称收益。

## 总验收（阶段 DoD）
- [ ] T1-T4 全部过 Gate
- [ ] 伪流式 vs 串行首字延迟对比数据落盘
- [ ] 基线文档 docs/specs/kws-wakeup-params-baseline.md 变更记录追加 #136
- [ ] 冻结参数零漂移核对

## 验收要点
- [ ] py_compile SYNTAX_OK
- [ ] 双线程无死锁、无资源竞争（锁/队列正确）
- [ ] 回执含 reviewReason/stdoutText/evidence/acceptance

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-30 | 初版：双线程伪流式（采集∥识别，1s 重跑节流 + 说完终跑 + 异常回退） |
