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

- run 目录：无（T2 Gate 阻塞，未进入 T3/T4；未启动真实 Codex、未创建真实派发 run）。
- 改动文件：`tasks/queue_engine/relay.py`、`tasks/tests/test_relay.py`、本回执。未创建 `scripts/relay-loop.py`、`relay-policy.json`、`relay-state.json`。
- 三重与门证据：`tasks/queue_engine/relay.py:170-174`：`policy.real_dispatch_enabled is True` + `execute_requested is True` + `order in policy.eligible_orders`，缺一抛 `RelayContractError("real dispatch disabled")`。对应单测：`test_real_dispatch_requires_policy_execute_and_whitelist_triple_gate`（三种缺门参数化）、`test_precheck_not_ready_never_calls_execute`、`test_same_order_is_not_dispatched_twice_in_one_tick`。
- dry-run 证据：仅完成 T1 夹具 dry-run 单测 `test_dry_run_starts_no_subprocess_and_writes_no_relay_state`（子进程计数 0，`relay-state.json` 不存在）。按顺序门禁未进入 T3，未运行真实队列 `--once --dry-run`。`queue-status.json` 开工前与阻塞时 SHA256 均为 `850D11CA9B0C7CB7565E70611943359385D8D8E3FDC9BD8D03DD8122B5469050`，本次字节未变。
- 夹具 E2E：未执行；该项属于 T4，T2 Gate 未全绿后禁止进入。
- 无窗实测：未执行；该项属于 T3，T2 Gate 未全绿后禁止进入。
- pytest 结果：开工基线原始输出与逐 T 输出如下；T4 全量回归未执行。

  ```text
  COMMAND: H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest tasks/tests -o addopts= -p no:cacheprovider -q
  ................................................................ [ 90%]
  .......                                                                  [100%]
  71 passed, 8 subtests passed in 12.60s

  COMMAND: H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest scripts/tests -o addopts= -p no:cacheprovider -q
  ........................................................................ [ 62%]
  ............................................                             [100%]
  116 passed in 6.67s

  Gate T0: 13 passed in 0.05s
  Gate T1: 25 passed in 0.21s
  Gate T2 behavior rerun:
  ...............................                                          [100%]
  31 passed in 0.65s
  ```

- 已知限制 / unverifiable：**阻塞于 Gate T2，未自判通过。** 工单要求命令 `git diff --stat HEAD -- tasks/queue/queue-status.json` 输出为空；实际原始输出为：

  ```text
  COMMAND: git diff --stat HEAD -- tasks/queue/queue-status.json
   tasks/queue/queue-status.json | 10 ++++++++++
   1 file changed, 10 insertions(+)

  COMMAND: git diff --numstat HEAD -- tasks/queue/queue-status.json
  10      0       tasks/queue/queue-status.json
  ```

  该差异在本单开工前已存在，且开工前/阻塞时 SHA256 相同；为保护他人/既有工作，本执行端未还原、暂存、提交或改写它。`dispatch-work-order.py` / `validate_work_order.py` / `audit-work-order.py` / `render-queue-views.py` 的保护路径 diff-stat 输出为空。缺少的裁决：由派发器决定先由原改动所有者收口 `queue-status.json`，或明确修订 Gate 为“相对开工哈希字节未变”后重派。本次未提交不完整实现、未启用计划任务、未打 tag。DeepSeek 硬门复审不在本执行单权限内。
