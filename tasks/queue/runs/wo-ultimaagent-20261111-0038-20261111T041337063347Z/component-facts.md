# wo-ultimaagent-20261111-0038 · 组件事实与差距判定

> run：`wo-ultimaagent-20261111-0038-20261111T041337063347Z`
> 取证基线：工单锁定 revision `c9ecfb7a56e2335ec7bb6404faa9a9f8213b3a30` 是当前 `HEAD=6daf70c1bd13e6f1ca979b2b0ce10d16546d3ad3` 的祖先；`HEAD` 仅在锁定点之上新增本单方案、工单和队列登记，目标源码相对锁定点无漂移。
> 判读规则：以下事实均来自函数体；文档注释只用于定位，不单独作为职责证据。

## T0 · 现状盘点

### dsh 调度相关组件（9/9）

| # | 源文件 | 职责（函数体证据） | 输入 / 输出 | 持久化方式 | 触发方式 |
|---:|---|---|---|---|---|
| 1 | `research/dsh-superagent-prototype/src/app/passes.ts` | `Passes.start()` 每 2 秒请求一次 pass；`receive()` 先交给 `engine.receive()`，仅在返回 `stored` 时请求 pass；`pump()` 用 `pumping`/`pumpAgain` 把并发请求合并为当前轮加至多一轮；`pumpOnce()` 先 `effects.kick()` 再 `engine.evaluateDue()`。 | 输入：`Trigger`、生命周期/配置状态；输出：`ReceiveResult`、`Promise<void>`，或无返回的调度请求。 | 本文件不直接落盘；通过 `engine.receive/evaluateDue` 与 `effects.kick` 驱动其宿主持久层。内存仅保存 `timer`、`stopped`、`pumping`、`pumpAgain`。 | `start()` 的 `setInterval(..., 2000)` 周期触发；新 trigger 的 `receive()` 与外部调用 `request()` 即时触发。 |
| 2 | `research/dsh-superagent-prototype/src/core/part.ts` | `EnginePart` 为 Intake/Evals/Tickets/Assignments/Replies 提供共享仓储、时钟、策略、事件和 thread/ticket 帮助函数；`handBack()` 写 trigger disposition 并在无人持有时 `queueForEval()`；`queueForEval()` 幂等地追加 `Thread.pending`。 | 输入：`EngineOptions`、`Trigger`/`Ticket`/`ThreadRef`；输出：布尔排队结果、实体或异常，并通过 `emit()` 输出领域事件。 | 通过 `Repositories` 端口调用 `triggers.saveDisposition`、`threads.save`、`tickets.get`；本文件不定义具体数据库。 | 由各 `EnginePart` 子类的方法同步调用，不含自身定时器或后台线程。 |
| 3 | `research/dsh-superagent-prototype/src/app/effects.ts` | `Effects.enqueue()` 按 `(kind,key)` upsert；`dispatch()` 依 `limit()`、`ordered`、`due` 选行；`attempt()` 成功删除，`Later` 只延后，普通失败增加 `attempts` 并指数退避；`report()` 汇总健康状态。 | 输入：`EffectKind`、key、JSON payload、handler；输出：排队/取消/idle/drain 行为及 handler 的异步完成。核心字段为 `kind,key,value,seq,generation,attempts,due`。 | 直接使用 SQLite `effect` 表；upsert 保留 `seq`，以 `seq+generation` CAS 防止运行中的旧尝试删除新 payload。 | `enqueue()`/`handle()`/`start()` 调 `kick()`，`kick()` 用 microtask 调 `dispatch()`；`Passes.pumpOnce()` 也调用 `kick()`。 |
| 4 | `research/dsh-superagent-prototype/src/app/outbox.ts` | `Outbox.send()` 校验消息后在同一事务中 `receipts.add()` 与 `effects.enqueue('reply', id,{})`；重复 message id 不再入队；`deliver()` 按 source 可用性、同会话前序消息和 channel 可达性发送并 settle。 | 输入：`OutboundMessage`/receipt id；输出：`ReplyStatus`、发送完成 Promise；失败用 `Later` 表示暂不可执行。 | `Store.receipts` 持久 receipt，`Effects` 持久 reply effect；`store.atomic()` 保证 receipt 与 effect 同步。 | `send()` 主动触发；构造器注册 `reply` handler，Effects 到期后触发 `deliver()`。 |
| 5 | `research/dsh-superagent-prototype/src/core/tickets.ts` | `Tickets.create()` 建 ticket/首个 assignment/订阅并启动 executor；`addInput()` 幂等加 input 后选择 deliver/start；`retry()` 结束旧 assignment 并新建；`wake()` 只由人类消息恢复非人工停止的 ended ticket；`end()` 停 assignment、清订阅关联并落 outcome。 | 输入：decision/mandate/evaluation/trigger/input/ticket id；输出：`Ticket`、布尔或无返回；关键字段含 `assignments,inputs,undelivered,ended,attention,delivery,follows`。 | 经 `repo.tickets.save`、`repo.threads.save`、`repo.triggers.saveDisposition`；启动/停止外部动作经 `options.executor`。 | 由 Eval accept、Intake fanout、Assignment report、人工 stop/retry、thread close 等领域命令触发。 |
| 6 | `research/dsh-superagent-prototype/src/core/stage.ts` | `ticketStage()` 按固定先后把 ticket 归类为 `person/working/idle/ended` 及 action；`canRetry()` 只允许未结束且 `waitsForPerson(ticket)` 或存在 `delivery` 失败的 ticket 重试。 | 输入：`Ticket`；输出：`TicketStage` 或 `boolean`。 | 纯函数，无持久化。 | 由状态展示与 `Tickets.retry()` 前置判定同步调用。 |
| 7 | `research/dsh-superagent-prototype/src/core/assignments.ts` | `started/delivered/read/turnEnded/deliveryFailed` 记录 worker 生命周期；`interrupted()` 对未 settle 的运行 assignment 调 `tickets.restart()` 并带恢复提示，对已 settle 的仅补投未送 input；`report()` 校验并写 report/question/answer，`ready/dropped` 时结束 ticket。 | 输入：ticket/assignment/input ids 与 `WorkerReport(state,summary,question,askedBy,answers)`；输出：更新后的 `Ticket` 或无返回。 | 经 `repo.tickets.save` 持久 assignment/report/input read 状态；跨聚合动作委托 `Tickets`、`Replies`、`Executor`。 | Executor 生命周期回调、worker report 和 host restart 触发。 |
| 8 | `research/dsh-superagent-prototype/src/core/intake.ts` | `Intake.receive()` 规范时间、按 trigger id 去重、按 scope 过滤，保存 thread correlation，fanout 到订阅 ticket；无人拥有的 trigger 进入 Eval，并 wake 命中的 ticket。 | 输入：`Trigger`；输出严格为 `stored`/`duplicate`/`filtered`。 | 经 `repo.triggers.save/saveDisposition`、`repo.threads.save`，ticket input 经 `Tickets.addInput()` 持久。 | Engine/`Passes.receive()` 收到 source trigger 时同步触发。 |
| 9 | `research/dsh-superagent-prototype/src/infra/health.ts` | `HealthBoard.claim()` 确保每个 name 只有一个报告者，返回可 `get/set/release` 的 `HealthEntry`；`all` 暴露当前只读视图。 | 输入：name、可选初值；输出：`HealthEntry`/全部 health；重复 claim 抛错。 | 仅内存 `entries` 与 `claimed`，进程重启即丢失。 | Runtime/Effects/Executor/Settings/SourceRegistry 初始化时 claim，运行时 set/release，管理 HTTP 读取。 |

