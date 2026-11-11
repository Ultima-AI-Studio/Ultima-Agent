# wo-ultimaagent-20261111-0038 · 自动接力 tools 契约

> run：`wo-ultimaagent-20261111-0038-20261111T041337063347Z`
> 阶段边界：本文件是设计契约，不代表正式链路已接入。T4 PoC 只使用夹具，不读写正式队列、不调用 Codex。

## T2 · tools 形态与接口契约

### 形态选择

| 候选 | 取舍 | 结论 |
|---|---|---|
| 常驻无窗服务 | 能提供周期 pump、lease、崩溃恢复；但如果把状态机和选单逻辑写在服务入口，会形成第三控制面，也难以单测。 | 只作为后续 host，不承载域逻辑；本单不安装、不自启。 |
| `queue-engine` 子命令 | 适合人工运维、脚本调用和机检；但每条命令独立启动，不能单独承担常驻 lease/事件唤醒。 | 作为薄适配层，调用同一模块 API。 |
| 可调用模块 | 能直接组合 `QueueStorage/QueuePlanner/StateMachine/Dispatcher`，单次 `pump_once()` 可确定性测试，CLI 与服务共用同一实现。 | **推荐为唯一实现权威。** 后续无窗服务与 CLI 都只能调用该模块，不复制规则。 |

推荐结构（后续正式阶段，不在本单接线）：

```text
tasks.queue_engine.scheduler_tools        # 唯一域实现：六接口 + pump_once
             ↑                     ↑
queue-engine CLI 薄适配          Windows 无窗 host 薄适配
             └──────── 同一存储/锁/八态 ────────┘
```

与现有件的关系：

- `dispatch-work-order.py` 在迁移期只保留已验证的 Codex argv、run 监督、窗口审计与全局 WIP 探测，封装为 executor adapter；不得再自行选单或直接写状态。
- `queue_engine` 的 `QueuePlanner` 选单、`StateMachine` 迁移、`Dispatcher` 幂等/进程身份、`QueueStorage` 事务与 `receipt_contract` 分类继续复用。
- 服务、CLI、主脑显式调用共享同一模块；服务只是周期/唤醒 host，CLI 只是参数解析，不各自定义状态或重试。

### 统一返回外壳

所有接口返回 JSON 可序列化对象：

```python
ToolResult = {
    "ok": bool,
    "code": str,       # 操作结果码，不是任务状态
    "revision": str,   # 成功写入后的存储 revision；只读时为当前 revision
    "data": dict,
}
```

公共结果码：`OK`、`INVALID_INPUT`、`LOCK_BUSY`、`PAUSED`、`NOT_RUNNING`、`REVISION_CONFLICT`、`NO_ELIGIBLE_TASK`、`DEPENDENCY_BLOCKED`、`CAPACITY_FULL`、`IDEMPOTENCY_CONFLICT`、`RETRY_EXHAUSTED`、`HUMAN_GATE_REQUIRED`、`STORAGE_ERROR`。这些是接口结果码，不持久为 task state。

### 六个公开接口

