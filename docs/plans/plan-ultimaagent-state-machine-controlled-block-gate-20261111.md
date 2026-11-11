# 方案 · 0041 正式状态机受控冻结门（消除全链路直接写 state）

> 日期：2026-11-11 ｜ 依据：DeepSeek 单门 ACC-6 复审两轮 FAIL（run `wo-ultimaagent-20261111-0040-acc6-recheck-20261111T055223097Z`），豆包回源码逐行 + 实跑探针坐实为真实缺陷
> 对应工单：`wo-ultimaagent-20261111-0041`（独立修复单，独立于 0040）
> 推理强度：high（改造既有正式组件的门禁结构，非全新架构）
> 前置：0040 已提交 `a8821457`（PoC 自身已委托，干净）；本单改的是被委托链下游的正式组件

## 1. 根因（精确，已实跑坐实）

1. `tasks/queue_engine/state_machine.py` 有两处绕过 `transition()` 直接写状态：
   - `block_failed_dependents`（93–119）在 113–115 行原地写 `task["state"]/updated_at/terminal_reason`，仅 append 事件，未走任何迁移校验。
   - `block_for_unclear_audit`（121–137）在 132–134 行在副本上直接写 `state`，虽有独立守卫，但同样不经过 `transition()`。
2. `_ALLOWED[QUEUED]`（29 行）只有 `EXECUTING/CANCELLED`，**QUEUED→BLOCKED 在常规生命周期里本就非法**。探针实跑：同一迁移走 `transition()` 抛 `illegal transition: QUEUED -> BLOCKED`，而 `block_failed_dependents` 靠直接写才走通；这是活路径（`test_blocked_dependency_freezes_dependent_through_formal_gate` 经此产生 BLOCKED），非死代码。
3. 调用链：PoC `_dependency_gate` → `QueuePlanner.dependency_gate`（`priority_deps.py:136`）→ `block_failed_dependents`。0040 让 PoC 委托后首次接上该路径，缺陷因此暴露；缺陷本身在正式组件里早已存在。

## 2. 目标

让全链路（含 PoC 触达的正式组件路径）所有状态变更收敛到唯一入口 `transition()`，消除直接写 `task["state"]` 的旁路，同时保持 fail-closed、现有行为契约与八态模型不变。完成后交 DeepSeek 把「全链路无直接写 state」当硬门复审，过了才回头判 ACC-6 PASS，再谈落地。

本单不推进任何业务任务，不接真实 Codex，不做正式 auto_relay 接线。

## 3. 范围冻结

**只做**

1. 给 `StateMachine.transition()` 增加受控冻结门（keyword-only `freeze` 参数），在不污染常规 `_ALLOWED` 的前提下，让「依赖冻结」「审计冻结」两类到 BLOCKED 的迁移经统一守卫、统一写入段完成。
2. 把 `block_failed_dependents`、`block_for_unclear_audit` 改为委托 `transition()`，删除两处直接写 state 的代码。
3. 更新受契约升级影响的现有测试，并新增受控门禁用例与「全链路无直接写 state」可执行硬门检查。
4. 全量回归 + 反向验证。

**不做（Non-goals）**

1. 不新建正式 `auto_relay.py` / `scheduler_tools.py`，不做 P0–P3 落地接线，不把 PoC 接正式入口/自启/看门狗，不调真实 Codex/付费接口。
2. 不新增状态枚举，域内仍只有 `QueueState` 八态；不复制 `_ALLOWED` 到任何调用方。
3. 不改 `priority_deps.py` 的 `dependency_gate` 调用方式（它调 `block_failed_dependents` 的签名与返回语义保持），不改 `dispatch-work-order.py` / `validate_work_order.py` / `audit.py` / `dispatcher.py` / `middleware/ticket.py` 的调用代码。
4. 不改 `queue-status.json` 业务数据（派发器对本单的状态登记除外）；不联网、不装依赖、不 `git add -A`。

## 4. 写域（精确文件）

| 文件 | 动作 |
|---|---|
| `tasks/queue_engine/state_machine.py` | 修改：`transition()` 加 `freeze` 受控门；两个 block 方法改委托；新增受控 actor 集合常量 |
| `tasks/tests/test_state_machine.py` | 修改：升级 1 处依赖原对象引用的断言；新增受控门禁用例与全链路无直接写 state 硬门检查 |

> 若实现中发现硬门检查更适合落在 `scripts/tests/`，以 T0 实测为准，但写域不得超出 state_machine 与测试两类文件。

## 5. 核心设计：受控冻结门（不放开常规 `_ALLOWED`）

### 5.1 新增 keyword-only 参数

`transition(..., audit_passed=False, freeze=None)`；`freeze` 合法值仅 `None` / `"dependency"` / `"unclear_audit"`。

- `freeze is None`：完全走原 `_ALLOWED` 逻辑，常规迁移零影响。
- `freeze` 非空：进入专门冻结守卫，**跳过 `_ALLOWED[source]` 常规检查**，但必须通过下列专属门，守卫通过后复用 72–85 行的统一副本写入段（建副本→写 state→retryCount→updated_at→terminal_reason→事件→append→返回），不另写赋值。

