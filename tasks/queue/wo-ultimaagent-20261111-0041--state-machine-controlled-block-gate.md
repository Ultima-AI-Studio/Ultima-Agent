# Codex 工单 · 0041 正式状态机受控冻结门（消除全链路直接写 state）

> 版本：v1.0 ｜ 状态：可开工 ｜ 适用工具：Codex
> 链路：`wo-ultimaagent-20261111-0041`
> 执行端：Codex（独立任务通道，主脑不参与判据定夺）
> 前置：0040 已提交 `a8821457`（PoC 自身已委托、干净）；本单改被委托链下游的正式组件
> 方案依据：`docs/plans/plan-ultimaagent-state-machine-controlled-block-gate-20261111.md`
> 锁定 revision：`a8821457a4f413319869484007bbcd0b522b8512`
> 工作目录锁定：`H:\UltimaAI\UltimaAgent`
> 用法：按 T0→T3 顺序执行，每 T 的 Gate 全绿再进下一条，禁止跳序。

---

## 0. 本单定位

本单只做一件事：修掉 DeepSeek 单门 ACC-6 复审两轮 FAIL、并经豆包回源码实跑坐实的真实缺陷——正式状态机里两个 block 方法绕过 `transition()` 直接写 `task["state"]`，且 `QUEUED→BLOCKED` 在常规 `_ALLOWED` 本就非法。改造目标是让全链路（含 PoC 触达的正式组件路径）所有状态变更收敛到 `transition()` 唯一入口，保持 fail-closed 与八态模型不变。

本单不推进任何业务任务，不接真实 Codex，不做正式 auto_relay 接线。完成后交 DeepSeek 把「全链路无直接写 state」当硬门复审，过了才回头判 ACC-6 PASS。

---

## 1. 范围冻结

**本阶段只做**

1. 给 `StateMachine.transition()` 增加 keyword-only `freeze` 受控冻结门，在不污染常规 `_ALLOWED` 的前提下，让依赖冻结、审计冻结两类到 BLOCKED 的迁移经统一守卫、统一写入段完成。
2. 把 `block_failed_dependents`、`block_for_unclear_audit` 改为委托 `transition()`，删除两处直接写 state 的代码。
3. 升级受契约影响的现有测试断言，新增受控门禁用例与「全链路无直接写 state」可执行硬门检查。
4. 全量回归与反向验证。

**本阶段不做（Non-goals）**

1. 不新建正式 `auto_relay.py` / `scheduler_tools.py`，不做 P0–P3 落地接线，不把 PoC 接正式入口/自启/看门狗，不调真实 Codex/付费接口。
2. 不新增状态枚举，域内仍只有 `QueueState` 八态；不复制 `_ALLOWED` 到任何调用方。
3. 不改 `priority_deps.py`、`audit.py`、`dispatcher.py`、`middleware/ticket.py` 的调用代码，不改 `dispatch-work-order.py`、`validate_work_order.py`。
4. 不改 `queue-status.json` 业务数据（派发器对本单的状态登记除外）；不联网、不装依赖、不 `git add -A`。

---

## 2. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `tasks/queue_engine/state_machine.py` | `transition()` 含 `freeze` 受控门，常规 `_ALLOWED` 未放开，不带 freeze 的 QUEUED→BLOCKED 仍被拒绝，现有测试全绿 |
| T1 | `tasks/queue_engine/state_machine.py` + `tasks/tests/test_state_machine.py` | 两个 block 方法委托 `transition()`，直接写 state 命中计数为 1，依赖/审计冻结行为与改造前一致 |
| T2 | `tasks/tests/test_state_machine.py` | 新增受控门禁用例与全链路硬门检查全绿，硬门检查计数与设计一致 |
| T3 | `scripts/tests/` + `tasks/tests/` + 本卡回填位 | 全量回归只增不减、反向验证变红、硬门 grep 成立，回执填写完整 |

---

## 3. 任务明细

### T0 · transition 增加受控冻结门

**文件**：`tasks/queue_engine/state_machine.py`

**写什么**：

