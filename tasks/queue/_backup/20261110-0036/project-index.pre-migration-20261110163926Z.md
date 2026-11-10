# UltimaAgent 项目队列主表

> 唯一权威：本表为 UltimaAgent 项目 Codex 执行队列的**项目级唯一权威汇总**；明细源 = `tasks/queue/<工单文件>`；状态聚合镜像 = `queue-status.json`。
> 建立：2026-10-29（M29 工单派发时补建）｜ 依据：Codex 外部执行端调用范式 §3（工单队列三件套）
> 状态机：待派发 → 执行中 → 审计中 → 已冻结；WIP 双层（每项目执行中 ≤1 + 全项目执行进程 ≤3；审计中 ≤1）；一单一进程，禁止一包多单。

## 一、项目队列总览

| 工单 | 任务数 | 待派发 | 执行中 | 待审计 | 阻塞 | 已完成/闭环 |
|---|---|---|---|---|---|---|
| wo-ultimaagent-20261029-0001 | 4 | 0 | 0 | 0 | 0 | 1 |
| wo-ultimaagent-20261029-0002 | 5 | 0 | 0 | 0 | 0 | 1 |
| wo-ultimaagent-20261030-0003 | 5 | 0 | 0 | 0 | 1 | 0 |
| wo-ultimaagent-20261030-0006 | 3 | 1 | 0 | 0 | 0 | 0 |
| wo-ultimaagent-20261030-0004 | 5 | 1 | 0 | 0 | 0 | 0 |
| wo-ultimaagent-20261030-0005 | 5 | 0 | 0 | 0 | 0 | 1 |
| wo-ultimaagent-20261030-0007 | 5 | 0 | 0 | 1 | 0 | 0 |
| wo-ultimaagent-20261031-0008 | 6 | 0 | 1 | 0 | 0 | 0 |
| wo-ultimaagent-20261031-0009 | 5 | 0 | 0 | 0 | 0 | 1 |
| wo-ultimaagent-20261031-0010 | 5 | 0 | 0 | 0 | 0 | 1 |
| wo-ultimaagent-20261031-0011 | 4 | 0 | 0 | 0 | 0 | 1 |
| wo-ultimaagent-20261031-0012 | 4 | 0 | 1 | 0 | 0 | 0 |
| wo-ultimaagent-20261101-0013 | 5 | 0 | 0 | 0 | 0 | 1 |
| wo-ultimaagent-20261101-0014 | 5 | 1 | 0 | 0 | 0 | 0 |
| wo-ultimaagent-20261101-0015 | 5 | 1 | 0 | 0 | 0 | 0 |
| wo-ultimaagent-20261101-0016 | 6 | 1 | 0 | 0 | 0 | 0 |
| wo-ultimaagent-20261101-0017 | 5 | 1 | 0 | 0 | 0 | 0 |

| wo-ultimaagent-20261108-0028 | 4 | 0 | 0 | 0 | 0 | 1 |
| wo-ultimaagent-20261108-0029 | 6 | 0 | 0 | 0 | 1 | 0 |
| wo-ultimaagent-20261110-0032 | 1 | 0 | 0 | 0 | 0 | 0 |
| wo-ultimaagent-20261110-0034 | 10 | 9 | 0 | 0 | 1 | 0 |
| wo-ultimaagent-20261110-0035 | 8 | 8 | 0 | 0 | 0 | 0 |

## 二、明细

