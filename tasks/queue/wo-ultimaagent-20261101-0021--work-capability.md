# UltimaAgent｜集成｜Jarvis 工作能力逐阶段交付

- **task_id**: wo-ultimaagent-20261101-0021
- **stage**: v0.4（复用既有 M1 底座；本单局部阶段 T0—T5）
- original_work_order_id: wo-ultimaagent-20261101-0021
- revision: 2
- authorization: 用户“那按顺序开始推进吧”；批准按已提交的工作能力契约与计划顺序执行，保留最终 Owner 验收和发布门。
- 状态：T0/T1技术门保持；源码4/195测试通过但独立代码复核3Important，现按用户续推后的既定累计上限进入源码修复5；当前8B/无14B，真实gate与T3—T5未放行，所有历史保留。
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
## 2026-11-02 当前停点补记（原目标与验收不变）

T0/T1技术门通过；T2最后候选10fec03在2/2有界修复后真实E02失败。E01PASS3，E03此候选未启动，T3—T5未进入。149项测试通过不代表实际工作验收。原单与T2阶段索引FAILED/不可派发，全局blocked；所有历史继承、不新增原单重置次数。证据与后续决策材料见docs/reports/jarvis-work-capability-t2-20261102.md。生产服务、已接受KWS和默认主脑未切换；模型对照提案尚未执行，等待Owner明确范围决定。


## 2026-11-02 单次兼容例外接续（不修改验收与历史）

上段为历史停点。SDK 实际首轮工具描述遗漏嵌套参数 schema 已由零推理诊断确认，控制器在原用户目标内作一次手动兼容例外裁定，并真实转移 T2 FAILED→QUEUED→EXECUTING，全局 executing/Manager 已读回。仅授权既有双文件补丁，累计修复3（默认2+例外1）；不声称 Owner 新批准，不换当前 8B，不开启 14B，不切生产。先 RED/GREEN 与全新独立复审，再单次 E02；失败即停本次例外。裁定与证据：data/evidence/jarvis-work-capability/T2/schema-prompt-diagnosis/compatibility-exception-authorization.json。

## 单次兼容例外结束

610005e：151回归及fresh代码复核通过，唯一E02实际机械/语义FAIL，needs_attention/CLI2。首错为非法JSON，原facts:string本次未复现；S2 OpenAI已实现断言仍错。此例外结束，无第二轮/新修复/换模型授权；T2索引FAILED/不可派发、全局blocked/Manager读回，T3—T5未放行。最新报告docs/reports/jarvis-work-schema-compatibility-result-20261102.md，原历史保留。

## 用户明确继续后的架构前置复核

用户现要求继续。原3次失败/blocked检查点和累计数保留，控制器仅恢复同一T2的架构诊断与方案预审，下一次源码修复累计第4，累计上限5由本轮控制器限定，不是重置额度或冒充Owner批准。当前8B、不切14B，不改验收；代码需精确方案与独立审查先通过。依据data/evidence/jarvis-work-capability/T2/architecture-resume-20261102/resume-disposition.json。T3—T5尚未放行。

## 第4次源码修复放行

r3方案7fe32a4b独立PASS，设计检查点c6bcc3c/ultimaagent-work-t2-r4-plan-pass-20261102远端已核验。源码仅按明确四文件/测试/哈希元数据/新内部证据协议范围RED/GREEN，当前8B不换。实现端/root/implement_work_capability_t2_r4，source-repair4-release.json为具体放行回执；不得自动启动真实模型、UI或后续阶段。

## 源码修复5（最后有界轮）

针对review-r4-30b6b14的I1—I3，按fix-round-5/controller-release.json和同一r3设计修正调用声明判别、引用坐标及同一响应快照。不是重置原单或增加模型/权限，不自动开启真实运行。旧源码30b6b14及code-revise tag已推送。fresh执行者/root/implement_work_capability_t2_r5，完成后仅fresh scoped复核。
