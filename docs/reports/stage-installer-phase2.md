# 安装包主线 Phase 2 执行报告

工单：`wo-ultimaagent-20261112-0052`

## Gate 结果

- T1 JobObjectManager：PASS。Release 构建退出码 0，0 warning / 0 error；P/Invoke、Kill-on-close 与调试器旁路均命中，`CreateProcess` 和 `JOB_OBJECT_UILIMIT` 均为 0。证据：`docs/reports/evidence/installer-phase2/t1-gate.txt`。
- T2 ChildProcessSupervisor：PASS。Release 构建退出码 0；`Process.Start` 位于 L164，紧随其后的 Job assignment 位于 L166，顺序断言为 True；采用标记 3 处，`CreateProcess` 为 0；正常停止等待真实 `stopped` 落盘。证据：`docs/reports/evidence/installer-phase2/t2-gate.txt`。
- T3 ReadinessProbe：PASS。Release 构建退出码 0；六条判据所需的 health/status/worker/TTS/provider-probe 信号全部命中；20/30/300/120/10 秒超时全部存在；无 TODO 或未实现异常。证据：`docs/reports/evidence/installer-phase2/t3-gate.txt`。
- T4 App.xaml.cs：PASS。Release 构建退出码 0；`OnStartup`/`OnExit`/本文件 `Process.Start` 均为 0；`UseProcessHost` 默认 `true`，自动退出与崩溃注入变量均保留/命中；真实 throw 与 WinUI handler 汇入唯一 `HandleUnhandledException` 停止路径；文件 143 行。证据：`docs/reports/evidence/installer-phase2/t4-gate.txt`。
- T5 daemon.py：PASS。唯一 `taskkill` 行不含 `/T`，`_take_over` 仍命中 2 处，AST 解析退出码 0；490 行，相对 489 基线差 1。证据：`docs/reports/evidence/installer-phase2/t5-gate.txt`。
- T6 live.py / launch.py：PASS。`warm_progress` 共 5 处并由 0/25/50/75/100 的真实加载里程碑驱动；AST 通过；移除新增遥测后与基线逐字一致，五类语音参数均未变化；`launch.py` SHA256 与基线一致。证据：`docs/reports/evidence/installer-phase2/t6-gate.txt`。
- T7 agent_server.py：PASS。`SIGBREAK` 命中 2、`signal.signal` 命中 1；大写且区分大小写的 `MODEL\s*=` 为 0；AST 通过；四处 `provider_for(_MAIN).chat` 仍位于 L719/L1007/L1160/L1217。证据：`docs/reports/evidence/installer-phase2/t7-gate.txt`。
- T8 test-jobkill.ps1：PASS。真机完整复跑退出码 0，判据 1–5 全绿；两次强杀和真实崩溃路径均在 3 秒内清空本轮全部新增 HostShell/Job PID，且 failure JSON 证明 `UI_UNHANDLED` handler 执行；正常 `WM_CLOSE` 清理 pid 文件并将状态落为 `stopped`。脚本不直接停止 watchdog/Python/Tuppo 进程。证据：`docs/reports/evidence/installer-phase2/t8-gate.txt`；运行时 Host 证据：`docs/reports/evidence/installer-phase2/runtime/`。

## 总验收

- Release build：PASS，退出码 0，0 warning / 0 error。
- `test-jobkill.ps1`：PASS，退出码 0，判据 1–5 全绿。
- Python AST：3/3 PASS。
- 四项反向断言：4/4 PASS；`taskkill /T=0`、`OnStartup/OnExit=0`、大写 `MODEL\s*=0`、`launch.py` 哈希不变。
- 派发基线差集：PASS；相对 `before.json` 的 tracked 差集仅 4 个本工单既有文件，意外差集 0；新建文件全部位于本工单路径或 evidence 目录。
- 保护边界：PASS；providers / release-assets / installer 的 git diff 为 0，语音配置哈希不变，watchdog 与 Tuppo 进程仍存活。

总证据：`docs/reports/evidence/installer-phase2/total-gate.txt`。

## 回执

链路号/工单号: wo-ultimaagent-20261112-0052

执行端: Codex

完成状态: 已完成

根因结论: HostShell 原先没有统一的 Windows Job Object 生命周期托管，强杀或异常退出时无法保证语音子进程树随宿主回收。

产出路径: `src/host-shell/UltimaAgent.HostShell/ProcessHost/JobObjectManager.cs`; `src/host-shell/UltimaAgent.HostShell/ProcessHost/ChildProcessSupervisor.cs`; `src/host-shell/UltimaAgent.HostShell/ProcessHost/ReadinessProbe.cs`; `src/host-shell/UltimaAgent.HostShell/App.xaml.cs`; `src/brain/voice/daemon.py`; `src/voice-next/live.py`; `src/brain/agent_server.py`; `tools/test-jobkill.ps1`; `docs/reports/stage-installer-phase2.md`; `docs/reports/evidence/installer-phase2/t1-gate.txt`; `t2-gate.txt`; `t3-gate.txt`; `t4-gate.txt`; `t5-gate.txt`; `t6-gate.txt`; `t7-gate.txt`; `t8-gate.txt`; `total-gate.txt`; `docs/reports/evidence/installer-phase2/runtime/`（最终四轮 HostShell 真机证据）。

验收证据: Release build 退出码 0、0 warning/0 error；test-jobkill 退出码 0、判据 1–5 全绿；三个 Python 文件 AST 3/3 PASS；四项反向断言 4/4 PASS（taskkill `/T`=0、`OnStartup`/`OnExit`=0、大写 `MODEL\s*=`=0、launch.py SHA256=`46941A1BD043C268707AF2536C2F4E5B755729E8476E1D3BD0D4E80E9D7ADD01`）。

越界声明: 无

环境声明: 本机是实际开发机，所有构建、进程强杀、崩溃注入、窗口关闭、AST 与反向断言均为真实执行，无模拟器声明。

开源替代排查: 已确认工单 §7 结论；本单未引入任何第三方 NuGet 或 pip 依赖，仅使用 .NET BCL、PowerShell 与官方 Win32 P/Invoke。
