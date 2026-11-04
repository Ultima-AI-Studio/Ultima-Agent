# UltimaAgent 中间层 v1（内脑编排）阶段报告

- 工单：`wo-ultimaagent-20261103-0022`
- 执行端：Codex CLI / `gpt-5.6-sol`
- run：`20261103T082344721762Z`
- 基线提交：`df0bd96768bf2e8889a5755c3d3dbda4f9d8d912`
- 专用解释器：`tools/venv-openjarvis/Scripts/python.exe`（Python 3.13.16）

## T0 基线与环境盘点

状态：**PASS（盘点 Gate）；工程测试基线为 KNOWN_RED，不等于工程验收通过。**

- 已读项目 INDEX、G-TASKFLOW-001、Codex 执行范式、根目录/工单命名/接入范式、Console 标准中枢、工单、交付计划和开源替代结论。
- 已核对 `_normalize_utterance`、0016 `IntentGate` 三态、L8 `CapabilityPolicy` 白名单、OpenJarvis `ToolRegistry`/`SessionStore`、`queue_engine.StateMachine` 和任务窗队列投影接入点。
- T0 技术方案：`data/evidence/middleware-v1/T0/technical-design.md`。
- 输入/环境/哈希：`data/evidence/middleware-v1/T0/input-baseline.json`。
- 基线 JUnit：`data/evidence/middleware-v1/T0/baseline-default-temp-junit.xml`。
- 基线命令结果：`886 passed, 5 failed, 120 subtests passed, 36 warnings in 183.36s`。
- 已知失败：PreferenceStore 同毫秒时间戳；0017 测试与当前时间注入不一致；时间意图旧测试与确定性直答不一致；生产 `tasks.json` 当前不可读；冻结 `voice-next` 缺 `soxr`。
- 保护证明：未停止/重启现有语音进程，未删除共享锁，未改 KWS/模型/推理参数/W6 UI/0016/0017 冻结资产，未触碰 0021 写域。

Ruling：允许 T1-T4 在新 `src/middleware` 包内按 TDD 隔离推进；T5 保持完整 `pytest src` 全绿硬门。若既有失败仍在，则整单如实 BLOCKED，不 commit/tag/push。

## T1 骨架

状态：**PASS**

- RED：`src.middleware.outbox` 尚不存在，专项测试按预期在收集阶段失败。
- GREEN：`7 passed in 0.29s`；JUnit `data/evidence/middleware-v1/T1/green-junit.xml`。
- 实现：Ticket 迁移复用 `queue_engine.StateMachine`；`FrozenToolRegistry` 无注册入口；`BoundedRetry` 有总时限/单次时限/重试上限；`ReceiptOutbox` 同事务写回执与 reply；Session 适配真实 OpenJarvis `SessionStore`；Watchdog 按幂等回执跳过已完成效果。
- Gate 回执：`data/evidence/middleware-v1/T1/gate.json`。

## T2 Router 路径编排

状态：**PASS**

- RED：`src.middleware.delegation` 尚不存在，测试按预期失败。
- GREEN：`10 passed in 0.13s`；JUnit `data/evidence/middleware-v1/T2/green-junit.xml`。
- 六条冻结路径均可判定；短问答 `DIRECT_ANSWER` 直连旁路；“查新闻热点”固定走 `GENERIC_FALLBACK:web_search`，专用 `news_hotspot` 工具被拒。
- 复杂多跳 `ABSTAIN` 只生成 `DELEGATE_TICKET` 接线点；不实际启动 CodeX/DeepSeek。
- Router 无 `register_route`，未知路径和冻结注册表外工具 fail-closed。
- Gate 回执：`data/evidence/middleware-v1/T2/gate.json`。

## T3 Worker 动作级裁决

状态：**PASS**

- RED：`src.middleware.adjudication` 尚不存在，测试按预期失败。
- GREEN：本阶段 `7 passed in 1.00s`；T1-T3 累计 `24 passed in 1.10s`。
- `ALLOW` 通过真实 OpenJarvis `ToolExecutor` 执行并写 Outbox；同幂等键重放不重复工具副作用。
- `DENY/ABSTAIN` 在每个动作前由 0016 + `CapabilityPolicy` + 冻结注册表重判，工具不运行。
- 工具超时按确定性瞬态分类在上限内重试；非瞬态错误不盲试。
- 受控脚本：限制字节/AST/import/危险调用/运行目录/时限，隔离解释器运行，记录源码 SHA-256，结束后删除临时 `.py`。
- Gate 回执：`data/evidence/middleware-v1/T3/gate.json`；累计 JUnit `data/evidence/middleware-v1/T3/cumulative-junit.xml`。

## T4 任务窗人话提炼

状态：**PASS**

- RED：`src.middleware.task_window` 尚不存在，测试按预期失败。
- GREEN：本阶段 `5 passed in 0.08s`；T1-T4 累计 `29 passed in 1.03s`。
- 固定快照字段：任务 id / 阶段 / 状态 / 阻塞类型 / 剩余动作 / 验收口径。
- 本地主脑每次仅接收当前快照 canonical JSON 和字符上限，不接收历史或工单正文；输出过长、为空或异常均走有界模板降级。
- 后端契约同时提供 `summary` 人话与 `expand.snapshot` 原文；触发仅 `STATE_CHANGE` / `ROUTINE_REPORT`；输入快照不变。
- 未修改 W6 UI；本单只提供任务窗可消费的数据契约。
- Gate 回执：`data/evidence/middleware-v1/T4/gate.json`。