| 接口 | Python 签名 | 入参 | 成功返回 | 失败与结果码 | 可机检成功 / 失败输入 |
|---|---|---|---|---|---|
| 启动 | `start(config: SchedulerConfig, *, expected_revision: str) -> ToolResult` | `interval_s`（0.1–300）、`max_actions_per_pump`（1–100）、`max_retries`（固定为 2）、存储根、调用者身份；必须带 revision。 | `OK`，`data={running: true, lease_id, pid, started_at}`；只创建单一 lease，host 后续调用同一模块。 | 非法范围 `INVALID_INPUT`；已有有效 lease `LOCK_BUSY`；revision 漂移 `REVISION_CONFLICT`；pause 标记 `PAUSED`。 | 成功：空闲夹具 + interval=2 + max_actions=1；失败：`interval_s=0`，断言 `INVALID_INPUT` 且无 lease 文件。 |
| 停止 | `stop(*, lease_id: str, deadline_s: float = 10) -> ToolResult` | 精确 lease id 与 0.1–60 秒 deadline；不按 PID 单独认领。 | `OK`，`data={running:false, stopped_at}`；置 stop event，等待当前有界 pump 收口，不杀其他树。 | lease 不存在 `NOT_RUNNING`；身份不符 `IDEMPOTENCY_CONFLICT`；deadline 非法 `INVALID_INPUT`。 | 成功：用 start 返回的 lease id；失败：换一个 lease id，断言不改变真实 lease。 |
| 状态查询 | `status(*, now: datetime | None = None) -> ToolResult` | 可选测试时钟；只读。 | `OK`，`data` 至少含 `running,lease_id,last_pump_at,next_due_at,queue_counts,effect_backlog,last_error,revision`。 | 存储不可读/JSON 损坏 `STORAGE_ERROR`；不得为修复而写盘。 | 成功：健康夹具返回 `running=true`；失败：给损坏 journal，断言 `STORAGE_ERROR` 且文件字节不变。 |
| 选单 | `select_next(*, expected_revision: str, override_task_id: str | None = None) -> ToolResult` | snapshot revision；可选主脑 override，仅覆盖排序、不覆盖依赖/状态/容量/暂停门。 | `OK`，`data={task_id,state:"QUEUED",reason}`；候选来自 `ordered_tasks()` 且通过 `dependency_gate()`。 | 无候选 `NO_ELIGIBLE_TASK`；override 非 QUEUED/不存在 `INVALID_INPUT`；依赖未满足 `DEPENDENCY_BLOCKED`；满额 `CAPACITY_FULL`；revision 漂移 `REVISION_CONFLICT`。 | 成功：A/B 都 QUEUED，A priority 高且依赖完成，返回 A；失败：override=B 但 B 依赖 EXECUTING，断言 `DEPENDENCY_BLOCKED`。 |
| 接力触发 | `relay(*, completed_run_id: str, receipt_id: str, receipt_digest: str, expected_revision: str) -> ToolResult` | 已结束 run 身份、稳定 receipt id、内容 digest、CAS revision。 | `OK`，原 task 只通过 `StateMachine` 推进；若达到可接力终点，`data={accepted:true,next_task_id|None,receipt_count:1}` 并至多派发一单。 | 同 id 同 digest 返回 `OK` 且 `accepted=false`；同 id 不同 digest `IDEMPOTENCY_CONFLICT`；无有效 run/receipt `INVALID_INPUT`；人工门 `HUMAN_GATE_REQUIRED`；满额 `CAPACITY_FULL`。 | 成功：合法 SELF_CHECK/AUDIT 事实与唯一 receipt；失败：同 id 改 digest 再投，断言冲突、receipt_count 仍 1、task 字节不变。 |
| 重试 | `retry(*, task_id: str, failure_id: str, actor: str, expected_revision: str) -> ToolResult` | FAILED task、稳定 failure id、actor、CAS revision；仅调用 `retry_or_block()`。 | retryCount <2：`OK` 且 task→QUEUED；retryCount ≥2：`RETRY_EXHAUSTED` 且 task→BLOCKED。相同 failure id 再投不重复计数。 | 非 FAILED `INVALID_INPUT`；BLOCKED 自动释放 `HUMAN_GATE_REQUIRED`；revision 漂移 `REVISION_CONFLICT`。 | 成功：FAILED/retryCount=1 → QUEUED/retryCount=2；上限：FAILED/retryCount=2 → BLOCKED；失败：BLOCKED + actor=service，断言 `HUMAN_GATE_REQUIRED`。 |

### 持久化与唯一写入者

1. **域权威**：`QueueStorage` 管理的 task index、append-only events、run facts 与后续 scheduler journal 是自动调度唯一可写事实源；状态值只允许 `QueueState` 八态。
2. **单写事务**：任一状态/receipt/effect/lease 改动先取共享工程锁，再核对 `revision`，调用 `StateMachine`，原子写新 revision，最后释放锁。锁外快照不得覆盖锁内新事实。
3. **`queue-status.json` 关系**：它是兼容展示镜像，不是自动 tools 的输入权威。只有一个 projection writer 可在同一共享锁下从域权威生成它；scheduler、CLI、service、executor adapter 都不得直接写该文件。
4. **迁移约束**：在 `dispatch-work-order.py::state()` 尚未退役前，正式 scheduler 只能影子读、不得启用写模式；切换必须先让旧 writer 停写并完成一次 revision/哈希对账，再启用 projection writer。
5. **PoC 隔离**：T4 只在 `tmp_path`/内存夹具持久化，不读取或生成正式 `tasks.json`、`queue-status.json`、共享锁、真实 run，也不 import 正式入口。

