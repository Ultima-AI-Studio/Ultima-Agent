# 安装包主线 Phase 3 阶段报告

- 工单：`wo-ultimaagent-20261113-0054`
- 执行端：Codex
- 环境：真实 Windows 开发机（非模拟器）
- 结论：T0–T10 全部 Gate 通过；UltimaAgent 计划任务为 0，后台守护已内化到 HostShell，开机自启收敛到 Startup 文件夹快捷方式。

## 概览结论

本阶段完成 A 级裁决的 A 方案：`GuardianService` 以 20 秒探测间隔、3 次连续失败阈值、300 秒冷却守护 `http://127.0.0.1:8756/health`，仅自动重启 `agent-server`。外部 watchdog、Preload、TrackerLive 及九条一次性遗留任务均已移除，未创建任何新计划任务。HostShell 及其 Python 子进程全部使用无窗直启路径；强杀恢复、自启动、任务面板动作三条独立链路均取得零可见控制台证据。

Release 构建结果为 0 警告、0 错误；Phase 2 Job 托管五项回归通过。三次真实冷启动首帧为 458/471/479 ms，中位数 471 ms，低于 1500 ms Gate。暖机环支持 25/50/75/100 进度、ready 淡出和环境变量旁路。

## 逐项完成情况

- T0：新增唯一 shipped-task 声明和守卫；`shipped_tasks=[]`，最终 `SHIPPED_TASKS_RESULT=PASS`。
- T1：按 §0.2 精确删除九条具名的一次性遗留任务；工单表头写“10 条”但清单实际为九条，执行以 12 条冻结总表的精确名字为准。`schedule_runner` 在 `finally` 中按本任务名自删，12 个恢复测试通过。
- T2：新增 Guardian、任务注册表和配置；先证明实时探测，再卸载外部 watchdog、停止其 `pythonw`、迁移脚本，顺序无倒置。强杀 agent-server 后 21.8 秒恢复，零控制台。
- T3：删除 Preload 任务；`preload.py` 只改 docstring，`launch.py` 保持冻结 SHA256。
- T4：TrackerLive 迁入 `devtools`，删除任务并更新活跃引用；执行代码不变，AST 通过。
- T5：记录进程起点、窗口可见、首帧、语音 ready 四时点；拒绝陈旧 PID；改前中位数 488 ms。
- T6：新增暖机环而不改既有 orb 视觉；开关旁路、ready 淡出、四档进度均通过真实渲染验证。
- T7：三次真实冷启动均进入 ready，首帧中位数 471 ms；关闭后零残留、零可见控制台。
- T8：新增 COM 晚绑定的 Startup 快捷方式管理，不启动 PowerShell/cmd。复验时返回 T8 修正测试脚本的 `System.Drawing.Common`/`System.Drawing` 运行时回退，Windows PowerShell 5.1 下最终闭环通过并清除快捷方式。
- T9：交付应用内任务管理器；状态、PID、重启次数、最近探测、启停与重启动作均与 `HostTaskRegistry` 一致，真实重启/停用/恢复通过。未引入网络资源或前端依赖。
- T10：Release、Job kill、零任务、自启动、Guardian、AST、冻结面及依赖审计全部通过。

## 问题清单与处置

1. 直接运行 `python.exe` 即使设置 `UseShellExecute=false`、`CreateNoWindow=true`，本机仍会生成 conhost；同一环境的 `pythonw.exe` 不生成控制台。两条 Python 子进程路径因此改为 `pythonw.exe`，仍保留两个强制 ProcessStartInfo 标志，并由 Guardian、voice ready 和 Job 回归覆盖。
2. `pythonw.exe` 下 agent-server 直接写标准错误会因无有效流退出；对子进程开启重定向并异步排空到既有 process-host 日志后解决。
3. 工单点名的 `docs/specs/kws-wakeup-params-baseline.md` 已在此前仓库迁移中归档到 `archive/voice-legacy-E1E2-20261111/docs/specs/`；当前权威 `docs/specs/voice-next-product-baseline.md` 指向 `config/voice-next/live.json`。当前配置、关键词、权威文档和归档基线均无本工单 diff。
4. 共享工作区执行期间，其他文档提交更新了 HEAD，并把当时已存在的少量本工单未跟踪文件一并提交；未改写外部提交/标签。`tasks/queue/index.md` 与 `queue-status.json` 的 before.json 哈希也随外部提交变化，但两文件当前相对 HEAD 干净且本工单未编辑、未暂存。其余 16 个既有脏路径字节不变。
5. T6/T9 诊断阶段的失败截图与日志全部保留，最终验收只引用 `t6-runtime-final-*`、`t9-render-states-accepted` 和 `t9-actions-coherent-final`。

## 越界声明

无。未触碰 TuppoAvatarLab、Codex 进程或工单外用户数据；未清理、stash、revert 既有工作区变更。共享仓库并发提交不是本工单操作。

## 验收证据

- 总 Gate：`docs/reports/evidence/installer-phase3/total-gate.txt`
- 分项 Gate：同目录 `t0-gate.txt` 至 `t9-gate.txt`
- Guardian 强杀恢复：`t2-gate.txt`、`t2-guardian-restart-no-console-pass.png`
- 启动计时：`t5-baseline.json`、`t7-firstframe-runs.json`
- 暖机环：`t6-runtime-final-on/`、`t6-runtime-final-off/`、`t7-warm-ring-visible.png`
- Startup 自启：`t8-gate.txt`、`t8-shortcut-launch-no-console.png`
- 任务面板：`t9-render-states-accepted/`、`t9-actions-coherent-final/`

关键结果：`TEST_JOBKILL_RESULT=PASS criteria=1,2,3,4,5`；`SHIPPED_TASKS_RESULT=PASS`；`AUTOSTART_RESULT=PASS`；Python AST 3/3；Release 0/0；`launch.py` SHA256 为 `46941A1BD043C268707AF2536C2F4E5B755729E8476E1D3BD0D4E80E9D7ADD01`。

## 下一阶段前置核验

Phase 4 安装器必须调用 `AutostartEntry` 完成 Startup 文件夹接线，不得建立 schtasks，也不得写 HKCU/HKLM Run。安装、重复安装、卸载三条路径分别复验快捷方式目标、工作目录、幂等和清除；继续运行 `check-shipped-tasks.ps1` 保证 UltimaAgent 前缀为 0。

任务面板的未来挂载点为四角壳左下锚位，数据契约是 `TaskManagerRenderer` 当前发送的 `HostTaskRegistry` 快照 JSON。后续四角壳工单直接消费该契约；本阶段没有提前搭建四角壳框架。

## 冻结建议

建议主脑完成独立验收后冻结本阶段并统一打 `wo-ultimaagent-20261113-0054-frozen-<日期>` 标签。本执行端未 push、未创建标签，也未创建第三方 NuGet、pip、前端或 CDN 依赖。