## T5 回归与收口

状态：**BLOCKED（完整工程门未全绿；禁止提交/tag/push）**

- 中间层端到端专项：`2 passed in 0.90s`，覆盖边界内自主执行、Outbox/Session/任务窗闭环，以及复杂多跳 `ABSTAIN` 只预留外脑工单接线点。
- 自审修复：冻结必须由 `human` owner 批准；重试不吞 `KeyboardInterrupt`；失败回执进入 `RECONCILE_FAILED`；仅冻结注册表可声明工具可安全重试；沙箱拒绝反射/dunder 内省逃逸。复核专项 `17 passed in 1.00s`。
- 最终组合门：`85 passed, 10 warnings in 2.55s`；JUnit `data/evidence/middleware-v1/T5/focused-gate-junit.xml`。
- 最终完整工程门：`921 passed, 4 failed, 120 subtests passed, 36 warnings in 187.18s`；JUnit `data/evidence/middleware-v1/T5/full-src-final-junit.xml`。
- 四个失败均与本单 `src/middleware` 无关，且与 T0 基线的剩余失败一致：
  1. `test_agent_server_keeps_user_question_separate`：当前 agent_server 注入时间前缀，旧断言期待原始问题；
  2. `test_time_intent_is_allowed_to_agent`：当前确定性时间直答与旧测试期待 agent 返回冲突；
  3. `test_production_library_readable_without_mutation`：生产 `tasks/tasks.json` 当前队列快照不可读；
  4. `test_discontinuity_reset_clears_framers_and_model_cache`：冻结 voice-next 环境缺 `soxr`。
- T0 的 PreferenceStore 同毫秒时间戳失败本轮未复现，因此最终由 5 项降为 4 项；未为追求全绿修改冻结/越界资产。
- Gate 规则生效：未执行 `git add`、commit、tag 或 push；HEAD 保持 `df0bd96768bf2e8889a5755c3d3dbda4f9d8d912`，目标 tag 不存在，暂存区为空。
- Gate 回执：`data/evidence/middleware-v1/T5/gate.json`。

## T6 八字段回执

状态：**PASS（阻塞态如实回执）**

1. 链路号：`wo-ultimaagent-20261103-0022 / 20261103T082344721762Z`
2. 执行端：Codex CLI / `gpt-5.6-sol`
3. 完成状态：`BLOCKED`；T0-T4 PASS，T5 专项 PASS，但完整工程门 4 项失败，收口 Gate 未通过。
4. 根因结论：中间层 v1 的确定性骨架、六路径 Router、动作级裁决、Outbox/Session、受控脚本与任务窗契约已实现且专项全绿；整单仅被四个既有/冻结写域外的工程测试失败阻塞。
5. 产出路径：`src/middleware/`、`data/evidence/middleware-v1/`、`docs/reports/stage-middleware-v1-20261103.md`。
6. 验收证据：组合门 85/85；完整门 921 pass / 4 fail；JUnit 与各阶段 gate JSON 见证据目录。
7. 越界声明：未改模型/推理参数、KWS/唤醒词、voice 主链、jarvis.md、daemon、W6 UI、0016/0017 冻结资产；未真实派发 CodeX/DeepSeek；未停止或重启现有进程；未暂存无关改动。
8. 环境声明：Windows / PowerShell；唯一验收解释器 `tools/venv-openjarvis/Scripts/python.exe`，Python 3.13.16；未使用默认 Python312。

机器可读回执：`data/evidence/middleware-v1/T6/receipt.json`；独立读回：`data/evidence/middleware-v1/T6/independent-readback.json`。

## 2026-11-04 收口验证（0025 修复后完整工程门重跑）

状态：**PASS（完整工程门全绿；本单验收通过并冻结）**

- 依据：2026-11-04 用户拍板"按审计最优方案执行"=独立修复不挂账；0025 修复单（`wo-ultimaagent-20261103-0025`）已全绿收口，commit `38dd5a54`（932 passed / 0 failed / 120 subtests / 36 warnings），四项 T0 基线红灯修复闭环（agent_server 时间前缀断言 / 时间意图直答断言 / queue_source 库可读不变异 / voice-next soxr 在线补装）。
- 主脑触发本单完整工程门重跑：专用解释器 `tools/venv-openjarvis/Scripts/python.exe`（Python 3.13.16）全量 `pytest src -q --tb=short --junitxml=...`。
- attempt1（`T5/full-src-rerun-20261104/`）：`1 failed, 931 passed, 36 warnings, 120 subtests passed in 147.60s`；失败= `test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains`（`ollama` CLI 不在 PATH，FileNotFoundError WinError 2）——环境类非代码缺陷（与 0025 续跑 attempt1 同源），已定位 ollama.exe 并补 PATH。
- attempt2（`T5/full-src-rerun-20261104-attempt2/`，补 `C:\Users\Administrator\AppData\Local\Programs\Ollama` 入 PATH）：**`932 passed, 0 failed, 36 warnings, 120 subtests passed in 148.32s`，EXIT=0**；JUnit 与 exit-code 已落盘。
- 结论：T5 完整工程门由 BLOCKED（921/4）转绿（932/0）；本单验收通过，冻结 tag `ultimaagent-middleware-v1-20261103`（2026-11-04 主脑收口，与 0025 修复 commit 38dd5a54 衔接）。
