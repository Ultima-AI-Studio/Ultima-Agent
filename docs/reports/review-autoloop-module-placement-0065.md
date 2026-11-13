# Autoloop 融合方案「模块归属」独立评审

> 工单：`wo-ultimaagent-20261113-0065`  
> 评审对象：`docs/plans/next-autoloop-融合实施方案-20261113.md` §11  
> 执行日期：2026-11-14（Asia/Shanghai）  
> 写域：仅本报告；不改方案、基线、三卡、队列、tracker 或代码。

## §1 结论

**结论等级：有条件通过。**

理由：六块口径、Console 逻辑账与 Middleware 物理写口的分层可以成立，且无需新增第七块；但方案 §11 的 M7 与 `cancel_observe` 两行需要改判，0062 的 §27.3 归属标注和 §27.4 第二主文风险必须在开工前收敛。结论依据分别见方案六行原文 `docs/plans/next-autoloop-融合实施方案-20261113.md:204-209`、模块职责 `docs/tracker/next-基础能力架构-20261113.html:185-243`、任务库与主链契约 `docs/specs/next-感知交互参数基线-20261113.md:1298-1329,1540-1553,1739-1751`。

### 1.1 六行裁定摘要

| # | 方案行 | 裁定 | 摘要与原文坐标 |
|---|---|---|---|
| 1 | P0 三件套 | **维持** | 物理写实现落 Middleware.queue_engine；方案 `:204` 原文“Middleware · queue_engine”，基线 `:1310-1313` 原文同时区分“Console 名下”与“物理实现沿用 tasks/queue_engine”。 |
| 2 | M3 指令数据分离 | **维持** | Middleware.delegation 执行业务校验，治理⑤只出防投毒约束；方案 `:205` 原文正是该分工，架构页 `:243` 原文治理⑤“自身不执行业务动作”。 |
| 3 | M4 跳数＋扇出 | **维持** | Console 拥有编排阈值，Middleware 只执行与留票据；方案 `:206` 原文“Console · 任务编排”，架构页 `:304` 原文“Console 决定……Middleware 负责跑起来、留票据”。 |
| 4 | M7 `ask.key` | **改判** | 改为 Console.task_store 主体＋Core.clarify 生产者＋Surface 只读呈现；方案 `:207` 原文只列 Core＋Surface，但架构页 `:207` 原文 Surface“只画、不管”，基线 `:1310` 原文任务账“Console 名下”。 |
| 5 | `session_id` | **维持** | 归 Core↔Senses.Voice，唯一主文只认 §25.1；方案 `:208` 原文“主文已在 §25.1”，基线 `:1547` 原文来源为“Voice / Core 会话管理”。 |
| 6 | `cancel_observe` | **改判** | 主体改到 queue_engine run 取消投影/票据；Shell 供证、state_machine 只守八态；方案 `:209` 原文挂 state_machine＋Shell，0063 `:71` 原文却明确“三值是 run 层观测结果，不是第九种队列状态”。 |

### 1.2 三卡写域结论

- 0061：**一致**。allowlist 见 `tasks/queue/wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md:147-158`，原文只列 inbox/writer/reconcile/schema/派发器最小调用收敛。
- 0062：**需调整**。卡 `tasks/queue/wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md:173-188` 对 §27.4 再写字段表与会话规则，和基线 §25.1 `docs/specs/next-感知交互参数基线-20261113.md:1540-1553` 的既有主文重复；§27.3 还须补 Console.task_store 主体。
- 0063：**一致**。卡 `tasks/queue/wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md:162-168` 只写 §25.10，且 `:113` 原文要求八态 diff 为空、`CANCELLED_PENDING` 不得成为新状态。

**未决项：4 条**，见 §6。

### 1.1 依据清单

| 实际读取材料 | 版本／定位标识 | 本报告使用范围 |
|---|---|---|
| `docs/INDEX.md` | 版本行见文件开头；审计入口规则见 §0～§2 | 导航与权威源定位 |
| `tasks/queue/wo-ultimaagent-20261113-0065--autoloop-module-placement-review.md` | v1.0；T1→T5 | 本单范围、段序、Gate、唯一写域 |
| `docs/plans/next-autoloop-融合实施方案-20261113.md` | 派单身份为 v0.3＋§11；但文件头 `:1-4` 仍写“v0.1（待评审，未派发）”，文件 `:192` 又写“本方案 v0.3” | 全文；重点 §2、§3、§11 |
| `docs/plans/next-autoloop-三单拆解-20261113.md` | 2026-11-13；`:5` 原文“派单事实指定为 v0.3” | 全文；主文归属、依赖、Gate 覆盖 |
| `docs/tracker/next-基础能力架构-20261113.html` | 2026-11-13；§02、Console 边界、§06 | 六块、Console、治理⑤及相邻关系 |
| `docs/specs/next-感知交互参数基线-20261113.md` | v1.0 初版；§二十一、§二十二、§二十五 | 归属定案、任务库、八态与主链契约 |
| `tasks/queue/wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md` | v1.0，待审卡 | P0 写域 |
| `tasks/queue/wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md` | v1.0，待审卡 | P1 §27.1～§27.4 写域与唯一主文 |
| `tasks/queue/wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md` | v1.0，待审卡 | §25.10 唯一写域与八态边界 |

版本标识冲突是已读事实，不在 T1 裁决：`docs/plans/next-autoloop-三单拆解-20261113.md:30` 原文“方案文件首行仍显示‘v0.1’，而派单卡与用户载荷指定该文件为 v0.3”。

## §2 模块职责事实表

