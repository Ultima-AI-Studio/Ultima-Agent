# Codex 工单 · 0042 自动接力接入正式派发链路

> 版本：v1.0 ｜ 状态：可开工 ｜ 适用工具：Codex
> 链路：`wo-ultimaagent-20261111-0042`
> 执行端：Codex（独立任务通道，主脑不参与判据定夺）
> 前置：0041 已冻结（`c2ac1a2e`，硬门复审 `hardgate-20261111T072551Z` 四门 PASS）；0040 PoC 已提交 `a8821457`
> 方案依据：`docs/plans/plan-ultimaagent-auto-relay-landing-20261111.md`
> 锁定 revision：`bc914eb09573d246636e40213876bfbe2637c265`
> 工作目录锁定：`H:\UltimaAI\UltimaAgent`
> 用法：按 T0→T4 顺序执行，每 T 的 Gate 全绿再进下一条，禁止跳序。

---

## 0. 本单定位

本单只做一件事：把已在夹具上验证过的接力零件（0040 PoC + 0041 受控状态门）接进**真实派发链路**，使「上一单完成 → 取下一单 → 派发」由常驻进程自动跑起来，且**默认不可能真派**。

本单**不**改 `dispatch-work-order.py` 的契约、**不**写 `queue-status.json` 的状态、**不**新建第二套状态枚举。Relay 只读判定 + 委派派发；状态变更仍全部由既有派发器与门禁负责。

---

## 1. 范围冻结

**本阶段只做**

1. 新建 `tasks/queue_engine/relay.py`：queue-status 状态↔`QueueState` 单向映射、候选选择、停止理由判定、有界泵、幂等状态读写、委派 `dispatch-work-order.py` 子进程。
2. 新建 `scripts/relay-loop.py`：常驻入口、`--start` / `--stop` / `--status` / `--once` / `--dry-run` / `--execute` 开关。
3. 新建 `tasks/queue/relay-policy.json`（策略：白名单/依赖/配额/真派开关，默认空与 false）与 `tasks/queue/relay-state.json`（运行状态）。
4. 新建 `tasks/tests/test_relay.py`：映射、门禁判定、幂等、委派预检、真派不可达四类用例。
5. 夹具端到端：假 Codex 桩 + 临时队列根，跑通「完成→取下一单→派」。

**本阶段不做（Non-goals）**

1. 不改 `scripts/dispatch-work-order.py`、`scripts/validate_work_order.py`、`scripts/audit-work-order.py`、`scripts/render-queue-views.py` 的任何行为与参数。
2. 不改 `queue-status.json` 的任何业务记录；不在其记录上加字段。
3. 不新建第二套状态枚举或状态权威；不把 queue-status 迁进 `tasks/tasks.json`。
4. 不在真实 Codex 上跑任何真实派发；真实队列只允许 dry-run。
5. 不启用计划任务 `UltimaAgent-RelayLoop`（只交付脚本与说明，启用由 Owner 决定）。
6. 不联网、不装依赖、不 `git add -A`。

---

## 2. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `tasks/queue_engine/relay.py` + `tasks/tests/test_relay.py` | 7 值映射全覆盖、未知状态 fail-closed、白名单顺序优先，单测全绿 |
| T1 | `tasks/queue_engine/relay.py` + `tasks/tests/test_relay.py` | WIP/暂停/配额/无候选四类停止理由各自命中，dry-run 零子进程零状态写入 |
| T2 | `tasks/queue_engine/relay.py` + `tasks/tests/test_relay.py` | 预检未 ready 不真派、非 0 退出进退避、同单不重派、开关为 false 时真派分支不可达 |
| T3 | `scripts/relay-loop.py` + `tasks/tests/test_relay.py` | `--status` 可读、`--stop` 后 ≤1 间隔退出、实测 0 可见窗口 |
| T4 | 夹具 E2E + 本卡回执 | 夹具闭环成立、真实队列 dry-run 选中单号正确且 queue-status.json 字节未变 |

---

## 3. 任务明细

### T0 · 状态映射与候选选择