### dsh Ticket → queue_engine 八态完整映射

映射用于导入/理解 dsh 概念；持久化后只保留右侧 `QueueState`。按表从上到下匹配，八个右侧值各出现且只出现一次。

| dsh `ticketStage()` / outcome 观察 | 唯一 queue_engine 去向 | 说明 |
|---|---|---|
| `{stage:'working', action:'queued'}` | `QUEUED` | 尚未启动 assignment。 |
| `{stage:'working'}` | `EXECUTING` | assignment 正运行且未进入报告门。 |
| `{stage:'idle'}` | `SELF-CHECK` | worker turn 已停，等待本地自检/回执分类；dsh 无同名态，只作一次性导入映射。 |
| `{stage:'person', action:'review'}` | `AUDIT` | ready report 等独立复核。 |
| `{stage:'ended'}` 且 outcome 为成功/合并/正常关闭 | `COMPLETED` | Owner 冻结仍是元数据/后续门，不增加状态。 |
| `{stage:'person', action:'failed'}` | `FAILED` | 可按现有上限重试。 |
| `{stage:'person', action:'blocked'|'answer'|'delivery'}` | `BLOCKED` | 需要人/brain 输入或交付修复；不得自动释放。 |
| `{stage:'ended'}` 且 outcome 为 stopped/dropped | `CANCELLED` | 人工停止或明确丢弃。 |

反向展示也只使用上述同一行：`QueueState` 到 dsh 概念视图不写回 dsh 字段。不存在第二个本地枚举，更不存在新增第三枚举。

### 人工门边界

- `BLOCKED` 释放：只允许 `actor in {human, brain}`。源码证据：`tasks/queue_engine/state_machine.py:60-62` 在 source 为 BLOCKED 且 actor 非 human/brain 时抛出 `InvalidTransition("BLOCKED may be released only by human or brain")`。
- 独立审计：scheduler 可登记/触发审计请求，但不能生成 audit PASS；只有外部独立复核事实才能令 `AUDIT -> COMPLETED`，并必须传 `audit_passed=True`。
- Owner 验收、冻结 tag、发布：全部停等人；COMPLETED 不自动等于冻结或发布。
- 自动范围：安全选单、依赖/容量检查、派发、回执分类、至多两次 FAILED 重试、状态/健康查询。任何门不明即 fail-closed。

### Gate T2 机检清单

- 六接口字面覆盖：启动 / 停止 / 状态查询 / 选单 / 接力触发 / 重试；每项均有签名、入参、返回、错误码、成功与失败夹具。
- 八态映射右列集合必须严格等于 `QueueState` 的八个值，且每值计数为 1。
- 设计稿不得声明新的 Python `Enum/StrEnum`；`ToolResult.code` 明确是操作结果码，不是 task state。
- `BLOCKED` 释放与现有源码一致；`queue-status.json` 明确只有 projection writer 一个写者。

**Gate T2：PASS。**

## T3 · 自动接力循环、失败恢复与名额兜底

### 有界主循环

正式实现分成无循环的 `pump_once(max_actions)` 与 host 的可停止等待循环。`pump_once` 每次最多完成 `max_actions` 个持久动作，每条分支都返回；host 只用 `stop_event.wait(interval_s)` 等待定时或事件唤醒，不做空转轮询。

