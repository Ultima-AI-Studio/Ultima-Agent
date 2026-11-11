# 方案 · 自动接力接入正式派发链路（2026-11-11）

> 状态：主脑已定方向，随工单 `wo-ultimaagent-20261111-0042` 落盘（G-PLAN-001）
> 关系：0038 出设计+PoC、0039 独立审计判 ACC-6 FAIL、0040/0041 已把状态门与依赖门修到受控（硬门复审四门 PASS）
> 本单做**最后一件事**：把已验证的接力零件接进**真实派发链路**
> 锁定 revision：`bc914eb09573d246636e40213876bfbe2637c265`
> 工作目录锁定：`H:\UltimaAI\UltimaAgent`

## 1. 现状事实（以代码为准，不凭文档反推）

| 事实 | 证据 |
|---|---|
| 真实派发唯一入口是 `scripts/dispatch-work-order.py --execute` | 它自己起 Codex 进程、写 run 目录、改 queue-status 状态、做 DoR/卡哈希/WIP/暂停标记复核 |
| 状态权威是 `tasks/queue/queue-status.json`（162 条） | `dispatch-work-order.py` 的 `registered()`/`state()` 读写它；`render-queue-views.py --check` 也以它为源 |
| `queue_engine` 的 `QueueStorage` 用的是另一份 `tasks/tasks.json` | `storage.py` 第 63 行 `index_path = root/"tasks.json"`；与 queue-status.json **不是同一权威** |
| `queue-status.json` 的记录字段只有 8 个 | project / work_order / state / audit_passed / dispatched_at / audit_run / freeze_commit / note —— **没有 dependsOn、没有 priority** |
| queue-status 的 state 有 7 值，QueueState 有 8 值，且不一一对应 | queue-status: pending/executing/audit/frozen/closed/blocked/cancelled；QueueState: QUEUED/EXECUTING/SELF-CHECK/AUDIT/COMPLETED/FAILED/BLOCKED/CANCELLED |
| 依赖关系在真实队列里**没有机器可读来源** | 工单卡正文有前置描述，但不是结构化字段；因此依赖门在真实队列上当前无输入 |
| 单工单内部已全自动，缺的只是「上一单完成 → 取下一单 → 派发」的常驻循环 | 0038 结论；仓内无任何 auto-next 常驻进程 |

## 2. 核心设计决策（三条，各自带取舍）

### 决策 1：Relay 只读决策、委派派发，**自己不写任何状态**

Relay 不碰 `queue-status.json` 的 state，状态变更 100% 仍由 `dispatch-work-order.py` 负责（它内部走既有门禁与 `state()` 落盘）。

- 取舍 A（采纳）：relay 只读 + 调派发器。好处是「泛化接管」不存在——全链路写 state 的点没有增加一个，0041 的硬门（唯一受控写入点）在 relay 上继续成立，复审可机检。
- 取舍 B（否决）：relay 自己写 queue-status 状态。坏处是立刻多出第二个写状态的地方，把刚修好的受控门重新打开。
- 取舍 C（否决）：把 queue-status 迁进 queue_engine 的 tasks.json。这是 162 条真实记录的权威迁移，风险与本单目标无关，且会造出第二权威并存期。

### 决策 2：状态映射单向、显式、只做判定输入，且不可逆写回

Relay 读到 queue-status 的小写状态后映射为 `QueueState` 只用于**判定**（是否可派、是否在跑），永远不反向写回。

| queue-status | QueueState | 用途 |
|---|---|---|
| pending | QUEUED | 可派候选 |
| executing | EXECUTING | 占 WIP，禁派 |
| audit | AUDIT | 占审计名额，禁派 |
| frozen | COMPLETED | 已闭环，可作为依赖完成 |
| closed | COMPLETED | 已闭环，可作为依赖完成 |
| blocked | BLOCKED | 需人工，不自动派 |
| cancelled | CANCELLED | 终态，跳过 |

`SELF-CHECK` 与 `FAILED` 在真实队列没有对应值：映射表**显式声明缺失**，遇到未知值即 fail-closed（停止本轮、记事件、不改任何状态），不猜。

