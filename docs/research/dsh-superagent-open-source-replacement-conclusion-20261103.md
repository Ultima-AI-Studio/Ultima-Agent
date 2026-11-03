# dsh-superagent 开源替代排查结论与逐组件精读迁移评估

- **日期**：2026-11-03
- **作者**：豆包主脑（UltimaAgent 管理端）
- **关联**：UltimaAgent 工单 `wo-ultimaagent-20261101-0021--work-capability.md`（0021，Jarvis 工作能力）；产品本体下一步架构决策（Super Agent 式中间层）
- **触发**：开源优先硬边界 G-OSS-001（任何自研/自写模块开工前必须附开源替代排查结论；判定标准 = 现成件能否直接解决需求、集成成本是否低于重写）
- **对象仓库**：`deepseek-ai/dsh-superagent-prototype`（DeepSeek Super Agent 开源原型）
- **结论一句话**：**借鉴重写、不整仓拼装**——Super Agent 给的是组织方式与设计蓝图，落地为本地 Python/OpenJarvis 轻量中间层 v1；正确拼装对象 = "OpenJarvis 底座 + Super Agent 设计蓝图"。

---

## 1. 判定卡（结论摘要）

| 候选路径 | 判定 | 理由 |
| --- | --- | --- |
| 整仓拼装 dsh-superagent | **不推荐** | ①跨栈：DSH = Node/TS/npm 插件生态，本地 = Python/OpenJarvis 专用解释器 + qwen3-8b；②它是 DeepSeek Harness（dsh）平台的 bundle/插件原型，非独立组件；③v0.1 非官方研究原型，README 自述"may still contain bugs"，breaking changes 频繁 |
| 借鉴代码自行重写 | **推荐** | MIT 许可允许；Router/Worker/Ticket/Watchdog/消息过滤/飞书入口是成熟设计蓝图；落地 Python/OpenJarvis 写轻量中间层 v1（~1500-2000 行概念级重写），复用 OpenJarvis 已有件 native_react/ToolRegistry/SessionStore |
| 换底座为 DSH | **被否** | 破坏已冻结的本地语音链路（KWS→ASR→8B→TTS，0014-0020 线）与 OpenJarvis 验收基础；底座迁移是独立大工程，收益不抵成本 |

## 2. 开源事实核验（已核验）

- 仓库：`github.com/deepseek-ai/dsh-superagent-prototype`
- 许可证：MIT；Copyright (c) 2026 DeepSeek Harness Team
- 技术栈：TypeScript；版本 0.1
- 发布：2026-10-31 09:32 UTC 开源；约 22 小时内 4340 stars / 401 forks
- 定位：**非官方产品**。README 原话："Research prototype for reference only, not an official DeepSeek product…may still contain bugs…Review and adapt it before using it in your own environment"；"proactive coding agent for one GitHub repository, packaged as a bundle for DeepSeek Harness. It listens to GitHub and, optionally, Feishu."
- 形态：DeepSeek Harness（dsh）平台的 bundle/插件，非独立组件；dsh 平台 `github.com/deepseek-ai/deepseek-harness`，MIT，Node 生态，`npx @deepseek-ai/dsh web`，插件为 npm 包 workspace peerDependencies（@deepseek-ai/dsh-agent/dsh-llm/dsh-scope/dsh-session 等），Cordis 驱动一切皆插件
- 场景：GitHub issues/PR 评论 + 可选飞书消息 → 工单（work item，独立 agent session 和目录）→ PR 交付；p95 15.7 min
- 核心理念："人的注意力才是多任务 agent 工作流的瓶颈，Router 是全局协调者"

## 3. 整仓拼装不推荐（三条理由）

1. **跨技术栈**：DSH 是 Node/TypeScript/npm 插件生态，本地底座是 Python（OpenJarvis 专用解释器 `venv-openjarvis`，Python 3.13.16）+ qwen3-8b 本地模型。整仓拼装意味着引入一整套 Node 运行时、DSH 平台依赖、Cordis 插件机制，与本地 Python 底座形成双运行时常驻。
2. **非独立组件**：它是 dsh 的 bundle/插件原型，离开 dsh 平台无法独立运行；其价值在组织方式（Router/Worker/Ticket/Watchdog），不在可移植代码。
3. **v0.1 非官方研究原型**：README 明确警告需"Review and adapt"，版本 0.1、breaking changes 频繁，作为生产底座风险高。

## 4. 借鉴重写推荐（设计蓝图六点，全部落进 0021 蓝图与中间层 v1）