### 本地组件（7/7）

| # | 源文件 | 职责（函数体证据） | 输入 / 输出 | 持久化方式 | 触发方式 |
|---:|---|---|---|---|---|
| 1 | `tasks/queue_engine/state_machine.py` | `QueueState` 定义八态；`StateMachine.transition()` 校验 `_ALLOWED`、AUDIT PASS、BLOCKED 人工释放与 retry 上限后才追加事件；`retry_or_block()` 在两次失败重试后转 BLOCKED；`block_failed_dependents()` 与 `block_for_unclear_audit()` fail-closed。 | 输入：task dict、目标八态、actor/reason/audit_passed；输出：更新副本与事件，非法输入抛 `InvalidTransition`。 | task 本体由调用者保存；事件经 `QueueStorage.append_event()` 写 `events/<task_id>.jsonl`；缺 `retryCount` 时从事件恢复。 | CLI、中间件、Dispatcher/Audit/Recovery 等显式调用；无自身循环。 |
| 2 | `tasks/queue_engine/priority_deps.py` | `QueuePlanner.ordered_tasks()` 仅选 QUEUED，按 priority、持久顺序、created_at、task_id 排序；`dependency_gate()` 校验缺失/失败/未完成依赖；`enqueue()` 校验 DAG；优先级和插队写审计事件。 | 输入：task 列表或存储；输出：有序 task 列表、`(ready,reason)`，或规划异常。 | task 写 `tasks.json`；显示顺序原子写 `queue/queue.md`；事件写 JSONL；高层改写由 `.dispatch.lock` 串行化。 | CLI/交互工具/Dispatcher 显式调用；无定时触发。 |
| 3 | `tasks/queue_engine/dispatcher.py` | `Dispatcher.dispatch()` 在 pause、非阻塞 OS 锁、三类幂等 probe、八态、卡版本、依赖、容量门全绿后建 run 并隐藏启动 `run_worker.py`；`_capacity_reason()` 实现本队列串行或同 parallelGroup 最多 2；PID 与创建身份共同判活。 | 输入：task id、argv；输出 `DispatchDecision(dispatched,reason,task_id,pid,run_paths)`；`DispatchedProcess.wait()` 要求 durable done。 | 写 run 的 `before/out/err/done/session/progress`，状态/事件写 `tasks.json` 与 JSONL；锁文件仅作 OS lock 载体。 | 外部一次性调用 `dispatch()`；不选下一单，不自循环。 |
| 4 | `tasks/queue_engine/storage.py` | `QueueStorage` 管理索引、事件、run 与保守归档；`validate_index_record()` 固定字段；`_atomic_write_json()` 临时文件 + `os.replace()`；`create_run_artifacts()` 创建六件套。 | 输入：root/task records/events；输出：校验后的 task 列表、artifact 路径或 `StorageError`。 | `tasks.json`、`queue/`、`events/*.jsonl`、`runs/`、`archive/index-items.jsonl`；事件 append+fsync，索引原子替换。 | 被 planner/state machine/dispatcher/audit/CLI 同步调用。 |
| 5 | `tasks/queue_engine/run_worker.py` | `main()` 读取 progress 配置，启 Windows window monitor，使用隐藏标志和精简 `CODEX_HOME` 启子进程，等待退出，最后原子写 done；可见窗口或 supervisor 异常强制 exit 1。 | 输入：`argv[1]` progress JSON（`command,cwd,done`）；输出：进程退出码和 done JSON（`exit_code,supervisor_error?,window_audit,finished_at`）。 | 更新 progress 的 worker PID/identity；临时文件替换写 progress 与 done。 | 仅由 `Dispatcher.dispatch()` 作为每次 run 的 supervisor 启动；不是常驻调度器。 |
| 6 | `tasks/queue_engine/receipt_contract.py` | `classify_receipt_path()` 读 structured/text final receipt；必须匹配工单，成功必须 exit 0 + READY 标记 + 自检证据，才返回小写 `audit`；明确 BLOCKED 返回 `blocked`；其他 fail-closed 为 invalid blocked。 | 输入：receipt path、work_order、exit_code；输出 `ReceiptDecision(state,valid,format)`。 | 只读 receipt，不持久化；由调用者写 run/队列结果。 | `dispatch-work-order.py` 在 worker 退出后同步调用。 |
| 7 | `scripts/dispatch-work-order.py` | 老链一次处理一单：DoR/卡/暂停/WIP 检查，持共享工程锁，直接启真实 Codex，监控 pause/parent/runtime，分类 receipt，再检查 audit 名额并回写；`state()` 对 `queue-status.json` 做字节 CAS 后调用 renderer。 | 输入：`--order/--prompt/...`；输出：JSON、exit 0（audit）或 2（blocked/拒派）；隐式状态守卫允许普通派发 `pending`，repair 允许 `pending/blocked/audit`，运行中写 `executing`，结尾写 `audit/blocked`。 | 直接写 `tasks/queue/queue-status.json`、run 目录与 renderer 管理的登记；run 含 prompt/before/session/exit/done 等。 | 人工/外部每单启动一次；内部 `while worker.poll() is None` 仅监控该 run，受 worker exit、pause、parent loss 与 runtime deadline 约束，不选下一单。 |

