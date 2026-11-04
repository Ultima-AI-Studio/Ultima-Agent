# UltimaAgent｜T0 基线修复｜0022 收口前置（4 项红灯专治）

- **task_id**: wo-ultimaagent-20261103-0025
- **stage**: T0 基线修复（0022 收口前置单；审计最优裁定=独立修复、不挂账）
- original_work_order_id: wo-ultimaagent-20261103-0025
- revision: 1
- authorization: 用户 2026-11-04 拍板"按照审计最优方案执行"→ 0022 收口走独立修复路径（不挂账），本单修绿 4 项 T0 基线红灯后 0022 过完整工程门并验收冻结。
- 状态：ready_for_review（T0/T1/T2 已 PASS，执行收口已提交；待独立审计、Owner 真实体验与冻结 tag）
- 计划：docs/plans/t0-baseline-fix-plan-20261103.md（本单随方案落盘，G-PLAN-0025）
- 契约：本工单卡即契约；修复方案 G-PLAN-0025 为权威口径
- 草案检查点：无（修复方向已由主脑盘点，执行端核实后落地）

## goal

把完整工程门从 `921 passed / 4 failed / 120 subtests`（venv-openjarvis 3.13.16 口径）修复为全绿，专治下列 4 项 T0 基线既有红灯（gate.json 证实均非 0022 中间层引入的回归）：

1. `src/brain/routing/tests/test_mainbrain_rules_prompt.py::test_agent_server_keeps_user_question_separate`
2. `src/brain/routing/tests/test_routing_integration.py::test_time_intent_is_allowed_to_agent`
3. `src/brain/tests/test_queue_source.py::QueueSourceTests::test_production_library_readable_without_mutation`
4. `src/voice-next/test_live.py::test_discontinuity_reset_clears_framers_and_model_cache`

修复以"行为确认优先、断言随之对齐、环境依赖补齐"为原则，禁止为绿而绿。技术方案由执行端（Codex）核实根因后按 G-TASKFLOW-001 分阶段执行。

## acceptance[]

- ACCEPT: 完整工程门全绿——venv-openjarvis 专用解释器（3.13.16）运行 `921 passed, 0 failed`（按修复后实际计数），4 项点名测试各自转绿。
- ACCEPT: 修复说明逐项留档（data/evidence/t0-baseline-fix/）：每项写清归因（行为确认 / 断言更新 / 环境修复），禁止删除测试或弱化断言掩盖真实回归。
- ACCEPT: 时间意图能力不倒退——test_time_intent_is_allowed_to_agent 修复后，确定性时间直答语义（0020 已确认基线）仍可用；agent_server 时间前缀与用户问题分离语义保持。
- ACCEPT: 生产库只读语义保持——tasks/tasks.json 修复为可读且不可变异（test_production_library_readable_without_mutation 的"不可变异"断言语义保留）。
- ACCEPT: voice-next 断开重置语义可验证——soxr 补齐或测试隔离修正后，discontinuity reset 清理 framers/model cache 行为可被真实断言验证。
- ACCEPT: 不改变生产默认行为；不重启现有语音/daemon 进程；不改主脑模型与推理参数；不改 KWS/唤醒词参数基线（kws-wakeup-params-baseline.md）。
- ACCEPT: 独立审计 + Owner 真实体验 + 冻结 tag + 产出与回滚说明齐备后关闭本单；0022 同步完成验收冻结。

## dependsOn[]

- 0022 中间层 v1（本单修复其完整工程门红灯；0022 验收依赖本单全绿）
- 既有 voice-next 环境（仅补依赖/隔离，不改参数基线）
- G-TASKFLOW-001 工作流（登记→计划→执行→审计→验收→冻结）

## fileDomain[]

- `H:/UltimaAI/UltimaAgent/src/brain/routing/tests`（#1/#2 断言或路由分支）
- `H:/UltimaAI/UltimaAgent/src/brain/tests` + `src/brain/queue`（#3 生产库可读性）
- `H:/UltimaAI/UltimaAgent/src/voice-next`（#4 环境/隔离）
- `H:/UltimaAI/UltimaAgent/docs`（阶段报告）
- `H:/UltimaAI/UltimaAgent/tasks/queue/wo-ultimaagent-20261103-0025--t0-baseline-fix.md`
- `H:/UltimaAI/UltimaAgent/tasks/queue/runs/wo-ultimaagent-20261103-0025`
- `H:/UltimaAI/UltimaAgent/data/evidence/t0-baseline-fix`

## priority

- 90（0022 收口前置，卡 WIP）

## reasoningEffort

- high

## category + skill

- 工程治理 / T0 基线修复；test-driven-development、verification-before-completion；根因核实 + 分阶段执行。

## receipt

- data/evidence/t0-baseline-fix/ 各阶段记录原单/阶段/run_id、输入哈希、执行端、真实退出、证据、越界声明和开源选择。

## retryCount

- 0；审计 REVISE 最多两轮，继承本单失败历史和修订，不新建原单重置额度。

## 写什么与禁止

1. 先核实根因（复现 4 项失败现场，落盘 T0），再逐项 RED→GREEN 修复；禁止在未复现前直接改断言。
2. 修复归因三选一（行为确认/断言更新/环境依赖）并在 evidence 中留档；行为确认为主，断言随之对齐；环境问题（soxr）以补依赖/隔离为主。
3. 全部只读收口：不改生产默认行为；禁止重启现有语音/daemon 进程；禁止改主脑模型与推理参数、KWS、唤醒词；禁止改 0016/0017 已冻结语义。
4. 禁止删除测试、弱化断言、伪造完成或冻结；禁止跳过前序验收。
5. 开源优先（G-OPEN-001）：soxr 等依赖补齐走现有依赖管理，新增依赖先出开源替代排查表。
6. git add 仅本单写域；commit 标注工单 0025；**不代 0022 commit/tag/push**（0022 由其验收动作收口，防串单）。

## 2026-11-04 建卡补记

- 用户 2026-11-04 拍板"按照审计最优方案执行"：0022 收口走独立修复（不挂账），0025 为前置修复单；修绿后 0022 完整工程门重跑通过 → 验收冻结（tag `ultimaagent-middleware-v1-20261103`）→ 按 WIP 派 0023 → 重派 0024。
- 18766 UltimaManager 服务离线，登记走全局主表，待服务恢复后由主脑补登接口。