**文件**：`tasks/queue_engine/relay.py`、`tasks/tests/test_relay.py`

**写什么**：

1. 定义 `STATUS_TO_STATE` 映射表，覆盖 queue-status 全部 7 值：pending→QUEUED、executing→EXECUTING、audit→AUDIT、frozen→COMPLETED、closed→COMPLETED、blocked→BLOCKED、cancelled→CANCELLED；显式注释 `SELF_CHECK`/`FAILED`/`TERMINATED` 在真实队列无对应。
2. 实现 `to_state(raw: str) -> QueueState`，未知值抛 `RelayContractError`，**不得猜测或回落默认值**。
3. 实现 `orders_in_state(records, state)` 与 `select_candidate(records, policy) -> Candidate | None`：候选必须状态 pending、单号在 `policy.eligible_orders`、依赖（`policy.dependsOn`）全部为 frozen/closed；**按 eligible_orders 声明顺序取第一个**，不按单号数值排序。
4. 实现 `dependency_ready(order, records, policy) -> tuple[bool, str]`，依赖缺失声明、依赖未完成、依赖被 blocked 三种情形分别返回不同原因串。
5. `tasks/tests/test_relay.py` 用夹具记录覆盖上述全部分支。

**验收（Gate T0）**：

- 命令 `& H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest tasks/tests/test_relay.py -o addopts= -p no:cacheprovider -q` 全绿，贴完整输出。
- 用例中含未知状态（如 `"weird"`）断言抛 `RelayContractError`，贴该用例名与断言。
- 用例证明白名单顺序优先：构造两条 pending 且编号大者在白名单首位，断言选中者是它，贴输出。

**禁止**：不得对未知状态回落默认值；不得按编号/字符串排序替代白名单顺序；不得在本 T 引入任何 IO 或子进程。

---

### T1 · 只读泵与 dry-run

**文件**：`tasks/queue_engine/relay.py`、`tasks/tests/test_relay.py`

**写什么**：

1. 实现 `QueueStatusView`：只读加载 `tasks/queue/queue-status.json`（纯 LF、无 BOM），提供 `records()` 与本项目记录过滤；**只读，不提供写方法**。
2. 实现 `RelayGate.evaluate(view, policy, state, now) -> GateResult`，按方案 §4 的 10 条规则顺序判定，返回 `stop_reason`（取值为 `PAUSED`/`WIP_BUSY`/`QUOTA_EXHAUSTED`/`NO_CANDIDATE`/`DEPENDENCY_NOT_READY`/`HALTED`/`READY` 之一）与 `reason` 文本。
3. 暂停判定读两个标记：`tasks/.pause-dispatch`、`_shared/.pause-dispatch`（后者路径按 `scripts/dispatch-work-order.py` 的 `_resolve_shared_queue` 同口径解析）。
4. 配额判定用 `state.day_key`（`YYYY-MM-DD`，UTC）与 `actions_today`；跨日自动归零。
5. 实现 `RelayPump.pump_once(max_actions)`：有界，最多 `max_actions` 次；`max_actions` 非正整数抛 `RelayContractError`。
6. dry-run 分支：只返回 `{"stop_reason","candidate","would_dispatch","reason"}`，**不启动任何子进程、不写 relay-state.json**。

**验收（Gate T1）**：

- `pytest tasks/tests/test_relay.py` 全绿，贴输出，确认四类停止理由 `PAUSED`/`WIP_BUSY`/`QUOTA_EXHAUSTED`/`NO_CANDIDATE` 各有独立用例。
- 用例断言 dry-run 期间 `subprocess.Popen` 未被调用（monkeypatch 计数为 0），且 `relay-state.json` 未生成，贴断言输出。
- 用例断言存在 executing 记录时 `stop_reason == "WIP_BUSY"`，存在 audit 记录时同样 `WIP_BUSY`，贴输出。

**禁止**：不得在 `QueueStatusView` 上暴露任何写方法；不得把 dry-run 实现成「先派再判」；不得用 `json.dump` 整体重写 queue-status。

---

### T2 · 委派正式派发器