### 双轨现状

| 环节 | 老脚本链（`scripts/dispatch-work-order.py` + renderer） | `tasks/queue_engine` | 对应与缺口 |
|---|---|---|---|
| 登记/存储 | `queue-status.json` schema 1，renderer 接受 `frozen/blocked/cancelled/pending/closed/audit/executing`。 | `QueueStorage` 的 `tasks.json` + events/runs/archive。 | 两个事实载体并存，字段与大小写不同。 |
| 状态 | 守卫散在 `main()`；无状态类。 | `QueueState` 八态：`QUEUED/EXECUTING/SELF-CHECK/AUDIT/COMPLETED/FAILED/BLOCKED/CANCELLED`，统一由 `StateMachine` 校验。 | 现有映射：`pending→QUEUED`、`executing→EXECUTING`、`audit→AUDIT`、`blocked→BLOCKED`、`cancelled→CANCELLED`、`frozen|closed→COMPLETED`；老链没有 `SELF-CHECK/FAILED`。`frozen` 应迁为 COMPLETED 上的冻结元数据，不再作为第三套状态。 |
| 选单/依赖 | 不选单；调用者必须给 `--order`。依赖只靠派发前外围登记/工单门。 | `ordered_tasks()` + `dependency_gate()` + DAG 校验。 | 选单零件只在 queue_engine，有调用者但无自动泵。 |
| 派发/WIP | 全局真实 exec ≤3、同项目 ≤1；直接启动 Codex，拥有正式生产 run/回写链。 | `Dispatcher.dispatch()` 针对 queue_engine 根，支持串行或同组 ≤2，隐藏 supervisor、幂等 probe。 | 两套容量语义与 run 布局未收敛；老链仍是正式入口。 |
| 回执/恢复 | `receipt_contract` 分类后写 `audit/blocked`；runtime/pause/parent loss 有界停止；audit slot 逻辑在脚本内。 | 八态与 audit/recovery 零件可接，但本次指定六件中没有跨单驱动者。 | 回执分类已被老链复用，状态写回仍走老枚举。 |
| 审计/冻结 | audit 只占名额并停等外部复核；冻结由其他脚本/人工门执行。 | 八态支持 AUDIT→COMPLETED 必须显式 audit PASS；BLOCKED 仅 human/brain 释放。 | 门禁方向一致，但控制面未统一。 |
| 常驻接力 | **不存在**；一次进程只跑一张工单。 | **不存在**；没有组件周期调用 `ordered_tasks()`→`dispatch()`→消费完成回执→再选单。 | 这是本单要设计的缺口。 |