### 2.1 六块＋Console＋治理⑤（八条原文）

| 对象 | 坐标 | 原文直引 |
|---|---|---|
| Core | `docs/tracker/next-基础能力架构-20261113.html:185-188` | “Core · 理解与裁决”；“听懂 → 决策 → 路由 → 复述确认；记忆写入的唯一裁决者” |
| Senses.Voice | `docs/tracker/next-基础能力架构-20261113.html:192-195` | “Senses.Voice · 语音进出”；“唤醒 → 收声 → 识别 → 合成；会话不因一轮结束而中断” |
| Shell | `docs/tracker/next-基础能力架构-20261113.html:199-202` | “Shell · 进程治理”；“唯一允许「起进程、管进程、收进程」的地方；启停意图由 Console 下达” |
| Surface | `docs/tracker/next-基础能力架构-20261113.html:206-209` | “Surface · 界面与呈现”；“只画、不管：呈现内容与时机由 Console 定；四角壳 8 锚点是唯一显示形态” |
| Memory | `docs/tracker/next-基础能力架构-20261113.html:213-216` | “Memory · 记忆与自学习”；“三库一索引；写入由 Core 裁决，检索按库分开” |
| Middleware | `docs/tracker/next-基础能力架构-20261113.html:220-223` | “Middleware · 执行端与票据”；“执行端可替换、一次一主、票据可追；八态定义权在此层（不是 Console）” |
| Console（不是六块之一） | `docs/tracker/next-基础能力架构-20261113.html:229-238` | “Console ＝ 引擎中心管理调度器”；“任务编排 派发 / 优先级 / 依赖”；“八态只读写、不定义（定义在 queue_engine.state_machine）” |
| 治理⑤（不是六块之一） | `docs/tracker/next-基础能力架构-20261113.html:241-247` | “⑤ 治理与约束 · 横切（不占运行时模块）”；“不属于六块中的任何一块，也不单独成块；对所有模块施加约束，自身不执行业务动作。” |

模块数口径的原文坐标为 `docs/tracker/next-基础能力架构-20261113.html:128,144-147`：“模块数仍是六块”；“六块运行时：Core / Senses.Voice / Shell / Surface / Memory / Middleware”；“＋ Console”；“＋ 治理与约束 ⑤：横切，不占运行时模块”。

### 2.2 队列、票据、状态机与主链归属事实

| 事实 | 坐标 | 原文直引 |
|---|---|---|
| PTY 的执行面归 Shell，Middleware 只持句柄 | `docs/specs/next-感知交互参数基线-20261113.md:1213-1221`（§21.2） | “归属 Shell.pty_host，与 JobObjectManager 同层；Middleware 只持句柄、不自己造终端”；“会碰进程的代码归 Shell” |
| worktree 建立动作归 Middleware | 同文件 `:1224-1229`（§21.3） | “派发前由 Middleware 建” |
| Console 用量账本只读，阈值与动作归治理⑤ | 同文件 `:1231-1239`（§21.4） | “Console.usage_ledger”；“性质：只读消费，不参与派发决策”；“阈值与动作：归 治理⑤ 规则库” |
| Console 与治理⑤是结构位，不增六块 | 同文件 `:1259-1264`（§21.7） | “Console 与治理⑤ 必须各有卡（结构性缺口）”；Console Gate 为“碰进程/网络/磁盘/像素的代码 0 处” |
| 任务库逻辑归 Console | 同文件 `:1298-1313`（§22.1～§22.2） | “任务库归 Console（它本来就是 Console 的账）”；“归属：Console 名下，与 usage_ledger 同级，属「管」的账本” |
| 任务库物理实现沿用 queue_engine | 同文件 `:1310-1313`（§22.2） | “物理实现：沿用 tasks/queue_engine：QueueStorage（tasks.json 索引 ＋ run/&lt;id&gt;/）＋ card_contract 卡契约 ＋ receipt_contract 票据 8 键” |
| 任务状态唯一枚举仍是八态 | 同文件 `:1315-1318,1356-1360`（§22.2、§22.5） | “状态轴只走八态（queue_engine.state_machine 为唯一枚举源，禁第二套状态名）”；“任务库唯一实现面是 tasks/queue_engine” |
| Console 对任务库给 Surface 的是只读视图 | 同文件 `:1329`（§22.2） | “Console 只读视图交 Surface 呈现” |
| session_id 已在 Voice↔Core 信封成为必填字段 | 同文件 `:1540-1553`（§25.1） | “Voice ↔ Core 回合与播报信封”；“session_id｜是｜Voice / Core 会话管理｜归属会话标识” |
| 澄清决策由 Core 主链产生 | 同文件 `:1600-1610`（§25.4） | `clarify` 后续动作：“只发澄清问题，不建计划、不派发” |
| Console 接收计划并返回队列状态 | 同文件 `:1645-1672`（§25.6） | “Console 计划交接”；首次受理 `queue_state` “只能为 QUEUED”；“拒绝后 Console 不落 EXECUTING” |
| 派发完成事实只认 receipt | 同文件 `:1674-1715`（§25.7） | “冻结时序只有一条：prepare → policy.check → start → stream* → finalize”；“完成事实只认 receipt” |
| 取消唯一主文位于 §25.10，强杀证据是 ActiveProcesses==0 | 同文件 `:1739-1751`（§25.10） | “统一取消映射（E-01，取消唯一主文）”；run 缺 ack 强杀后“须证明 ActiveProcesses==0”；“不新增状态” |

### 2.3 T2 只登记、不裁决的字面冲突