1. **会话隔离** → `work_service` / `work_tools` 拆分（每工单独立会话+目录，对应 CodeX worktree 隔离）
2. **Ticket 状态机**（Ticket 自有状态，open→ended→open 由人消息恢复）→ 0021 T4/T5 任务链路
3. **Watchdog 自守护** → 全局看门狗超时/卡死检测
4. **计算与状态分离** → SessionStore 持久化（效果队列/Outbox）
5. **事件驱动 + 两级消息过滤**（Source→Trigger→scope 过滤）→ 统一事件入口
6. **订阅直通**（订阅扇出，人只验收结果）→ 交付/播报链路

**已符合（无需照搬）**：环境分离（独立 worktree）、人只管验收、主动不打扰（不被打扰原则）。
**不适合抄**：GitHub PR 为中心场景（本地产品无此形态）、无状态云容器底座（本地常驻进程）。

## 5. 换底座为 DSH 被否

- 破坏已冻结验收基础：本地语音链路（KWS 参数基线、ASR、8B 主脑、CV3 TTS）与 OpenJarvis 验收标准均已冻结；
- 底座迁移 = 独立大工程，且产品北极星（贾维斯）不依赖 DSH；
- 与"拼装现成件+自写接线"开源先例（OpenJarvis + Jarvis.ceo 借鉴）冲突，重复引入同层能力。

## 6. G-OSS-001 合规论证（不违反开源优先硬边界）

判定标准两条，逐条对照：

1. **现成件能否直接解决需求？** Super Agent 不能直接解决——它是 dsh 插件形态、GitHub/PR 场景、Node 栈；本地需要的是 Python 中间层（内脑编排→外脑调配）。它给的是组织方式/设计模式，不是可直接接入的组件。
2. **集成成本是否低于重写？** 整仓拼装成本（双运行时常驻 + 调试不稳定 v0.1 + 场景适配改造）＞ 借鉴重写成本（概念级 Python 重写 ~1500-2000 行，复用 OpenJarvis 已有件）。

**结论**：判定标准未触发"必须拼装现成件"的情形；"借鉴重写"符合开源优先精神（优先消化开源设计而非自创），且 MIT 许可明确允许。正确拼装对象 = "OpenJarvis 底座 + Super Agent 设计蓝图"。

## 7. 拉取与精读记录

- 调研副本（clone 只读，未改代码）：`H:\UltimaAI\UltimaAgent\research\dsh-superagent-prototype`（2.5MB / 216 文件）
- HEAD：`6337fc823ce20251c8de8085948165c81aaa701e`
- 网络：git 全局代理（http.proxy 1080 / http.https://github.com.proxy 1083 / https.proxy 1080）均无监听失效；本机唯一可用代理 `http://127.0.0.1:7897`；clone 使用 `-c http.https://github.com.proxy=http://127.0.0.1:7897`
- 顶层结构：docs/（000-philosophy…008-cookbook 编号文档）、examples/、locale/、prompts/、scripts/、skills/、src/、tests/、LICENSE、package.json、pnpm-lock.yaml、README.md、SETUP.md、tsconfig.json、tsdown.config.ts、vitest.config.ts、cordis.patch.yml（三插件、Feishu 默认禁用）
- 精读范围：`docs/007-architecture.md`、`docs/001-domain.md` 全文；src 全量 .ts 统计 **12,390 行**；精读 12 个核心组件源码

## 8. 组件精读 → 迁移评估矩阵（三档判定）