### Gate T0 证据

组件计数：dsh `9`，本地 `7`，与工单指定清单逐项一致。

至少三组可复核 grep 命中（本次实际执行）：

```text
> rg -n "setInterval|pumpOnce|enqueue<|receipts\.add|ticketStage|interrupted\(|receive\(|claim\(" <9 个 dsh 文件>
.../passes.ts:28:  start(): void { if (!this.stopped) this.timer = setInterval(() => { this.request() }, 2000) }
.../passes.ts:63:  private async pumpOnce(): Promise<void> {
.../effects.ts:61:  enqueue<K extends EffectKind>(kind: K, key: string, payload: EffectPayloads[K]): void {
.../outbox.ts:31:    store.atomic(() => { if (store.receipts.add(message)) effects.enqueue('reply', message.id, {}) })
.../stage.ts:9:export function ticketStage(ticket: Ticket): TicketStage {
.../assignments.ts:83:  interrupted(ticketId: string, assignmentId: string): void {
.../intake.ts:19:  receive(received: Trigger): ReceiveResult {
.../health.ts:18:  claim(name: string, initial?: Health): HealthEntry {

> rg -n "class QueueState|BLOCKED may be released|retry limit reached|ordered_tasks|dependency_gate|def dispatch\(|_capacity_reason|create_run_artifacts|classify_receipt_path" <6 个 queue_engine 文件>
tasks/queue_engine/state_machine.py:13:class QueueState(StrEnum):
tasks/queue_engine/state_machine.py:62:            raise InvalidTransition("BLOCKED may be released only by human or brain")
tasks/queue_engine/state_machine.py:67:                raise InvalidTransition("retry limit reached; FAILED must transition to BLOCKED")
tasks/queue_engine/priority_deps.py:28:    def ordered_tasks(...)
tasks/queue_engine/priority_deps.py:123:    def dependency_gate(...)
tasks/queue_engine/dispatcher.py:174:    def dispatch(...)
tasks/queue_engine/storage.py:131:    def create_run_artifacts(...)
tasks/queue_engine/receipt_contract.py:79:def classify_receipt_path(...)

> rg -n "STATE|pending.*executing|frozen|cancelled" scripts/render-queue-views.py
scripts/render-queue-views.py:26:STATES = {"frozen", "blocked", "cancelled", "pending", "closed", "audit", "executing"}
```

