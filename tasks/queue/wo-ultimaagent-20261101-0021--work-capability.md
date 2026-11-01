# UltimaAgent｜集成｜Jarvis 工作能力逐阶段交付

- **task_id**: wo-ultimaagent-20261101-0021
- **stage**: v0.4（复用既有 M1 底座；本单局部阶段 T0—T5）
- original_work_order_id: wo-ultimaagent-20261101-0021
- revision: 2
- authorization: 用户“那按顺序开始推进吧”；批准按已提交的工作能力契约与计划顺序执行，保留最终 Owner 验收和发布门。
- 状态：T0 r2 独立计划评审 PASS；T1 即将开始，原单未完成。
- 计划：docs/plans/jarvis-work-capability-delivery-plan-20261101.md
- 契约：docs/specs/jarvis-work-capability-contract-20261101.md
- 草案检查点：ultimaagent-jarvis-work-plan-draft-20261101 @ f6eb808348302cec55bddcf44ee03f5b5736c4d9

## goal

按 R01—R08/E01—E08 顺序实现统一工作任务链路。先完成 T0 基线、固定样本和独立计划评审，再执行 T1 文件交付；后续阶段保留各自出口门。T0 完成不能冒充原单完成。

## acceptance[]

- ACCEPT: T0 固定样本、必要输入哈希、实际源码/运行差异、开源替代排查和精确写域齐备；独立新会话评审绑定同一方案 SHA256。
- ACCEPT: T1 真实 Agent 调用受限文件工具，独立读回核验，E01 连续三轮；旧接口兼容；禁止只凭回复报告完成。
- ACCEPT: T2—T5 按关联契约逐项实现 E02—E08；前序用例持续回归，失败不跳级。
- ACCEPT: 最终独立审计、Owner 真实体验、冻结 tag、产出与回滚说明全部齐备后才关闭原单。

## dependsOn[]

- 无（复用已存在的 v0.3-frozen 门与 voice-next 已确认基线，保持旧 0018/0019/0020 状态）

## fileDomain[]

- `C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent/src/brain`
- `C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent/docs`
- `H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability`
- `H:/UltimaAI/UltimaAgent/tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md`
- `H:/UltimaAI/UltimaAgent/tasks/queue/runs/wo-ultimaagent-20261101-0021`

## priority

- 80

## reasoningEffort

- high

## category + skill

- 集成；executing-plans、test-driven-development、verification-before-completion；T0 规划和独立计划评审分会话。

## receipt

- data/evidence/jarvis-work-capability/T0/input-baseline.json
- 各阶段记录原单/阶段/run_id、输入哈希、执行端、真实退出、证据、越界声明和开源选择。

## retryCount

- 0；审计 REVISE 最多两轮，继承本单失败历史和修订，不新建原单重置额度。

## 写什么与禁止

1. T0 只固定当前材料与执行计划，不编写产品实现；T1 仅按评审通过的精确文件清单实现。
2. 复用现有 SDK 工具、ReAct、SessionStore 和 Ultima 通道；适配代码必须说明现成替代选择。
3. 测试使用隔离目录和会话库。禁止写生产记忆/真实用户文件；禁止改 KWS、换唤醒词、重启现有语音进程。
4. 禁止安装未列入计划的依赖、增加后台感知/主动提醒、跳过前序验收、伪造完成或冻结。

## 开源替代排查

| 子功能 | 现成件 | 采用与理由 |
|---|---|---|
| 任务推理与工具循环 | 已安装 OpenJarvis native_react、ToolRegistry、ToolResult | 采用；不另写 Agent 循环 |
| 文件读写与范围约束 | OpenJarvis FileReadTool/FileWriteTool | 采用；仅在产品接口补授权绑定与成果核验 |
| 会话持久化 | OpenJarvis SessionStore、现有 Ultima memory gate | 采用；补实际调用路径接入 |
| 工作上下文 | 现有 Environment/LocalExecChannel/BrowserChannel，Jarvis.ceo ContextDetector 设计 | 优先接通既有接口；Mac 原生 API 不复制到 Windows |
| 组织方式参考 | Jarvis.ceo bec50ef6 | 采用任务分流、提供商抽象和会话取消思路，逐路径验证实际能力 |
| 最小产品接线 | 本计划 work_service/work_tools/work_verifier | 属产品接线与交付体验适配；不重写上述开源能力。T0 独立评审需核实必要性 |
