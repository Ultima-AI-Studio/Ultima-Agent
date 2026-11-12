# Codex 工单 · 安装包主线 Phase 2（Job Object + HostShell 拉起）

> 版本：v1.0 ｜ 状态：可开工 ｜ 适用工具：Codex
> 用法：按 T1→T8 顺序逐条执行，Gate PASS 后冻结再进下一条。
> 范围依据：`docs/plans/plan-ultimaagent-monolith-installer-lifecycle-provider-20261112.md` §3.1 / §3.2 / §6 Phase 2
> 前置：Phase 0、Phase 1 **已完成**（见 §0 实测），本工单**不得重做**。
> 拆分来源：DeepSeek `deepseek-flash`（4765 tokens）初稿，主脑按实测现状审校修正 7 处（见 §0.3）。
> 参数：--short（仅用于 `git status --short` 查改动面，非本工单交付脚本的入参）

---

## 0. 现状校准（方案原文与实测不符，执行时以本节为准）

| # | 方案原文 | 实测事实 | 处置 |
|---|---|---|---|
| 1 | Phase 0 待做 | `agent_server.py` 已无 `MODEL`/`OLLAMA_CHAT_URL`；L157 `_MAIN = _load_main_settings()`，L718/1006/1159/1216 走 `provider_for(_MAIN).chat()` | **已完成，不重做** |
| 2 | Phase 1 待做 | `src/brain/providers/` 已存在 `__init__/base/ollama_native/openai_compat/probe/resolve` 六文件 | **已完成，不重做** |
| 3 | HostShell 为 **WPF** | 实为 **WinUI 3**：`using Microsoft.UI.Xaml;`、`public partial class App : Application` | 按 WinUI 3 实现 |
| 4 | 挂载点 `OnStartup` / `OnExit` | `App.xaml.cs` 共 **33 行**，**无** `OnStartup`/`OnExit`，只有 `protected override void OnLaunched(LaunchActivatedEventArgs args)` | 改挂 `OnLaunched` 尾部 + `UnhandledException` + 窗口关闭 |
| 5 | 改 `launch.py` 写 `warm_progress` | 落盘方为 `live.py` L62（`tmp.write_text(...)` + `os.replace(tmp, DATA/'status.json')`）；`launch.py` L17 命中 `read_text` | 改 `live.py`；`launch.py` 的 SHA256 须等于基线 `46941A1BD043C268707AF2536C2F4E5B755729E8476E1D3BD0D4E80E9D7ADD01` |
| 6 | `daemon.py`（未给路径） | 实为 **`src/brain/voice/daemon.py`**，430 行；`_take_over()` 在 **L214**；`["taskkill","/PID",str(pid),"/T","/F"]` 在 **L226**；调用点 **L286** | 按精确行号改 |
| 7 | 项目 target 未声明 | `net8.0-windows10.0.19041.0` | 构建按此 target |

**双起冲突（方案未覆盖）**：当前 agent_server（pid 29580）与 voice-next 由**外部机制**拉起，Phase 3 才清理。`ChildProcessSupervisor` 必须**先探后起**：拉起前探测，若目标已在运行则**只记账不新起**，日志写 `adopted=existing`。这样 Phase 2 与 Phase 3 可并存，不需改默认开关。

---

## 1. 范围冻结

### 本工单只做

1. 新建 `src/host-shell/UltimaAgent.HostShell/ProcessHost/JobObjectManager.cs`
2. 新建 `src/host-shell/UltimaAgent.HostShell/ProcessHost/ChildProcessSupervisor.cs`
3. 新建 `src/host-shell/UltimaAgent.HostShell/ProcessHost/ReadinessProbe.cs`
4. 改 `src/host-shell/UltimaAgent.HostShell/App.xaml.cs`：在 WinUI 3 实际生命周期挂载 ProcessHost
5. 改 `src/brain/voice/daemon.py` 的 `_take_over()`：`taskkill /T /F` → 精确 PID kill
6. 改 `src/voice-next/live.py`：`status.json` 增加 `warm_progress` 字段
7. 保持 `src/voice-next/launch.py` 内容不变（仅作校验对照）
8. 改 `src/brain/agent_server.py`：新增 `signal.signal(SIGBREAK, ...)` 与优雅停路径汇聚
9. 新建 `tools/test-jobkill.ps1`

### 本工单不做（硬边界）