**文件**：`tasks/queue_engine/relay.py`、`tasks/tests/test_relay.py`

**写什么**：

1. 实现 `DispatcherClient.precheck(order) -> DispatchOutcome`：以**不带 `--execute`** 的方式调 `scripts/dispatch-work-order.py`，解析 stdout JSON 的 `ready` 与拒绝原因。
2. 实现 `DispatcherClient.execute(order) -> DispatchOutcome`：带 `--execute`、`--max-runtime-seconds`（取自 policy，默认 1800）调用；子进程用 `creationflags=CREATE_NO_WINDOW|DETACHED_PROCESS`（复用 `dispatcher.BACKGROUND_CREATION_FLAGS`），stdout/stderr 落 run 目录外的独立日志文件，不打印到控制台。
3. 真派可达性必须**三重与门**：`policy.real_dispatch_enabled is True`、调用方显式 `execute=True`、单号在 `eligible_orders`。任一为假时，`execute()` 直接抛 `RelayContractError("real dispatch disabled")`，不得静默降级为预检。
4. 实现退避与不重派：同一 `order` 在一个 tick 内最多一次；失败写 `state.last_failure = {order, code, reason, ts}`，连续失败达 `policy.max_consecutive_failures`（默认 2）置 `halted=true` 并停泵。
5. 幂等落盘：`RelayStateStore.save()` 用临时文件 + `os.fsync` + `os.replace`，纯 LF、无 BOM。
6. `tasks/tests/test_relay.py` 用假派发器（临时脚本或 `sys.executable -c` 桩）覆盖：预检 ready=false 不真派、真派 exit 非 0 进退避、开关 false 抛错、同单不重派。

**验收（Gate T2）**：

- `pytest tasks/tests/test_relay.py` 全绿，贴输出。
- 用例断言 `real_dispatch_enabled=false` + `execute=True` 时被拒绝并抛 `RelayContractError`，贴异常断言与 pytest 输出。
- 用例断言预检返回 `ready=false` 时桩计数为 0（未发生 `--execute` 调用），贴计数输出。
- 零写入证据以**派发快照为基线**（不以相对 HEAD diff 为准，派发器自身会写该文件）：`tasks/queue/queue-status.json` 的 sha256 与 run 目录 `queue-status-before-executing.json` 对应记录逐项比对，业务记录（除本单自身 state 字段外）输出一致；并断言 `QueueStatusView` 无任何写方法（对写入口调用抛 `AttributeError`），贴两次 sha256 与断言输出。

**禁止**：不得修改 `dispatch-work-order.py` 一行；不得在 relay 内自己起 Codex；不得在开关关闭时「降级真派」或「悄悄跳过预检」。

---

### T3 · 常驻入口与启停

**文件**：`scripts/relay-loop.py`、`tasks/tests/test_relay.py`

**写什么**：

1. `scripts/relay-loop.py` 提供子命令：`--once`（跑一拍）、`--dry-run`（默认）、`--execute`（配合 policy 开关）、`--status`（只读打印 relay-state.json）、`--stop`（写停止标记）。
2. 单实例锁 `%TEMP%\ultima-relay.pid`，用 `dispatcher.process_identity` 比对进程创建身份，不用 pid 存在性。
3. `run(stop_event, interval_s)` 有界节拍循环（复用 `RelayPump`），间隔默认 30s，`--stop` 后 ≤1 个间隔内退出。
4. 脚本头部注释写明：由计划任务 `UltimaAgent-RelayLoop` 以 venv `pythonw.exe` 无窗拉起，默认不启用。
5. 交付一份不启用的计划任务注册说明（写在 `docs/plans/` 方案 §6 已述，本 T 只在脚本 `--help` 里给出命令串）。

**验收（Gate T3）**：

- `& ...python.exe scripts/relay-loop.py --status` 输出 JSON（`halted/actions_today/last_order`），贴输出。
- `--once --dry-run` 在真实队列上输出 `stop_reason` 与 `candidate`，贴输出；并在 tick 前后各算一次 `sha256(tasks/queue/queue-status.json)`，两次输出必须一致（零写入以基线快照比对为准，不以相对 HEAD diff 为准）。
- 用项目真实 `WindowMonitor`（WinEvent hook，`tasks/tests` 既有实现）实测入口进程可见窗口数，输出为 0 才通过，贴 8 次采样结果。
- `pytest tasks/tests/test_relay.py` 含 `--stop` 退出用例，全绿，贴输出。