1. 新增模块级常量 `_DEPENDENCY_FREEZE_ACTORS = frozenset({"queue-engine", "brain", "human"})`。
2. 给 `transition()` 增加 keyword-only 参数 `freeze: str | None = None`，合法值仅 `None` / `"dependency"` / `"unclear_audit"`。
3. 实现 freeze 守卫，按序：非法 freeze 值拒绝；目标非 BLOCKED 拒绝；源为 COMPLETED/CANCELLED 终态拒绝；`freeze="dependency"` 要求源为 QUEUED 且 actor 在 `_DEPENDENCY_FREEZE_ACTORS`；`freeze="unclear_audit"` 要求 actor 在 `frozenset({"auditor","brain"})`。
4. freeze 非空时跳过 `_ALLOWED[source]` 常规检查，守卫通过后复用现有建副本→写 state→retryCount→updated_at→terminal_reason→事件→append 的统一写入段；`freeze is None` 路径保持原样。

**验收（Gate T0）**：

- 命令 `& H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest tasks/tests/test_state_machine.py -o addopts= -p no:cacheprovider -q` 全绿，贴完整输出，记录现有用例无回退。
- 临时探针或测试：不带 freeze 对 QUEUED 任务调 `transition(BLOCKED)` 输出 `illegal transition: QUEUED -> BLOCKED` 并被拒绝，贴输出，证明常规门未放开。
- grep 确认 `freeze` 参数、`_DEPENDENCY_FREEZE_ACTORS` 与两类守卫在 `state_machine.py` 出现，贴 grep 输出。

**禁止**：不得把 BLOCKED 加进常规 `_ALLOWED[QUEUED]`；不得在本 T 修改两个 block 方法；不得改动 freeze=None 的常规迁移行为。

---

### T1 · 两个 block 方法委托与契约升级

**文件**：`tasks/queue_engine/state_machine.py` + `tasks/tests/test_state_machine.py`

**写什么**：

1. `block_failed_dependents` 保留现有筛选职责（建 states 映射、只处理 QUEUED、找 FAILED/BLOCKED 依赖、取首个、reason=`依赖 X 未完成`），对每个待冻结任务改调 `transition(..., freeze="dependency")`，用 enumerate 定位并以返回副本 `tasks[index] = updated` 替换，不再原地写，仍返回 `[(task_id, event)]`。
2. `block_for_unclear_audit` 函数体改为 `return self.transition(task, QueueState.BLOCKED, actor=actor, reason=reason, freeze="unclear_audit")`，返回结构不变。
3. 删除现 113–115、132–134 行两处直接写 state/updated_at/terminal_reason 的代码。
4. 升级 `test_state_machine.py` 中依赖原对象引用的依赖冻结断言：改为从返回列表元素或 `changes` 对应更新对象取值，state/terminal_reason/event(from=QUEUED,to=BLOCKED) 预期值不变。

**验收（Gate T1）**：

- grep `state_machine.py` 直接写 state 的赋值命中计数为 1（仅 transition 统一写入点，写在 dict 副本上），贴 grep 输出与计数。
- 依赖冻结用例输出 state=BLOCKED、terminal_reason=`依赖 base 未完成`、事件 from=QUEUED to=BLOCKED，与改造前一致，贴对照输出。
- 审计冻结相关测试（`tasks/tests` 与 `src/brain/tests` 中经 `block_for_unclear_audit` 的路径）全绿，贴 pytest 输出，确认 actor 守卫一致。

**禁止**：不得改 `priority_deps.py`/`audit.py`/`dispatcher.py`/`ticket.py` 的调用代码；不得保留任何直接写 state 的旁路；不得改变两个方法的返回结构。

---

### T2 · 受控门禁用例与全链路硬门检查

**文件**：`tasks/tests/test_state_machine.py`

**写什么**：

1. 新增受控门禁用例，均须抛 `InvalidTransition`：① 不带 freeze 的 QUEUED→BLOCKED 被拒；② `freeze="dependency"` 源非 QUEUED、actor 不在受控集合、目标非 BLOCKED 分别被拒；③ `freeze="unclear_audit"` actor 非 auditor/brain、源为终态分别被拒；④ 非法 freeze 值被拒。
2. 新增「全链路无直接写 state」可执行硬门检查：读取 queue_engine 源文件，用能区分单等号赋值与 `==` 比较的正则，断言 `state_machine.py` 直接写 state 命中计数为 1、`priority_deps.py` 与 `auto_relay_poc.py` 命中计数为 0。
3. 硬门检查定位真实源文件路径，进入测试套件可重复执行，而非一次性手工 grep。

