# 任务卡：s2-capability-overview

- **task_id**：s2-capability-overview
- **标题**：能力总览与技能学习入口（Agent 自述能力）
- **优先级**：60（P1）
- **reasoningEffort**：low
- **category**：skill　**skill**：voice
- **依赖**：s2-tool-extend（需工具集扩展完成后，能力总览才能真实盘点）
- **登记核验**：已查注册表，无重复组件；对齐用户诉求"我不知道 Agent 有什么能力"

## goal（做什么 / 禁止做什么）

**做什么**：让 14B 在用户问"你有什么能力 / 能做什么 / 有哪些技能 / 装了什么插件"时，自主汇总并回答真实能力清单（对齐用户："我感觉我们这个 Agent 什么功能也没有……我不知道都有哪些能力"）：

1. 新增 Ultima 域工具 `ultima_capability_overview`（注册进 `agent_tools_ultima.py`）：盘点三部分——① 工具集（agent_server 白名单 + Ultima 域工具）；② 技能（底座 skill 注册清单）；③ 插件/外部接入（已注册的外部能力）；输出结构化中文清单；
2. 系统提示（`C:\Users\Administrator\.openjarvis\agents\native_react\system_prompt.md`）补一条：用户问能力/技能/插件时必须调用该工具，禁止凭通用常识列举；
3. "学习新技能"引导：用户说"学个新技能/教你一个新技能"时，14B 引导进入技能注册流程（说明技能卡要素：名称/触发/步骤/边界），不编造已学技能；
4. 真机验证：问"你有什么能力"返回真实清单（含任务查询/队列调整/环境快照等已注册能力）；问"能学新技能吗"返回引导话术。

**禁止**：
- 禁止改动队列引擎；
- 禁止把未注册/未实现的能力写进清单（防夸大）；
- 禁止向 fileDomain 之外写文件。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT-1：`ultima_capability_overview` 工具已注册并返回真实能力清单（工具/技能/插件三部分）
- [ ] ACCEPT-2：真机问"你有什么能力"，14B 自主调用该工具，回答与注册表一致
- [ ] ACCEPT-3：真机问"你能查任务吗/你会查配置吗"，14B 正确回答有对应能力
- [ ] ACCEPT-4：真机问"学个新技能"，14B 返回引导话术（含技能卡要素），不编造已学技能
- [ ] ACCEPT-5：系统提示已补能力查询规则
- [ ] ACCEPT-6：回归不破坏——原有工具（查任务/调队列/环境快照）仍正常
- [ ] ACCEPT-7：回执完整——receipt 含 reviewReason / stdoutText / evidence / acceptance

## fileDomain[]

- `H:/UltimaAI/UltimaAgent`（src / docs）

## receipt（完成时回执）

- reviewReason / stdoutText / evidence / acceptance 逐项核对

## 变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-24 | 初版：能力总览与技能学习入口 |