1. **任务账归属与物理写实现的表面张力**：方案 `docs/plans/next-autoloop-融合实施方案-20261113.md:204,213` 写“P0 三件套 → Middleware · queue_engine”及“写口在 Middleware、读视图在 Console”；基线 `docs/specs/next-感知交互参数基线-20261113.md:1310-1313` 同时写“归属 Console 名下”与“物理实现沿用 tasks/queue_engine”。本 T 只记录两层措辞，留 T3/T4 判断是否真冲突。
2. **卡片幂等的行为主体未在方案行内写全**：方案 `:207` 写“Core · 澄清出口主文 ＋ Surface · task_manager_panel 呈现细则”；但架构页 `docs/tracker/next-基础能力架构-20261113.html:207` 写 Surface “只画、不管”，基线 `docs/specs/next-感知交互参数基线-20261113.md:1310,1329` 又把任务账归 Console、Surface 定为只读呈现。留 T3 裁决幂等账落点。
3. **session_id 唯一主文与 §27.4 新定义之间有重复风险**：方案 `docs/plans/next-autoloop-融合实施方案-20261113.md:208` 写“主文已在 §25.1，§27.4 只登记字段不重定义”；0062 卡 `tasks/queue/wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md:173-188` 又给出字段表、三条映射规则和两条负例。留 T4 检查是否形成“两处主文”。
4. **取消观测值与八态定义权需要分层**：方案 `docs/plans/next-autoloop-融合实施方案-20261113.md:209` 把 `cancel_observe/CANCELLED_PENDING` 挂到 “Middleware · state_machine ＋ Shell”；0063 卡 `tasks/queue/wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md:69-73` 原文“三值是 run 层观测结果，不是第九种队列状态”。留 T3 判断 `state_machine` 是主落点还是只提供不变式。

## §3 方案 §11 六行裁定

### 3.1 S11-1 · P0 三件套 → Middleware.queue_engine

**裁定：维持。**

- 方案原判断：`docs/plans/next-autoloop-融合实施方案-20261113.md:204` 原文“P0 三件套……Middleware · queue_engine（票据与八态唯一写权）”。
- 职责原文：`docs/tracker/next-基础能力架构-20261113.html:220-223` 原文“Middleware · 执行端与票据”“票据可追；八态定义权在此层（不是 Console）”。基线 `docs/specs/next-感知交互参数基线-20261113.md:1310-1313` 同时写明任务库“归属 Console 名下”而“物理实现沿用 tasks/queue_engine”。
- 行为性质：writer、inbox 消费、claim 票据与 reconcile 都直接围绕队列物理实现和执行票据；0061 `tasks/queue/wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md:12-16` 的原文写域是 `inbox/`、`queue-writer.py`、`reconcile-inbox.py`、队列新记录与派发器写入收敛。
- 排他理由：不能落 Console 执行面，因为架构页 `:238` 原文“代码只要会碰进程 / 网络 / 磁盘 / 像素，就不属于 Console”；也不能落 Shell，因为本行不负责进程启停。
- **补充边界（方案 §11 未写全）**：Console 保留任务账本的逻辑归属、编排与只读视图；Middleware.queue_engine 持有物理写实现。两层不可互换：Console 不得直写队列文件，Middleware 不得据此接管优先级／依赖决策。后半句依据 `docs/tracker/next-基础能力架构-20261113.html:304` 原文“Console 决定『做什么、先做谁』，Middleware 负责『跑起来、留票据』”。

### 3.2 S11-2 · M3 指令数据分离 → Middleware.delegation 主体＋治理⑤约束

**裁定：维持。**

- 方案原判断：`docs/plans/next-autoloop-融合实施方案-20261113.md:205` 原文“Middleware · delegation（派发 ABI 入口）主体；治理⑤ · 防投毒只出约束声明”。
- 职责原文：架构页 `docs/tracker/next-基础能力架构-20261113.html:220-223` 把 `delegation` 列在 Middleware 子件；同页 `:241-247` 写治理⑤“对所有模块施加约束，自身不执行业务动作”，并列出“防投毒”。
- 行为性质：0062 `tasks/queue/wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md:62-78` 定义入站事件字段白名单、未知字段拒绝和本地执行上下文补齐，属于进入派发 ABI 前的接入校验。
- 排他理由：治理⑤可定义“不得把资料/执行上下文变成指令”的不变式与红线，但若由治理⑤承载解析、拒收或派活调用，就违反“自身不执行业务动作”；Core 也不应直接解析外部执行事件，否则绕开 delegation 边界。

### 3.3 S11-3 · M4 跳数＋扇出熔断 → Console.orchestration

**裁定：维持。**

- 方案原判断：`docs/plans/next-autoloop-融合实施方案-20261113.md:206` 原文“P1 M4 跳数 8 ＋ 同轮扇出 3｜Console · 任务编排”。
- 职责原文：架构页 `docs/tracker/next-基础能力架构-20261113.html:229-238` 把 Console 的任务编排写为“派发 / 优先级 / 依赖”；关系表 `:304` 写“Console 决定『做什么、先做谁』，Middleware 负责『跑起来、留票据』”。
- 行为性质：0062 `tasks/queue/wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md:101-121` 的 `hops` 阈值和同轮候选上限决定“本轮还能派几个、是否继续派”，本质是编排放行／熔断策略。
- 排他理由：不落执行器或 Shell，因为它不负责启动/终止进程；也不把阈值主文放 Middleware，避免执行票据层自行决定编排策略。
- **补充边界（方案 §11 未写）**：Console 拥有阈值和放行决策；Middleware.delegation 只能执行该决定并记录“截断候选/熔断原因”票据，不得另设 `hops` 或 fan-out 阈值。这样仍符合 `:304` 的“Console 决定、Middleware 跑与留票据”。

