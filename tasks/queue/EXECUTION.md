# 当前执行入口与验收边界

2026-10-21 修复：CLI 已支持任务登记、查看、执行、结束回收；不再只有插队命令。

本项目 Python 使用隔离 `_pth`，使用绝对脚本路径启动：

```powershell
$py = 'H:\UltimaAI\UltimaAgent\tools\python31313\python.exe'
$cli = 'H:\UltimaAI\UltimaAgent\tasks\queue_engine\cli.py'
& $py $cli status
& $py $cli enqueue 'H:\absolute\approved-task-index-record.json'
& $py $cli run task-id -- 'C:\absolute\executor.exe' argument
& $py $cli recover task-id
```

登记文件只包含 queue-spec 的11个索引字段；完整任务卡必须实际存在，task_id、依赖、fileDomain、优先级与推理强度须与索引一致。只允许新建 QUEUED，不能从登记入口导入 COMPLETED。执行命令应使用绝对路径，工作目录沿用任务库根目录（默认 tasks）；执行器需要项目根目录时应使用自身的工作目录参数。

`run` 经过既有依赖、执行容量、暂停标记、进程身份和 run 幂等闸门，保存真实运行六件套。退出后自动回收到 SELF-CHECK，再读取 stdout 最后一个非空行的结构化 JSON。只有 `business_success: true` 且退出码0才进入 AUDIT；该状态不释放下游依赖。缺证据 BLOCKED，业务失败 FAILED。不会自动重试、解除阻塞、签署独立审计或打冻结 tag。

`recover` 适用于入口退出后读取已有回执；仍活跃的真实执行进程不被修改。监督进程退出且完成回执缺失时，无法确认分离的执行进程是否终止，因此保留 EXECUTING 及其容量占用，交主脑核查；审计收尾也不能释放该容量。返回码0仅表示已到待审计或已完成；返回码2表示未派发、仍运行、失败、阻塞或输入错误，不代表最终业务验收通过。

## 版本冻结凭据

派发器按任务卡版本核对：v0.2/v0.3 等待 v0.1，v0.4 等待 v0.3，v1.0 等待 v0.2 与 v0.4。各前置须同时存在实际 Git 冻结 tag 和 `tasks/queue/gates/<tag>.json`。审批回执必须包含 `gate`（tag 名）、`decision: PASS`、`approved_by: owner`、非空 `approved_at`、非空 `evidence` 数组（每项含证据 `path` 与 `sha256`）。这是主脑在用户实际批准后登记的凭据，本轮未生成任何冻结审批或 tag。缺项或证据变化均拒绝派发。

## 工程调度与产品队列是两层

这里的 CLI 是产品任务队列入口。它不等于跨项目工程调度服务，不会扫描 Markdown 后自行启动8个 Codex 工单。工程派单仍要求全局登记、每项目实际执行≤1、全局≤3、一单一进程、主脑生命周期以及工单版本门检查。不能用此 CLI 的内部并行组上限替代工程全局 WIP 检查。

`tasks.json` 当前空数组表示尚未逐任务登记生产运行，不表示8张开发工单已经完成。历史独立 Codex 执行回执位于 `tasks/queue/runs/` 与 `docs/reports/`；本次测试全部在隔离临时目录执行，不注入生产任务库。

当前工单事实以 `stage1-unit-queue.md`、工单总卡和全局逐工单登记为准。W2已独立通过35项技术验收与62项回归，并结合独立U01环境门建立内部tag `wo-s1-queue-engine-done`；W1已在维护重启后独立验收并内部收口。Owner已明确批准，v0.1冻结门已通过；v0.2/v0.3可进入派发前检查，本次未启动后续工单。语音与文本同依赖 v0.1；文本不额外等待语音工单完成。

## 真实工程工单派发适配器

`scripts/dispatch-work-order.py --order <已登记工单> --prompt <绝对载荷路径>` 默认只检查；`--execute` 才启动真实Codex。修复既有blocked/audit工单须显式 `--repair`。载荷必须引用 `docs/INDEX.md` 与当前唯一工单；适配器检查全局唯一登记、每张卡存在且阶段一致、版本门、暂停标记、真实进程命令角色和WIP，并持有全局工程派发锁。app-server/exec-server及其已验证助手不计开发执行进程，用途不明则拒绝派发。

一次只执行一单，保留before/session/out/err/final/done证据。进程退出且结构化READY_FOR_REVIEW回执可核对时，最多进入audit；审计槽被占、失败或缺回执时保持blocked，不自动完成、批准或续派。父进程失联会降级停止后续派发。产品内部任务库不会因此被伪造填充。

当前真实接入轮为 `runs/wo-s1-host-shell-20261021T023427316731Z/`。新CLI的stdout JSON可能漏列MCP工具活动，`scripts/read-dispatch-progress.py <绝对run路径>`交叉核对持久会话，只输出进度摘要；不得仅凭stdout停更判僵死并中断任务。该适配器是主脑调用入口，不是持续自动批准的后台守护器。

## 计划和状态校验

`scripts/check-stage1-plan.py` 检查25张任务卡的依赖ID、缺失节点和环；`scripts/reconcile-project-state.py --apply` 对齐本次阶段一登记与项目状态，保存原始文件及独立回读回执。本轮对齐脚本是阶段一修复工具，不是后续阶段的自动状态裁决器。