**禁止**：不得前台弹窗启动；不得用 `sys._base_executable` 绕过；不得启用计划任务。

---

### T4 · 夹具端到端与真实 dry-run

**文件**：夹具（`tasks/tests` 内临时根）、本卡回执

**写什么**：

1. 夹具 E2E：临时队列根（`queue-status.json` 两条 pending：A 无依赖、B 依赖 A）+ 假派发器桩，跑「A 完成 → 下一 tick 选中 B → 派 B」，断言派发顺序为 `["A","B"]`、B 的预检与真派各发生一次。
2. 夹具 E2E-2：把 A 置为 blocked，断言 B 不派且 `stop_reason=="DEPENDENCY_NOT_READY"`。
3. 真实队列 dry-run：在 `tasks/queue/queue-status.json` 上跑 `--once --dry-run`，记录它选中的单号与理由（此步只读）。
4. 回填本卡回执段。

**验收（Gate T4）**：

- 夹具 E2E 两用例进 `tasks/tests/test_relay.py` 并全绿，贴输出与派发顺序断言。
- 真实 dry-run 输出贴出（含 `stop_reason`、`candidate`、`reason`）；若 `NO_CANDIDATE` 或 `WIP_BUSY` 属正常，须写明当前真实队列的实际状态（存在 0041 frozen、0037/0038/0040 blocked）。
- 全量回归 `pytest tasks/tests` 与 `pytest scripts/tests` 通过数只增不减（基线 71 / 116），贴两段原始输出。
- `git status --porcelain -- tasks/queue/queue-status.json` 输出为空，贴命令与输出。

**禁止**：不得在真实 Codex 上派任何一单；不得为让 dry-run「有候选」而改真实队列记录；不得删除或弱化既有断言。

---

## 4. 总验收

1. Relay 只读判定 + 委派派发，全仓写 `queue-status.json` 状态的点未增加（仍为 `dispatch-work-order.py` 的 `state()`）。
2. 真派三重与门齐备，默认（空白名单 + 开关 false）下真派分支不可达。
3. 未知状态 fail-closed；映射单向，无反向写回。
4. 夹具 E2E 与两类停止理由成立；真实队列 dry-run 零写入。
5. 无窗实测 0 可见窗口；`--stop` 可退出；单实例锁生效。
6. 全量回归只增不减；提交显式列路径、中文信息，不 `git add -A`。

---

## 5. 禁止清单

1. 不得改 `dispatch-work-order.py` / `validate_work_order.py` / `audit-work-order.py` / `render-queue-views.py`。
2. 不得改 `queue-status.json` 任何业务记录或加字段。
3. 不得新增第二套状态枚举或第二状态权威。
4. 不得在 relay 内直接写任何 task 的 state。
5. 不得在真实 Codex 上跑真实派发；不得启用计划任务。
6. 不得联网装依赖；不得 `git add -A`。

---

## 回执（执行端填写）

