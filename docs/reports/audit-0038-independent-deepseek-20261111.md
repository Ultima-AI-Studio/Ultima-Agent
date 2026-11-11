# 0038 自动接力 tools 设计 · DeepSeek 独立审计裁决

- 审计时间：2026-11-11 ｜ 审计单：`wo-ultimaagent-20261111-0039`
- 执行端：DeepSeek（`deepseek-chat`，经 `scripts/audit-work-order.py` 直调，两轮）
- 被审对象：0038 整合设计 + 隔离 PoC（Codex 制作）
- 机器产物：`tasks/queue/runs/wo-ultimaagent-20261111-0039-20261111T050032839000Z/audit.json`

## 一、结论（先行）

**有条件不通过：8 项审计门中 7 项 PASS、1 项 FAIL（ACC-6）。** 0038 的核心机制（有界循环、fail-closed、幂等、失败恢复、名额兜底、测试有效性、隔离性）经独立核对成立；但 PoC 用了一条正式落地时被其自身设计明令禁止的捷径，正式实现前必须修正，不得照抄 PoC 的状态迁移写法。

两轮 DeepSeek 独立判断完全收敛、结论一致；本裁决的关键事实已由主脑回读源码复核，非仅采信模型自述。

## 二、关于 audit.json 顶层「8 门全 FAIL」的口径说明

`audit.json` 顶层 `audit_passed=false` 且每轮 `per_gate` 显示 8 门全 FAIL，**这是分批聚合造成的表象，不代表存在 8 个真实缺陷**。

- 随附对象约 98KB，超过批阈值 64KB，被拆成 2 批：批 1 含 0038 卡与 `tools-contract.md`（无 PoC 源码），批 2 含 PoC、测试与真实源码。
- 每批独立判全部 8 门。批 1 因看不到 PoC 源码，按「证据不足即 FAIL」纪律对 8 门全部判 FAIL；批 2 在能读到代码的情况下，对 7 门判 PASS、仅 ACC-6 判 FAIL。
- 聚合时任一 FAIL 即 FAIL，故顶层被批 1 的「证据不足」污染成全 FAIL。

真实判定以**能读到完整代码的批 2（两轮一致）**为准：7 PASS / 1 FAIL。这同时暴露 `audit-work-order.py` 的一个口径局限——跨批才能验证的门会被「证据分散」误判，需后续单独改进（本单不改该脚本）。

## 三、逐项裁决（基于完整代码证据，两轮一致）

| 门 | 判定 | 证据要点 |
|---|---|---|
| ACC-1 循环有界性 | PASS | 唯一循环 `for _ in range(max_steps)`，各分支均返回或推进任务，超限抛 `BoundedLoopExceeded` 而非静默继续；`max_steps<1` 被拒 |
| ACC-2 fail-closed | PASS | 缺依赖/非法状态/非 AUDIT 回执/缺时间证据/摘要冲突均抛错或拒绝，未发现异常路径被静默当成功 |
| ACC-3 状态唯一 | PASS | PoC 仅 import 复用 `QueueState`，无自定义枚举或未登记状态名 |
| ACC-4 失败恢复与幂等 | PASS | 重试上限转 BLOCKED；重复回执不写状态、记录仅 1 条；PoC 无进程/网络副作用 |
| ACC-5 名额兜底 | PASS | 无 run AUDIT 单：有时间证据算出等待时长，无则标无效持有，两分支均成立，不永久占位 |
| **ACC-6 设计一致性** | **FAIL** | 见下节 |
| ACC-7 测试有效性 | PASS | 6 用例均断言可观察行为；删除步数上限/幂等/依赖门分别会使对应用例变红 |
| ACC-8 隔离与事实 | PASS | 无 subprocess/socket/真实 Codex 调用；`component-facts` 对真实组件的判定与源码一致 |

## 四、唯一真实缺陷：ACC-6（P1，落地前必修）

**事实**：PoC 的私有方法 `_transition`（`tasks/queue_engine/auto_relay_poc.py` 中 `task["state"] = target.value` 一处）直接改写任务状态并自造事件，未调用 `StateMachine.transition()`；`_dependency_gate` 亦为自行实现，未委托 `QueuePlanner.dependency_gate()`；且未实现设计声明的 `RelayPump.pump_once(max_actions)` / `run(stop_event, interval_s)` 接口。

**与设计的冲突**：0038 自己在 `component-facts.md` 定下可证伪条件——

- T1 第 5 项：「所有状态变更必须通过 `transition()`；直接改 `task['state']` 的 scheduler 实现即失败。」
- T1 第 6 项：失败恢复须用 `StateMachine.retry_or_block()`。
- T1 第 8 项：选单依赖门若绕过 `QueuePlanner.dependency_gate()` 即失败。
- T1 第 1 项：正式件应提供 `RelayPump.pump_once` / `run` 接口。

**风险定性**：这不是现网缺陷——PoC 物理隔离、不被正式入口引用，当前不影响任何真实派发。风险在落地环节：若正式 `auto_relay` 照抄 PoC 的私有 `_transition`，将架空 `StateMachine` 的 `_ALLOWED` 校验、AUDIT→COMPLETED 的 `audit_passed` 门、BLOCKED 人工释放门与重试守卫，使「fail-closed 状态机」名存实亡。这正是要避免的「未经独立验证的循环接进真实派发」。

## 五、正式落地的前置条件（只列条件，不在本单改代码）

1. 正式自动接力件的每一次状态变更必须委托 `StateMachine.transition()`，失败恢复走 `retry_or_block()`，禁止任何直接写 `task["state"]` 的路径。
2. 选单依赖门必须复用 `QueuePlanner.dependency_gate()`，不得另写一套等价判断。
3. 公开 `RelayPump.pump_once(max_actions)` / `run(stop_event, interval_s)` 接口，PoC 仅作行为参考、不作接线模板。
4. 上述每条须有测试断言：尝试绕过状态门/依赖门时应被拒绝且测试变红。
5. 另立工单改进 `audit-work-order.py` 的跨批聚合口径，避免「证据分散即全 FAIL」。

## 六、本审计的局限

- DeepSeek 为静态只读判断，未实际运行正式链路；结论基于随附字节，未随附的对象不纳入判断。
- 两轮为同一模型、同一证据，属强化复核而非真正的第三方独立审计；最终把关权仍在用户。
- 批 1 的「证据不足 FAIL」属工具口径问题，已在第二节说明，不计入 0038 的真实缺陷。