```text
start → 取得唯一 lease？
  ├─ 否：返回 LOCK_BUSY，进程结束
  └─ 是：wait(stop_event 或 event 或 interval)
       ├─ stop：收口当前 pump → 释放 lease → 进程结束
       └─ wake：pump_once(max_actions)
            ├─ pause / revision 冲突 / lease 丢失：返回，等待或停止 host
            ├─ 有已结束 run：按 run identity 消费一次 receipt
            │    ├─ receipt 无效/冲突：走失败表 → 返回
            │    ├─ SELF_CHECK 未过：EXECUTING→FAILED → 有界重试/停人 → 返回
            │    ├─ SELF_CHECK 过：EXECUTING→SELF-CHECK→AUDIT
            │    │    ├─ 审计请求已存在：不重复发 → 返回
            │    │    ├─ AUDIT PASS：AUDIT→COMPLETED；若需 Owner 冻结则停等人
            │    │    └─ AUDIT FAIL：AUDIT→FAILED → 有界重试/停人 → 返回
            │    └─ 已记录同 receipt：幂等 no-op → 返回
            └─ 无已结束 run：只取 ordered_tasks() 的队首
                 ├─ 无候选：返回 NO_ELIGIBLE_TASK，host 进入 wait
                 ├─ 队首依赖未满足：不越过它派后项，返回 DEPENDENCY_BLOCKED
                 ├─ 容量/锁不足：返回 CAPACITY_FULL/LOCK_BUSY，host 进入 wait
                 ├─ 派发成功：QUEUED→EXECUTING，记录 run/幂等键 → 返回 OK
                 └─ 派发失败：记录 effect attempt/退避；到上限由 StateMachine
                      的受控 block_unrunnable() 转 BLOCKED → 返回
```

“不跳单”的定义：只检查 `ordered_tasks()` 的第一项；其依赖未满足时本轮结束，不越过它派发排序靠后的 task。下一次唤醒仍重新读取 revision 和队首，因此人工调优先级或依赖完成后可继续。

外层服务可以长期存在，但每轮都在有限步内结束；空队列、容量满、依赖等待都进入可中断的阻塞 wait，不存在 `while True` 的无 sleep 空转。一次 pump 若因持续新事件达到 `max_actions`，返回 `OK` 并设置一次 follow-up event；仍不在本轮无限处理。

### 分支终止表

| 输入分支 | 本轮动作 | 本轮终止 | 后续唤醒 |
|---|---|---|---|
| stop event | 不再取新动作，等待当前原子写完成 | host 释放 lease 并退出 | 无 |
| pause marker | 不派发；活动 worker 走下表 pause 处置 | `pump_once` 返回 `PAUSED` | pause 清除事件，且需要对应人工处置 |
| lease/revision 失配 | 不写任何状态 | 返回 `REVISION_CONFLICT`；lease 丢失则 host 退出 | 新 owner 或显式 restart |
| 无 QUEUED | 不动作 | 返回 `NO_ELIGIBLE_TASK` | 新任务/状态事件或 interval |
| 队首依赖未满足 | 不跳过、不派发 | 返回 `DEPENDENCY_BLOCKED` | 依赖状态事件 |
| 容量满/锁忙 | 不占用失败次数 | 返回 `CAPACITY_FULL/LOCK_BUSY` | run 完成事件或有抖动的 interval |
| 派发成功 | 只派一单、写 run identity | 返回 `OK` | run 完成事件 |
| 派发失败未到上限 | 写 attempt 与 `next_due_at` | 返回失败结果 | 到期 timer |
| 派发失败到上限 | 受控转 BLOCKED | 返回 `RETRY_EXHAUSTED` | 仅 human/brain 释放 |
| receipt 重复 | 不重复迁移/副作用 | 返回 `OK accepted=false` | 无 |
| receipt 冲突/无效 | fail-closed，走失败恢复 | 返回错误结果 | 按失败表或人工门 |
| AUDIT 等独立复核 | 只确保审计请求幂等存在 | 返回 `HUMAN_GATE_REQUIRED` | 外部审计事实 |
| COMPLETED 但需冻结/发布 | 不打 tag、不发布 | 返回 `HUMAN_GATE_REQUIRED` | Owner 事实 |

### 失败恢复策略

上限：派发动作共 `3` 次（首次 + 2 次重试），退避 `10s, 30s`；worker/task 失败沿用 `StateMachine` 的最多 `2` 次 FAILED→QUEUED 重试。所有次数从持久 event/effect journal 恢复，重启不清零。退避用绝对 `next_due_at`，host 重启后只执行已到期项。