- run 目录：`tasks/queue/runs/wo-ultimaagent-20261111-0042-20261111T080654133464Z`。本轮复用该二轮派发 run 的 `queue-status-before-executing.json`；未启动真实 Codex 子派发、未创建 relay 真派 run。
- 改动文件：`tasks/queue_engine/relay.py`、`scripts/relay-loop.py`、`tasks/queue/relay-policy.json`、`tasks/queue/relay-state.json`、`tasks/tests/test_relay.py`、本工单卡回执。四个保护脚本和 `tasks/queue/queue-status.json` 均未由本实现改写。
- 三重与门证据：`tasks/queue_engine/relay.py:170-174` 依次要求 `policy.real_dispatch_enabled is True`、`execute_requested is True`、`order in policy.eligible_orders`，缺一抛 `RelayContractError("real dispatch disabled")`。对应单测：`test_real_dispatch_requires_policy_execute_and_whitelist_triple_gate`（false 开关 / 未显式 execute / 不在白名单三种缺门参数化）、`test_precheck_not_ready_never_calls_execute`、`test_same_order_is_not_dispatched_twice_in_one_tick`。默认 `relay-policy.json` 为 `eligible_orders: []` 且 `real_dispatch_enabled: false`。
- dry-run 证据：`test_dry_run_starts_no_subprocess_and_writes_no_relay_state` 断言 `Popen` 调用计数 0、`relay-state.json` 不存在；真实队列两次 `--once --dry-run` 均返回 `WIP_BUSY` / `candidate: null`，因为本单 0042 正在 `executing`。实际相关记录：0041=`frozen`，0037/0038/0040=`blocked`，0042=`executing`。两次真实 dry-run 前后当前文件 SHA256 均为 `043DBD83F7A9AD11F3A4B5C1BBFEEF070D0FA19CC0932C4FA55D818B96A6157C`。
- 夹具 E2E：`test_fixture_e2e_dispatches_a_then_dependent_b` 在临时队列根 + 假派发器桩上断言 execute 顺序严格为 `["A", "B"]`，B 的 precheck / execute 各 1 次；`test_fixture_e2e_blocks_b_when_a_is_blocked` 断言 B 零派发且 `stop_reason == "DEPENDENCY_NOT_READY"`。夹具桩只修改 `tmp_path` 内夹具队列，生产 relay 不写 task state。
- 无窗实测：仓内真实 `WindowMonitor` 对 `pythonw.exe scripts/relay-loop.py --start --dry-run --interval-s 0.10` 做 8 次独立采样；每次用 `scripts/relay-loop.py --stop` 收口，8 次 `exit_code=0`、`stop_exit=0`、`visible_window_count=0`，未启用计划任务。
- 已知限制：依赖信息仍须由 Owner 在策略文件 `dependsOn` 显式声明；默认空白名单不会选择任何自动候选；真实 Codex execute 按工单禁止未实测，真派 E2E 仅用假派发器夹具；计划任务只在 `--help` 给出注册示例，未注册/未启用；未打 tag（按本单要求留给主脑验收后处理）。DeepSeek 独立硬门复审不在本执行单权限内。

### 新 Gate：派发快照基线对账

旧的相对 HEAD 判据已按二轮派发说明废止。本轮原始输出如下：

```text
RUN=H:\UltimaAI\UltimaAgent\tasks\queue\runs\wo-ultimaagent-20261111-0042-20261111T080654133464Z
4477279A76716F291DF99C6FFC7983DCF3017423026814C9E7927DDA15957F52  H:\UltimaAI\UltimaAgent\tasks\queue\runs\wo-ultimaagent-20261111-0042-20261111T080654133464Z\queue-status-before-executing.json
043DBD83F7A9AD11F3A4B5C1BBFEEF070D0FA19CC0932C4FA55D818B96A6157C  H:\UltimaAI\UltimaAgent\tasks\queue\queue-status.json
OTHER_RECORDS_EXACT_JSON_EQUAL=True
state: BEFORE=<blocked> AFTER=<executing>
dispatched_at: BEFORE=<11/11/2026 15:43:59> AFTER=<11/11/2026 16:06:54>
note: BEFORE=<上一轮退出待复核> AFTER=<真实工单派发 wo-ultimaagent-20261111-0042-20261111T080654133464Z，一单一进程；尚未验收>
has_save= False
has_write= False
save_call= AttributeError 'QueueStatusView' object has no attribute 'save'
```

两份文件原始 SHA256 预期不同：快照在派发器把本单登记为 executing 前生成；结构化对账确认其余 162 条记录逐字序列化一致，仅本单的 `state/dispatched_at/note` 由本轮既有派发器更新。进入 relay 复核后的当前文件哈希在 T0–T4、两次真实 dry-run 与全量回归前后始终为 `043DBD...6157C`。`git status --porcelain -- tasks/queue/queue-status.json` 当前输出 ` M tasks/queue/queue-status.json`，仅作信息记录，不再用作 Gate，也未暂存/提交该文件。

