# 任务卡：s4-brain-loop
- **task_id**：s4-brain-loop
- **标题**：主脑决策回路串接（M01）+ TD-05 执行参数契约落地
- **优先级**：90（P0）
- **reasoningEffort**：medium
- **category**：core　**skill**：engineering
- **依赖**：s3-bus-kernel、s3-guard-resident、s3-orchestrator、s3-audit-trail
- **登记核验**：已查注册表与产品对齐报告（docs/reports/product-alignment-20261027.md 缺口 N1）；执行参数契约 v0.1-draft 位于 docs/specs/execution-param-contract.md（TD-05）；主脑现状 = OpenJarvis Jarvis + qwen2.5:14b native_react（src/brain/agent_server.py），决策回路未串接。

## goal
把主脑决策回路串接为一条真实可跑的链路，并把执行参数契约（TD-05）落地：
1. 决策回路全链：受理→意图→领域→范式→规划→派发→闸门→执行→审计→编排→表达→呈现→记忆归档（新目录 src/brain/loop/，作为主脑回路入口）；
2. 执行参数契约：下发带参数（max_turns / temperature / max_tokens / output_protocol / tools_allowlist / permission_scope / acceptance_gate），返回带参数明细（execution_report 字段校验，缺即打回）；
3. 审计校正四查三态：方向查（偏离任务目标→打回重算）、权限查（越界→拒绝+降级）、一致性查（与记忆/档案/状态冲突→拒绝+征询）、结构查（输出合规 + 参数明细齐全，缺=打回）；
4. 本地/外部路由分工接口：本地 14B 为编排者、外部大模型为执行者；本批次外部执行以确定性桩实现（执行参数明细可断言），真实外部路由预留接线点；
5. 回路入口接 agent_server /ask 与总线事件流（语音/IM 入站复用），保持旧接口向后兼容；执行全过程走审计留痕。

**禁止**：
- 禁止改动冻结参数基线（docs/specs/parameter-baseline.md）；
- 禁止绕过闸门/审计直接放行；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：决策回路全链端到端通过（受理→记忆归档），每环有留痕
- [ ] ACCEPT-2：下发带完整执行参数（七参数齐全），缺参=拒绝
- [ ] ACCEPT-3：返回带 execution_report 明细；缺明细=结构查打回
- [ ] ACCEPT-4：审计校正四查生效（方向/权限/一致性/结构，各自可触发）
- [ ] ACCEPT-5：本地/外部路由分工接口存在（外部执行桩 + 真实路由预留）
- [ ] ACCEPT-6：agent_server /ask 与总线事件入口兼容不倒退
- [ ] ACCEPT-7：回执完整（receipt.json 四字段 + 证据路径）

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：主脑决策回路串接 + TD-05 参数契约落地（P0） |