全仓循环/daemon 搜索先列出 50 个命中文件；落到 `tasks/queue_engine` 或正式派发器的只有两个：

```text
repo_hit_file_count=50
queue_engine_or_dispatch_hit_count=2
tasks\queue_engine\guardian.py:13:    while True:
tasks\queue_engine\windows_runtime.py:33:    while True:
tasks\queue_engine\windows_runtime.py:52:            self.thread = threading.Thread(target=self.observe, daemon=True)
```

逐函数读回证明它们不是接力循环：`guardian.guard()` 在 parent identity 丢失或 done 非空时 `return`，且注释与行为均表明它从不派发；`windows_runtime.descendants()` 的 `while True` 在进程树达到不动点即 `return`，`WindowMonitor.observe()` 则受 `stopping` Event 终止，只做可见窗口审计。正式派发器唯一监控循环是 `scripts/dispatch-work-order.py:637 while worker.poll() is None`，受 worker exit、pause、parent loss 与 `max_runtime_seconds` 截止约束。全仓没有把 `QueuePlanner.ordered_tasks()`、`Dispatcher.dispatch()` 与完成回执消费串起来的常驻循环。

**Gate T0：PASS。**

## T1 · 差距与复用判定

### 逐组件判定（9/9，每项恰一个结论）

| # | dsh 组件 | 唯一判定 | 本地落点与理由 | 可证伪条件 |
|---:|---|---|---|---|
| 1 | `app/passes.ts` | **新写** | 后续正式阶段新建 `tasks/queue_engine/auto_relay.py::RelayPump.pump_once(max_actions: int) -> PumpResult` 与 `run(stop_event, interval_s)`。本地没有任何循环把 `ordered_tasks()`、`dispatch()` 和完成回执串起来；不能把 Agent server watchdog 当工单调度器。 | 构造两个无依赖 QUEUED task，调用一次有界 pump 后第一个进入 EXECUTING；模拟其完成并再次 pump 后第二个进入 EXECUTING；任一次 pump 处理动作数 `> max_actions` 或空队列不返回即失败。 |
| 2 | `core/part.ts` | **直接复用** | 不移植继承基类，正式组合现有 `QueueStorage.load_tasks()`（`tasks/queue_engine/storage.py:82`）、`save_tasks()`（`:94`）、`StateMachine` 与 `QueuePlanner`。这些端口已经提供仓储、时钟落盘点、事件与状态守卫，Python 再造 `EnginePart` 只会增加抽象。 | 本地 grep 必须继续命中下列函数；若 scheduler 绕过它们自行写 task/state，则本判定失败。 |
| 3 | `app/effects.ts` | **新写** | 后续正式阶段新建 `tasks/queue_engine/effect_queue.py::enqueue_effect(kind, key, payload, due_at)` 与 `run_due(now, limit) -> list[EffectResult]`；底层复用 `QueueStorage` 的原子写与 `.dispatch.lock`，但需要新增持久 effect journal，因为现有事件 JSONL 不能表达待执行行、due、attempts 与 generation CAS。 | 同一 `(kind,key)` 连续 enqueue 两次，只保留一个待执行行且 generation 增 1；handler 连续失败时 due 按上限退避，达到配置次数后不再自动执行并令关联 task 进入 BLOCKED；旧 generation 完成不得删除新 payload。 |
| 4 | `app/outbox.ts` | **改造** | 在后续正式阶段改造 `tasks/queue_engine/receipt_contract.py`：保留 `classify_receipt_path()`（`:79`）的 fail-closed 分类，新增 `accept_receipt(storage, receipt_id, digest, decision)`，把 receipt id/digest 写入 scheduler journal；不复制 dsh 的 IM 发送逻辑。 | 构造同一 `receipt_id+digest` 连续投递两次，第一次返回 accepted、第二次返回 duplicate；journal 计数必须为 1，task 状态与单次投递完全一致。相同 id 不同 digest 必须冲突并停止，不可覆盖。 |
| 5 | `core/tickets.ts` | **直接复用** | Ticket 生命周期收敛到 `QueueState`（`tasks/queue_engine/state_machine.py:13`）与 `StateMachine.transition()`（`:45`）；创建/输入/订阅等 dsh 会话语义不属于本地工单域，不移植。任务输入仍由现有 queue index/card 管理。 | 所有状态变更必须通过 `transition()`；直接改 `task['state']` 的 scheduler 实现即失败。 |
| 6 | `core/stage.ts` | **直接复用** | 以八态为唯一域状态，使用 `StateMachine.retry_or_block()`（`tasks/queue_engine/state_machine.py:87`）执行失败恢复；不保存 dsh `TicketStage`。展示层仅做既定映射。 | 第 1、2 次 FAILED 重试进入 QUEUED 并累计；达到上限后进入 BLOCKED。非 human/brain 释放 BLOCKED 必须抛 `InvalidTransition`。 |
| 7 | `core/assignments.ts` | **直接复用** | assignment 启动/身份/恢复落到 `Dispatcher.dispatch()`（`tasks/queue_engine/dispatcher.py:174`）、run 六件套与 `process_identity()`（`:351`）；`run_worker.py` 保留 durable done 与零窗口监督。调度器只消费 run 事实，不自行重复外部操作。 | 同 task 已有存活 process/session/active run 任一证据时再次 dispatch，`DispatchDecision.dispatched` 必须为 false；PID 相同但创建身份不同不得判为原 worker。 |
| 8 | `core/intake.ts` | **直接复用** | 本地域的“输入”是已登记 QUEUED task，不是聊天 Trigger；直接使用 `QueuePlanner.ordered_tasks()`（`tasks/queue_engine/priority_deps.py:28`）与 `dependency_gate()`（`:123`）做去重后的候选读取和依赖门，不移植 Source/Thread fanout。 | 缺失、FAILED/BLOCKED、未 COMPLETED 依赖分别返回不可派发；仅所有依赖 COMPLETED 时返回 ready。若选单绕过该函数即失败。 |
| 9 | `infra/health.ts` | **新写** | 后续正式阶段新建 `tasks/queue_engine/scheduler_health.py::read_health(now) -> dict`，从 scheduler lease、最近 pump、effect backlog、最近 error 生成只读快照；不改 `scripts/watchdog-loopguard.py`，因为其 `main()`（`:358`）守护的是 8756 Agent server，`while True`（`:434`）与工单调度职责不同。 | 给定过期 lease、积压 effect 与最近错误，返回结构必须同时呈现三者且整体不为 ready；停止服务后 health 查询不得启动进程或改变 queue。 |