| 异常输入 | 预期 QueueState / 记录 | 是否自动重试 | 终止条件 |
|---|---|---|---|
| worker timeout，identity 匹配且已收整本 run 子树 | `EXECUTING→FAILED`，event 带 timeout/run identity | 未暂停且 retryCount<2 时 `retry_or_block()`；否则停人 | 两次重试后 BLOCKED；本轮立即返回 |
| 显式 pause | 活动 run 收口后 `EXECUTING→FAILED`，journal 标 `manual_required=true`；不伪造完成 | 否；pause 清除也不自动消费该 failure | human/brain 显式 retry 或裁决；本轮返回 PAUSED |
| `parent_lost` | worker identity 仍存活则保持 EXECUTING 并停止 scheduler，避免双派；已确认退出才 `EXECUTING→FAILED`，标 manual_required | 否 | 等身份核验/brain；host 退出 |
| receipt 缺失、格式无效、工单/run 不匹配 | `EXECUTING→FAILED`，保存 receipt digest/分类证据 | 可按相同原单最多 2 次；不得把无效回执当 PASS | 两次后 BLOCKED；每次 pump 返回 |
| receipt id 相同但 digest 不同 | 状态不变，写冲突事件 | 否 | 立即 `IDEMPOTENCY_CONFLICT`，停人 |
| 派发器在创建 worker 前失败 | task 仍 QUEUED；effect attempt + due 持久化 | 最多 2 次 | 第 3 次失败调用 StateMachine 的未来受控方法 `block_unrunnable()` 转 BLOCKED |
| 派发器返回容量/锁忙 | 状态不变，不计失败 attempt | 不称为重试；等待资源事件 | 每轮立即返回，host 阻塞 wait |
| AUDIT FAIL | `AUDIT→FAILED` | retryCount<2 可回 QUEUED；否则 BLOCKED | 两次后停人 |
| BLOCKED | 保持 BLOCKED | 自动重试禁止 | 仅 human/brain 可释放 |

`block_unrunnable()` 是后续正式阶段对 `StateMachine` 的窄扩展：只接受 `source=QUEUED`、持久 effect attempts 已达到 3、actor 为 queue-engine 且 evidence 指向同 revision 时转 BLOCKED。它复用同一 `QueueState.BLOCKED`、同一事件格式，不允许调用者直接写 `task['state']`，也不新增状态枚举。该缺口必须先有单测再接正式派发。

### 幂等键与“不重复已完成外部副作用”

| 动作 | 幂等键 | 恢复语义 |
|---|---|---|
| 派发 | `dispatch:<task_id>:<source_revision>` | 已有 run identity 或存活 session 时不再 spawn；只 reconcile。 |
| receipt | `receipt:<run_id>:<receipt_id>` + digest | 同 digest no-op；不同 digest 冲突停人。 |
| 审计请求 | `audit:<task_id>:<run_id>` | 请求已落盘则不再创建第二审计会话。 |
| projection | `projection:<revision>` | 已生成同 revision 镜像则不重写。 |
| 外部效果 | `effect:<task_id>:<effect_kind>:<semantic_id>` | handler 前查完成 receipt；已完成则只重放本地状态，不再次调用外部操作。 |

崩溃恢复顺序固定为：读取 run identity → 核对 PID+创建身份 → 读取 done/final/receipt → 查 effect 完成记录 → 只补本地尚未提交的状态。任何一步无法证明外部操作未完成，都不重做外部操作，标 `manual_required` 并停人。

同一回执连续投递两次的实际夹具输出（指定解释器、纯内存）：

```text
FIRST={"accepted":true,"receipt_count":1,"state":"AUDIT"}
SECOND={"accepted":false,"receipt_count":1,"state":"AUDIT"}
IDEMPOTENCY_ASSERT=PASS
```

两次后的记录数为 1，状态与第一次后完全相同。

### 无 run 的 AUDIT 名额兜底

判定流程只影响“是否占 audit 名额”，不改 task 的 AUDIT 状态：

