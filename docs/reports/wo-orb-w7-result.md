# WO-ORB-W7 · G-ORCH 编排层接线结果报告

> 日期：2026-11-08
> 执行端：Codex
> 状态：**BLOCKED**（T4 独立 staged 审阅发现 2 项 Important；Tn 根目录全量门另有 28 failed）
> 性质：repair 续行；不打 tag，等待 ⑦ 独立审计

## 1. 改动清单

1. T1/T4（沿用上轮实现与绿灯证据）
   - 新增 `scripts/orchestrate-order.py`：按 `decompose -> work_order -> schedule` 顺序执行，支持无副作用 `--dry-run`，失败短路。
   - 新增 `tasks/queue_engine/receipt_contract.py` 并接入 `scripts/dispatch-work-order.py`：待审计、BLOCKED、未知/空回执按 fail-closed 契约分类。
   - 新增 `tests/test_orchestrate_order.py`、`tests/test_receipt_contract.py`。
2. T2（沿用上轮实现与绿灯证据）
   - `src/brain/sentinel.py` 同时识别 `final.json` 与 `final-message.json`，终态/连续异常后自行退出。
   - `scripts/dispatch-work-order.py` 在 worker 启动后无窗拉起 sentinel，并在收尾等待 sentinel 退出。
   - 扩展 `tests/test_sentinel.py`，覆盖终态、3 tick 异常、单例锁、派发挂载与 dry-run 契约。
3. T3（本轮 repair）
   - 重写 `pytest.ini`：`testpaths = tests src scripts tasks execution`。
   - `norecursedirs` 排除 `"Topo Backup" .git node_modules venv-* tools/venv-* libs legacy-topo data docs artifacts research models dist logs reports`。
   - 未设置或修改 `addopts`。
4. 本报告：`docs/reports/wo-orb-w7-result.md`。

## 2. 四项 Gate 证据

### Gate T1 · orchestrator 接入派发链 — PASS（沿用上轮证据）

- `tests/test_orchestrate_order.py` 上轮专项全绿：三 stage 顺序、落盘位置、失败即停、缺 key 报错、dry-run 零 stage 写入均已覆盖。
- 所有 API 测试均为 mock；未真实调用 DeepSeek API。
- 本轮根目录全量门未将 `tests/test_orchestrate_order.py` 列入失败清单。

### Gate T2 · sentinel 挂 run 目录 — PASS（沿用上轮证据）

- `tests/test_sentinel.py` 上轮专项全绿：`final.json`/`final-message.json`、3 tick 心跳与异常、恢复、单例锁、无窗拉起与收尾均已覆盖。
- 上轮派发器 dry-run 保持 `{"ready": true, ...}`，`--order/--prompt/--execute/--repair` 参数未改变。
- sentinel 仍是只读观察者：未写主表、未改 `done.json`、未杀真实业务进程。
- 本轮根目录全量门未将 `tests/test_sentinel.py` 列入失败清单。

### Gate T3 · pytest 作用域固定 — PASS（集合与数字），Tn 仍红

- 配置：`pytest.ini` 已含五个项目自有 `testpaths` 和完整 `norecursedirs`；无 `addopts`。
- 仓库根执行（无位置参数）：

  ```text
  H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest -o addopts= -q
  ```

- 真实结果：**1115 passed / 28 failed / 0 skipped**，另有 36 warnings、125 subtests passed，耗时 581.17s。
- 收集总量：**1143 tests**（1115 + 28），collection errors=0；未再收进 `Topo Backup`。
- 判定：T3 的测试集合修复达到核准口径；Tn 要求 `0 failed`，因此总验收不通过。

### Gate T4 · 回执契约对齐 — BLOCKED（上轮绿灯证据被独立反例推翻）

- `tests/test_receipt_contract.py` 上轮专项曾全绿：
  - `wo-orb-w6-20261108T125637445858Z/final.json` -> `blocked`；
  - `wo-orb-w6-20261108T133604629405Z/final.json` -> `audit`；
  - 未知/空回执 -> `blocked`；
  - 无显式“自检 PASS”的待审计文本仍 -> `blocked`。
- 未修改 `state_machine.py` 的 8 态枚举，未知格式继续 fail-closed。
- 本轮根目录全量门未将 `tests/test_receipt_contract.py` 列入失败清单。
- 提交前独立 staged 审阅用纯内存反例证实两项未覆盖缺陷：
  1. 文本回执使用工单号子串匹配，且只识别“当前状态/完成状态”前缀的 BLOCKED；`状态：BLOCKED` 与历史 `自检 PASS`/`READY_FOR_REVIEW` 同时出现时会误判 `audit`，相似工单号 `wo-orb-w70` 也可能被当作 `wo-orb-w7`。
  2. 合法 JSON 若 `status=[]` 或 `status={}`，集合成员判断会抛 `TypeError`，而不是返回 fail-closed 的 `blocked`。
- 因此上轮样例通过只能证明已覆盖样例，不能证明 T4 契约全绿；本轮 repair 授权只含 T3 与报告，不擅自扩大到 T4 代码修复。

## 3. 根目录全量门失败清单