| 工单 | 状态 | 依据/说明 |
|---|---|---|
| wo-ultimaagent-20261029-0001 | 已冻结 | M29 登记控制面（编号核发 + 全局主表 + WIP）；T0-T3 Gate 全绿（专项 12 passed / 编排回归 32 passed / 全量 679 passed + 120 subtests）；提交 b4d282d + tag wo-ultimaagent-20261029-0001-closed-20261029；2026-10-29 主脑独立审计通过 |
| wo-ultimaagent-20261029-0002 | 已冻结 | SSE /events 事件出口（HUD 四角壳真实数据源）；T0-T4；2026-10-29 登记，用户明确要求补 SSE 出口；2026-10-29 派发 codex gpt-5.6-sol PID 10892；独立验收复核 PASS + 四角壳真数据模式端到端演示验收通过 + Owner 确认冻结；tag wo-ultimaagent-20261029-0002-frozen-20261029 |
| wo-ultimaagent-20261030-0003 | 阻塞 | 多层级覆盖 voice-profile（L1 内置默认=贾维斯 / L2 voice-profile.json / L3 运行期覆盖；唤醒词热重载；回答风格三硬约束）；T0-T3 PASS、T4 BLOCKED（2 个范围外既有失败：HUD 冻结哈希漂移 + tasks.json QUEUED 缺 terminal_reason 致 fail-closed）；2026-10-30 登记；派发 codex gpt-5.6-sol PID 18480（已结束）；工单卡 tasks/queue/wo-ultimaagent-20261030-0003--voice-profile.md；清障交 0006 |
| wo-ultimaagent-20261030-0006 | 待派发 | 0003 T4 阻塞清理（HUD 冻结哈希重冻结 + 队列读取容缺）；T0-T2；2026-10-30 登记；优先派发（清障后再推 0004/0005）；工单卡 tasks/queue/wo-ultimaagent-20261030-0006--t4-clear.md |
| wo-ultimaagent-20261030-0004 | frozen | 语音输入通道升级（设备自动探测 + 48k WASAPI A/B）；T0-T4；2026-10-30 登记；冻结 tag wo-ultimaagent-20261030-0004-frozen-20261030；工单卡 tasks/queue/wo-ultimaagent-20261030-0004--input-channel.md |
| wo-ultimaagent-20261030-0005 | frozen | CV3 贾维斯音色（voice 段 + TTS 本地优先）；T0-T4；2026-10-30 登记；三派 PID 21828 收尾（首派 11764 网络失败留证、二派 26236 T4 收尾 OOM 留证）；主脑复核 906/0 + 真机中英转写命中 + 4 Important 一次修复；冻结 tag wo-ultimaagent-20261030-0005-frozen-20261030；工单卡 tasks/queue/wo-ultimaagent-20261030-0005--cv3-jarvis-voice.md |
| wo-ultimaagent-20261030-0007 | audit | 验收 PASS（报告 stage-pseudo-streaming-20261030.md 3,287B，T4 物理音频耦合 3+3 组全 PASS），但代码改动（daemon _LOG_LOCK）仍在工作树未入库。【2026-11-10 核对】维持 audit：待代码入库后才能打冻结 tag。 |
| wo-ultimaagent-20261031-0008 | executing | GPT-SoVITS V3 few-shot 微调训练（杨幂 MOV 音色，LoRA 路线）；T0-T5；2026-10-31 登记；多轮重派（T1 人工听读定稿 A/C 段 → T2 重入 PASS → T3 TCPStore 端口 10013 → MASTER_ADDR/PORT 固定绕随机端口）执行中；冻结门=tag ultimaagent-gptsovits-v3-fewshot-20261031 |
| wo-ultimaagent-20261031-0009 | completed | KWS 唤醒词动态改词自动化验证闭环（scripts/kws_reconfig.py 四子命令）；T0-T3 全 PASS；commit e6ee286 + tag ultimaagent-kws-wakeword-reconfig-20261031 已推远端 |
| wo-ultimaagent-20261031-0010 | completed | 主脑模型降档 qwen2.5:14b → qwen3-8b 无审查版（内存实降 4.1GB）；T0-T3 全 PASS；commit 69d46c0+09a7abc + tag ultimaagent-mainbrain-qwen3-8b-20261031 已推远端 |
| wo-ultimaagent-20261031-0011 | completed | HUD 四角壳 8 锚点布局改造；T0/T1/T2-C1~C5/C7 全 PASS；commit 5cdfca3 + 报告 e00d927 + tag ultimaagent-hud-8anchor-20261031（本地=远端）；T3 八字段回执已交 |
| wo-ultimaagent-20261031-0012 | executing | HUD 天气组件接入（#hud-weather 纯文本占位 → 官方 Meteocons Monochrome 动画图标 + cyan 辉光 + 降水细分映射）；T0-T3；2026-10-31 登记；工单卡 tasks/queue/wo-ultimaagent-20261031-0012--hud-weather-component.md；派发载荷 dispatch-wo-ultimaagent-20261031-0012-prompt.txt；2026-10-31 派发 codex gpt-5.6-sol PID 24736（静默后台）；冻结门=tag ultimaagent-weather-component-20261031 |
| wo-ultimaagent-20261101-0013 | completed | 8B 切换残留引用清理（做干净）：前置 0010 写域外的 5 文件 7 处非测试引用（子智能体工厂/记忆提取/路由键/bootstrap/注释）+ 5 个测试文件断言同步 + 全量回归 + tag；T0-T4；2026-11-01 登记；工单卡 tasks/queue/wo-ultimaagent-20261101-0013--qwen3-8b-cleanup.md；派发载荷 dispatch-wo-ultimaagent-20261101-0013-prompt.txt；2026-11-01 派发 codex gpt-5.6-sol PID 19172（静默后台）→ 实为 BLOCKED_BEFORE_T0（全局主表无登记、fail-closed、源码零改动）；2026-11-08 主脑已在全局主表补登记并回读命中，解除阻塞，2026-11-08 等 0027 收口后由监视器自动重派（PID 24460），T0-T4 全 PASS 已收口，提交 da85b88d/89503678，冻结 tag ultimaagent-mainbrain-qwen3-8b-cleanup-20261101（远端一致） |
| wo-ultimaagent-20261101-0014 | executing | KWS 唤醒词用户入口+持久化（工单 E）：语音"把唤醒词改成XX"→ 改词+热重载+播报确认+写回 profile（save_user_override）+ 一致性收敛；T0-T4；2026-11-01 登记；方案 docs/plans/plan-voice-three-issues-20261101.md；工单卡 tasks/queue/wo-ultimaagent-20261101-0014--kws-user-entry.md；派发载荷 dispatch-wo-ultimaagent-20261101-0014-prompt.txt；冻结门=tag ultimaagent-kws-user-entry-20261101 |
| wo-ultimaagent-20261101-0015 | executing | ASR 纠错系统化（工单 F）：initial_prompt 扩充天气/时间高频词 + 近音映射独立化 config/asr-normalize.json + "水天"类扩充；T0-T4；2026-11-01 登记；方案 docs/plans/plan-voice-three-issues-20261101.md；工单卡 tasks/queue/wo-ultimaagent-20261101-0015--asr-correction.md；派发载荷 dispatch-wo-ultimaagent-20261101-0015-prompt.txt；冻结门=tag ultimaagent-asr-correction-20261101 |
| wo-ultimaagent-20261101-0016 | executing | 意图路由门+回答校验器+主脑规则接入（工单 C）：三态判定 ALLOW/DENY/ABSTAIN + banned 语义化/≤2 句/grounded 接口 + agent_server 规则块恒加载；T0-T4（含 T2.5）；2026-11-01 登记；方案 docs/plans/reply-constraint-implementation-plan-20261031.md（8B 引用+规则接入已更新）；工单卡 tasks/queue/wo-ultimaagent-20261101-0016--reply-constraint-routing.md；派发载荷 dispatch-wo-ultimaagent-20261101-0016-prompt.txt；冻结门=tag ultimaagent-reply-constraint-routing-20261101 |
| wo-ultimaagent-20261101-0017 | executing | 约束解码结构化输出（工单 D）：ollama format/grammar 实测 qwen3-8b → {reply_text,confidence,grounded} schema + 校验器启用 grounded/confidence；T0-T4；2026-11-01 登记；依赖 0016 出口稳定后派发；方案 docs/plans/reply-constraint-implementation-plan-20261031.md；工单卡 tasks/queue/wo-ultimaagent-20261101-0017--reply-constraint-structured.md；派发载荷 dispatch-wo-ultimaagent-20261101-0017-prompt.txt；冻结门=tag ultimaagent-reply-constraint-structured-20261101 |
| wo-ultimaagent-20261108-0029 | blocked | T1-T4 产物在分支 codex/jarvis-e02-source-grounding-r1（src/brain/work_navigation.py 691 行 / 38,517B，主分支完全没有该文件），但 T5 报告 jarvis-work-e02-offline-minimal-repair-20261108.md 全仓缺失。【2026-11-10 核对】frozen 不成立，改 blocked：报告未落盘 + 主干不可见。 |