### 3.4 S11-4 · M7 ask.key 卡片幂等 → Core＋Surface

**裁定：改判。** 具体落点改为 **Console.task_store（持久幂等主体）＋ Core.clarify（问题与事项键的生产者）＋ Surface.task_manager_panel（只读呈现）**；0062 §27.3 仍可作为唯一跨模块契约主文，但必须按这三个职责标注，不新增第二节。

- 方案原判断：`docs/plans/next-autoloop-融合实施方案-20261113.md:207` 原文“Core · 澄清出口主文 ＋ Surface · task_manager_panel 呈现细则”。
- 职责原文：Core 的主链 `docs/specs/next-感知交互参数基线-20261113.md:1600-1610` 在 `clarify` 时“只发澄清问题，不建计划、不派发”；Surface 在架构页 `docs/tracker/next-基础能力架构-20261113.html:206-209` 明定“只画、不管”。任务账本则由基线 `docs/specs/next-感知交互参数基线-20261113.md:1310-1313,1329` 定为“Console 名下”且通过 `task.query` 的只读视图交 Surface。
- 行为性质：0062 `tasks/queue/wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md:137-157` 不只描述“问什么/画什么”，还要求按 `ask.key` 查询未关闭事项、持有 `closed_at`、关联关闭凭据并控制 `resolve`，这是有持久状态的卡片账本幂等。
- 改判理由：若把未关闭查询与关闭凭据交 Core，会让 Core 持有第二套卡账；若交 Surface，则违反“只画、不管”。因此 Core 只生成 `clarify` 问题和稳定事项键，Console.task_store 做唯一未关闭查重/关闭账，Surface 只渲染并把用户动作回交 Console。

### 3.5 S11-5 · session_id → Core↔Senses.Voice 对话信封

**裁定：维持。**

- 方案原判断：`docs/plans/next-autoloop-融合实施方案-20261113.md:208` 原文“Core ↔ Senses.Voice 对话信封（主文已在 §25.1）”；“§27.4 只登记字段不重定义”。
- 职责原文：架构页 `docs/tracker/next-基础能力架构-20261113.html:185-195` 将理解/裁决给 Core、语音回合给 Senses.Voice；基线 `docs/specs/next-感知交互参数基线-20261113.md:1540-1553` 已在“Voice ↔ Core 回合与播报信封”把 `session_id` 定为必填，来源为“Voice / Core 会话管理”。
- 行为性质：`session_id` 标识对话会话边界并随 Voice↔Core 信封传递，不是 claim、票据或队列状态。
- 排他理由：不能归 Middleware.claim，因为 claim 是一次派发身份；0061 `tasks/queue/wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md:113` 也原文禁止“把 claim_id 与 session_id 合并”。
- **落点纪律**：唯一主文保持 §25.1；0062 §27.4 只能写“事件入口引用并原样透传 §25.1 的 session_id”，不得再次定义必填性、创建/切换规则或会话语义。此纪律将在 T4 对 0062 卡作写域结论。

### 3.6 S11-6 · cancel_observe／CANCELLED_PENDING → state_machine＋Shell

**裁定：改判。** 具体落点改为 **Middleware.queue_engine 的 run 取消投影／ticket-receipt 子件（主文）＋ Shell（终止事实证据源）＋ Middleware.state_machine（只守八态不变与终态迁移门）**；主文仍只落基线 §25.10、由 0063 承担。

- 方案原判断：`docs/plans/next-autoloop-融合实施方案-20261113.md:209` 原文“Middleware · state_machine（八态定义权）＋ Shell（终止凭据来源）”。
- 职责原文：架构页 `docs/tracker/next-基础能力架构-20261113.html:199-202` 明定 Shell 是唯一进程治理处；`:220-223` 明定 Middleware 持票据且定义八态。基线 `docs/specs/next-感知交互参数基线-20261113.md:556-569` 原文“唯一枚举源＝queue_engine.state_machine 的 QueueState（八态）”。
- 行为性质：0063 `tasks/queue/wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md:61-73` 明说三值“只挂 run”“不是第九种队列状态”，`CANCELLED_PENDING` 只是队列投影；`:89-92` 又要求 receipt 不伪造取消完成、按同一 run 身份对账。因此它是 run 观测/票据投影，不是状态枚举定义。
- 改判理由：把三值主体挂 `state_machine` 容易把 `CANCELLED_PENDING` 升格成第九态；正确分工是 Shell 只提供 `cancel_ack`/`ActiveProcesses==0` 进程事实，queue_engine 的取消投影/receipt 固化三值，state_machine 只在闭合证据成立时允许迁移到既有 `CANCELLED`。基线 §25.10 `:1739-1751` 继续作为取消唯一主文。

### 3.7 是否新增第七块

**否。** 模块数继续是六块，不新增第七块。架构页 `docs/tracker/next-基础能力架构-20261113.html:128,144-147` 原文“模块数仍是六块”，并把 Console、治理⑤分别列为“＋ Console”“＋ 治理与约束 ⑤：横切，不占运行时模块”；基线 `docs/specs/next-感知交互参数基线-20261113.md:1356-1360` 原文“六块模块数不变”“任务库、日志库……不得升格为模块”。本评审的两个改判都只调整既有模块/子件之间的职责，不创造新块。

### 3.8 T3 非复述性判断