- 不清计划任务、不移 watchdog；不终止正在运行的 `watchdog-loopguard`（pid 26052），不改它的启动方式（Phase 3）
- 不建 `installer/`、不写 `.iss`（Phase 4）
- 不改 `src/brain/providers/`（Phase 1 已完成）
- 不改任何语音参数字段值（关键词/阈值/增益/设备索引），只允许新增 `warm_progress` 遥测字段
- 不改 `dist/release-assets.json`
- 不重做 Phase 0（`MODEL`/`OLLAMA_CHAT_URL` 已不存在）

---

## 2. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T1 | 新建 `ProcessHost/JobObjectManager.cs` | 编译过；P/Invoke 三件齐；`Debugger.IsAttached` 时不建 Job |
| T2 | 新建 `ProcessHost/ChildProcessSupervisor.cs` | 编译过；assign 在 start 之后；先探后起 |
| T3 | 新建 `ProcessHost/ReadinessProbe.cs` | 编译过；实现六条就绪判据 |
| T4 | `src/host-shell/UltimaAgent.HostShell/App.xaml.cs` | 编译过；`OnStartup`/`OnExit` 命中 0 |
| T5 | `src/brain/voice/daemon.py` | `taskkill` 行内 `/T` 命中 0；AST 过 |
| T6 | `src/voice-next/live.py`、`src/voice-next/launch.py` | `warm_progress` 命中 ≥1；launch.py 哈希不变 |
| T7 | `src/brain/agent_server.py` | `SIGBREAK` 命中 ≥1；`MODEL\s*=` 命中 0 |
| T8 | 新建 `tools/test-jobkill.ps1` | 判据 1–5 全绿；退出码 0 |

---

## 3. 任务明细

### T1 · JobObjectManager

**文件**：`src/host-shell/UltimaAgent.HostShell/ProcessHost/JobObjectManager.cs`

**写什么**：
1. P/Invoke 三件：`CreateJobObjectW`、`SetInformationJobObject`（`JobObjectExtendedLimitInformation`）、`AssignProcessToJobObject`。
2. 创建 Job 后立即 `SetInformationJobObject` 设 `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`。
3. 提供 `Assign(IntPtr hProcess) -> bool`、`Close()`、`bool IsActive { get; }`。
4. `Debugger.IsAttached == true` 时**不创建 Job**，`IsActive` 返回 `false`。
5. **不设置**任何 `JOB_OBJECT_UILIMIT_*` UI 限制位（方案 §3.2 代价 3）。

**验收（Gate T1）**：
- `dotnet build src/host-shell/UltimaAgent.HostShell/UltimaAgent.HostShell.csproj -c Release` 退出码 0
- `Select-String` 命中 `CreateJobObjectW`、`SetInformationJobObject`、`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`、`Debugger.IsAttached` 各 ≥1
- `CreateProcess` 命中 0；`JOB_OBJECT_UILIMIT` 命中 0

**禁止**：不得引入材料外的 Job 配置项；不得在 `Debugger.IsAttached` 分支仍创建 Job。

---

### T2 · ChildProcessSupervisor

**文件**：`src/host-shell/UltimaAgent.HostShell/ProcessHost/ChildProcessSupervisor.cs`

**写什么**：
1. `Process.Start` 起子进程后**立即**调 `AssignProcessToJobObject`（竞态窗口最小化）。
2. **先探后起**：拉起前调 `ReadinessProbe`，若目标已在运行则不新起，记 `adopted=existing` 并写日志。
3. 记录子进程 PID，供 T8 校验与优雅停使用。
4. 提供 `StopAll(TimeSpan grace)`：先投 `SIGBREAK` 优雅停，超时后强制 kill。
5. 子进程清单（按方案 §3.1）：

| 序 | 子进程 | 启动时机 |
|---|---|---|
| P1 | `agent_server.py` | 立即（并行） |
| P2 | `voice-next/launch.py` | 立即（并行，必须与 P1 并行，否则用户白等 4 分钟） |
| P4 | ASR/KWS | P2 上报 `loading` 后起（与 TTS 共享麦克风，必须串行） |
| P5 | 外脑 probe | P1 ready 后 |

**验收（Gate T2）**：
- 编译退出码 0
- 命中 `Process.Start` 与 `AssignProcessToJobObject`，且后者行号 > 前者
- 命中 `adopted` 或等价复用标记 ≥1
- `CreateProcess` 命中 0