## 新路径验证接续（2026-11-01）

| 工单 | 状态 | 说明 |
|---|---|---|
| wo-ultimaagent-20261101-0019 | audit | 新中文持续流KWS离线技术审计PASS；待真人与采集接入验证，未冻结、未切换；旧0018保持取消；报告 docs/reports/voice-next-wekws-proof-20261101.md |

| wo-ultimaagent-20261101-0020 | audit | 新独立语音入口原生KWS/SenseVoice/SAPI；33测试、24真人回放用例、独立审计PASS；20:38用户确认唤醒及时间语音回答；检查点ultimaagent-voice-next-live-pass-20261101，长期质量未冻结；报告docs/reports/voice-next-live-20261101.md |

## 模块3 审计加固（2026-11-08）

| 工单 | 状态 | 说明 |
|---|---|---|
| wo-ultimaagent-20261108-0026 | frozen | 单Agent主干审计加固：标准化审计提示词（guardrails/prompts）+ 统一审计报告规范与生成器（docs/specs/audit-report-spec.md / audit_report.py）+ 端到端闭环测试与失败 case 归档；T0→T1→T2 每步回写北极星看板并单独 commit；工单卡 tasks/queue/wo-ultimaagent-20261108-0026--audit-hardening.md；派发载荷 dispatch-wo-ultimaagent-20261108-0026-prompt.txt；冻结门=tag ultimaagent-audit-hardening-20261108 【2026-11-10 核对】0026 已冻结：T0-T2 全完成，tag ultimaagent-audit-hardening-20261108 指向 f0cad32b；此前误记 executing。 |
| wo-ultimaagent-20261108-0027 | blocked | 审计阶段门硬化（分阶段派发 + 每阶段独立复核）：新增 stage_gate.py（fail-closed 阶段门）+ 独立复核结论规范 + 派发模板硬化 + 用 0026 真实产出演练；起因=0026 实证「执行者=判定者=验收者=进度宣布者」四合一（T0/receipt.json 自写自判、commit 46adbd1f 自改看板）；方案 docs/plans/audit-stage-gate-plan-20261108.md；工单卡 tasks/queue/wo-ultimaagent-20261108-0027--audit-stage-gate.md；**等 0026 收口后派发（WIP 每项目执行中 ≤1）**；冻结门=tag ultimaagent-audit-stage-gate-20261108 【2026-11-10 核对】状态由 interrupted 修正为 blocked：T0/T1 已落地（stage_gate.py、independent-review-contract.md、stage-gated-dispatch-template.md），T2 缺 wo-ultimaagent-20261108-0027-t2.md 报告，无 tag，待补收口。 |
| wo-ultimaagent-20261110-0032 | pending | 分支产出合入主干唯一归口：P1 合 0031（12 文件/1 冲突）、P2 合 0029（210 文件/2 冲突）+ 补 0029 T5 报告；定合并门（frozen 前须主干可见） |
| wo-ultimaagent-20261110-0034 | blocked | 语音真机门（当前唯一未闭合项）：T1-T10；2026-11-10 登记；方案由主脑三阶段 DeepSeek 产出（run wo-ultimaagent-20261110-0034-voice-real-gate-20261110T125206632Z，三阶段全 COMPLETED）；工单卡 tasks/queue/wo-ultimaagent-20261110-0034--voice-real-gate.md。**T1 已执行（2026-11-10，codex runtime run wo-ultimaagent-20261110-0034-20261110T125802009719Z）**：核查表 11,832B / SHA256 D28E82F1…（runs/wo-ultimaagent-20261110-0034-t1-20261110T131134Z/核查表.md），结论 1.1–1.6 **全部未闭合**——7 个契约产物（kws.json/capture.wav/capture.meta.json/asr.json/brain.json/reply.txt/attest.txt）全仓 Count=0；data\voice-next 为 2026-11-01 创建的扁平运行时状态，非单 run 产物；11-08 最后一次真机链 keyword=你好问问 score=null、ASR=「长城用品。」、回复=「我没听清，请再说一遍。」。**参数基线不一致**：产品主入口 9/11 相等，src/voice-next 仅 2/12 相等（threshold 0.25 vs 0.08、score 1 vs 2.0、trailing_blanks 1 vs 8、唤醒词 你好问问 vs 幂幂、增益固定 10 vs 自适应、门控 WebRTC VAD vs peak/rms、BEEP_SETTLE 0.15s vs 1.2s）。判 blocked 的直接原因是 T1 Gate 要求 `git status --short -- src/ config/` 字面为空，入场时已有 76 行既有改动；执行端拒绝清理用户工作树伪造干净状态，改用前后 SHA 指纹证明本次零改动（matches_pre_status/​diff=True）——**属 gate 口径缺陷，非实质失败**。**【2026-11-10 修正】本行「参数基线不一致」一节的定性已更正：`src/voice-next` 的 10 项差异经逐项核对，均有 `src/voice-next/README.md` 的自述设计理由（唤醒词固定「你好问问」、threshold 0.25 为 sherpa 官方默认工作点、固定增益 10、WASAPI 名字解析不依赖旧索引、SoXR 重采样、独立模型 SHA256 锁定），属**有理由的设计差异**而非漂移；仅 `keywords_score` / `num_trailing_blanks` / `BEEP_SETTLE_SEC` 三项 README 未述、判「待定」。另基线文档 §适用入口只点名 E1/E2，`src/voice-next` 本就不在基线定义范围内——「不在范围内」≠「违反基线」。详见 L106 与工单 0035 裁决记录。** |
| wo-ultimaagent-20261110-0035 | blocked | 语音入口权威**改判**：产品主线 = E3（src/voice-next/）+ 音色接回 CV3（E1 那套），E1/E2 降历史实现（不删/不停用/不归档）。**v1.1 的「A：E1 主线 + E3 实验线」已作废**，依据 Owner 原话「E3 的测试我是测过的，好用。但是没有使用我们 E1 训练的声音。」——v1.1 的前提「E1 是唯一被真机验收过的链路」被否证。T0-T7（T0 指纹 / T1 裁决记录改判版 / T2 建产品基线（E3 a–j + CV3 音色段）/ T3 原基线改「历史实现基线」+ PLAY_DEVICE 26→24 / T4 建 CV3 接入规格（只规格不出代码）/ T5 代码 kws_listener.py:43 26→24 / T6 索引登记三份 / T7 总验收差分断言）；2026-11-10 登记。**方案由主脑三阶段 DeepSeek 产出**：改判版 decompose run `wo-ultimaagent-20261110-0035c-e3-main-20261110T141257494Z`（out=1,339 / COMPLETED / 2,282 字符，8 问全答 + D1–D6 写域）；工单 work_order run `wo-ultimaagent-20261110-0035d-work-order-20261110T141648847Z`（out=2,089 / COMPLETED / 3,840 字符）；A 版前序 run（`...0035-entry-baseline-governance-20261110T135656265Z` + `...0035b-work-order-...`）仅留证。**Owner 拍板两条**：Q3 = CV3 不可用时降级 SAPI 并上报（`tts_backend=sapi_fallback` + 日志告警，禁静默）；Q5 = E1 最小修 26→24（只改常量与注释）。`PLAY_DEVICE` 机检结案 = 24（idx=24 WASAPI 44100Hz 耳机 POISON M@LOFREE；idx=26 WASAPI 48000Hz 为 Steam 虚拟声卡）；同一副耳机 MME=4 / DirectSound=15 / WASAPI=24 三栈三索引。**本单不含 CV3 实现**，E3 在本单后仍为 SAPI 音色；工单卡 `tasks/queue/wo-ultimaagent-20261110-0035--voice-baseline-split.md`（v2.0）。**【2026-11-10 执行完成】Codex 已按 T0→T7 全绿并提交 `fc0e1708d301be807532c0e43c6a9fe440be7040`（`docs(voice): establish E3 baseline and CV3 spec`，`show --stat` 恰 6 文件：INDEX +3 / baseline 7 行 / 三份新文档 43+63+48 / kws_listener 2 行）；回执 `VERDICT: COMPLETED` / 自检 PASS / `READY_FOR_DEEPSEEK_AUDIT`，越界声明无；run `wo-ultimaagent-20261110-0035-20261110T143301355804Z`（回执全文已落该目录 `codex-final-report.md`，34,982 字符）。state 记 blocked 的原因是**审计名额已满**（`done.json`：`receipt_valid=true` / `exit_code=0` / `audit_slot_busy=true`，名额被 `wo-ultimaagent-20261108-0030`、`wo-ultimaagent-20261110-0033` 占满 2/2），**属排队而非失败**。**【2026-11-10 审计已完成并通过】**DeepSeek 两轮 Gate T0–T7 各 **8/8 PASS**，`audit_passed=true`（同 run 目录第 3 轮，`audit-20261110-round3.log`）。前两轮仅 T7 FAIL：根因是卡 T7 第 1 条「恰 6 条 =>」与第 5 条「完成提交」互斥——提交后 6 路径即从 status 消失，故以 detached worktree（父提交 `fe23b9e2`）重建「提交前那一刻」，`Compare-Object` 得 **6 条 => / 0 条 <=**，另有 `docs/decisions` 在 T0/T7 的行数对照 2=2 与提交对象差分 6 条（4 A / 2 M）互为印证，证据见 `evidence-t7-diff.txt`（2,144 B）。**审计名额已释放**：全局表 UltimaAgent 侧 `state=audit` 计数由 2 降为 0。冻结未做——`freeze-work-order.py` 的重跑门与 clean-tree 门受仓库既有 562 条未提交改动所阻，与本单产物无关 |
| wo-ultimaagent-20261108-0028 | 已完成（待验收） | E02 写入资格与证据范围提案独立评审（只读）：对 docs/plans/jarvis-work-e02-write-eligibility-and-evidence-scope-proposal-20261108.md 五条建议逐条给结论 + 核验最小改动边界与预算余量 + 产出评审报告；零模型调用、零配额、零源码改动；起因=c794f6fd 待签对象已不在盘上、source37 受控实际运行 FAIL_CONFIRMED、配额归零；工单卡 tasks/queue/wo-ultimaagent-20261108-0028--e02-evidence-scope-plan-review.md；派发载荷 dispatch-wo-ultimaagent-20261108-0028-prompt.txt；2026-11-08 业主拍板走评审路线；2026-11-08 15:26:07 派发 codex gpt-5.6-sol PID 12460（静默后台）；15:43:47 结束，产出评审报告 15,018B（SHA a0eef240…），结论=需补充澄清后再修；4 个阻断点（两文件边界漏 work_research.py 重放模块 / 新增 S4 页后 messages+schema 最小 33,837B 超 32,768 硬门 / 覆盖契约缺可计算定义 / 提案基于 43da3f0 而当前分支缺 work_navigation.py）；主脑独立复核通过（SHA 一致、源码零改动、review/ 未建、current-run 未动）|
| wo-ultimaagent-20261110-0036 | 待派发 | 任务系统改造（元工单）：队列/派发/确定性校验/LLM审计门/冻结打tag 收敛为干净内核；T0-T7 八段；DoR strict PASS（0 error 0 warning）；方案 docs/plans/plan-ultimaagent-task-system-rework-20261110.md；需求 tasks/queue/request-ultimaagent-task-system-rework-20261110.md（§7 Owner 裁决：冻结门=只在写域内干净、状态权威源=新建 JSON 由脚本生成 md）；工单卡 tasks/queue/wo-ultimaagent-20261110-0036--task-system-rework.md；revision 90a4a9d5；2026-11-10 登记 |
