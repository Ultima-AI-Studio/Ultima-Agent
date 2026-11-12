# 任务卡：s2-tool-extend

- **task_id**：s2-tool-extend
- **标题**：底座能力接入工具集（子智能体派发 / 技能管理 / 记忆检索 / 网络检索）
- **优先级**：90（P0）
- **reasoningEffort**：medium
- **category**：core　**skill**：code
- **依赖**：无
- **登记核验**：已查注册表（docs/shared/registry.md 三·已登记能力），无重复组件；能力清单 L2/L3/L9 缺口

## goal（做什么 / 禁止做什么）

**做什么**：把底座 OpenJarvis 自带能力接入 `src/brain/agent_server.py` 的 TOOLS 白名单并真机验证，让本地 14B 主脑可自主调用以下四类能力（对齐用户诉求：子智能体派发真正执行、Agent 自主决策应答方式）：

1. 子智能体派发执行：底座 `agent_spawn` 类工具接入，14B 说"派个子任务/让子智能体去查X"能真实派发并回传结果；
2. 技能管理：底座 `skill_manage` 类工具接入，14B 能列出/创建技能（对应 L2 技能注册）；
3. 记忆检索：底座 `memory_*` 工具接入，14B 能存/查记忆（对应 L9）；
4. 网络检索：底座 `web_search` 接入，14B 说"上网查X"能返回真实来源（对应 L3 外部接入）。

实现路径：先读底座真实工具名与签名（`libs/base/openjarvis/src/openjarvis/tools/` 下 agent 类工具 + `tools/__init__.py` 注册模式），确认真实可用后加入 `agent_server.py` 的 `TOOLS` 白名单并重启验证；工具描述（spec.description）按 Ultima 语境改写，保证 14B 能正确触发。注册新 Ultima 域工具（如 `ultima_subagent` 包装）时遵循 `agent_tools_ultima.py` 现有模式。

**禁止**：
- 禁止改动队列引擎（tasks/queue_engine）任何逻辑；
- 禁止绕过冻结写通道（QueuePlanner 官方入口）改任务；
- 禁止改动语音 daemon 唤醒词 / ASR / TTS 链路；
- 禁止把非白名单工具暴露给 14B（保持最少权限）；
- 禁止向 fileDomain 之外写文件。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT-1：`agent_server.py` TOOLS 白名单包含四类新工具（子智能体/技能管理/记忆/网络检索），health 接口返回白名单含新增项
- [ ] ACCEPT-2：子智能体派发真机验证——问"派个子智能体去查一下当前任务状态"，14B 自主调用子智能体工具，返回结果与任务队列真实一致
- [ ] ACCEPT-3：技能管理真机验证——问"列出你能用的技能"，14B 自主调用技能工具返回真实技能清单；创建技能动作真机执行一次并回读确认
- [ ] ACCEPT-4：记忆真机验证——问"记住我喜欢简洁回答"后，再问"我的偏好是什么"能回读记忆（存/查闭环）
- [ ] ACCEPT-5：网络检索真机验证——问"上网搜一下今天天气"（或等价真实问题），返回含真实来源 URL 的结果
- [ ] ACCEPT-6：工具失败不编造——断网场景下网络检索失败时 14B 如实告知，不虚构结果
- [ ] ACCEPT-7：回归不破坏——原有 3 个 Ultima 域工具（查任务/调队列/环境快照）仍正常
- [ ] ACCEPT-8：回执完整——receipt 含 reviewReason / stdoutText / evidence / acceptance 逐项核对

## fileDomain[]

- `H:/UltimaAI/UltimaAgent`（允许写项目内；底座 libs 只读）

## receipt（完成时回执）

- reviewReason：本次交付判断依据
- stdoutText：真机验证输出摘录
- evidence：验证时间/输入/输出证据
- acceptance：ACCEPT-1~8 逐项结果

## 变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-24 | 初版：缺口工单（#87 遗留② + 能力清单 L2/L3/L9 对齐） |