### 直接复用项 grep 证据（本次实际执行）

```text
> rg -n "def load_tasks|def save_tasks|class QueueState|def transition|def retry_or_block|def ordered_tasks|def dependency_gate|def dispatch\(|def process_identity" <本地文件>
tasks/queue_engine/storage.py:82:    def load_tasks(self) -> list[dict[str, Any]]:
tasks/queue_engine/storage.py:94:    def save_tasks(self, tasks: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
tasks/queue_engine/state_machine.py:13:class QueueState(StrEnum):
tasks/queue_engine/state_machine.py:45:    def transition(
tasks/queue_engine/state_machine.py:87:    def retry_or_block(
tasks/queue_engine/priority_deps.py:28:    def ordered_tasks(self, tasks: Iterable[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
tasks/queue_engine/priority_deps.py:123:    def dependency_gate(
tasks/queue_engine/dispatcher.py:174:    def dispatch(self, task_id: str, command: Sequence[str]) -> DispatchDecision:
tasks/queue_engine/dispatcher.py:351:def process_identity(pid: int) -> str | None:
```

### 双轨收敛建议

**推荐：以 `tasks/queue_engine` 为唯一域模型和状态权威，老脚本链按“外壳兼容 → 委托 → 封存”退役。**

1. **影子对账期**：新增只读 legacy codec，把 renderer 的七个小写值解码为现有 `QueueState`；只读比较选单、依赖、容量与状态，不写 `queue-status.json`，也不派发。
2. **委托期**：把 `dispatch-work-order.py` 的启动/监工能力封装成 queue_engine executor adapter；选单、状态迁移、重试、事件与幂等全部走 `QueuePlanner/StateMachine/QueueStorage`。旧 `state()` 禁止继续作为并发写者。
3. **单写期**：queue_engine 的事务存储成为唯一写入者；`queue-status.json` 只由一个 projection writer 在同一共享锁/CAS 下生成。正式消费者先双读校验，再切到 projection。
4. **封存期**：移除正式入口对老脚本状态守卫和直接 JSON 写入的调用；保留只读归档与迁移回滚脚本，不删除历史 run/receipt。

