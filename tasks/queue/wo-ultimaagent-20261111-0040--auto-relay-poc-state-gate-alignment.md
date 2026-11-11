# Codex 工单 · 0040 自动接力 PoC 对齐正式状态门 / 依赖门并补齐 RelayPump

> 版本：v1.0 ｜ 状态：可开工 ｜ 适用工具：Codex
> 链路：`wo-ultimaagent-20261111-0040`
> 执行端：Codex（独立任务通道，主脑不参与判据定夺）
> 前置：无（0038 设计与 PoC、0039 审计均已提交推送）
> 方案依据：`docs/plans/plan-ultimaagent-auto-relay-poc-state-gate-alignment-20261111.md`
> 锁定 revision：`436e755383d4eb862713340b6ea9bb87f5a44d93`
> 工作目录锁定：`H:\UltimaAI\UltimaAgent`
> 用法：按 T0→T3 顺序执行，每 T 的 Gate 全绿再进下一条，禁止跳序。

---

## 0. 本单定位

本单只做一件事：修掉 0039 DeepSeek 独立审计点出的唯一真实缺陷 **ACC-6**。现状 PoC（`tasks/queue_engine/auto_relay_poc.py`）的 `_transition` 直接写 `task["state"]`、`_dependency_gate` 自实现，绕过正式 `StateMachine` 与 `QueuePlanner` 的 fail-closed 门禁，且未实现设计声明的 `RelayPump` 接口。

改造目标是让 PoC **委托**正式组件、补齐接口，满足 `component-facts.md` T1 第 1/5/6/8 项可证伪条件，再交 DeepSeek 只复审 ACC-6，通过后才允许正式落地。本单不推进任何业务任务，不接真实 Codex。

---

## 1. 范围冻结

**本阶段只做**

1. 把 PoC 全部状态变更改为委托 `StateMachine.transition()`，失败恢复改用 `retry_or_block()`，删除直接写 `task["state"]` 的路径。
2. 把依赖判定改为委托 `QueuePlanner.dependency_gate()`。
3. 新增 `RelayPump`，提供 `pump_once(max_actions)` 与 `run(stop_event, interval_s)`，复用同一套委托逻辑。
4. 更新 / 新增测试，覆盖门禁生效与接口有界可停，并做反向验证。

**本阶段不做（Non-goals）**

1. 不新建正式 `auto_relay.py` / `scheduler_tools.py`，不做 P0–P3 落地接线。
2. 不把 PoC 接入正式入口、CLI、自启、看门狗，不调真实 Codex / 付费接口。
3. 不改 `tasks/queue/queue-status.json` 业务数据（派发器对本单的状态登记除外）。
4. 不改 `state_machine.py`、`priority_deps.py`、`dispatch-work-order.py`、`validate_work_order.py` 等正式组件。
5. 不新增状态枚举，域内仍只有 `QueueState` 八态；不联网、不装依赖、不 `git add -A`。

---

## 2. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `tasks/queue_engine/auto_relay_poc.py` | 全部状态变更走 `transition()` / `retry_or_block()`，grep 无直接写 state，定向测试全绿 |
| T1 | `tasks/queue_engine/auto_relay_poc.py` | 依赖门委托 `QueuePlanner.dependency_gate()`，依赖阻断行为一致，测试全绿 |
| T2 | `tasks/queue_engine/auto_relay_poc.py` | 新增 `RelayPump.pump_once/run`，有界可停、不忙等，新测试全绿 |
| T3 | `scripts/tests/test_auto_relay_poc.py` + `tasks/queue_engine/auto_relay_poc.py` + 本卡回填位 | 全量回归只增不减、反向验证变红、隔离 grep 成立，回执填写完整 |

---

## 3. 任务明细

### T0 · 状态迁移委托 StateMachine

**文件**：`tasks/queue_engine/auto_relay_poc.py`

**写什么**：