### 逐 Gate 原始命令与输出

Gate T0：

```text
COMMAND: H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest tasks/tests/test_relay.py -o addopts= -p no:cacheprovider -q
...............................                                          [100%]
31 passed in 0.68s
PYTEST_EXIT=0
test_to_state_rejects_unknown_status_fail_closed:72-74
  with pytest.raises(RelayContractError, match="unknown queue-status state: 'weird'")
test_select_candidate_honors_whitelist_order_not_numeric_order:119
  larger_first = "wo-ultimaagent-20261111-0099"
  assert candidate.order == larger_first
```

Gate T1：

```text
COMMAND: H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest tasks/tests/test_relay.py -o addopts= -p no:cacheprovider -q
...............................                                          [100%]
31 passed in 0.68s
PYTEST_EXIT=0
test_gate_reports_paused_for_each_dispatch_marker:158
test_gate_reports_wip_busy_for_executing_and_audit:172
test_gate_reports_quota_exhausted:186
test_gate_reports_no_candidate:209
test_dry_run_starts_no_subprocess_and_writes_no_relay_state:219
  assert calls == 0
  assert not (tmp_path / "tasks" / "queue" / "relay-state.json").exists()
```

Gate T2（补齐无写入口固化断言后的最终结果）：

```text
COMMAND: H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest tasks/tests/test_relay.py -o addopts= -p no:cacheprovider -q
................................                                         [100%]
32 passed in 0.72s
PYTEST_EXIT=0
test_real_dispatch_requires_policy_execute_and_whitelist_triple_gate:415
test_precheck_not_ready_never_calls_execute:437
  assert log.read_text(encoding="utf-8").splitlines() == ["precheck"]
test_same_order_is_not_dispatched_twice_in_one_tick:523
  assert log.read_text(encoding="utf-8").splitlines() == ["precheck", "execute"]
test_queue_status_view_exposes_no_write_entrypoint:251
  with pytest.raises(AttributeError): view.save(None)
```

Gate T3：

```text
COMMAND: H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe scripts/relay-loop.py --status
{"actions_today": 0, "halted": false, "last_order": null}
STATUS_EXIT=0

COMMAND: H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe scripts/relay-loop.py --once --dry-run
{"candidate": null, "reason": "project has executing or audit work", "stop_reason": "WIP_BUSY", "would_dispatch": false}
ONCE_EXIT=0
SHA256_BEFORE=043DBD83F7A9AD11F3A4B5C1BBFEEF070D0FA19CC0932C4FA55D818B96A6157C
SHA256_AFTER =043DBD83F7A9AD11F3A4B5C1BBFEEF070D0FA19CC0932C4FA55D818B96A6157C
HASH_EQUAL=True

COMMAND: H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest tasks/tests/test_relay.py -o addopts= -p no:cacheprovider -q
..................................                                       [100%]
34 passed in 0.73s
PYTEST_EXIT=0
test_relay_loop_status_is_read_only_json:258
test_relay_loop_stop_exits_within_one_interval:276
```

8 次 `WindowMonitor` 原始采样：

```text
{"exit_code": 0, "monitor_samples": 3, "pid": 26336, "sample": 1, "stop_exit": 0, "visible_window_count": 0}
{"exit_code": 0, "monitor_samples": 3, "pid": 13296, "sample": 2, "stop_exit": 0, "visible_window_count": 0}
{"exit_code": 0, "monitor_samples": 3, "pid": 26412, "sample": 3, "stop_exit": 0, "visible_window_count": 0}
{"exit_code": 0, "monitor_samples": 3, "pid": 22276, "sample": 4, "stop_exit": 0, "visible_window_count": 0}
{"exit_code": 0, "monitor_samples": 3, "pid": 452, "sample": 5, "stop_exit": 0, "visible_window_count": 0}
{"exit_code": 0, "monitor_samples": 3, "pid": 24388, "sample": 6, "stop_exit": 0, "visible_window_count": 0}
{"exit_code": 0, "monitor_samples": 3, "pid": 11620, "sample": 7, "stop_exit": 0, "visible_window_count": 0}
{"exit_code": 0, "monitor_samples": 3, "pid": 23784, "sample": 8, "stop_exit": 0, "visible_window_count": 0}
{"result": "PASS", "runs": 8, "visible_windows_total": 0}
```