可单独引用的独立结论有三条：① M7 的持久幂等主体从“Core＋Surface”改判为 `Console.task_store`，Core 与 Surface 分别退回生产者/呈现者；② `cancel_observe` 主体从 `state_machine` 改判到 queue_engine 的 run 取消投影/票据子件，state_machine 只守八态；③ M4 补“Console 定阈值、Middleware 只执行与留票据”的单向边界。三条坐标分别见本报告 §3.4、§3.6、§3.3，源文坐标均已随判断列出。

## §4 双源判定

### 4.1 “写口在 Middleware.queue_engine、读视图在 Console”何时不是双源

**不是双源的成立条件**：同一任务事实只有一个持久化裁决链——Console 只持逻辑账本归属、编排意图和查询视图；所有队列文件变更经 Middleware.queue_engine 的唯一 writer 落盘；状态值只取 `queue_engine.state_machine` 八态；Surface 只读呈现。坐标与原文链如下：

1. 方案 `docs/plans/next-autoloop-融合实施方案-20261113.md:213`：“写口在 Middleware、读视图在 Console”“Console 只读消费、不得写 queue-status.json”。
2. 基线 `docs/specs/next-感知交互参数基线-20261113.md:1310-1318`：“归属 Console 名下”＋“物理实现沿用 tasks/queue_engine”＋“状态轴只走八态”。
3. 架构页 `docs/tracker/next-基础能力架构-20261113.html:238`：“八态只读写、不定义（定义在 queue_engine.state_machine）”；关系表 `:304,307`：“Console 决定……Middleware 负责跑起来、留票据”“Surface 不回写状态”。

这不是“Console 有一份可写账、Middleware 又有一份可写账”，而是**逻辑所有者/编排者与物理持久化执行者分层**；二者共享同一份 `tasks.json`/run/receipt 事实与八态枚举。基线 `docs/specs/next-感知交互参数基线-20261113.md:1311-1312,1366-1367` 原文把 `tasks.json` 定为唯一索引，并要求“第二份任务索引 0”“第二套状态名 0”。

### 4.2 何时退化成双源

满足下列任一项即退化成双源：

1. Console 或 Surface 出现可写 `queue-status.json`/`tasks.json` 的路径，与 writer 并列裁决同一状态；这违反架构页 `docs/tracker/next-基础能力架构-20261113.html:207,238` 的“只画、不管”与 Console 边界。
2. reconcile 从只读告警变成自动改队列，成为第二写者；0061 `tasks/queue/wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md:81-93` 原文要求“不得自动修改任一输入”“不得让 reconcile 调用 writer 修复差异”。
3. `tasks.json` 之外出现第二任务索引，或 Console/Surface 自建同义状态；基线 `docs/specs/next-感知交互参数基线-20261113.md:1312,1318,1366-1367` 原文分别禁止第二套任务系统与第二套状态名。
4. writer、Console 与卡片层各自定义一份 `ask.key/closed_at/resolve` 事实，而没有 Console.task_store 作为唯一未关闭查重账；这会违反基线 `:1310-1313` 的任务账唯一归属。
5. `CANCELLED_PENDING` 被加入 `QueueState`，与既有 `CANCELLED` 并列；0063 `tasks/queue/wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md:69-73,110-113` 原文明确它“不是第九种队列状态”，且八态 diff 必须为空。

### 4.3 可机检判别句

**PASS 当且仅当**以下四个断言同时成立；任一失败即判“双源退化”：

1. 对仓库 Python AST/文件 I/O 做静态扫描：所有把 `tasks/queue/queue-status.json` 或任务索引以写模式打开、替换、重命名为正式目标的调用者集合 **恰为** `{scripts/queue-writer.py}`；`scripts/reconcile-inbox.py` 对两文件的写调用数为 `0`，且不调用 writer 执行修复。检查文件：`scripts/**/*.py`；检查操作：`open(..., w/a/x/+)`、`Path.write_*`、`os.replace/rename` 及 writer 调用图。
2. 扫描 Console 与 Surface 实现目录：对 `queue-status.json`/`tasks.json` 的持久写调用数为 `0`；Surface 的状态写回调用数为 `0`。其允许行为仅为 `task.query`/只读视图，依据基线 `docs/specs/next-感知交互参数基线-20261113.md:1329` 原文“Console 只读视图交 Surface 呈现”。
3. 解析任务存储配置与状态定义：任务索引正式目标集合只有 `tasks.json` 一个；状态枚举集合与 `queue_engine.state_machine.QueueState` 八态逐字相等，差集为空。依据同文件 `:1318,1366-1367`。
4. 用同一 `claim_id` 重放两次并读取持久结果：首次后队列有效记录集合固定，第二次只产 duplicate 证据而不改状态/note/report 指针；0061 `:61-71` 原文要求“重复投递返回首次结果……不产生第二份有效队列变更”。

判别对象、文件范围、字段/操作和唯一期望均已给出，可由脚本返回布尔 PASS/FAIL；没有使用“大体一致”等不可判定措辞。

## §5 三卡写域核对

### 5.1 0061 · P0 唯一写入口

**结论：一致。**

- 卡内写域坐标：`tasks/queue/wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md:147-158`，原文列出 `inbox/.gitkeep`、`inbox/README.md`、`queue-writer.py`、`reconcile-inbox.py`、对应测试/schema 及 `dispatch-work-order.py` 调 writer的最小改动；队列只能经 writer 写。
- 归属坐标：本报告 §3.1；源文 `docs/plans/next-autoloop-融合实施方案-20261113.md:204` 将其落 `Middleware.queue_engine`，基线 `docs/specs/next-感知交互参数基线-20261113.md:1311` 又确认物理实现沿用 `tasks/queue_engine`。
- 越界核对：0061 `:160-167` 明禁改基线、tracker、全局主表和其他卡，也明禁访问 Next/调用 18766；其 allowlist 没有 Console 实现目录、Surface 或 Shell 进程代码。因此没有越到 Console 或 Shell 的写入。