**禁止**：不得用 CreateProcess 标志绕过 assign；不得在 assign 前拉起可能 fork 孙进程的程序；不得把 P1/P2 改成串行。

---

### T3 · ReadinessProbe

**文件**：`src/host-shell/UltimaAgent.HostShell/ProcessHost/ReadinessProbe.cs`

**写什么**：实现方案 §3.1 六条就绪判据，逐条可测，不留空实现：

| 序 | 判据 | 超时 |
|---|---|---|
| P0 | HostShell 自身：`Window.Activated` 事件已触发（WinUI 3，**不是** WPF 的 `Loaded`） | — |
| P1 | `agent_server`：`GET http://127.0.0.1:<PORT>/health` 返回 200 且 body 含 `provider` 与 `model` 字段（不校验具体值） | 20s |
| P2 | `voice-live`：读 `data/voice-next/status.json`，`state == "ready"` 为就绪；`state == "loading"` 视为已托管 | 托管 30s / 就绪 300s |
| P3 | CV3 daemon：`_pid_alive` 探活通过，且 `status.json` 中 `backend == "cv3"` 且 `pending == false` | 300s |
| P4 | ASR/KWS：`status.json.asr_ready == true` 且 `kws_pid` 进程存活 | 120s |
| P5 | 外脑：调 provider `probe()` 一次，结果写 `Data\logs\provider-probe.log` | 10s |

**验收（Gate T3）**：
- 编译退出码 0
- 六条判据各有对应方法或常量，命中 `/health`、`status.json`、`asr_ready`、`kws_pid`、`provider-probe` 各 ≥1
- 超时值 20/30/300/120/10 秒在代码中出现
- 无 `TODO`、无 `throw new NotImplementedException`

**禁止**：不得编造材料外的就绪信号；不得把 P2 的 `loading` 当作已就绪上报给 UI。

---

### T4 · App.xaml.cs 生命周期挂载

**文件**：`src/host-shell/UltimaAgent.HostShell/App.xaml.cs`

**写什么**：
1. 在 `OnLaunched` 尾部（`_mainWindow.Activate()` 之后）按 `UseProcessHost` 启动 ProcessHost。顺序不得提前——先出窗再起子系统，保证首帧预算。
2. 在现有 `UnhandledException` 处理器内，`Exit()` 之前调 `StopAll()` + `JobObject.Close()`。
3. 在窗口关闭路径（`_mainWindow.Closed`）触发同一套优雅停。
4. 新增 `UseProcessHost` 配置读取，默认 `true`；为 `false` 时不启动 ProcessHost，应用退化为纯 UI。
5. 保留现有 `ULTIMA_HOST_AUTO_EXIT_MS` 逻辑不变。
6. 新增崩溃注入点：读 `ULTIMA_HOST_CRASH_SELF`，为真时主动抛异常（供 T8 判据 4 使用）。
7. 不新增 `OnStartup`/`OnExit`（WinUI 3 无此挂载点）。

**验收（Gate T4）**：
- 编译退出码 0
- `OnStartup` 命中 0、`OnExit` 命中 0
- `UseProcessHost` 命中 ≥1 且默认值字符串为 `true`
- `Process.Start` 在本文件命中 0（拉起逻辑只在 T2）
- `ULTIMA_HOST_AUTO_EXIT_MS` 仍命中 ≥1
- `ULTIMA_HOST_CRASH_SELF` 命中 ≥1
- 文件行数 > 33

**禁止**：不得改 `OnLaunched` 现有自动退出逻辑；不得引入 WPF 生命周期 API（`Startup`/`Exit` 事件亦不用）。

---

### T5 · daemon.py 精确 PID kill

**文件**：`src/brain/voice/daemon.py`

**写什么**：
1. 将 L226 的 `["taskkill", "/PID", str(pid), "/T", "/F"]` 改为不含 `/T` 的精确 PID kill。
2. 保持 `_take_over()` 其余逻辑与调用点 L286 不变。
3. 改动处留一行注释说明原因：Job 内 `/T` 会杀同 Job 其它进程。

**验收（Gate T5）**：
- `Select-String -Pattern "taskkill"` 命中的行内 `/T` 命中 0
- `_take_over` 仍命中 ≥1
- `python -c "import ast;ast.parse(open('src/brain/voice/daemon.py',encoding='utf-8').read())"` 退出码 0
- 文件行数与改动前 430 行差异 ≤ 3

