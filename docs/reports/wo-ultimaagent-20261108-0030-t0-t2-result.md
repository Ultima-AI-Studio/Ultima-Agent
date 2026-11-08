# wo-ultimaagent-20261108-0030 · T0–T2 阶段报告

日期：2026-11-08
状态：READY_FOR_REVIEW（仅 T0–T2；未自判整单 PASS）

## 结论

- T0：PASS。脚本读取 Manager `store.py` 的 13 张表并逐字段比较；全 13 表与核心 5 表均为 `0 differences`。
- T1：PASS。轻量 SQLite store 使用标准库实现 5 表、put、work order CAS、事务回滚、WAL、并发写与 run 生命周期；正式 Gate 为 `10 passed`。
- T2：PASS。md 主表成功写入后才尝试 ledger；正常双写、缺表、只读库、缺目录、意外异常和 `ULTIMA_LEDGER_DISABLED=1` 均有自动测试；相关回归合计 `31 passed`。
- 按本次阶段范围冻结，在 T2 全绿后停止；未进入 T3–T7。

## 裁定与取舍

1. 本次提示给出的写域比冻结方案更窄，且是当前直接指令。因此 ledger 落在 `src/brain/orchestration/ledger/`，契约结果落在 `docs/reports/`；未写 `src/brain/ledger/` 或 `docs/specs/`。若该裁定错误，代价是后续需要一次路径迁移，但没有越过本次写域。
2. Manager 当前源码中 `work_orders` 实际有 15 列、`runs` 实际有 25 列；冻结方案中的 14/26 计数与源码不符。T0 以逐字段源码事实为准，没有伪造 14/26 的通过结果。
3. 本次提示明确把核心 5 表定义为 `projects/goals/work_orders/stages/runs`，因此 T1 没有创建 `approvals/events`。T2 的降级审计使用 Python logging，并通过 `last_ledger_result` 暴露原因；`approvals/events` 留在明确未授权的 T5 范围。若复审要求按工单旧文本把 `events` 纳入 T1，则需 Owner 先调整当前写域/核心表口径后另行处理。
4. `GlobalQueueRegistrar.record()` 保留原布尔返回值（代表 md 主表是否写成功），ledger 结果单独放在 `last_ledger_result`；这样 ledger 的 `degraded` 不会被既有派发方误判为主登记失败。

## Gate 命令与结果

### T0

```text
H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -B -m pytest tests\test_ledger_schema_check.py -o addopts=
1 passed

H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -B scripts\ledger_schema_check.py
13 tables; 0 differences (core 0); PASS
```

T0 结果：`docs/reports/wo-ultimaagent-20261108-0030-t0-schema-result.json`

### T1

```text
H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -B -m pytest tests\test_ledger_store.py -o addopts=
10 passed

from src.brain.orchestration.ledger import LedgerStore, VersionConflict
ledger import ok

本地 schema.sql 与冻结核心契约：5 tables, 0 differences
```

T1 JUnit：`docs/reports/wo-ultimaagent-20261108-0030-t1-pytest.xml`

### T2

```text
H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -B -m pytest \
  tests\test_ledger_schema_check.py tests\test_ledger_store.py \
  tests\test_ledger_registrar.py \
  src\brain\orchestration\tests\test_register_control_m29.py \
  -o addopts=
31 passed
```

T2 JUnit：`docs/reports/wo-ultimaagent-20261108-0030-t2-pytest.xml`

## 已知基线问题

首次基线运行 `src/brain/orchestration/tests` 时，提交态工作树已有两个收集错误：缺少 `src/brain/orchestration/__init__.py` / `registry.py` 导出，以及缺少 `src/brain/guardrails/paradigm.py`。只读核对发现这些文件存在于 `H:\UltimaAI\UltimaAgent` 主仓工作区，但均为未提交文件。本工单没有复制或修改这些主仓未提交工作。

为使 T2 的 queue 登记能力可独立导入，`queue.py` 仅把 `ParadigmGate/FLOW_RINGS` 改成 `SevenRingCheck` 使用时延迟导入；原有 `test_register_control_m29.py` 12 项全部通过。完成后的全目录复跑仍有 1 个提交基线收集错误：`test_orchestration_m4.py` 无法从缺少 `__init__.py` 的 namespace package 导入 `LangGraphStateMachine`；未把它伪报为通过。

## 越界声明与未做项

- 未修改 `H:\UltimaAI\UltimaManager\**`；只读提取 `store.py` 契约。
- 未修改 `docs/tracker/北极星上线任务清单.html`、`scripts/tracker-live.py`、`ultima_bus/**`。
- 未进入或实现 T3、T4、T5、T6、T7。
- 未引入第三方依赖；实现仅使用 Python 标准库。
- 未创建冻结 tag、未改主仓工作区、未推送远端。

## 复审关注点

- 复核 Manager 后续 schema 漂移时，重跑 `scripts/ledger_schema_check.py`；脚本不会用当前源码自动重写冻结核心基线。
- `LedgerRegistrar` 只有在显式注入 `GlobalQueueRegistrar` 时启用，保持既有调用无额外数据库副作用；`ULTIMA_LEDGER_DISABLED=1` 会在已注入场景完全跳过写入。
- SQLite 并发通过 WAL、10 秒 busy timeout 和事务边界验证；单次登记把 project/goal/work order 放在同一事务内，失败不会留下半套父记录。