Gate T4：

```text
COMMAND: H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest tasks/tests/test_relay.py -o addopts= -p no:cacheprovider -q
....................................                                     [100%]
36 passed in 1.04s
PYTEST_EXIT=0
test_fixture_e2e_dispatches_a_then_dependent_b
  assert dispatch_order == ["A", "B"]
  assert events.count({"order": order_b, "mode": "precheck"}) == 1
  assert events.count({"order": order_b, "mode": "execute"}) == 1
test_fixture_e2e_blocks_b_when_a_is_blocked
  assert result["stop_reason"] == "DEPENDENCY_NOT_READY"
  assert not log.exists()

COMMAND: H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe scripts/relay-loop.py --once --dry-run
{"candidate": null, "reason": "project has executing or audit work", "stop_reason": "WIP_BUSY", "would_dispatch": false}
DRY_RUN_EXIT=0
SHA256_BEFORE=043DBD83F7A9AD11F3A4B5C1BBFEEF070D0FA19CC0932C4FA55D818B96A6157C
SHA256_AFTER =043DBD83F7A9AD11F3A4B5C1BBFEEF070D0FA19CC0932C4FA55D818B96A6157C
HASH_EQUAL=True
```

### 最终全量回归原始输出

```text
COMMAND: H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest tasks/tests -o addopts= -p no:cacheprovider -q
..................................................................... [ 64%]
......................................                              [100%]
107 passed, 8 subtests passed in 12.33s
TASKS_EXIT=0

COMMAND: H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest scripts/tests -o addopts= -p no:cacheprovider -q
........................................................................ [ 62%]
............................................                             [100%]
116 passed in 5.37s
SCRIPTS_EXIT=0
```

保护脚本原始检查：

```text
COMMAND: git diff --stat HEAD -- scripts/dispatch-work-order.py scripts/validate_work_order.py scripts/audit-work-order.py scripts/render-queue-views.py
OUTPUT: <empty>
```

---

## 4. 主脑独立验收与 DeepSeek 硬门复审（收口）

- 实现提交：`3407b2bc`（6 文件 1656 insertions；`scripts/relay-loop.py`、`tasks/queue_engine/relay.py`、`tasks/tests/test_relay.py`、`tasks/queue/relay-policy.json`、`tasks/queue/relay-state.json`、本卡回执段）

### 4.1 主脑独立验收（不采信实现方回执，全部实跑复核）

| 项 | 原始结果 |
|---|---|
| 保护文件 diff | `git diff --stat bc914eb0 3407b2bc -- <7 个保护文件>` → 空 |
| 全链路直接写 state | 硬门正则全 `tasks/queue_engine/*.py` + `scripts/relay-loop.py`：命中 1 处，`state_machine.py:95`（副本写入）；新增 `relay.py`/`relay-loop.py`/`test_relay.py` 均 0 |
| relay 写 queue-status | `relay.py` 11 处 `queue-status` 全为 docstring/注释/路径常量/异常文案；`relay-loop.py` 0 处；类体 `QueueStatusView` 只有读取方法 |
| 三重与门反向 | 三缺一（开关关 / 未显式 execute / 不在白名单）全部 `RelayContractError("real dispatch disabled")`；三条件全真才到达桩脚本 `ready=True code=0` |
| 真实队列零写入零派发 | `--once --dry-run` 与 `--once --execute` 均 `stop_reason=WIP_BUSY`、`would_dispatch=false`；`sha256(queue-status)` 前 `CB177ADD…` 后 `CB177ADD…` `IDENTICAL=True` |
| 无窗 | `pythonw --start --dry-run`，进程树 8 次独立采样全部 `visible_window_count=0`（monitor samples=107，observed_pids=[23992]）；`--stop` 后 13.92s（< interval 30s）退出 `rc=0` |
| 幂等 | 同内容连续两次 `RelayStateStore.save()` sha256 均为 `FF4A5A23…`；目录仅 `relay-state.json`、零临时残留；回读字段正确；`same_order_is_not_dispatched_twice_in_one_tick` + 退避/停机定向用例 `2 passed` |
| 全量回归 | `tasks/tests`：`107 passed, 8 subtests passed`（基线 71，只增不减）；`scripts/tests`：`116 passed`（与基线一致） |