**禁止**：不得改 `_take_over()` 以外逻辑；不得改 daemon 侧 Job 继承（孙进程自动入 Job）；不得改任何语音参数。

---

### T6 · live.py 增加 warm_progress（launch.py 保持不变）

**文件**：`src/voice-next/live.py`、`src/voice-next/launch.py`

**写什么**：
1. 在 `live.py` L62 写 `status.json` 之前，向 `self.status` 增加 `warm_progress` 字段（0–100 整数，表示 CV3/ASR 加载进度）。
2. 进度来源必须是真实加载进度，不得用定时器伪造。
3. `launch.py` **不得改动任何字节**——它在 L17 只做 `read_text`，本工单用它做「未被误改」的对照：改动前后 `Get-FileHash -Algorithm SHA256` 必须一致。

**验收（Gate T6）**：
- `warm_progress` 在 `src/voice-next/live.py` 命中 ≥1
- `python -c "import ast;ast.parse(open('src/voice-next/live.py',encoding='utf-8').read())"` 退出码 0
- 语音参数字段 `keyword`/`threshold`/`input_device`/`dsp_gain_db`/`tts_backend` 在改动中无值变化
- `launch.py` 的 `Get-FileHash -Algorithm SHA256` 结果与开工前记录一致

**禁止**：不得改 `launch.py`；不得用假进度；不得改参数字段值。

---

### T7 · agent_server.py SIGBREAK

**文件**：`src/brain/agent_server.py`

**写什么**：
1. 新增 `import signal`（若未导入）与 `signal.signal(signal.SIGBREAK, <handler>)`。
2. handler 置优雅停标志，与现有退出路径汇聚，不引入第二套退出机制。
3. 对非 Windows 平台做 `hasattr(signal, "SIGBREAK")` 保护。

**验收（Gate T7）**：
- `SIGBREAK` 命中 ≥1，`signal.signal` 命中 ≥1
- `MODEL\s*=` 命中 0
- `python -c "import ast;ast.parse(open('src/brain/agent_server.py',encoding='utf-8').read())"` 退出码 0
- `provider_for(_MAIN).chat` 调用次数仍为 4 处（行号允许因新增 import 位移）

**禁止**：不得改 `provider_for(_MAIN).chat(...)` 调用逻辑；不得改 `_MAIN` 读取逻辑 L157；不得改门控 `_clean_content` L649 / `_no_tool_gate` L980 / `_risk_gate` L988 / `_QUERY_SYSTEM` L1100。

---

### T8 · tools/test-jobkill.ps1

**文件**：`tools/test-jobkill.ps1`

**写什么**：实现方案判据 1–5，逐条断言并汇总退出码。

| 判据 | 动作 | 断言 |
|---|---|---|
| 1 | 启动 `UltimaAgent.HostShell.exe`，等待就绪 | python 进程中 UltimaAgent 系 ≥3 个 |
| 2 | 用 `Stop-Process -Force` 模拟任务管理器强杀 HostShell | 3 秒内相关 PID 全消失（核心验收） |
| 3 | 另起一次，再次 `Stop-Process -Force` | 检查项同 2 |
| 4 | 置 `ULTIMA_HOST_CRASH_SELF=1` 启动，使 `UnhandledException` 路径被真实走到 | 检查项同 2 |
| 5 | 正常退出（关闭窗口） | 所有 pid 文件被清；`status.json` 落 `state == "stopped"` |

判据 4 不使用 `Debug.Assert` 注入源码——改由 T4 新增的显式环境变量触发，避免改源码再回滚。

**验收（Gate T8）**：
- `powershell -NoProfile -File tools/test-jobkill.ps1` 退出码 0
- 判据 1–5 对应断言各 ≥1
- 判据 2/3/4 的三秒超时以显式断言体现（`-TimeoutSec 3` 或等价）
- 脚本不含针对 pid 26052 的 `Stop-Process`
- 失败时输出失败判据编号

**禁止**：不得终止 `watchdog-loopguard`（pid 26052）；不得改 `dist/release-assets.json`；不得改任何语音参数；不得用 `Debug.Assert` 注入源码。

---

## 4. 总验收

按序全绿：

