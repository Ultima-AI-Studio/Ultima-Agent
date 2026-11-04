# T0 基线四红灯修复方案（0022 收口前置单）

- 方案编号：G-PLAN-0025
- 日期：2026-11-04
- 关联工单：wo-ultimaagent-20261103-0025（修复单）；wo-ultimaagent-20261103-0022（被修复对象，收口前置）
- 裁定：0022 收口走**独立修复路径**（审计最优，不挂账冻结）。4 项红灯均为 T0 基线既有失败（gate.json 证实 `middleware_regression: no new middleware failures`），非 0022 中间层引入的回归，故拆独立修复单专治，修绿后 0022 完整工程门通过 → 验收 → 冻结 tag `ultimaagent-middleware-v1-20261103`。

## 1. 目标

把完整工程门从 `921 passed / 4 failed / 120 subtests` 修复为全绿（venv-openjarvis 专用解释器 3.13.16），为 0022 验收冻结开路，并消除 T0 基线长期悬挂的红灯。

## 2. 四项红灯与已知根因（执行端需核实后落地，禁止为绿而绿）

| # | 失败测试 | 已知根因（T0 基线既有） | 修复方向（需执行端核实） |
|---|---|---|---|
| 1 | `src/brain/routing/tests/test_mainbrain_rules_prompt.py::test_agent_server_keeps_user_question_separate` | agent_server 时间前缀与旧测试断言冲突 | 对齐断言到当前真实行为，或核对行为是否偏离 0020 已确认基线（用户已确认"唤醒与正确时间语音回答"），以行为确认为准，断言随之更新 |
| 2 | `src/brain/routing/tests/test_routing_integration.py::test_time_intent_is_allowed_to_agent` | 确定性时间直答与旧路由测试冲突 | 时间直答为既有确认行为；旧断言未预期，更新断言或补路由分支，不得删除/削弱时间意图能力 |
| 3 | `src/brain/tests/test_queue_source.py::QueueSourceTests::test_production_library_readable_without_mutation` | 生产 tasks/tasks.json 不可读 | 定位是权限还是路径问题；修复为只读可访问且不改动内容；测试断言保留"不可变异"语义 |
| 4 | `src/voice-next/test_live.py::test_discontinuity_reset_clears_framers_and_model_cache` | 冻结 voice-next 环境缺 soxr | 补 soxr 依赖或修正测试隔离，使断开重置语义可验证；不改语音参数基线（kws-wakeup-params-baseline.md） |

## 3. 验收口径

- ACCEPT-1：完整工程门全绿——venv-openjarvis 专用解释器运行 `921 passed, 0 failed`（或按修复后实际全绿计数），4 项点名测试各自转绿并有修复说明。
- ACCEPT-2：修复说明逐项留档（data/evidence/t0-baseline-fix/）：每项说明"行为确认 vs 断言更新 vs 环境修复"归因，禁止以删测试/弱化断言掩盖真实回归。
- ACCEPT-3：不改变生产默认行为；不重启现有语音进程；不改主脑模型与推理参数；不改 KWS/唤醒词参数基线。
- ACCEPT-4：独立审计 + Owner 真实体验 + 冻结 tag 齐备后关闭本单；0022 同步完成验收冻结。

## 4. 阶段门（执行端细化）

- T0：基线盘点 + 4 项失败现场复现与根因确认，落盘 data/evidence/t0-baseline-fix/T0/
- T1：修复实现（逐项），每项 RED→GREEN
- T2：全量回归 + 收口（完整工程门全绿；阶段报告 docs/reports/t0-baseline-fix-20261103.md）
- T3：八字段回执

## 5. 硬约束

- 禁止跳过前序验收、伪造完成或冻结；禁止重启现有语音/daemon 进程。
- 只修本单点名的 4 项红灯及其根因关联；不扩大范围到 0023/0024 写域。
- git add 仅本单写域；commit 标注工单 0025；不代 0022 commit（0022 由其验收动作收口）。
- 测试与证据用隔离目录/虚拟环境；禁止写生产记忆/真实用户文件。

## 6. 恢复链路（本单修绿后）

0025 全绿 → 0022 完整工程门重跑通过 → 0022 commit/tag/push 冻结（tag `ultimaagent-middleware-v1-20261103`，免代理 push）→ 0022 验收关闭 → 按 WIP 派 0023（Jarvis P0）→ 重派 0024（全盘理解 P0，本轮可真正开工 M1）。
