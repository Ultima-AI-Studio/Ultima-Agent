# UltimaAgent｜中间层 v1（内脑编排）交付

- **task_id**: wo-ultimaagent-20261103-0022
- **stage**: v0.5（中间层 v1 内脑编排；本单局部阶段 T0—T6）
- original_work_order_id: wo-ultimaagent-20261103-0022
- revision: 1
- authorization: 用户 2026-11-03 确认方向"边界内自主执行 + 边界外契约转派"并指示"把任务规划落盘，让 Codex 自己分析方案和执行"。
- 状态：frozen（2026-11-04 主脑收口：0025 修复全绿后完整工程门重跑 932/0/120/36w 通过，验收冻结；tag `ultimaagent-middleware-v1-20261103`；证据 `data/evidence/middleware-v1/T5/full-src-rerun-20261104-attempt2/`；收口说明见 `docs/reports/stage-middleware-v1-20261103.md`）
- 计划：docs/plans/middleware-v1-delivery-plan-20261103.md（本单随规划落盘）
- 契约：本工单卡即契约；规划文档 §2/§3/§4/§7 为权威口径
- 草案检查点：无（本单方案由执行端分析细化，规划已确认）

## goal

按规划文档 §4 实现中间层 v1（内脑编排）：Ticket 状态机 / Router 路径编排 / 工具注册表+白名单 / Worker 动作级裁决 / SessionStore / 超时重试 / Outbox 回执 / Watchdog；实现"边界内自主执行 + 边界外契约转派"执行原则（能力缺口四级路径），并落地任务窗人话提炼子需求（§6）。技术方案由执行端（Codex）自行分析细化后按 G-TASKFLOW-001 执行。

## acceptance[]

- ACCEPT: 中间层 v1 组件清单（规划 §4.1）实现，venv-openjarvis 专用解释器 pytest 全绿。
- ACCEPT: 边界内自主执行链路端到端跑通：意图 → 路由决策 → 工具执行 → 结果裁决，0016 三态语义（ALLOW/DENY/ABSTAIN）在动作级生效。
- ACCEPT: 边界外四级路径可触发（组合 / 通用兜底 / 沙箱脚本 / 转派登记与跟踪），转派路径落工单三段式 + G-TASKFLOW-001 骨架。
- ACCEPT: 任务窗人话提炼链路跑通（中间层结构化快照 → 本地主脑无状态翻译 → 任务窗"人话+展开原文"双入口 → 模板话术降级），工单契约不动。
- ACCEPT: 8B 无路由创建能力（白名单外被拦截、工具注册表只读）；路由/工具为冻结资产，构建走登记→方案→工单→验收冻结→注册白名单。
- ACCEPT: 独立审计、Owner 真实体验、冻结 tag、产出与回滚说明全部齐备后才关闭本单。

## dependsOn[]

- 0016 意图路由门（已冻结，三态出口稳定）
- 0017 约束栈（已冻结，白名单外拦截）
- 既有 tasks 队列与 queue_engine（复用，不重写）

## fileDomain[]

- `H:/UltimaAI/UltimaAgent/src/brain`
- `H:/UltimaAI/UltimaAgent/src/middleware`（v1 新组件落位）
- `H:/UltimaAI/UltimaAgent/docs`
- `H:/UltimaAI/UltimaAgent/tasks/queue/wo-ultimaagent-20261103-0022--middleware-v1.md`
- `H:/UltimaAI/UltimaAgent/tasks/queue/runs/wo-ultimaagent-20261103-0022`
- `H:/UltimaAI/UltimaAgent/data/evidence/middleware-v1`

## priority

- 85

## reasoningEffort

- high

## category + skill

- 架构 / 集成；executing-plans、test-driven-development、verification-before-completion；方案分析 + 分阶段执行。

## receipt

- data/evidence/middleware-v1/T0/input-baseline.json
- 各阶段记录原单/阶段/run_id、输入哈希、执行端、真实退出、证据、越界声明和开源选择。

## retryCount

- 0；审计 REVISE 最多两轮，继承本单失败历史和修订，不新建原单重置额度。

## 写什么与禁止

1. 先分析细化技术方案（读规划文档 §4/§5/§7 蓝本与验收口径），分 T 阶段执行；T0 只固定基线与环境盘点，不编写产品实现。
2. 骨架用确定性代码（Ticket 状态机/工具注册表/超时重试/Outbox），不依赖模型自觉；8B 只做路由决策，不得实现路由创建。
3. 复用既有 SDK 工具、ReAct、SessionStore、queue_engine 和 Ultima 通道；适配代码必须说明现成替代选择。
4. 测试使用隔离目录和会话库。禁止改生产记忆/真实用户文件；禁止改主脑模型与推理参数、KWS、唤醒词；禁止重启现有语音进程。
5. 禁止安装未列入计划的依赖、增加后台感知/主动提醒、跳过前序验收、伪造完成或冻结。外脑调配（DeepSeek/CodeX 执行链）不在本单范围，仅预留接线点。

## 开源替代排查

| 子功能 | 现成件 | 采用与理由 |
|---|---|---|
| 任务状态机 | 既有 queue_engine（StateMachine/Task/Dispatcher） | 采用；语义对齐，不另写状态机 |
| Agent 工具循环 | OpenJarvis native_react、ToolRegistry、ToolResult | 采用；不另写 Agent 循环 |
| 编排蓝本 | dsh-superagent（MIT，调研副本 research/dsh-superagent-prototype） | 借鉴重写 Ticket/效果队列/Outbox/授权 gate/派发报告恢复五概念；不整仓拼装 |
| 会话持久化 | OpenJarvis SessionStore、现有 Ultima memory gate | 采用；补实际调用路径接入 |
| 动作级裁决 | 0016 路由门三态 + 0017 约束栈 | 采用；贯彻到 Worker 动作级，不重复造轮子 |
| 最小产品接线 | 本计划 middleware 组件 | 属产品接线与交付体验适配；不重写上述开源能力 |

## 2026-11-03 派发前补记

- 规划已随工单落盘：docs/plans/middleware-v1-delivery-plan-20261103.md。
- 用户指示执行端（Codex）自行分析技术方案并执行；本卡 goal/acceptance/约束为不可变口径，技术细化由执行端在 T0 产出并随证据落盘。
- 18766 UltimaManager 服务当前离线（127.0.0.1 拒绝连接），本单派发按先例直接维护全局登记表（_shared/queue/global-queue-index.md），18766 登记接口待服务恢复后由主脑补登。