### 5.2 0062 · P1 §27.1～§27.4

**结论：需调整。** 写域作为“共享基线 §二十七＋对应契约测试”可以承载跨模块契约，但卡面有两个需在开工前改正的归属/唯一主文问题：

1. **§27.3 归属标注需调整**：0062 `tasks/queue/wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md:137-157` 定义按 `ask.key` 查未关闭事项、持有 `closed_at`、关联关闭凭据与 `resolve`。按本报告 §3.4，应在该唯一主文中标明 `Console.task_store` 是幂等账主体，Core 是事项键/澄清问题生产者，Surface 只读呈现；不得继续只标成 Core＋Surface。依据原文分别是基线 `docs/specs/next-感知交互参数基线-20261113.md:1310-1313` 的 Console 任务账与架构页 `docs/tracker/next-基础能力架构-20261113.html:207` 的 Surface“只画、不管”。
2. **§27.4 需收敛为指针而非第二主文**：基线 §25.1 `docs/specs/next-感知交互参数基线-20261113.md:1540-1553` 已将 `session_id` 定为 Voice↔Core 必填信封字段；方案 `docs/plans/next-autoloop-融合实施方案-20261113.md:208` 明说“§27.4 只登记字段不重定义”。但 0062 `:173-188` 又拟写字段表、创建/切换/透传规则与负例，已超出“只登记”。具体调整为：§27.4 只引用 §25.1，并规定 Autoloop 事件入口必须原样携带该既有字段、不得由 `claim_id` 推导；必填性、会话创建/切换语义只认 §25.1，不在 §27.4 重定义。

其余两节无第二主文：0062 `:58-93` 的 §27.1 唯一承载 M3 接入校验；`:97-129` 的 §27.2 唯一承载 M4 熔断。卡的总 allowlist `:211-221` 只写 §二十七及三份对应测试，未越到 §25/§26、队列或实现目录。故本卡不是整域错位，而是上述两处需精确收敛。

### 5.3 0063 · §25.10 cancel_observe

**结论：一致。**

- 唯一写域坐标：`tasks/queue/wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md:162-168` 原文“唯一允许写入：……§25.10 段内新增块”；`:19-22` 明禁改 §15.2.1、写代码、写队列及新增状态。
- 归属坐标：本报告 §3.6 将唯一主文落 Middleware.queue_engine 的 run 取消投影/票据子件，Shell 只供终止证据，state_machine 只守八态；基线 §25.10 `docs/specs/next-感知交互参数基线-20261113.md:1739-1751` 正是 run 取消、强杀与 `ActiveProcesses==0` 的唯一主文。
- 第九态核对：0063 `:69-73` 原文“三值是 run 层观测结果，不是第九种队列状态”；`:110-113` 的 G-25.10-D 要求 §15.2.1 八态 diff 为空，三值与 `CANCELLED_PENDING` 均不得成为新状态枚举。因此卡内没有把 `CANCELLED_PENDING` 写成第九态。

## §6 未决与建议落点

| 未决项 | 为什么本单不代改 | 承担方 | 建议落点／关闭条件 |
|---|---|---|---|
| U-01 方案版本头 `v0.1` 与派单身份 `v0.3` 冲突 | 方案 `docs/plans/next-autoloop-融合实施方案-20261113.md:1-4` 原文仍写“v0.1（待评审，未派发）”；拆解 `docs/plans/next-autoloop-三单拆解-20261113.md:30` 原文确认派单事实为 v0.3。本单禁止改方案。 | 方案维护者＋Owner | 在方案头统一实际版本/状态，并让引用卡使用同一标识；关闭条件是头部、拆解与派单卡三处版本一致。 |
| U-02 M7 持久幂等主体需确认并回写 | 方案 `:207` 原文只列 Core＋Surface；本评审按 Surface“只画、不管”和 Console 任务账作了改判。 | Owner／架构维护者＋0062 卡维护者 | 更新方案 §11 M7 行与 0062 §27.3 归属说明为 Console.task_store 主体、Core 生产者、Surface 只读呈现；不新增第二主文。 |
| U-03 `cancel_observe` 主体标签需确认并回写 | 方案 `:209` 把主体挂 state_machine；0063 `:69-73` 明定它是 run 观测而非状态。本单禁止改方案/卡。 | Owner／架构维护者 | 更新方案 §11 行为 queue_engine run 取消投影/票据主体＋Shell 证据源＋state_machine 八态门；0063 内容无需迁节，只在审卡时核对该标签。 |
| U-04 0062 §27.4 需改为指针式契约 | 方案 `:208` 原文“§27.4 只登记字段不重定义”，0062 `:173-188` 却重写必填、透传、切换和负例。本单不做审卡修改。 | 0062 卡维护者＋后续独立审卡者 | §27.4 只引用 §25.1 并约束 Autoloop 入口原样携带/不得从 claim 推导；会话必填性、创建、切换语义只认 §25.1。 |

除以上 4 条外，本单没有要求新增模块、改六块口径或移动 0063 主文；P2 Autoloop spike 的技术可行性也不属于本单范围。范围依据为本单卡 `tasks/queue/wo-ultimaagent-20261113-0065--autoloop-module-placement-review.md:17-21` 原文“不评审方案的技术正确性”“不新增模块、不改『模块数仍是六块』的口径”。

