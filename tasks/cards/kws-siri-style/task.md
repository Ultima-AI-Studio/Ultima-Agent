# 任务卡：kws-siri-style

- **task_id**：kws-siri-style
- **标题**：KWS 唤醒 Siri 式改造（VAD 前置 / 唤醒回听 / 自适应阈值 / 两级检测）
- **优先级**：85（P0）
- **reasoningEffort**：medium
- **category**：core　**skill**：code
- **依赖**：无
- **登记核验**：已查注册表（tasks/tasks.json 无同名任务；voice-kws-wake 已 COMPLETED 但未覆盖本改造范围），无重复组件（M1）
- **stage**：v0.4

## goal（做什么 / 禁止做什么）

**背景**：真机唤醒不灵（用户需喊两遍"贾维斯"才触发）＋ KWS 常态推理占 CPU（每约 0.7s 一次 zipformer 推理）。参照 Siri 式多级级联监听架构做改造：**流式监听不费电的关键 = VAD 前置过滤 + 唤醒回听（环形缓冲二次确认）+ 自适应阈值 + 两级检测**。目标：唤醒灵敏（治"喊两遍"）且常态 CPU 下降（治"机器拉满"）。

**做什么**（全部在 `src/brain/voice/kws_listener.py` 内实现，可新增配置开关，默认值不得改变现有行为外的冻结参数）：

1. **T1 · VAD/能量前置**：每段音频进入 KWS 推理前先做短时能量/活动检测（RMS 或等价短时能量，窗口与现 CHUNK=0.1s 对齐）。静音帧/段直接跳过 zipformer 推理。新增可配开关 `KWS_VAD_GATE`（默认 on）、能量阈值 `KWS_VAD_ENERGY`（默认 0.005，可在 0.001~0.05 调）。
2. **T2 · 唤醒回听（环形缓冲二次确认）**：维护最近 2~3 秒 PCM 环形缓冲（16kHz 单声道，与现 SR=16000 一致）。KWS 初判命中后，不用"当前段"直接触发，而用**环形缓冲里的历史音频（覆盖命中时刻前 0.5~1.5s + 命中段）**做一次二次确认（复用同一 KWS 模型打分或轻量打分），二次通过才真正触发唤醒。目的：第一次说话尾部被截断/偏小声也能靠历史音频确认，治"喊第二遍"。
3. **T3 · 自适应阈值**：按短时噪声能量动态调整 KWS 判定阈值。安静环境阈值自动抬升（防误唤醒）、嘈杂环境阈值自动降低（防漏唤醒）。新增可配 `KWS_THRESH_MIN`（下限，默认 0.05）、`KWS_THRESH_MAX`（上限，默认 0.15），当前动态阈值须输出到日志（每次调整记一行 `THRESH_ADJ`）。
4. **T4 · 两级检测（增强，可配开关）**：新增 `KWS_PRE_FILTER`（默认 on）：zipformer 前先做超轻量预筛（短时能量 + 过零率 + 若可得则音素似然粗筛），预筛不通过直接 SKIP（记 `PRE_FILTER_SKIP`），通过才跑 zipformer。目标：常态推理次数再降。

**保留**：现有单实例锁（`%TEMP%\ultima-kws-listener.pid`）、预热后台化（WARMUP_DONE/WARMUP_TTS_FAIL/WARMUP_FAIL 日志）、KWS_READY 监听态、真机参数默认值（SR=16000、MIC_DEVICE=1、PLAY_DEVICE=26、GAIN=30、MIN_LEN=0.5、END_SIL=1.2、CHUNK=0.1、MAX_LEN=8.0、KWS_THRESHOLD=0.08 作为自适应阈值的静态基线参考值保留）。

**禁止**：
- 禁止改动 ASR（`asr.py`，SenseVoice 主链路）与 TTS 链路任何逻辑；
- 禁止改动 `agent_server.py`、`daemon.py`、`watchdog-loopguard.py`（刚完成性能单实例修复，不得回归）；
- 禁止改动队列引擎（tasks/queue_engine）任何逻辑；
- 禁止修改冻结真机参数默认值（只能新增开关/新参数，不得改既有默认值语义）；
- 禁止向 fileDomain 之外写文件；
- 禁止引入新第三方依赖（纯标准库/sounddevice/现有依赖内实现）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT-1: VAD 前置生效——安静环境 60s 日志显示 KWS 推理次数较改造前显著下降（改造前约每 0.7s/次；改造后静音段跳过，有 `SKIP_VAD` 计数日志，≥50% 跳过）
- [ ] ACCEPT-2: 唤醒回听生效——日志有 `REARM`（环形缓冲二次确认）事件；模拟"第一遍小声/被截断、第二遍完整"场景，命中后先读历史缓冲再触发，触发一次成功
- [ ] ACCEPT-3: 自适应阈值生效——日志有 `THRESH_ADJ` 动态阈值记录；安静时阈值高于基线、有噪声时低于基线；上下限参数（KWS_THRESH_MIN/MAX）可配且生效
- [ ] ACCEPT-4: 两级检测生效——`KWS_PRE_FILTER=on` 时日志有 `PRE_FILTER_PASS/SKIP` 计数，SKIP 段不跑 zipformer；设为 off 时行为回退到单级（仅 KWS）
- [ ] ACCEPT-5: 回归——正常说"贾维斯"仍能唤醒（真机/麦克风输入听测一次成功）；KWS_READY、单实例锁、预热后台化日志不倒退
- [ ] ACCEPT-6: 性能——60s 安静场景 CPU 占用与 KWS 推理次数较改造前下降，回执附改造前后对比数据（改造前基线：每 0.7s 一次 zipformer、常态占约 1 核）
- [ ] ACCEPT-7: 编译——`python -m py_compile` 零错误零警告；既有单实例锁/预热后台化代码无回归
- [ ] ACCEPT-8: 回执完整——receipt 含 reviewReason / stdoutText / evidence / acceptance 逐项核对
- [ ] ACCEPT: 汇总——ACCEPT-1~8 全部 PASS 方可交付

## dependsOn[]

- 无

## fileDomain[]

- `H:/UltimaAI/UltimaAgent`

## priority

- 85（P0）

## reasoningEffort

- medium

## category + skill

- core　skill：code

## receipt（完成时回执）

- reviewReason：本次交付判断依据
- stdoutText：验证输出摘录（含 SKIP_VAD / REARM / THRESH_ADJ / PRE_FILTER_* 日志行、唤醒成功输出）
- evidence：验证时间 / 输入 / 输出 / 改造前后对比数据
- acceptance：ACCEPT-1~8 逐项结果

## retryCount

- 0

## 变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-28 | 初版：Siri 式 KWS 改造工单（VAD 前置/唤醒回听/自适应阈值/两级检测，源自 Siri 监听架构调研 + 真机唤醒不灵/CPU 占满两个问题） |
