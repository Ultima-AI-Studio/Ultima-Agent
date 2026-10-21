# 能力 / 组件 / 技能注册表（Registry）

- **版本**：v1.4 · 2026-10-21
- **用途**：防重复开发（强制标准 M1：立项/开发前必查本表）；登记一切已有能力、组件与技能
- **登记规则**：新增能力/组件/技能必须先在此登记，未登记不得使用；删除/合并需审计确认并留痕
- **v1.1 变更（2026-10-16）**：登记「任务队列引擎」组件（codex-task-queue-spec v1.0）

## 一、技能注册（Skill Registry）

| 技能 ID | 角色 | 职责边界 | 适用任务类型 | 产出标准 | 验收口径 |
|---|---|---|---|---|---|
| `eng.code` | 智能工程师 | 写代码/修 bug/重构/单元自检 | code | 源码落 fileDomain | 编译通过+自检+回执 |
| `eng.ui` | UI 工程师 | 组件/界面/动效实现 | ui | 组件/页面按积木规格 | 视觉核对+交互可用 |
| `eng.audit` | 审计工程师 | 一致性/质量/回执核对/修正任务 | audit | 审计结论+修正任务 | 偏差全部闭环 |
| `eng.security` | 安全工程师 | 越界/权限/凭证/漏洞核查 | security | 安全报告+加固 | 高危项清零 |
| `eng.arch` | 架构工程师 | 分层/接口/选型/依赖 | arch | 架构方案+依赖图 | 评审通过+落规格 |
| `eng.database` | 数据库工程师 | 建模/存储/查询/迁移 | database | 模型+迁移脚本 | 数据校验通过 |
| `eng.test` | 测试工程师 | 验证/回归/验收证据 | test | 测试报告 | 验收项全过 |
| `eng.infra` | 运维工程师 | 部署/环境/守护/日志/设备集群 | infra | 部署/运行状态 | 服务可用 |
| `eng.voice` | 语音/多媒体 | 语音链路/音色/音频/CV3 接线 | voice | 链路验证+证据 | 真机验证报告 |
| `eng.docs` | 文档工程师 | 范式/规格/纪要/调研落盘 | docs | 文档落盘 | 回读一致+可追溯 |
| `eng.generic` | 通用执行器 | 兜底/无法判定任务 | generic | 按任务卡产出 | 按 acceptance |

## 二、能力注册（Capability Registry，L0–L10 骨架，逐步细化）

| 层 | 能力 | 状态 | 落点（预期） |
|---|---|---|---|
| L0 | 语音入口/出口 + 文字入口/出口（终端四 IO） | 待建 | execution/shells |
| L1 | 意图理解（含隐含补全） | 待建 | execution/server |
| L2 | 领域知识与技能注册 | 待建 | execution/server |
| L3 | 执行与外部接入（数据源/设备/多模型） | 待建 | execution/server |
| L4 | 编排与组合窗口（scene-orchestrator + 组件树 DSL） | 待建 | execution/server |
| L5 | 表达与总结（汇报范式三规则） | 待建 | execution/server |
| L6 | 输出呈现（渲染 + 语音汇报状态机） | 待建 | execution/shells + server |
| L7 | 交互循环（对话调整/征询/队列管理） | 待建 | execution/server |
| L8 | 行为约束与受控执行（安全/越界/凭证） | 待建 | execution/server |
| L9 | 记忆与自学习（工作/声明式/程序式 + 反思） | 待建 | execution/server |
| L10 | 范式引擎（7 环流程/范式检查） | 待建 | execution/server |

> 注：能力层迁移自 Top 阶段成果时，在此登记"来源 legacy-topo + 版本"，按 M7 显式引用。

## 三、组件注册（Component Registry，随 ui-kit 建立逐步登记）

| 组件 ID | 类型 | 规格依据 | 状态 | 落点 |
|---|---|---|---|---|
| `task-queue-engine` | 任务队列引擎 | specs/codex-task-queue-spec.md v1.3 | W2独立35项/62回归及U01已通过；Owner已批准v0.1-frozen，基线43ce130 | tasks/queue_engine/（存储/状态/派发/守护/进程树观测/审计/修正）；tasks/queue_engine/cli.py（操作入口）；execution/server 的 L7 接线尚未实现 |
| `task-status-text-loop` | 任务查询文字闭环（S1/v0.3） | wo-s1-task-text-loop；queue-spec v1.3 §4/10/11 | W4通过；16项文本测试、49项独立检查；Owner已批准v0.3-frozen固定731710a | src/brain/（窄规则意图、八态只读源、异常聚合、ID下钻、CLI）；完整L0-L10及execution/server接线仍待后续阶段 |
| （待 ui-kit 冻结后登记：窗口/按钮/开关/滑块/进度条/列表卡片/输入框/弹窗/悬浮球/播放器/传感器卡片…） | | | | |

## 四、登记与查询规则

- 开发前：读本表 → 确认无重复 → 任务卡写"已查注册表，无重复"（M1）。
- 开发后：新 package/组件/技能回填本表，版本号 + 落点路径必须填全。
- 审计轮：核对"新产物 vs 注册表"是否重复/漏登（M4）。

## 变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.3 | 2026-10-21 | 登记任务查询文本闭环组件与实际src/brain落点，仅覆盖工单④的窄文字场景，不把能力骨架全层标为完成。 |

| v1.4 | 2026-10-21 | Owner批准v0.3文本闭环冻结731710a，不扩大为完整语音或组合窗口通过。 |