| 文件 | 失败数 | 失败项 |
|---|---:|---|
| `src/brain/tests/test_connectivity_m6.py` | 1 | `TestC2Entry::test_jarvis_ask_real_inference` |
| `scripts/test_kws_reconfig.py` | 3 | `test_tts_new_wakeword_hits_offline_kws`; `test_tts_retained_jarvis_hits_offline_kws`; `test_tts_replaced_word_does_not_hit_offline_kws` |
| `scripts/tests/test_engineering_dispatch.py` | 1 | `DispatchContracts::test_owned_job_close_stops_worker_and_child_without_touching_other_process` |
| `tasks/tests/test_audit_e2e.py` | 3 | `test_empty_library_real_end_to_end_completes_with_zero_windows`; `test_real_exit_zero_with_business_failure_fails_self_check`; `test_recovery_after_completed_process_does_not_execute_again` |
| `tasks/tests/test_cli_execution.py` | 3 | `test_chinese_business_receipt_is_utf8`; `test_exit_zero_without_business_proof_is_blocked`; `test_real_command_reaches_audit_without_self_approval` |
| `tasks/tests/test_dispatcher.py` | 3 | `test_actual_dispatched_child_has_zero_visible_windows`; `test_parallel_group_allows_second_but_never_third_execution`; `test_real_duplicate_dispatch_creates_only_one_run` |
| `tasks/tests/test_priority_deps.py` | 1 | `test_completed_dependency_allows_real_dispatch` |
| `tasks/tests/test_review_regressions.py` | 2 | `test_old_audit_pass_cannot_close_a_changed_task_revision`; `test_real_parent_death_leaves_durable_child_completion` |
| `tasks/tests/test_w2_acceptance_regressions.py` | 3 | `test_same_principal_cannot_self_audit`; `test_tree_evidence_covers_worker_and_grandchild`; `test_wrong_order_cannot_pass` |
| `execution/server/tests/test_ultima_bus.py` | 8 | `test_accept_2_lifecycle_is_sequential_and_emitted`; `test_accept_3_sync_async_dedupe_timeout_and_events`; `test_accept_4_direct_connection_and_undeclared_scope_are_audited`; `test_accept_5_blue_green_failure_rolls_back_and_retains_three`; `test_dependency_cycle_and_missing_dependency_are_rejected_on_load`; `test_accept_6_cli_six_commands_parse`; `test_accept_7_three_pilots_end_to_end`; `test_intent_adapter_preserves_49_independent_cases` |

观测到的失败簇：

- KWS 3 项直接报 `ModuleNotFoundError: No module named 'sherpa_onnx'`。
- 真实推理入口 `jarvis ask` 返回码为 1；本单未扩大范围诊断其内部错误。
- 派发/队列用例出现子进程未退出、子进程返回 1、任务落 `FAILED` 而非预期状态等现象。
- Ultima Bus 用例被驻留插件注册/路由 fail-closed 拒绝，另有 discover 数量期望 3、实际 6。

以上失败均如实保留；本 repair 不修改这些既有测试，也不把它们加入 skip/ignore。当前脏工作区含其他工单改动，未做无基线依据的归因，需另单逐簇诊断。

## 4. 越界声明

- 未改 `state_machine.py` 的 8 态枚举。
- 未改 `H:\UltimaAI\_shared\queue\global-queue-index.md`。
- 未改派发器 CLI 参数或 WIP 闸门规则。
- 未真实调用 DeepSeek API；未把真实 `DEEPSEEK_API_KEY` 写入落盘文件。
- 本轮 repair 未修改任何既有测试文件；只改 `pytest.ini` 与本报告。T1/T2/T4 文件为上轮已获绿灯的待提交实现。
- 未隐藏失败、未新增 skip、未打 tag。
- 精确提交只包含本工单实现、测试、`pytest.ini` 与本报告；不包含工作区其他工单的脏改动。

## 5. 遗留项

1. T4 需精确解析工单 ID 与当前终态，令显式/矛盾 BLOCKED 优先 fail-closed；并在集合成员判断前验证 `status` 为字符串。应补“历史 PASS + 当前 BLOCKED”“相似工单号”“`status` 非字符串”回归。
2. `tests/test_receipt_contract.py` 当前依赖未跟踪的现场 run 回执；后续修复应加入脱敏、可跟踪 fixture，避免干净 checkout 不可复现。
3. Tn 根目录全量门仍有 28 failed，WO-ORB-W7 当前只能回执 `BLOCKED`，不得写“完成”。
4. 28 项失败应按上述四个失败簇另行建立诊断/修复工单；本单不越界修复。
5. ⑦ DeepSeek 独立审计尚未执行，因此不打 tag。

## 6. T0 必读出处

1. `H:\UltimaAI\INDEX.md`：G-ORCH-001 整段与阅读顺序。
2. `H:\UltimaAI\_shared\paradigms\Ultima-工程铁律清单.md` §9。
3. `H:\UltimaAI\_shared\paradigms\UltimaAI-任务工作流范式.md` §12。
4. `docs/plans/dispatch-rules-v0.2-20261108.md`：八环节判据、打回四级、§13 试跑结论。
5. `docs/reports/wo-orb-w6-oversight-20261108.md` 第七节。
6. `tasks/queue/wo-orb-w7.md` 与三张 W7 任务卡磁盘最新版。