1. 持有一个 `StateMachine(storage=None)` 实例；改造 `_transition` 为调用 `machine.transition(task, target, actor=..., reason=..., audit_passed=...)`，用返回的 updated 副本替换列表中的对应 task，事件记录以返回 event 为准。
2. 初始化给每个 task 设 `retryCount=0`；失败恢复路径改用 `machine.retry_or_block(task, actor=..., reason=...)`，重试上限（2 次）由状态机裁决，删除 PoC 自管的并行重试计数；`snapshot` 的重试视图从 task 的 `retryCount` 派生。
3. 回执接受触发的 `AUDIT → COMPLETED` 显式传 `audit_passed=True`；其余迁移的 actor 用固定非空身份（如 `queue-engine`），reason 非空。
4. 删除任何形如 `task["state"] = ...` 的直接赋值。

**验收（Gate T0）**：

- 命令 `& H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest scripts/tests/test_auto_relay_poc.py -o addopts= -p no:cacheprovider -q` 全绿，贴完整输出。
- grep `auto_relay_poc.py` 中 `task["state"] =` / `task['state'] =` 命中数为 0，贴 grep 输出；同时 grep 确认 `StateMachine` 与 `retry_or_block` 被实际调用。
- 失败重试用例仍得到 BLOCKED 且 `retryCount` 为 2，结果与改造前一致，贴断言输出。

**禁止**：不得在 PoC 内复制一份 `_ALLOWED` 或重试规则；不得给 storage 传入真实队列存储。

---

### T1 · 依赖门委托 QueuePlanner

**文件**：`tasks/queue_engine/auto_relay_poc.py`

**写什么**：

1. 把 `_dependency_gate` 改为 `return QueuePlanner.dependency_gate(task, self.tasks, self.machine)`，不再自实现缺失 / 未完成判定。
2. 保留其对 failed / blocked 依赖触发 `block_failed_dependents` 的阻断语义；确认 PoC 在依赖未满足时仍返回 `DEPENDENCY_BLOCKED`，不跳过低优先级任务。

**验收（Gate T1）**：

- 定向 pytest 全绿，贴输出；依赖未满足用例仍为 `DEPENDENCY_BLOCKED` 且 `dispatch_order` 为空。
- grep 确认 `_dependency_gate` 函数体仅委托 `QueuePlanner.dependency_gate`，贴源码与 grep 输出。
- 构造依赖为 BLOCKED 的夹具，断言依赖任务被正确阻断，贴输入→预期/实际输出，预期与实际一致。

**禁止**：不得保留 PoC 私有依赖判定分支；不得吞掉 `dependency_gate` 返回的 reason。

---

### T2 · 补齐 RelayPump 接口

**文件**：`tasks/queue_engine/auto_relay_poc.py`

**写什么**：

1. 新增 `RelayPump` 类，`pump_once(max_actions: int) -> dict`：单拍最多处理 `max_actions` 个持久动作，复用 T0/T1 的委托逻辑，空队列安全返回含 `stop_reason` / `dispatch_order` / 动作数的摘要。
2. `run(stop_event, interval_s)`：循环 `pump_once` 并用 `stop_event.wait(interval_s)` 等待，不做无 sleep 的忙等；sleep / 时钟可注入，确保可单测、可停止。
3. 该类与 `AutoRelayPoc` 共享同一套状态门 / 依赖门调用，不复制规则；仍不被正式入口 import。

**验收（Gate T2）**：

- 新增 RelayPump 测试全绿：`pump_once(max_actions=1)` 处理动作数不超过 1，贴断言；预置已 set 的 `stop_event` 调 `run` 时动作数为 0 且正常退出，贴输出。
- 空队列调用 `pump_once` 安全返回 `NO_ELIGIBLE_TASK`，不抛异常，贴输出。
- grep 确认 `run` 内使用 `stop_event.wait`、无裸 `while True` 忙等，贴 grep 输出。

**禁止**：不得在 RelayPump 里起进程、开网络或读真实队列；不得复制状态迁移规则。

---

### T3 · 测试回归、反向验证与回填