## §7 自证

### 7.1 T1 Gate 证据

- 骨架要求坐标：`tasks/queue/wo-ultimaagent-20261113-0065--autoloop-module-placement-review.md:43-46`；原文片段：“按 §1 结论／§2 模块职责事实表／§3 方案 §11 六行裁定／§4 双源判定／§5 三卡写域核对／§6 未决与建议落点／§7 自证 的段序建立骨架”。
- 写入前确认：`REPORT_PREEXISTS=False`，本报告为新增文件。
- 依据路径存在性实测输出：

```text
True  docs/INDEX.md
True  tasks/queue/wo-ultimaagent-20261113-0065--autoloop-module-placement-review.md
True  docs/plans/next-autoloop-融合实施方案-20261113.md
True  docs/plans/next-autoloop-三单拆解-20261113.md
True  docs/tracker/next-基础能力架构-20261113.html
True  docs/specs/next-感知交互参数基线-20261113.md
True  tasks/queue/wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md
True  tasks/queue/wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md
True  tasks/queue/wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md
```

- T1 写入动作：只新增 `docs/reports/review-autoloop-module-placement-0065.md`；尚未写最终结论。
- T1 骨架回读原始输出：

```text
REPORT_EXISTS=True
8:## §1 结论
28:## §2 模块职责事实表
32:## §3 方案 §11 六行裁定
36:## §4 双源判定
40:## §5 三卡写域核对
44:## §6 未决与建议落点
48:## §7 自证
SECTION_COUNT=7
```

- **Gate T1：PASS**。判据坐标为本单卡 `:48-53`；原文片段：“报告文件存在，七段标题齐全且顺序与上文一致”。

### 7.2 T2 Gate 证据

- 已按本单卡 `tasks/queue/wo-ultimaagent-20261113-0065--autoloop-module-placement-review.md:59-68` 完成六块、Console、治理⑤共八条原文摘录，并补 §21/§22/§25 归属事实与四项字面冲突。
- 八条职责均为可在源文件逐字搜索的原文，不以概括冒充引文；坐标均已在本轮从带行号全文回读。
- 原文命中回读摘要（源文件行号由 `rg -n` 输出）：

```text
186 Core: 听懂 → 决策 → 路由 → 复述确认；记忆写入的唯一裁决者
193 Senses.Voice: 唤醒 → 收声 → 识别 → 合成；会话不因一轮结束而中断
200 Shell: 唯一允许「起进程、管进程、收进程」的地方；启停意图由 Console 下达
207 Surface: 只画、不管：呈现内容与时机由 Console 定
214 Memory: 三库一索引；写入由 Core 裁决，检索按库分开
221 Middleware: 执行端可替换、一次一主、票据可追；八态定义权在此层（不是 Console）
230 Console ＝ 引擎中心管理调度器
243 治理⑤: 不属于六块中的任何一块，也不单独成块；对所有模块施加约束，自身不执行业务动作
1302 基线: 任务库归 Console
1311 基线: 物理实现沿用 tasks/queue_engine
1318 基线: 状态轴只走八态
1547 基线: session_id｜是｜Voice / Core 会话管理｜归属会话标识
1715 基线: 完成事实只认 receipt
1739 基线: 统一取消映射（E-01，取消唯一主文）
T2_PLACEHOLDER_COUNT=0
```

- **Gate T2：PASS**。八条职责齐全、直引可命中、冲突均双向给出坐标；本阶段未作裁定。

### 7.3 T3 Gate 证据

- 已按本单卡 `tasks/queue/wo-ultimaagent-20261113-0065--autoloop-module-placement-review.md:76-87` 对方案 §11 六行逐行给出固定三态、理由链和具体落点。
- 六行结果：`维持 / 维持 / 维持 / 改判 / 维持 / 改判`；未裁定行数为 0。
- “是否新增第七块”已明确回答“否”，且给出六块口径原文坐标。
- 非复述性判断已在 §3.8 单列，含两项改判与一项补充边界。
- 三态计数回读原始输出：

```text
SIX_ROWS=6
VERDICTS=6
MAINTAIN=4
RECLASSIFY=2
OPPOSE=0
```

- **Gate T3：PASS**。六行与六个固定三态一一对应；无“建议进一步研究”替代裁定。

### 7.4 T4 Gate 证据

- 双源判定已同时给出成立条件、退化条件与四条可脚本执行的 PASS/FAIL 断言；坐标见本报告 §4.1～§4.3。
- 三卡固定结论：0061 `一致`；0062 `需调整`；0063 `一致`。0062 的两个调整点均给出精确节、字段与源文坐标。
- 三卡均以卡内 allowlist/T 编号和源文件行号核对；未把卡面自检当成已开工或技术验收。
- 结构与固定用词回读原始输出：

```text
CARD_SECTIONS=3
CARD_CONCLUSIONS=3
CONSISTENT=2
NEEDS_ADJUSTMENT=1
T4_PLACEHOLDER_COUNT=0
```

- **Gate T4：PASS**。双源两侧与三卡结论均可判定；0062 的 `需调整` 已落到 §27.3 归属标注和 §27.4 指针化两个具体点。

### 7.5 T5 Gate、抽检回读与越界声明

#### 7.5.1 逐 T Gate 汇总