| 组件（行数） | 精读要点 | 判定 | 中间层 v1 / 0021 落点 |
| --- | --- | --- | --- |
| Ticket 状态机（tickets.ts 423 + stage.ts 26） | Ticket 自有状态：open→ended→open，人消息恢复；Assignments 独立于 Ticket；报告分类 progress/waiting/ready/blocked/failed/dropped；canRetry 判 stalled | **高**（概念级 Python 重写） | T4/T5 任务链路 + 工单卡状态机 |
| 效果队列（effects.ts 161） | SQLite 持久队列：kind/key 一行、同 key 替换 payload、指数退避、Later 推迟不计数失败、事务内 enqueue 提交后执行、generation 防覆盖 | **高** | SessionStore 加 effect 队列表（状态不丢） |
| Outbox 回执（outbox.ts 52） | 回执唯一写入者；send 保留回执+排队 reply effect 单事务；Source off 等待、conversation gone 丢弃 | **高** | 通知/播报交付不丢 |
| 授权 gate（policy.ts 242） | Mandate 记录授权（strength explicit/inferred + scope + 匹配规则 + policyVersion 哈希）；策略变不撤销 Mandate 只通知；`assessmentOutcome` 要求每条启用规则 exactly-once 评估 + intent_evidence + directionAllowed（implementation_requested、target_basis≠undetermined、无未决设计） | **高** | 审批门/Owner 门 + 防 ACK 自证 |
| 派发/报告/恢复（assignments.ts 140） | assignmentStarted/delivered/read/interrupted/report；interrupted 用 RECOVERY_NOTE 恢复："检查 worktree/git/外部状态，不重复已完成的外部操作" | **高** | 外脑回执→审计→修复闭环；Watchdog 重启恢复 |
| 事件接入（intake.ts 63） | Trigger 幂等去重→scope 过滤→Thread 关联→订阅扇出→排队 Eval；人消息可恢复 ended | **中** | 统一事件入口（语音/工单/外部消息） |
| Pass 调度（passes.ts 69） | 每 2 秒一拍、串行 pump、并发合并（pumpAgain）、setup 未完不干活、失败上报健康 | **中** | 看门狗/定时驱动 |
| 健康注册表（health.ts 35） | 每组件一条、单一写入者（claim 防重复）、release 后 set 失效 | **中** | 全局健康面板 |
| 飞书入口（feishu-* 共约 700） | 事件消费→历史恢复→主题轮询→频道回复；幂等键（每 key 一条回复） | **中** | 可选事件旁路（非主入口，幂等键可抄） |
| 执行器（dsh.ts 673，全仓最大业务文件） | 每 Ticket 一个 DSH Session+目录；WorkerSlots 容量；human wake 优先于 launch；provider/network 失败重试 3 次（transient 判定=408/429/5xx/ECONNRESET 等正则）；失败 turn 15/30/60s continuation | **仅借鉴模式** | CodeX worktree 隔离同构；transient 判定抄成 Python；DSH Session 机制本身不适用 |

**行数估算**：高迁移五项概念级 Python 重写约 1500-2000 行（tickets/assignments/intake/effects/outbox/policy 概念），远低于整仓拼装的集成成本。

## 9. 精读新增 3 发现

1. **`interrupted` 恢复语义**：RECOVERY_NOTE 要求"检查 worktree/git/外部状态，不重复已完成的外部操作"——对应我们的 Watchdog 重启恢复，明确禁止重复外部副作用。
2. **Outbox 回执**：交付不丢的机制化——回执与排队发送同事务，Source 离线等待、会话消失才丢弃。
3. **exactly-once 评估审计**：每条启用规则 must 恰好评估一次 + intent_evidence + directionAllowed——防"ACK 自证"的机制化方案；与 0021 已确立的 observe_runtime_marks 三态（attempt/admitted/verified）互为印证，证明方向一致。

## 10. 落点映射（衔接三层架构判断）

- 三层架构：①本地主脑 qwen3-8b（大脑和嘴，不背任务上下文）②中间层（编排服务层：Ticket 状态机/调度队列/Watchdog 超时卡死检测/SessionStore 持久化/动作级裁决）③外脑（CodeX/DeepSeek，按工单照单执行→回执→独立审计→有界修复→冻结）
- 落地顺序：先"中间层 v1（内脑编排：主脑→工具）"验收冻结，再接"外脑调配"（沿用 G-TASKFLOW-001 闭环，不另起炉灶）
- 本结论的组件级评估即为中间层 v1 与 0021 T4/T5 的组件级输入

## 11. 引用资料

- 仓库 README / LICENSE / docs/007-architecture.md / docs/001-domain.md / src 源码（本地 clone 副本）
- 参考文章：
  - aimagazine.blog/deepseek-super-agent-open-source-prototype/
  - daleelai.com/en/deepseek-dsh-superagent-en/
  - techbytes.app/posts/deepseek-open-sources-dsh-superagent-a-coding-agent-largely-built/
  - www.ainewstoday.net/deepseek-open-sources-a-proactive-coding-agent-and-warns-users-to-fence-it-in
  - dev.to/magnus_modelflare/an-open-source-desktop-agent-that-follows-deepseeks-super-agent-design-and-what-we-left-out-5aig
  - www.deepseek.com/harness/en/ ；dshai.org ；www.dsh.so/zh/

## 12. 落盘登记

- 本文件：`docs/research/dsh-superagent-open-source-replacement-conclusion-20261103.md`（项目 docs 层 ✅）
- UltimaDocs 镜像层：**未执行**（Lark connector 当前关闭，待恢复后镜像）
- 打 tag：随 git 提交登记（见 git 记录）
- 权威源：0021 工单卡 / 北极星清单待后续同步（不在本文件覆盖范围）