1. `dotnet build src/host-shell/UltimaAgent.HostShell/UltimaAgent.HostShell.csproj -c Release` 退出码 0
2. `powershell -NoProfile -File tools/test-jobkill.ps1` 退出码 0，判据 1–5 全过（核心：判据 2 强杀后 3 秒内无残留）
3. 三个 Python 文件 AST 解析全过（`src/brain/voice/daemon.py`、`src/voice-next/live.py`、`src/brain/agent_server.py`）
4. 反向断言：`src/brain/voice/daemon.py` 的 `taskkill` 行内 `/T` = 0；`App.xaml.cs` 的 `OnStartup`/`OnExit` = 0；`src/brain/agent_server.py` 的 `MODEL\s*=` = 0；`src/voice-next/launch.py` 哈希不变
5. 基线差集判定：`git status --short` 相对派发 run 目录 `before.json` `status_entries` 的**差异集**不含本工单文件清单与证据目录之外的任何文件；开工前已有的在途变更（约 17+ 项 `.superpowers/sdd/*`、`config/interface-routing.json` 等）全部保留，不得清理、stash 或回退（2026-11-13 v1.1 修订，口径与 0053 一致）
6. 未触碰：`src/brain/providers/`、`dist/release-assets.json`、`installer/`、watchdog pid 26052、任何语音参数字段值
7. 回执自述：越界声明（无 / 列明）、每 T 证据、改动文件清单

---

## 5. 已知风险与工单内对应位置

| 风险 | 位置 | 处置 |
|---|---|---|
| `_take_over` 的 `/T` 误杀同 Job 进程 | T5 | 去 `/T`，精确 PID |
| assign 与 start 竞态导致孙进程逃逸 | T2 | spawn 后立即 assign；禁止 CreateProcess 绕过 |
| VS 调试时 Job 连带杀子进程 | T1 | `Debugger.IsAttached` 时不建 Job |
| Phase 2 与外部拉起双起冲突 | T2 | 先探后起，`adopted=existing` |
| `SIGBREAK` 在非 Windows 不存在 | T7 | `hasattr` 保护 |
| 判据 4 崩溃模拟破坏源码 | T8 | 改环境变量触发，不改源码 |

---

## 7. 开源替代排查（DoR 第 6 项，G-OSS-001）

本工单含自写模块，按「能用开源绝不自研」逐模块给出排查结论：

| 模块 | 现成开源/官方替代 | 结论 |
|---|---|---|
| `JobObjectManager` P/Invoke 封装 | .NET BCL **无** Job Object 托管 API（`System.Diagnostics.Process` 只有 Kill/Tree，无跨进程组回收能力）。开源候选：`Microsoft.Devices.JobObject`、`JobObjectWrapper`（Codeplex 遗档，无维护） | **弃用开源**：两者均为 2010 年代无人维护的薄封装，引入即背依赖；官方 Win32 API 稳定，自写约 80 行 P/Invoke 成本更低、可控 |
| `ChildProcessSupervisor` | 无通用进程监督库覆盖「Win32 Job + WinUI 3 生命周期 + 先探后起」组合 | **自写**，逻辑量小 |
| `ReadinessProbe` | HTTP 部分用 BCL `System.Net.Http.HttpClient`（非第三方）；文件部分用 `System.IO.File` | **用 BCL，无第三方** |
| `test-jobkill.ps1` | Pester 可做测试框架，但本脚本是一次性验收工具，断言仅 5 条 | **不引入 Pester**，纯 PowerShell 断言 |

**统一结论**：本工单无第三方依赖引入，全部为 BCL + 官方 Win32 P/Invoke；自写理由如上，均属"官方能力无托管封装且开源封装已废弃"。

---

## 8. 给编码代理的任务粘贴模板

```
T1 JobObjectManager：已完成，Gate 全绿（附 build 输出 + grep 命中）
T2 ChildProcessSupervisor：已完成，Gate 全绿（附 assign 行号 > start 行号证据）
T3 ReadinessProbe：已完成，Gate 全绿（附六条判据命中）
T4 App.xaml.cs：已完成，Gate 全绿（附 OnStartup/OnExit=0、UseProcessHost=true）
T5 daemon.py：已完成，Gate 全绿（附 taskkill 无 /T、行数差异）
T6 live.py：已完成，Gate 全绿（附 warm_progress 命中 + launch.py 哈希一致）
T7 agent_server.py：已完成，Gate 全绿（附 SIGBREAK 命中 + 4 处 provider 调用仍在）
T8 test-jobkill.ps1：已完成，Gate 全绿（附脚本退出码 0 + 五判据输出）
总验收：build 0 / test-jobkill 0 / AST 3/3 / 反向断言 4/4 / git status 干净
```