### 决策 3：依赖与配额放**策略文件**，不放状态权威

新建 `tasks/queue/relay-policy.json`，它是**策略**（Owner 可改），不是状态。内容：

- `eligible_orders`：白名单（只允许自动接力的单号；空 = 一个都不自动派，安全默认）
- `dependsOn`：按单号声明的依赖（补 queue-status 缺字段）
- `max_actions_per_tick`：单次拍数上限（默认 1）
- `max_actions_per_day`：当日累计上限（默认 2）
- `cooldown_s`：失败退避
- `real_dispatch_enabled`：真派开关（默认 false）

取舍：不往 queue-status.json 加字段（`storage.validate_index_record` 对多余字段是硬拒的，加字段会同时打破 render 与派发器），也不从工单卡正文正则抠依赖（不可靠、会假阳性）。

## 3. 落地形态

```
tasks/queue_engine/relay.py        # 正式模块：只读决策 + 委派 + 有界泵
scripts/relay-loop.py              # 常驻入口（无窗，计划任务拉起）
tasks/queue/relay-policy.json      # 策略（白名单/依赖/配额/真派开关）
tasks/queue/relay-state.json       # 幂等状态（原子写、单实例锁）
```

**不新建**第二个派发器、不新建第二套状态枚举、不改 `dispatch-work-order.py` 的契约（仅以子进程方式调用它）。

## 4. 运行规则（自动接力的全部触发条件）

一次 tick 依次判定，任一不满足即停（fail-closed，不做部分动作）：

1. `real_dispatch_enabled=false` 或未传 `--execute` → 只做 dry-run，输出「本应派哪一单」，**不调派发器**。
2. 暂停标记 `tasks/.pause-dispatch` 或 `_shared/.pause-dispatch` 存在 → 停。
3. 本项目登记存在 `executing` 或 `audit` → 停（WIP ≤1，不抢名额）。
4. 当日已派数 ≥ `max_actions_per_day` → 停。
5. 候选 = 状态为 pending、在白名单、依赖全部为 frozen/closed。**按显式白名单顺序**取第一个，不按编号猜优先级（queue-status 无 priority 字段）。
6. 无候选 → 停。
7. 候选通过后：先调 `dispatch-work-order.py`（**不带 --execute**）做预检；预检 `ready=true` 才允许下一步。
8. 真派（仅当开关与 `--execute` 同时为真）：调 `dispatch-work-order.py --execute`，一单一进程，带 `--max-runtime-seconds`。
9. 派发器返回非 0 / 拒绝原因 → 记事件、进入退避，**不重试同一单**（换单由下一次 tick 重新判定）。
10. 连续失败达阈值 → relay 自动停并写 `relay-state.json` 的 `halted=true` 与原因（需人工清除才恢复）。

## 5. 幂等与崩溃恢复

- 单实例：`%TEMP%\ultima-relay.pid` + 进程创建身份比对（复用 `dispatcher.process_identity`，不用 pid 存在性判定）。
- 同一单号在同一 tick 内最多派一次；`relay-state.json` 记 `last_order` / `last_run` / `attempts` / `day_key` / `actions_today`。
- 停机重启后：若 `last_order` 在 queue-status 已是 executing/audit/frozen/closed，说明上次确实派出去了，**不重派**；若仍是 pending 且 run 目录无 `done.json`，按「上次未派出」处理，计数 +1 后再次判定。
- 原子写（临时文件 + `os.replace` + fsync），与既有 storage 写法一致。

## 6. 无窗与启停

- 入口用 `tools/venv-openjarvis/Scripts/pythonw.exe`（已由 0041 的 `fix-venv-launcher.ps1` 换成直接运行解释器 + DLL 自包含）。
- 计划任务 `UltimaAgent-RelayLoop`：ONLOGON、无窗、单实例；**默认不启用**，由 Owner 显式开启。
- 启停：`--start` / `--stop`（写停止标记文件让 run() 退出）/ `--status`（读 relay-state.json 打印，不改状态）。