1. 有可核验 run：优先取 run `done.finished_at` 或进入 AUDIT 的 transition event 时间，算 `wait_seconds`。
2. 无 run：依次取正式记录的 `audit_started_at`、`dispatched_at`、`updated_at`；必须是可解析且不晚于 now 的带时区时间。
3. 算出时间：返回 `{valid:true,counted:true,wait_seconds:<非空>}`；再按配置的 audit age 上限决定是否继续占位。
4. 所有时间缺失/无效：在 scheduler journal 写诊断 `{valid:false,counted:false,wait_seconds:null,reason:'missing_time_evidence'}`，该项不计名额；不得猜时长，也不得永久占位。
5. journal 的诊断不是 task state；task 仍是 `QueueState.AUDIT`，等待独立复核/人工修复证据。

实际构造的两个“无 run AUDIT”夹具输出：

```text
AUDIT_NO_RUN_WITH_TIME={"valid":true,"counted":true,"wait_seconds":3600,"reason":null}
AUDIT_NO_RUN_WITHOUT_TIME={"valid":false,"counted":false,"wait_seconds":null,"reason":"missing_time_evidence"}
AUDIT_HOLD_ASSERT=PASS
```

因此任一无 run AUDIT 都满足二选一：有非空等待时长，或被标为无效持有且不计名额。

### 主脑显式介入入口

主脑仅可一次性调用 `select_next(..., override_task_id=<id>)` 覆盖默认优先顺序。默认值始终为 `None`，服务配置中不得保存永久 override。override 必须：

- task 当前为 QUEUED；
- 仍通过同一个 `dependency_gate()`、容量、pause、revision、卡版本与幂等门；
- 在 event 中记录 `actor=brain`、原因和被覆盖的默认候选；
- 不得覆盖 BLOCKED 人工释放、AUDIT PASS、Owner 冻结或发布门。

任一条件失败，返回对应结果码且不退而选择别的 task；主脑 override 不是绕门指令。

### Gate T3 结论

- 每个正常/异常分支在本轮 `return`、host `wait` 或 host `exit` 结束；无无界空转。
- 派发与任务失败均有持久次数上限；BLOCKED 不自动释放。
- 无 run AUDIT 的时长/无效持有二选一断言已实跑通过。
- receipt 两次投递的计数与状态幂等断言已实跑通过。

**Gate T3：PASS。**

## T4 · PoC 证据与分阶段落地计划

### PoC 边界

- 实现：`tasks/queue_engine/auto_relay_poc.py`；只导入正式 `QueueState`，不定义状态枚举。
- 测试：`scripts/tests/test_auto_relay_poc.py`；所有状态文件由 `tmp_path` 提供。
- 无 `subprocess`、socket、HTTP、provider SDK、Codex 调用、共享锁、开机自启或 watchdog 接线。
- `tasks/queue_engine/__init__.py`、`cli.py`、`dispatcher.py`、`run_worker.py`、`scripts/dispatch-work-order.py` 和正式启动路径均未 import PoC。
- PoC 的 success outcome 表示夹具已经提供执行、自检和审计通过事实；它不模拟真实审计主体，也不把自检冒充审计。

### 测试与反向验证

定向测试（最终代码）：

```text
> H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest scripts/tests/test_auto_relay_poc.py -o addopts= -p no:cacheprovider -q
......                                                                   [100%]
6 passed in 0.10s
exit=0
```

全量 `scripts/tests` 回归（基线 104，本次最终为 110）：

```text
> H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest scripts/tests -o addopts= -p no:cacheprovider -q
........................................................................ [ 65%]
......................................                                   [100%]
110 passed in 7.34s
exit=0
```

反向验证：临时在 `run_until_wait()` 成功完成第一单后直接 return，禁用下一次选单；仅运行正常接力用例，测试如期失败：

```text
FAILED scripts/tests/test_auto_relay_poc.py::test_normal_relay_completes_first_then_automatically_dispatches_dependent_next
states: first=COMPLETED, second=QUEUED
dispatch_order: ['first'] != ['first', 'second']
receipt_count: 1 != 2
1 failed in 0.37s
exit=1
```

恢复该临时改动后，定向 `6 passed`、全量 `110 passed`，exit 均为 0。反向改动未保留。