| T | 结果 | 报告内证据 |
|---|---|---|
| T1 | PASS | §7.1：报告新增、七段标题 `SECTION_COUNT=7`、九条依据路径存在 |
| T2 | PASS | §7.2：八条职责原文、§21/§22/§25 事实与原文命中输出 |
| T3 | PASS | §7.3：`SIX_ROWS=6`、`VERDICTS=6`、维持 4／改判 2／反对 0 |
| T4 | PASS | §7.4：双源双侧判据；三卡结论 3 条（2 一致／1 需调整） |
| T5 | PASS | §1 结论、§6 四条未决、下列 8 条随机抽检、越界声明与末行总检查 |

#### 7.5.2 随机抽检回读

从本报告引用坐标池用固定种子 `65065` 随机抽取 8 条，逐行 `Get-Content` 回读；固定种子用于可复现抽样，不按结论人工挑行。

1. `tasks/queue/wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md:113` → “八态状态图 diff 为空；三值与 CANCELLED_PENDING 均不得成为新状态枚举。” → **一致**（支持 §3.6/§5.3）。
2. `docs/specs/next-感知交互参数基线-20261113.md:1310` → “归属｜Console 名下……属『管』的账本” → **一致**（支持逻辑账归属）。
3. `tasks/queue/wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md:71` → “三值是 run 层观测结果，不是第九种队列状态” → **一致**（支持 cancel_observe 改判）。
4. `docs/specs/next-感知交互参数基线-20261113.md:1329` → “Console 只读视图交 Surface 呈现” → **一致**（支持 M7 的 Surface 只读边界）。
5. `docs/tracker/next-基础能力架构-20261113.html:200` → “唯一允许『起进程、管进程、收进程』的地方；启停意图由 Console 下达” → **一致**（支持 Shell 只供进程执行/证据）。
6. `tasks/queue/wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md:183` → “cancel_observe 不在本卡，落 §25.10，由 0063 负责” → **一致**（支持跨卡唯一主文）。
7. `docs/plans/next-autoloop-融合实施方案-20261113.md:205` → “Middleware · delegation……主体；治理⑤ · 防投毒只出约束声明” → **一致**（支持 M3 维持）。
8. `docs/specs/next-感知交互参数基线-20261113.md:1715` → “完成事实只认 receipt” → **一致**（支持 run/receipt 事实边界）。

抽检原始输出：

```text
tasks/queue/wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md:113|- **G-25.10-D**：变更前后 §15.2.1 八态状态图 diff 为空；三值与 `CANCELLED_PENDING` 均不得成为新状态枚举。
docs/specs/next-感知交互参数基线-20261113.md:1310|| 归属 | **Console 名下**，与 `usage_ledger` 同级，属「管」的账本 |
tasks/queue/wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md:71|1. 三值是 run 层观测结果，不是第九种队列状态，也不是 step/plan 状态。
docs/specs/next-感知交互参数基线-20261113.md:1329|**检索入口**：`task.query` 单一入口（按 项目/卡/状态/时间/执行端 过滤），Console 只读视图交 Surface 呈现；**不与 `mem`/`kb`/`exp` 混检**。
docs/tracker/next-基础能力架构-20261113.html:200|<p class="role">唯一允许「起进程、管进程、收进程」的地方；启停意图由 Console 下达</p>
tasks/queue/wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md:183|3. `cancel_observe` 不在本卡，落 §25.10，由 0063 负责。
docs/plans/next-autoloop-融合实施方案-20261113.md:205|| P1 M3 指令数据分离……| **Middleware · delegation**（派发 ABI 入口）主体；**治理⑤ · 防投毒**只出约束声明 |……|
docs/specs/next-感知交互参数基线-20261113.md:1715|……完成事实只认 receipt。……
```

抽检结果：8/8 一致，0 条不一致，满足本单卡 `tasks/queue/wo-ultimaagent-20261113-0065--autoloop-module-placement-review.md:115,119` 的“不少于 5 条”要求。

#### 7.5.3 越界声明

- 基线：**未改**；只读完整读取并引用坐标。
- 方案：**未改**；只读完整读取并给出裁定。
- 三卡（0061/0062/0063）：**未改**；只读完整读取并核对写域。
- 队列：**未改**；未更新任何状态、主表或镜像。
- tracker：**未改**；只读完整读取并引用坐标。
- 代码：**未改**；未写实现、测试、模块或配置。
- 其他文件：**未改**；唯一写入为新增 `docs/reports/review-autoloop-module-placement-0065.md`。
- Git：未执行 `add/commit/tag/push`；一次只读 `git status` 尝试因当前 shell 找不到 `git` 而未执行成功，不产生仓库变更。
- 外部边界：**未访问** `H:\UltimaAI\UltimaAgentNext`；**未调用** 18766；未调用任何外部登记接口。

#### 7.5.4 结论一致性

§1 为“有条件通过”；条件正是 §6 的 4 条未决/修订落点。六行裁定、三卡结论与该等级不矛盾：主体归属框架成立，但两行改判和 0062 收敛未完成前不能无条件通过。

最终静态检查原始输出（写入 Gate 前）：

```text
REPORT_EXISTS=True
SECTIONS=7
SIX_ROWS=6
VERDICTS=6
MAINTAIN=4
RECLASSIFY=2
OPPOSE=0
CARD_CONCLUSIONS=3
UNRESOLVED_ROWS=4
READBACK_ROWS=8
T2_PLACEHOLDERS=0
T3_PLACEHOLDERS=0
T4_PLACEHOLDERS=0
T5_PLACEHOLDERS=0
CONCLUSION_LEVEL=1
```

**Gate T5：PASS**。报告七段齐全；结论等级、六行裁定、三卡结论、4 条未决、8 条随机抽检和逐项越界声明均已回读一致。

T5_GATE=PASS