## 7. 开源替代排查结论（G-OSS-001 要求，开工前必须附）

| 候选 | 许可/依赖 | 能否直接接入本仓 | 判定 |
|---|---|---|---|
| dsh SuperAgent 原型 | MIT，TS/Node | 不引入 Node 运行时（2026-11-03 结论） | 只借鉴蓝图，不拼装 |
| APScheduler | MIT，纯 Python | 计时可用，但它不管「读状态权威 + 门禁判定 + 委派派发」 | 计时部分不引入，用 `Event.wait` 已足够；后续要换计时可平滑替换 `run()` 内 sleep |
| Celery / RQ / Dramatiq | 需 broker（Redis/RabbitMQ） | 本机多引入一个常驻中间件与一份队列状态，等于第二权威 | 否决 |
| Temporal / Windmill / n8n | 需独立服务端 | 同上，且与工单卡派发契约无关 | 否决 |
| LangGraph（仓内 `libs/orchestration/langgraph`） | 已入库 | 面向 LLM 图编排，不带「文件权威 + 子进程派发」原语 | 不适用 |
| GitHub Actions / pre-commit | 云端/钩子 | 无法在本机按 queue-status 实时判定，且要联网 | 否决 |

**结论**：无一个现成开源件能在「不改状态权威 + 走既有派发契约」前提下接入；故只自写一个 ≤1 文件的常驻循环（约 200 行）+ 复用现有派发器，符合「能用开源拼装不自研」的例外条件，且例外理由已逐条列出。

## 8. 落地门（本单自设，不放宽）

- 首版**默认不可能真派**：`real_dispatch_enabled=false` + 白名单为空，双重默认关闭。
- 真派路径必须同时满足：开关为真、传了 `--execute`、单号在白名单、预检 ready、配额未满、WIP 空闲。少一条即停。
- 本单验收**只在夹具队列上做真派端到端**（假 Codex 桩，不触真实 Codex、不碰真实 queue-status.json）；真实队列只允许 dry-run，输出选中单号供人核对。
- 完成后交 DeepSeek 硬门复审，判据含「默认不可能真派」「无新增写状态点」「幂等与崩溃恢复」「无窗」。

## 9. 分阶段与 Gate

| 阶段 | 内容 | Gate（可机检） | 回滚 |
|---|---|---|---|
| T0 | 映射与候选选择（纯函数，无 IO） | 单测覆盖 7 值映射 + 未知值 fail-closed；白名单顺序优先于编号 | 删文件即回滚 |
| T1 | Relay 只读泵（读 queue-status，dry-run 输出选中单） | 单测：WIP 占用/暂停/配额/无候选 四种停止理由各自命中；dry-run 全程零子进程零状态写入 | 删文件即回滚 |
| T2 | 派发委派（子进程调 dispatch-work-order.py，先预检后真派） | 单测：预检未 ready 不真派；非 0 退出进退避；同一单不重派；`real_dispatch_enabled=false` 时真派分支不可达 | 删文件即回滚 |
| T3 | 常驻入口与启停 | `--status` 可读；`--stop` 后 run() 在 ≤1 间隔内退出；WindowMonitor 实测 0 可见窗口 | 删文件 + 计划任务不启用 |
| T4 | 夹具端到端 + 真实队列 dry-run | 夹具：完成→取下一单→派（桩）→状态正确；真实：dry-run 输出选中单号且 `git status` 显示 queue-status.json 未变 | 删文件即回滚 |

## 10. 已知风险

1. queue-status 无 priority/dependsOn → 首版依赖靠策略文件声明，声明缺失就不自动派（不是猜）。
2. 派发器自己有 WIP/暂停/DoR 复核，relay 的判定与它可能不同步 → 以派发器的拒绝为准，relay 只记不抢。
3. 真实 Codex 一次性成本高 → 首版把真派配额压到 2 单/日，且默认关闭。
4. 双轨并存仍是结构性问题（老脚本链 vs queue_engine）→ 本单明确以 queue-status 为唯一权威，queue_engine 只提供规则函数，不搬迁权威。