证据目录：`tasks/queue/runs/wo-ultimaagent-20261111-0042/hardgate-20261111T083322Z/`（write-audit.md、reverse-check.txt、pytest-tasks.txt、pytest-scripts.txt）、`.../hardgate2-20261111T083624Z/`（grep-recheck.txt、acc1-env-clarification.md、audit.json）。

### 4.2 DeepSeek 硬门复审

- 首轮 `hardgate-20261111T083322Z`：`audit_passed=false`，ROUND1/ROUND2 判 `ACC-1 FAIL / ACC-2 PASS / ACC-3 PASS / ACC-4 PASS`。读原始判词确认：**FAIL 的唯一成因是证据缺料**——证据包未含 `execute()` 函数体、`relay-loop.py` argparse 表、`relay-policy.json` 出厂值，判词原文要求「supplying the execute body, the argparse table, and the policy file contents」。不是代码缺陷，判据未改、未削弱。
- 补齐证据后重跑 `hardgate2-20261111T083624Z`：`audit_passed=true`，ROUND1 与 ROUND2 **四门全 PASS**，实际模型 `deepseek-flash`，`integrity_errors=[]`，11 个证据对象逐一 `injected_bytes == attested_bytes`（单批全 visible、无截断）。
- ROUND2 判词要点（原文摘）：ACC-1 三条件在 `execute()` 体内 L168–174、抛错早于 `log_dir.mkdir`(L177) 与 `Popen`(L189)，policy 出厂 `false`/`[]`，无绕过关键词，唯一 `os.environ` 读 `GORCH_SHARED_QUEUE` 只喂暂停标记路径；ACC-2 全目录 1 处直接写 state、`QueueStatusView` 只有读取、`test_queue_status_view_exposes_no_write_entrypoint` 断言 `AttributeError`；ACC-3 `save()` 走同目录临时文件 + `fsync` + `os.replace`、`pump_once` 有 `attempted` 集返回 `SAME_ORDER_THIS_TICK`、失败达上限置 `halted=true`；ACC-4 8 次采样全 0 且一个间隔内退出。

### 4.3 队列收口

- `queue-status.json`：0042 `blocked` → `frozen`，`audit_passed=true`，`audit_run=hardgate2-20261111T083624Z`，`freeze_commit=3407b2bc`；写前校验无 BOM/纯 LF/163 条/唯一本单记录，写后复核一致，`git diff --numstat` 仅 6 增 6 删（只本单块）。
- 视图重渲染：`records: 163, distribution{frozen:113, blocked:23, cancelled:16, closed:2, audit:5, pending:4}`；`--check` → `{"differences": []}`。

### 4.4 已知限制（登记，不在本单修）

1. `DispatcherClient.execute()` 内部 `process.wait()` 同步等待派发器结束（上限 `max_runtime_seconds=1800`），因此**真派进行中常驻循环的一拍会被阻塞到该派发结束**，`--interval-s` 在派发期间不生效。本单接受该行为（隔离验证阶段真派默认关闭且未启用计划任务）；若要并发或多单连推，需另开单改成非阻塞等待或独立 worker。
2. `tasks/queue/relay-state.json` 作为运行态被纳入版本控制：真实运行后内容会变化，产生工作区脏文件。本单保留初始值入库以便审计可复现；是否改为 gitignore 由 Owner 决定。
3. 计划任务 `UltimaAgent-RelayLoop` **未启用**、`eligible_orders` 仍空、`real_dispatch_enabled=false`：真派链路虽已接通但默认全闭，首批白名单与启用时机待 Owner 决策。