### 5.2 冻结守卫（fail-closed，按序）

1. `freeze` 不在两个合法值内 → 拒绝（unknown freeze gate）。
2. 目标必须是 `BLOCKED`，否则拒绝（freeze gate only targets BLOCKED）。
3. 源为 `COMPLETED/CANCELLED` 终态 → 拒绝（terminal cannot be frozen）。
4. 类型专属门：
   - `freeze="dependency"`：源必须是 `QUEUED`；actor 必须在受控集合 `_DEPENDENCY_FREEZE_ACTORS = frozenset({"queue-engine","brain","human"})`。
   - `freeze="unclear_audit"`：actor 必须在 `frozenset({"auditor","brain"})`（与现有 `block_for_unclear_audit` 第 128 行守卫精确一致）。

### 5.3 收敛结果

改造后 `tasks/queue_engine` 内直接写 state 的赋值点只剩 `transition()` 统一写入段那一处（当前 73 行，写在 `dict(task)` 副本上），且被全部守卫保护；`block_failed_dependents` 现 113–115、`block_for_unclear_audit` 现 132–134 两处直接写消失。

## 6. 两个 block 方法改造与契约升级

1. `block_failed_dependents`：保留 97–108 行的筛选职责（建 states 映射、只处理 QUEUED、找 FAILED/BLOCKED 依赖、取首个、reason=`依赖 X 未完成`）；对每个待冻结任务改调
   `self.transition(task, QueueState.BLOCKED, actor=actor, reason=reason, freeze="dependency")`，
   并用返回副本 `tasks[index] = updated` 替换列表元素（用 enumerate 定位，不再原地改），仍返回 `[(task_id, event)]`。
2. `block_for_unclear_audit`：函数体改为
   `return self.transition(task, QueueState.BLOCKED, actor=actor, reason=reason, freeze="unclear_audit")`；
   终态/actor 守卫由 `transition` 统一执行，返回 `(updated, event)` 结构不变。
3. **契约升级（需同步改 1 处测试）**：`block_failed_dependents` 不再原地改入参对象，改为副本替换列表元素。
   - 正式链路 `dispatcher.py:199-203` 经 `save_tasks(tasks)` 保存整个列表，PoC 经 `self.tasks` 列表工作，均按列表索引访问，兼容。
   - `tasks/tests/test_state_machine.py:97-107` 现直接断言原引用 `dependent["state"]`，需改为从返回列表元素或 `changes` 对应的更新对象断言；state/terminal_reason/event(from=QUEUED,to=BLOCKED) 的预期值全部不变。

## 7. 测试策略

1. 保留并跑通现有全部用例（除上述 1 处引用方式升级，断言值不变）。
2. 新增受控门禁用例（均须 `InvalidTransition`）：
   - 不带 freeze 对 QUEUED 直接 `transition(BLOCKED)` 仍被拒（证明常规门未被放开）。
   - `freeze="dependency"`：源非 QUEUED、actor 不在受控集合、目标非 BLOCKED，分别被拒。
   - `freeze="unclear_audit"`：actor 非 auditor/brain、源为终态，分别被拒。
   - 非法 freeze 值被拒。
3. 新增「全链路无直接写 state」可执行硬门检查：读取 queue_engine 源文件，用区分单等号赋值与 `==` 比较的正则，断言 `state_machine.py` 直接写 state 命中数为 1（即 transition 统一写入点）、`priority_deps.py` 与 `auto_relay_poc.py` 命中数为 0；该检查自身进测试套件，而非仅手工 grep。
4. 反向验证：临时把 freeze 门拆掉或把某方法改回直接写，确认新门禁用例/硬门检查变红，恢复后转绿。

## 8. 验收口径（封闭清单）

1. 全量命令 `& H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest scripts/tests -o addopts= -p no:cacheprovider -q` 全绿，当前基线 116 passed，只许增加、不许减少，贴完整原始输出。
2. 同解释器跑 `tasks/tests`（含 state_machine 硬门检查）全绿，贴输出。
3. 硬门检查与字面 grep 双重确认：state_machine 直接写 state 命中数为 1、priority_deps/auto_relay_poc 命中数为 0，贴 grep 与测试输出。
4. 受控门禁用例全红（反向）与恢复后转绿两段输出齐备。
5. 现有依赖冻结/审计冻结的 state、terminal_reason、事件 from/to 与改造前一致，贴对照。
6. 提交显式列路径、中文信息，不 `git add -A`；`git diff HEAD -- tasks/queue/queue-status.json` 为空（派发器登记除外）。

## 9. 硬门复审与落地门

完成后由 DeepSeek 走独立复审，把「全链路无直接写 state（含 state_machine 被 PoC 触达路径）」作为硬门，单 batch 载入全部相关字节，证据包须含 pytest 原始输出与反向验证。硬门通过才回头判 ACC-6 PASS；在此之前禁止正式 auto_relay 接线、接真实派发或发布。若硬门不过，按打回处理，不落地。