状态归并只使用现有八态：

| legacy 输入/展示 | 唯一 `QueueState` | 迁移说明 |
|---|---|---|
| `pending` | `QUEUED` | 等待选单。 |
| `executing` | `EXECUTING` | 已占执行名额。 |
| 无旧值 | `SELF-CHECK` | 新流程只在八态内表达，不向域内增加别名。 |
| `audit` | `AUDIT` | 等待/进行独立复核。 |
| `frozen`、`closed` | `COMPLETED` | 冻结 tag、Owner 门、关闭原因改为元数据；不是状态。 |
| 无旧值 | `FAILED` | 可恢复失败，受现有两次重试上限约束。 |
| `blocked` | `BLOCKED` | 仅 human/brain 可释放。 |
| `cancelled` | `CANCELLED` | 终态。 |

迁移期的 legacy codec 只是 I/O 映射，不定义枚举、不参与状态迁移；因此域内始终只有 `QueueState` 这一套八态，不产生第三个状态集合。

**反方方案：保留 `dispatch-work-order.py` 为权威、把 queue_engine 当库。** 优点是近期正式派发行为变化最小；缺点是状态守卫仍散在脚本、`queue-status.json` 仍是直接写入点、`SELF-CHECK/FAILED` 无法自然表达，自动接力最终会在老链旁再长一套持久循环，实质形成第三控制面。因此不推荐。

### unverifiable

`unverifiable` 条目数：`0`。9 个指定组件的函数体、调用点与本地落点均已读到足够证据；没有需要以缺证据替代判断的条目，因此也没有未执行的取证命令。

**Gate T1：PASS。**