**验收（Gate T2）**：

- 命令跑 `tasks/tests/test_state_machine.py` 全绿，贴输出，确认新增禁用例与硬门检查均被执行。
- 硬门检查输出三文件计数（state_machine 为 1、priority_deps 为 0、auto_relay_poc 为 0），与设计一致，贴断言输出。
- grep 确认硬门检查正则同时覆盖双引号与单引号两种 `["state"]`/`['state']` 写法，贴源码。

**禁止**：不得让硬门检查只验证 helper 而不读真实源文件；不得用宽松正则把 `==` 比较误计为赋值；不得删除既有断言。

---

### T3 · 全量回归、反向验证与回填

**文件**：`scripts/tests/` + `tasks/tests/` + 本卡回填位

**写什么**：

1. 跑全量 `scripts/tests` 与 `tasks/tests` 回归，确认通过数只增不减。
2. 反向验证：临时把 freeze 门拆掉或把某 block 方法改回直接写 `task["state"]`，确认新增门禁用例与硬门检查变红，再恢复转绿。
3. 回填本卡「回执」段，附改动文件、委托证据、pytest 原始输出与已知限制。

**验收（Gate T3）**：

- 全量命令 `& H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest scripts/tests -o addopts= -p no:cacheprovider -q` 全绿，当前基线 116 passed，只许增加，贴完整原始输出。
- 同解释器跑 `tasks/tests` 全绿，贴输出；反向验证贴出变红（exit 非 0）与恢复后转绿两段输出。
- grep 确认 `state_machine.py` 直接写 state 命中计数为 1、`priority_deps.py`/`auto_relay_poc.py` 为 0，贴 grep，证明全链路硬门成立。

**禁止**：不得删除或弱化原有断言；不得让测试只验证 helper 而不验证真实门禁；不得 `git add -A`。

---

## 4. 总验收

1. `transition()` 受控冻结门齐全，常规 `_ALLOWED` 未被污染，常规迁移零影响。
2. 两个 block 方法全部委托 `transition()`，全链路直接写 state 仅 transition 统一写入点一处。
3. 域内仍只有 `QueueState` 八态，无第三套枚举，无调用方复制规则。
4. 全量回归只增不减，反向验证已做，正式调用方代码未改、行为契约不变。
5. 数据未动：`git diff HEAD -- tasks/queue/queue-status.json` 为空（派发器自身状态登记除外）。
6. 提交显式列路径、中文信息，不 `git add -A`。

---

## 5. 禁止清单

1. 不得新建正式自动接力模块或做 P0–P3 接线，不得把 PoC 接正式链路/自启/看门狗或调真实 Codex/付费接口。
2. 不得新增状态枚举，或在调用方复制 `_ALLOWED`/重试/依赖规则。
3. 不得改 `priority_deps.py`/`audit.py`/`dispatcher.py`/`ticket.py`/`dispatch-work-order.py`/`validate_work_order.py`。
4. 不得保留任何绕过 `transition()` 的直接写 state 路径。
5. 不得联网装依赖；不得 `git add -A`，提交必须显式列路径。

---

## 回执（执行端填写）

- run 目录：（待填）
- 改动文件：（待填，限 `tasks/queue_engine/state_machine.py` 与 `tasks/tests/test_state_machine.py`）
- 委托证据：（待填，含 freeze 守卫行号、两个 block 方法调用 transition 的行号、统一写入点行号）
- 硬门计数：（待填，state_machine 直接写 state 命中数、priority_deps/auto_relay_poc 命中数）
- pytest 结果：（待填，含 scripts/tests 全量原始输出与 tasks/tests 输出、反向验证两段）
- 已知限制 / unverifiable：（待填；DeepSeek 硬门复审不在本执行单权限内，需后续独立复审单裁决）