**文件**：`scripts/tests/test_auto_relay_poc.py` + `tasks/queue_engine/auto_relay_poc.py` + 本卡回填位

**写什么**：

1. 保留原 6 个用例；新增至少 4 条：① 未审计直接 COMPLETED 抛 `InvalidTransition`；② 非 human/brain 释放 BLOCKED 被拒；③ `pump_once` 动作数受 `max_actions` 约束；④ 预置 stop 的 `run` 不动作并退出。
2. 跑全量 `scripts/tests` 回归，确认只增不减。
3. 反向验证：把委托临时改回直接写 `task["state"]`，确认新增门禁用例变红，再恢复转绿。
4. 回填本卡「回执」段。

**验收（Gate T3）**：

- 全量命令 `& H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest scripts/tests -o addopts= -p no:cacheprovider -q` 全绿，基线 110 passed，只许增加，贴完整输出。
- 反向验证贴出变红（exit 非 0）与恢复后转绿两段输出。
- grep 全仓无正式入口 import `auto_relay_poc`，贴输出，证明隔离性保持。

**禁止**：不得删除或弱化原有用例断言；不得让测试只验证 helper 而不验证真实门禁。

---

## 4. 总验收

1. T0–T2 委托改造齐全，PoC 内无直接写 state、无私有依赖判定、无并行重试规则。
2. RelayPump 两接口有界可停，域内仍只有 `QueueState` 八态，无第三套枚举。
3. 全量回归只增不减，反向验证已做，正式入口仍不引用 PoC。
4. 数据未动：`git diff HEAD -- tasks/queue/queue-status.json` 为空（派发器自身状态登记除外）。
5. 提交显式列路径、中文信息，不 `git add -A`。

---

## 5. 禁止清单

1. 不得新建正式自动接力模块或做 P0–P3 接线。
2. 不得把 PoC 接入正式链路、自启、看门狗或调真实 Codex / 付费接口。
3. 不得改 `state_machine.py` / `priority_deps.py` / `dispatch-work-order.py` / `validate_work_order.py`。
4. 不得新增状态枚举或复制 `_ALLOWED` / 重试 / 依赖规则。
5. 不得联网装依赖；不得 `git add -A`，提交必须显式列路径。

---

## 回执（执行端填写）

- run 目录：`tasks/queue/runs/wo-ultimaagent-20261111-0040-20261111T052401598676Z`
- 改动文件：`tasks/queue_engine/auto_relay_poc.py`；`scripts/tests/test_auto_relay_poc.py`；`tasks/queue/wo-ultimaagent-20261111-0040--auto-relay-poc-state-gate-alignment.md`
- 委托证据：`tasks/queue_engine/auto_relay_poc.py:65` 持有 `StateMachine(storage=None)`；`:184` 调用 `retry_or_block()`；`:209` 唯一委托 `QueuePlanner.dependency_gate()`；`:220` 调用 `transition()`；字面 grep `task["state"] =` / `task['state'] =` 均为 0。
- RelayPump：`tasks/queue_engine/auto_relay_poc.py:270`；`pump_once` 在 `:286`，`run` 在 `:313`，`:324/:329/:333` 使用 `stop_event.wait`；测试 `scripts/tests/test_auto_relay_poc.py:188/:203/:215` 覆盖 `max_actions=1`、空队列与预置 stop。
- pytest 结果：定向 `12 passed in 0.13s`；最终全量 `116 passed in 6.82s`（基线 110，只增不减）；反向验证临时恢复直接写 state 后 2 个新增门禁用例 FAIL、exit=1，恢复委托后定向 12 passed、全量 116 passed。
- 已知限制 / unverifiable：仍是 fixture-only PoC；未接正式入口、真实队列、真实 Codex/付费接口、服务、自启或看门狗；ACC-6 的 DeepSeek 独立复审不在本执行单权限内，需后续独立复审单裁决。`tasks/queue/queue-status.json` 仅保留派发器对本单的状态登记，本单未编辑、未暂存。