物理隔离 grep：

```text
> rg -n 'auto_relay_poc' tasks/queue_engine scripts src -g '*.py' \
    -g '!tasks/queue_engine/auto_relay_poc.py' \
    -g '!scripts/tests/test_auto_relay_poc.py'
FORMAL_IMPORT_MATCHES=0
```

### 分阶段落地计划

| 阶段 | 写入与行为 | 可机检 Gate | 回滚 | 存量隔离 |
|---|---|---|---|---|
| P0 影子选单 | 新增正式 `auto_relay.py` 的只读 `pump_once(dry_run=True)`；读取既有快照，输出候选/依赖/容量差异，不派发、不写状态。 | 1) 全量旧测试 + 新影子测试绿；2) 固定历史快照上，legacy/queue_engine 差异都有原因；3) `git diff -- queue-status.json` 为空；4) 正式入口仍无 service install。 | 删除/禁用影子命令即可；无业务写入可恢复。 | 默认所有存量单只读；只有测试夹具参与。 |
| P1 域能力补齐 | 新增 durable effect/receipt/scheduler journal；给 `StateMachine` 增加窄 `block_unrunnable()`；加入 revision CAS 与无 run AUDIT holder 判定。仍不接真实 Codex。 | 1) generation CAS、receipt 双投、三次派发失败→BLOCKED、BLOCKED 非 human/brain 拒绝；2) 崩溃恢复不重复 effect；3) 状态集合严格等于现有八态。 | feature flag 关闭 journal 消费；保留 append-only 证据；回退到 P0 只读。 | 仅带 `scheduler_enabled=true` 且在迁移清单登记的测试单可写；该布尔字段不是状态。 |
| P2 单项目显式启用 | 将老链的真实 Codex/run 监督封装为 executor adapter；停用其 `state()` 写权；启用唯一 projection writer。先在一个独立测试项目/工单手工 start，不自启。 | 1) 一单一进程、项目≤1/全局≤3/审计≤1（或当前批准上限）实测；2) kill/restart 后无重复 run/receipt/外部效果；3) queue-status 只有 projection writer；4) 正反依赖与名额夹具绿。 | stop 精确 lease，关闭 feature flag，恢复老链人工单次派发；journal 不删除。 | 非迁移清单工单继续老链；禁止同时有两个 writer。 |
| P3 常驻服务推广 | 独立工单批准后才安装无窗 service/计划任务；服务只 host 同一模块，加入 health/lease/last-pump 告警，再逐项目放量。 | 1) 24h soak 无空转/重复派发；2) stop/restart/parent_lost/暂停/超时演练全绿；3) 审计与 Owner 门未被越过；4) 进程窗口数 0；5) 禁用服务后老链回退演练成功。 | 先 stop lease，再禁用自启/feature flag，回 P2 手工启动或老链单次派发；不回滚已接受业务事实。 | 每项目单独 allowlist 与 revision；未迁移/历史缺证据单保持人工或标 unverifiable。 |

每阶段都先在干净提交/隔离夹具验收，随后独立审计；P2/P3 是后续独立工单，不在本单实施。

### 已知限制

1. PoC 是概念级：没有真实进程身份、共享工程锁、Codex、审计会话、projection writer 或 service lease。
2. PoC 为演示三次派发失败后 BLOCKED，内部记录 retry count；正式实现必须先按 P1 把受控 `block_unrunnable()` 落到 `StateMachine`，不得照搬 PoC 的直接赋值。
3. 当前老链 `audit_slot_holders()` 对缺时间记录仍 fail-closed 占位；本单只设计并在 PoC 验证新规则，没有改受保护的 `dispatch-work-order.py`。
4. 当前工作进程由派发器把本单 `queue-status.json` 从 pending 改为 executing；本单实现未写该文件，且提交路径明确排除它。最终状态仍由外层派发器在本执行进程退出后回写。
5. 开源替代：已审阅仓内 MIT dsh 原型并复用其 pass/effect/outbox 概念；硬边界禁止引入其 Node/TS 运行时，PoC 仅用 Python 标准库与本地 `QueueState`，未新增第三方依赖。

**Gate T4：PASS。**
