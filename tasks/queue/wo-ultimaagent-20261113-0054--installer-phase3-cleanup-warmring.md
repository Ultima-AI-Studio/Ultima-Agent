# Codex 工单 · 安装包主线 Phase 3（清计划任务 + 守护内化 + 首启样式）

> 版本：v2.0 ｜ 状态：可开工（前置：Phase 2 已冻结 `9febf442` / tag `wo-ultimaagent-20261112-0052-frozen-20261113`）
> 适用工具：Codex（推理档位 high）｜ 复杂度：L（跨 eng.infra + eng.ui，审计独立：eng.audit）
> **行数口径**：本卡所有"行数/行号"按含空行（raw）计；引用他人文件优先给**符号名**而非行号（PID/行号必漂移）
> 范围依据：`docs/plans/plan-ultimaagent-monolith-installer-lifecycle-provider-20261112.md` §Phase 3（L422–427）＋ **架构裁决 `docs/decisions/pd-20261113-0054-watchdog内化与零计划任务裁决.md`（冲突以裁决为准）**
> **本卡已按 2026-11-13 现场实测校准；方案原文 5 处失真见 §0.6，按本卡执行，勿按方案原文执行**
> 写入域：`installer/`、`tools/`、`devtools/`、`scripts/`（**仅 T2/T4 两个 `git mv` 源文件**：watchdog-loopguard.py、tracker-live.py，除 rename 外不得改 scripts 下其他文件）、`config/host-tasks.json`、`reports/queue-observer/`（仅建任务调用点）、`src/host-shell/UltimaAgent.HostShell/`（App.xaml.cs、MainWindow.xaml.cs、OrbLiveRenderer.cs、ProcessHost/ 新增 GuardianService.cs/HostTaskRegistry.cs/AutostartEntry.cs、TaskManagerRenderer.cs、ChildProcessSupervisor.cs、Assets/orb.html、Assets/taskmanager.html、csproj）、`src/voice-next/preload.py`（仅 docstring）、`docs/reports/`、`docs/decisions/`（只读引用）、计划任务（本卡 §0.2 点名清单，只删不建）、当前用户启动文件夹（仅 T8 一个 .lnk）；`data/` 下文件均为程序运行时读写的运行态（非源码写入域），不手工编辑

---

## 0. 阶段 3 现场冻结（实测 2026-11-13）

### 0.1 仓库基线
- 分支 `codex/voice-fsmn-new-path`，HEAD `4b2e58d3`（0054 v1.0 建卡提交），Phase 2 代码 `9febf442`
- 工作区在途变更约 17 项属他人基线：**禁止清理、禁止 stash、禁止 checkout 覆盖**；越界判定一律按派发时 `before.json` 差集（口径同 0053/0052）
- `tools/`、`scripts/` 部分文件被 `.gitignore` 忽略：本卡新增的 `tools/*.ps1` 若被拒，用 `git add -f` **只加本卡点名的文件**

### 0.2 计划任务实测：12 条（方案写"无条目"）

| # | 任务名 | 状态 / 触发 | 动作（实测） | 归因 | 处置 |
|---|---|---|---|---|---|
| 1 | `UltimaAgent-Preload` | Ready / ONLOGON | `tools\venv-voice-next\Scripts\pythonw.exe -X utf8 src\voice-next\preload.py` | Phase 1 遗留的第二拉起源 | **T3 删任务** |
| 2 | `UltimaAgent-QueueObserver-01a15b32` | Ready / 一次性 | `tools\python31313\pythonw.exe -B ... reports\queue-observer\observer.py --port 18764` | 一次性遗留（2026-10-24） | **T1 删** |
| 3 | `UltimaAgent-T1-Recovery-098dfa1b86cb` | Ready / 一次性 | `...\recovery_runner.py ...\20261023T234453-098dfa1b86cb\request.json` | 同上 | **T1 删** |
| 4–9 | `UltimaAgent-T1-Workflow-5b9d4dd9e4d9` / `-67c6611b29c8` / `-7bc43f362639` / `-85c518be3bbb` / `-9d30e0b48afd` / `-b721e3a95d29` | Ready / 一次性 | `...\workflow_runner.py ...\workflow\20261024T00xxxx-xxxxxxxxxxxx\request.json` | 同上，2026-10-24 批量 | **T1 删** |
| 10 | `UltimaAgent-T2-Core-84169f240563` | Ready / 一次性 | `...\t2_followthrough.py ...\t2\20261024T003445-84169f240563\request.json` | 同上 | **T1 删** |
| 11 | `UltimaAgent-Watchdog` | **Running** / ONLOGON | `tools\venv-openjarvis\Scripts\pythonw.exe scripts\watchdog-loopguard.py` | 现役守护（守 8756 agent_server） | **T2 守护内化后删任务、不重建；脚本 git mv 到 devtools** |
| 12 | `UltimaAgentTrackerLive` | Disabled / 每日 17:56 | `tools\venv-openjarvis\Scripts\pythonw.exe scripts\tracker-live.py` | 开发工具（北极星 live） | **T4 迁 devtools + 删任务** |

**阶段末判据（v2.0 已按裁决改）**：`schtasks /query` 中 `UltimaAgent` 前缀**零条**——12 条全部不存在，且无任何新建；开机自启由启动文件夹 `.lnk` 承担（T8）。

### 0.3 进程基线（PID 会漂移，仅作开工基线，不作断言锚）
- watchdog：pid 11356（`pythonw.exe`，命令行含 `scripts\watchdog-loopguard.py`）——**按命令行识别，禁止写死 PID**
- agent_server：pid 13760（`tools\venv-openjarvis\Scripts\python.exe -X utf8 src\brain\agent_server.py`）
- live.py：**未运行**（`status.json` 当前 `state=stopped`、`warm_progress=100`）
- HostShell：2 个 0 线程 / 40KB 僵尸（pid 24988、22572，2026-11-13 02:57/03:00 由 `test-jobkill.ps1` 复跑产生，内核终止挂起态、`taskkill` 不可回收）→ **重启即消失；T7 冷启动前若仍在，按 PID 基线排除，不得计入启动耗时**
- 必须避开：TuppoAvatarLab MCP 进程、Codex 自身进程、用户非本卡域内文件

### 0.4 Preload 静默失败实证（Phase 3 切掉它的直接依据）
`data\voice-next\preload.json`（2026-11-12T21:33 那次执行）：
- `launch.ok = false`，`FileNotFoundError [WinError 2]`——它调 `launch.py` 用的解释器指向 `...\Doubao\User Data\sandbox_runtime\bases\<hash>\python`，**不是项目 venv**，所以任务每次都在跑、却从未真正拉起 voice 栈
- 同一回执 `agent_probe.ok = true`（10.6s）——agent_server 是 watchdog 在 8756 健康检查失败后拉起的
→ 结论：Preload 与 HostShell 是**两条会互相踩的拉起路径**（Preload 一旦修好必双起）。Phase 3 必须切掉 Preload，语音栈唯一入口收敛到 HostShell `ProcessHost`。

### 0.5 外部 watchdog 职责清单（T2 内化的 1:1 映射依据）
`scripts\watchdog-loopguard.py` 实测常量与职责：
- 探活 `http://127.0.0.1:8756/health`（`AGENT_PORT=8756`）；`CHECK_INTERVAL=20` 秒
- 不健康时经 `LAUNCH_SCRIPT=scripts/start-agent-server.ps1` 拉起，等 3 秒再探
- `LAUNCH_FAIL_LIMIT=3`：连续拉起失败 3 次停手；`LAUNCH_COOLDOWN=300` 秒冷却后允许下一轮；`FUSE_CHECK_INTERVAL=15`
- 日志 `data/logs/watchdog.log` + `watchdog-events.jsonl`；自带 `--install`/`--uninstall`，尾部 schtasks 调用**硬编码任务名 `UltimaAgent-Watchdog`**
- 用户硬要求：**看门狗必须无窗后台运行** → 内化后所有拉起沿用 `CreateNoWindow=true`，且**不再经 `start-agent-server.ps1`**（PowerShell 拉起路径是弹窗根因之一）
- 内化后语义对齐表（T2 必须逐项满足）：20 秒检查间隔、3 次失败阈值、300 秒冷却、事件留痕；允许的差异仅"拉起动作从 ps1 改为 C# 直接 `Process.Start`（python.exe + CreateNoWindow）"与"日志文件名改为 guardian"

### 0.6 方案原文失真清单（本卡已校准，勿按方案原文执行）

| 方案原文 | 实测真相 | 本卡处置 |
|---|---|---|
| `dist/release-assets.json` 的 `shipped_tasks` 置空 | 该文件 922B，顶层键仅 `version/package/package_signature/manifest/manifest_signature/publisher_config/remote_upload_pull_status`，**无 `shipped_tasks`**；全仓检索仅方案文档自身出现该词 | T0 新建 `installer\shipped-tasks.json` 作唯一声明载体 + 守卫脚本（偏差理由见 §6） |
| UI 可交互时 `status.json` `state="warm"` | 真实状态机 `warming→ready→capturing→processing→speaking/acknowledging/stopped/error`，**无 `warm`** | 判据改 `state=="ready"` 或 `warm_progress==100` |
| `OrbLiveRenderer` 内 `EnableWarmRing` 开关旁路 | 全仓不存在该标识 | T6 新建开关（默认 true，`ULTIMA_HOST_WARM_RING=0` 旁路） |
| 冷启动"当前约 4.2s" | 无计时证据：`data\logs\orb-live-loop.txt` 最后写入 2026-10-26，无任何启动耗时埋点 | T5 先埋点、测改前基线（3 次），T7 用改后实测判 |
| `scripts\watchdog-loopguard.py` 移到 `devtools\watchdog.py` 并保留计划任务 | `devtools\` 目录**不存在**；`installer\` 亦不存在 | T2 建目录、脚本迁 devtools 作**开发机手动兜底**；计划任务按裁决删除不重建 |

### 0.7 UI 现状（T6/T9 改造面）
- `MainWindow.xaml.cs`（7046B）：`InitializeComponent()` 后顺序 `await` 三个渲染器（`ComboWindowRenderer` → `OrbLiveRenderer` → `OrbBallRenderer`）；**无 ReadyState 订阅、无启动计时、无任务面板挂点**
- `OrbLiveRenderer.cs`（11215B）：常驻循环每 250ms 轮询 `data\host\orb_command.json`，`seq` 递增即 `PostWebMessageAsString` 推送；已有 `ReadyMessage = "orb-ready"`；已注册 `WebMessageReceived`（web→host 通道可用）
- `ComboWindowRenderer.cs` 已示范完整双向范式：`core.WebMessageReceived += ...`（解析 `WebMessageAsJson`）+ `PostWebMessageAsJson` 推送 + 命令文件注入（`ULTIMA_HOST_COMBO_COMMAND_FILE`，仅验收用）
- `Assets\orb.html`：已处理 `orb-ready`/`drag-start`/`orb-error`；**无 ring/progress 元素**
- `data\voice-next\status.json` 真实字段（实测样本）：`pid/run_id/keyword/state/ready/warm_progress/model/threshold/input_gain/.../worker_pid/worker_ready/tts_backend/tts_cv3_pending/last_error`；`warm_progress` 取 0/25/50/75/100（Phase 2 已落）

### 0.8 四角壳现状与面板挂载约定（裁决 §二.5）
- 四角壳 8 锚窗（四角/顶/底/左右中）当前只有**定稿方案**（`docs/plans/hud-windows-window-interaction-plan-20261031.md` v0.6，工单未派发）与**静态预览**（`docs/previews/hud-live-four-corner/`）；HostShell 源码与全仓均无锚窗实现
- 本卡 T9 面板先在 orb 主窗体系内交付；`manager-console-combined-plan` 已把**左下锚位**规划为"任务队列简况"——后续四角壳工单落地时直接消费 `HostTaskRegistry` 的同一数据，面板挂载点即该锚位，本卡须在 T9 代码注释与阶段报告写明此约定

---

## 1. 任务清单

| 任务 | 文件 | 验收门（一句话） |
|---|---|---|
| T0 | 新建 `installer\shipped-tasks.json`、`tools\check-shipped-tasks.ps1` | 声明 `shipped_tasks=[]`；守卫脚本对零/非零任务面可判 PASS/FAIL，退出码正确 |
| T1 | 计划任务（§0.2 第 2–10 项，10 条）+ `reports\queue-observer\` 唯一建任务调用点 | 10 条零残留；调用点补自清扫；前后快照证据 |
| T2 | 新增 `ProcessHost/GuardianService.cs`、`ProcessHost/HostTaskRegistry.cs`、`config/host-tasks.json`；改 `ChildProcessSupervisor.cs`、`App.xaml.cs`；`scripts\watchdog-loopguard.py` → `devtools\watchdog.py` + `devtools/README.md` | Guardian 在跑且强杀 agent_server 后自动拉起；Watchdog 任务零命中、不重建；无窗 |
| T3 | 任务 `UltimaAgent-Preload`；`src\voice-next\preload.py`（仅 docstring） | 任务零命中；逻辑 diff 为 0；坏路径证据在案 |
| T4 | `scripts\tracker-live.py` → `devtools\tracker-live.py`；任务 `UltimaAgentTrackerLive` | 任务零命中；旧路径引用零命中；AST 通过 |
| T5 | `App.xaml.cs` | `startup-timing.json` 四时点齐全；改前基线 3 次 |
| T6 | `OrbLiveRenderer.cs`、`Assets\orb.html`、`MainWindow.xaml.cs` | 环随 `warm_progress` 变化；开关可旁路；既有视觉零改动 |
| T7 | 新建 `tools\test-phase3-firstframe.ps1` + 证据 | 3 次冷启动 `first_frame` 中位数 ≤1500ms |
| T8 | 新增 `ProcessHost/AutostartEntry.cs`、`tools\test-phase3-autostart.ps1`；启动文件夹一个 `.lnk` | 快捷方式指向正确、经它启动无任何控制台窗口；schtasks 零新增；可干净移除 |
| T9 | 新增 `TaskManagerRenderer.cs`、`Assets\taskmanager.html`（csproj 登记）；改 `MainWindow.xaml.cs` | 面板状态与注册表一致；重启/停用动作真实生效；无第三方依赖 |
| T10 | 总验收 | build 0/0 + Phase 2 `test-jobkill` 回归 + 零任务面 + Guardian 集成 + 自启 + 未触碰面为 0 |

---

## 2. 任务明细（严格三段式）

### T0 · 用户包任务声明载体 + 机器判据
**文件**：新建 `installer\shipped-tasks.json`、`tools\check-shipped-tasks.ps1`（如需 `git add -f` 只加这两个）；**不改** `dist\release-assets.json`
**写什么**：
1. `installer\shipped-tasks.json` 固定内容：
```json
{
  "schema": "ultimaagent-shipped-tasks/v1",
  "shipped_tasks": [],
  "note": "用户安装包不得创建任何计划任务（裁决 pd-20261113-0054）；本文件是唯一权威声明，Phase 4 的 .iss 只读不写。开机自启走启动文件夹，开发机手动兜底见 devtools/README.md。"
}
```
2. `tools\check-shipped-tasks.ps1`：①断言 `shipped_tasks` 为空数组；②枚举 `schtasks /query /v /fo csv` 中**任何** `UltimaAgent` 前缀任务，出现一条即 FAIL（**v2.0 白名单为空**，不再放行 Watchdog）；③输出 ASCII `SHIPPED_TASKS_RESULT=PASS|FAIL` 并配退出码 0/1
3. `devtools/README.md`（若 T2 未建则本 T 先建）：写清"用户包 = 零计划任务；`devtools/watchdog.py` 仅开发机手动兜底，**禁止在用户包注册**；开发机如手动 `--install` 须在交付前 `--uninstall`"
**验收（Gate T0）**：
- 脚本可运行：`powershell -NoProfile -File tools\check-shipped-tasks.ps1` 在 T1–T4 未完成时输出 `FAIL`（预期）、T10 时输出 `PASS`
- `git diff --stat -- dist\release-assets.json` 为空
**禁止**：不得给带签名的 `release-assets.json` 塞非签名语义字段；不得让守卫脚本自动删/自动修任务（只读判定）；不得在脚本里保留任何任务名白名单

### T1 · 清 10 条一次性遗留 + 根因自清扫
**文件**：计划任务（§0.2 第 2–10 项，共 10 条，**逐条点名**）；`reports\queue-observer\` 下唯一建任务调用点
**写什么**：
1. 先落证据：`schtasks /query /v /fo csv` 中这 10 条完整快照 → `docs\reports\evidence\installer-phase3\t1-tasks-before.json`
2. 逐条 `schtasks /Delete /TN "<精确任务名>" /F`；删除后再快照 `t1-tasks-after.json`
3. 定位"创建一次性任务后不回收"的调用点：`git ls-files reports/queue-observer` + 全目录 `Select-String -Pattern 'schtasks|Register-ScheduledTask|standalone-task.xml'`；**只改那一处**，改为 `try/finally` 自删（若现设计已是常驻则只补自删）；调用点若在未跟踪脚本，允许 `git add -f` 该文件并在阶段报告注明
4. 说明：本次 10 条均 `LastTaskResult=0x0`（或 `0x40010004`）、无下次触发时间，属可安全清除的一次性残留
**验收（Gate T1）**：
- 10 条任务名在 `schtasks /query` 中零命中；`UltimaAgent-Watchdog` / `UltimaAgent-Preload` / `UltimaAgentTrackerLive` **仍在**（本 T 时点证明未误删；它们由 T2/T3/T4 分别处理）
- 改后 runner 跑一次最小用例（有 `--selftest` 则用它）后新增任务数 = 0；证据落 `t1-gate.txt`
**禁止**：不得删 Watchdog/Preload/TrackerLive；不得删 `reports/queue-observer` 任何数据目录；不得清理工作区在途变更

### T2 · Guardian 守护内化 + 外部 watchdog 下线（本卡核心，切换顺序强制）
**文件**：新建 `src/host-shell/UltimaAgent.HostShell/ProcessHost/GuardianService.cs`、`ProcessHost/HostTaskRegistry.cs`、`config/host-tasks.json`；改 `ProcessHost/ChildProcessSupervisor.cs`（仅启动路径重构为可复用方法，行为保持）、`App.xaml.cs`（接线）；`scripts/watchdog-loopguard.py` → `devtools/watchdog.py`（`git mv`）+ `devtools/README.md`
**写什么**：
1. `config/host-tasks.json`（schema `ultimaagent-host-tasks/v1`）：声明托管任务，**至少含 `agent-server` 条目**（exe `tools/venv-openjarvis/Scripts/python.exe`，参数 `-X utf8 src/brain/agent_server.py`，重启策略 `check_interval_seconds=20 / fail_limit=3 / cooldown_seconds=300`）；其余条目与 `ChildProcessSupervisor` 现有两个 `StartAssigned` 调用（launch.py、agent_server.py）一一对应，`restart.policy` 标 `manual`
2. `HostTaskRegistry`：加载该 json（校验 schema、路径必须在 projectRoot 内）；维护运行态（pid、enabled、restart_count、last_probe_at、last_result、冷却截止时刻），状态文件写 `data/host/host-tasks-state.json`（data 目录已 gitignore，运行态不入库）；提供给 T9 的只读快照方法与 `RestartAsync/SetEnabledAsync` 写方法
3. `ChildProcessSupervisor`：把现有"agent 未就绪 → 直接拉起 agent_server.py"那段重构为内部可复用方法（**行为保持、判据不变**），供 Guardian 调用；`StartAssigned` 保持 `CreateNoWindow=true` 与 Job 立即挂载
4. `GuardianService`（后台 `Task`，单实例、可取消）：每 20 秒经 `ReadinessProbe.IsAgentReadyAsync` 探活 8756；失败即调上述复用方法拉起并等待一个周期再探；连续失败 3 次进入 300 秒冷却（冷却期不拉起）；每次探活/拉起/冷却/恢复写 `data/logs/guardian-events.jsonl`（事件字段含 ts/task_id/kind/detail）与 `guardian.log`；**v1 只对 agent-server 自动重启**（裁决非目标，其余任务仅呈现）
5. `App.xaml.cs` 接线：`StartProcessHost` 中 supervisor 启动后构造 registry 并启动 Guardian（同一取消令牌）；`StopProcessHost` 先停 Guardian 再停 supervisor；不得在 UI 线程做探活
6. **切换顺序（强制，防断档）**：① 先验证 Guardian 已在跑（events 有探活记录）；② 对外部 watchdog 跑 `--uninstall` 删 `UltimaAgent-Watchdog` 任务；③ 按命令行含 `watchdog-loopguard` 精确终止旧 pythonw（**禁写死 PID**）；④ `git mv` 到 `devtools/watchdog.py`，**不执行 `--install`、不重建任务**；脚本内 `--install/--uninstall` 代码保留（开发机手动用），但 devtools/README 写明用户包禁用
**验收（Gate T2）**：
- `schtasks /query` 中 `UltimaAgent-Watchdog` **零命中**，且全量 `UltimaAgent` 前缀任务数较 T1 后不增加（无新建）
- `GuardianService` 运行证据：`guardian-events.jsonl` 有连续探活事件；**集成实证**：`taskkill /PID <agent_server pid> /F`（pid 现场按命令行获取）后，8756 在一个检查周期 +20 秒容忍窗内恢复，事件流含 fail→restart→ok，`restart_count` 递增；agent_server 新 pid 落在 Job 内（用 0052 的 Job 校验口径）
- 重启拉起全程**无任何控制台窗口**：观察期截图 + 进程列表无 `conhost/cmd/powershell` 新进程（由该动作产生的）
- `devtools/watchdog.py` 存在且专用解释器 `ast.parse` 通过；`scripts/watchdog-loopguard.py` 旧路径不存在；无第二条 watchdog 职能进程
**禁止**：不得改 8756 端口、20/3/300 语义（允许的唯一差异已在 §0.5 列明）；不得经 `start-agent-server.ps1` 或任何 `.ps1/.cmd` 拉起；不得用 `python.exe` 可见窗口；不得重建/新建任何计划任务；不得删日志历史；不得给 launch.py/live/worker 加自动重启

### T3 · 切掉 Preload（消除第二拉起源）
**文件**：任务 `UltimaAgent-Preload`；`src\voice-next\preload.py`（**仅 docstring**）
**写什么**：
1. `schtasks /Delete /TN "UltimaAgent-Preload" /F`，前后快照入证据
2. `preload.py` 模块 docstring 顶部加三段：①Phase 3 起语音栈唯一入口为 HostShell `ProcessHost`，本脚本已弃用；②保留原因（历史/排障参考），**禁止再注册计划任务**；③附 2026-11-12 那次 `WinError 2`（错误解释器）的实证说明
3. 影响基线：删任务后下一次 HostShell 冷启动的 `t_voice_ready`（T5 埋点产出）与删前 `warm_progress` 时间线对比，写入阶段报告
**验收（Gate T3）**：
- `UltimaAgent-Preload` 零命中
- `src\voice-next\preload.py` 仍存在；`git diff` 仅 docstring 区域，**执行代码行 diff 为 0**
- 证据含删除前后快照 + `preload.json` 坏路径原样摘录
**禁止**：不得删 `preload.py` 文件；不得改其任何执行逻辑；不得顺手改 `launch.py`

### T4 · TrackerLive 归 devtools
**文件**：`scripts\tracker-live.py` → `devtools\tracker-live.py`；任务 `UltimaAgentTrackerLive`
**写什么**：
1. `git mv` 迁文件；全仓检索 `scripts\tracker-live`（含文档/脚本引用）逐处改新路径
2. `schtasks /Delete /TN "UltimaAgentTrackerLive" /F`（该任务 Disabled，删除不影响运行态）
3. 脚本内基于 `__file__` 的路径按新位置核查
**验收（Gate T4）**：
- 任务零命中；`git grep -n 'scripts\\tracker-live'` 零命中（历史文档明确标注"已迁移"的除外，须逐条列出）
- `devtools\tracker-live.py` 存在，专用解释器 `ast.parse` 通过
**禁止**：不得把 tracker-live 注册成任何**新的**计划任务；不得改其抓取/写盘逻辑

### T5 · 启动计时埋点（先有尺子再谈 1.5s）
**文件**：`src\host-shell\UltimaAgent.HostShell\App.xaml.cs`（唯一代码文件；与 T2 接线改动同文件时按 hunk 区分，不得互相覆盖）
**写什么**：
1. `OnLaunched` 起点取 `t0`（优先进程创建时间，取不到用 `Stopwatch`）；`MainWindow` 首次呈现后记 `t_window_visible`；首个渲染器 `RunAsync` 完成、UI 就绪后记 `t_first_frame`；`status.json` 首次 `state=="ready"` 或 `warm_progress==100` 时记 `t_voice_ready`
2. 输出 `data\logs\startup-timing.json`（每次覆盖）+ `startup-timing.jsonl`（追加），字段 `{t0_iso, window_visible_ms, first_frame_ms, voice_ready_ms, pid, build}`
3. 本 T **只埋点**，不改启动顺序、不做性能改动；埋点不得阻塞 UI 线程
4. 用**改前**代码跑 3 次，把基线写进 `docs\reports\evidence\installer-phase3\t5-baseline.json`
**验收（Gate T5）**：
- 启动一次后两文件存在，字段齐全且 `first_frame_ms > 0`；两次启动 `jsonl` 两行
- `test-jobkill.ps1` 仍 PASS（埋点未破坏托管链路）
**禁止**：不得在埋点里做同步网络/磁盘长等待；不得改启动顺序；不得把耗时写进 `status.json`（避免污染语音状态机）

### T6 · ReadyState → 首启环进度（UI）
**文件**：`OrbLiveRenderer.cs`、`Assets\orb.html`、`MainWindow.xaml.cs`
**写什么**：
1. `OrbLiveRenderer`：在现有 250ms 循环内新增对 `data\voice-next\status.json` 的轻量读取（读不到静默跳过），仅当 `(state, warm_progress)` 变化时 `PostWebMessageAsString` 推送 `{"kind":"orb-warm","state":"...","progress":N}`
2. 新增开关 `EnableWarmRing`（默认 `true`；`ULTIMA_HOST_WARM_RING=0` 时完全不推送，等价旧形态）；status 路径允许 `ULTIMA_HOST_STATUS_FILE` 覆盖（**仅验收注入用，默认不设**）
3. `orb.html`：**只新增**环层 DOM 与 `orb-warm` 处理（按 progress 画弧，`100` 或 `ready` 后满环淡出）；沿用现有配色/尺寸/字体，不改既有元素样式
4. `MainWindow.xaml.cs`：把 ReadyState 接到现有渲染链，保证"窗口先可交互、环随后补进度"，**不阻塞首帧**
**验收（Gate T6）**：
- 用 `ULTIMA_HOST_STATUS_FILE` 注入临时 json（progress 依次 25/50/75/100）→ 截图 4 张证据显示环随值变化、`ready` 后淡出
- `ULTIMA_HOST_WARM_RING=0` 启动 → 无环，视觉与改前一致（截图对比）
- `git diff --numstat Assets\orb.html` 的删除列 = 0（只新增）
**禁止**：不得改 `orb.html` 现有配色/尺寸/字体/动效参数；不得改 `orb_command.json` 的 seq 协议；不得引入第三方前端依赖

### T7 · 首启可交互实测（3 次冷启动）
**文件**：新建 `tools\test-phase3-firstframe.ps1`；证据 `docs\reports\evidence\installer-phase3\`
**写什么**：
1. 流程：记录启动前 HostShell/Python 基线（0 线程僵尸按 PID 排除）→ 启动 `UltimaAgent.HostShell.exe` → 轮询 `startup-timing.json` 至 `first_frame_ms` 出现 → 记录 `status.json` 到 `ready`/`100` 时间 → 走 WM_CLOSE 关窗（复用 0052 判据 5 路径）→ 重复 3 次
2. 产出 `t7-firstframe-runs.json`（3 次分布）+ `t7-gate.txt`
**验收（Gate T7）**：
- 3 次 `first_frame_ms` **中位数 ≤ 1500ms**（硬判；不达标如实记 `BLOCKED` 并给分布，**禁止改判据**）
- UI 可交互时刻 `status.json` 为 `state=="ready"` 或 `warm_progress==100`；环可见截图 1 张
- 关窗后无新增残留 PID（沿用 0052 的 3 秒消失断言）
**禁止**：不得预置 status 或跳过真实启动伪造结果；不得把僵尸进程算进耗时；不得改阈值

### T8 · 开机自启入口切换（启动文件夹，零 schtasks）
**文件**：新建 `src\host-shell\UltimaAgent.HostShell\ProcessHost\AutostartEntry.cs`、`tools\test-phase3-autostart.ps1`；启动文件夹 `UltimaAgent.lnk`（`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`）
**写什么**：
1. `AutostartEntry` 提供 `Install/Remove/IsInstalled` 静态方法：**在本进程内用晚绑定 COM**（`Type.GetTypeFromProgID("WScript.Shell")` → `CreateShortcut`，`dynamic` 调用，不依赖 PIA/互操作程序集）创建/删除 `.lnk`，Target = HostShell exe 绝对路径、WorkingDirectory = projectRoot、WindowStyle 正常；路径常量集中，不写死用户目录；**禁止 `Process.Start` 任何 cmd/powershell/外部进程**
2. 环境开关 `ULTIMA_AUTOSTART_KIND=shortcut|none`（默认 `shortcut`；`none` 供 CI/验收旁路）；exe 路径允许 `ULTIMA_HOST_EXE` 覆盖（仅验收注入）
3. 本 T 不写 HKCU Run、不碰 schtasks；`tools\test-phase3-autostart.ps1` 覆盖：Install 后 `.lnk` 存在且 Target/WorkingDirectory 正确 → 经资源管理器激活该快捷方式 → 断言进程树出现 HostShell 且**无 conhost/cmd/powershell 子进程、无控制台窗口**（截图）→ Remove 后 `.lnk` 消失
**验收（Gate T8）**：
- 输出 ASCII `AUTOSTART_RESULT=PASS|FAIL` + 退出码；`schtasks /query` 中 UltimaAgent 条目数在测试前后不变（零新增）
- 经快捷方式启动的 HostShell 正常被 Job 托管链路接管（`process-host.log` 有启动记录）
- Remove 后启动文件夹无 UltimaAgent 残留，重复 Install 幂等（不产生第二个 .lnk）
**禁止**：不得创建计划任务或写 HKCU/HKLM Run；不得经 cmd/powershell 进程创建快捷方式；不得把 .lnk 放进仓库（它是机器态，只在启动文件夹）

### T9 · 运行态面板（应用内任务管理器，四角壳左下锚位的前置形态）
**文件**：新建 `src\host-shell\UltimaAgent.HostShell\TaskManagerRenderer.cs`、`Assets\taskmanager.html`；改 `UltimaAgent.HostShell.csproj`（Content 登记 html）、`MainWindow.xaml.cs`（挂点）
**写什么**：
1. `TaskManagerRenderer`：复用 `ComboWindowRenderer` 已验证的 WebView2 范式——host→web 用 `PostWebMessageAsJson` 推 `HostTaskRegistry` 快照（状态变化即推，另加 1s 兜底轮询）；web→host 用 `WebMessageReceived` 解析动作 `{kind:"restart"|"set-enabled", task_id, enabled}`，调 registry 对应方法（经 Guardian 执行）
2. `taskmanager.html`：每条任务一行——名称、启用开关、状态灯（running/stopped/cooldown/error）、pid、重启次数、最近探活时间、"重启"按钮；空态/读不到 json 的显式占位；沿用现有 HarmonyOS 字体与 orb 配色，不引第三方库/CDN
3. `MainWindow.xaml.cs`：在现有渲染链后挂面板（默认不抢首帧；可由现有 combo 入口切换显示）；代码注释写明"未来挂载点 = 四角壳左下锚位，数据契约即本渲染器的快照 JSON"
**验收（Gate T9）**：
- 用 `ULTIMA_HOST_TASK_STATE_FILE` 注入伪造状态（含 running/cooldown/error 三态）→ 渲染截图 3 张，字段与注入一致
- 点"重启"→ `guardian-events.jsonl` 出现对应 restart 事件且面板 `restart_count` 刷新；停用 `agent-server` 后再杀 agent_server，Guardian **不**拉起（证明 enabled 开关生效），重新启用后恢复
- `git diff --numstat` 中本 T 全部为新增文件（除 MainWindow 挂点与 csproj 登记行）；无第三方依赖、无网络请求
**禁止**：不得在 html 里直连文件系统/本地端口（一切经 WebView 消息）；不得让面板轮询阻塞 UI 线程；不得实现四角壳锚窗框架；不得改动 orb.html/combo.html

### T10 · 总验收
**文件**：`docs\reports\stage-installer-phase3.md`、`docs\reports\evidence\installer-phase3\`（本阶段全部证据汇总）
**写什么**：
1. 把 T0–T9 全部 Gate 证据汇总到 `total-gate.txt`（逐项命令 + 关键输出行）
2. 写阶段报告：概览结论 / 逐 T 完成情况 / 问题清单 / 越界声明 / 证据汇总 / 下一阶段前置核验（含 Phase 4 改为调用 `AutostartEntry`、不建 schtasks 的接线点）/ 冻结建议；并注明面板与四角壳左下锚位的对接契约
**验收（Gate T10，全绿才可交主脑）**：
- `dotnet build src\host-shell\UltimaAgent.HostShell\UltimaAgent.HostShell.csproj -c Release` → **0 警告 0 错误**（`TreatWarningsAsErrors` 已开，警告即失败）
- **Phase 2 回归**：`powershell -NoProfile -File tools\test-jobkill.ps1` → `TEST_JOBKILL_RESULT=PASS criteria=1,2,3,4,5`
- `powershell -NoProfile -File tools\check-shipped-tasks.ps1` → `SHIPPED_TASKS_RESULT=PASS`（**schtasks 中 UltimaAgent 前缀零条**）
- `powershell -NoProfile -File tools\test-phase3-autostart.ps1` → `AUTOSTART_RESULT=PASS`
- Guardian 集成证据在案（T2 强杀重启 + T9 开关旁路）
- Python AST 3/3：`devtools\watchdog.py`、`devtools\tracker-live.py`、`src\voice-next\preload.py`（专用解释器 `tools\venv-openjarvis\Scripts\python.exe`）
- 未触碰面 diff 为空：`src\brain\providers`、`dist\release-assets.json`、`src\voice-next\launch.py`（SHA256 必须仍为 `46941A1BD043C268707AF2536C2F4E5B755729E8476E1D3BD0D4E80E9D7ADD01`）、`scripts\start-agent-server.ps1`、语音参数（对照 `docs\specs\kws-wakeup-params-baseline.md`）
- 报告 + 证据目录齐备；冻结 tag `wo-ultimaagent-20261113-0054-frozen-<日期>` **由主脑验收后统一打**
**禁止**：不得 push / tag；不得在总验收阶段补做 T0–T9 的改动（发现缺口回退对应 T，不得就地追加）

---

## 3. 给编码代理的任务粘贴模板
```
T# <标题>：Gate 全绿
- 命令：<实际命令原文>
- 输出：<关键行粘贴，ASCII 判定行必须原样>
- 证据：docs/reports/evidence/installer-phase3/<file>
- 越界声明：无 / <逐条列>
```

## 4. 验收要点
- [ ] §0.2 任务处置表逐条对齐，未误删现役任务；阶段末零 schtasks 条目
- [ ] 每条 T 有命令级证据，无"预计通过"
- [ ] Guardian 切换按强制顺序，守护零断档（先验证内化、再删外部）
- [ ] 全链路无控制台窗口（拉起、快捷方式、面板动作三处分别取证）
- [ ] Phase 2 Job 托管回归 PASS
- [ ] 首启判据用实测数说话，禁止倒推
- [ ] 阶段报告 + 冻结 tag（主脑执行）

## 5. 全局禁止
- 不得触碰 TuppoAvatarLab 进程、Codex 自身进程、本卡写入域之外的用户数据
- 不得删改 `dist\release-assets.json`；不得改 `launch.py`、`scripts\start-agent-server.ps1`、语音参数、`src\brain\providers`
- 不得用通配符批量删任务；**本卡只删不建——禁止创建任何新的 UltimaAgent 计划任务**（自启只走启动文件夹）
- 不得 push / 不得打 tag（统一由主脑验收后收口）

---

## 6. 修订记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-11-13 | 初版（实测校准版）。相对方案原文 5 处校正：①计划任务实测 **12 条**并逐条归因；②`shipped_tasks` 字段不存在 → 偏差裁决用 `installer\shipped-tasks.json`；③`state="warm"` 不存在 → 改 `ready`/`warm_progress==100`；④`EnableWarmRing` 不存在 → 本卡新建；⑤冷启动无证据 → T5 先埋点。另含 Preload 静默失败实证。 |
| v2.0 | 2026-11-13 | **A 级架构变更（裁决 `pd-20261113-0054`）**：watchdog 守护内化——新增 `GuardianService`（1:1 对齐 20s/3 次/300s 语义，拉起从 ps1 改 C# 无窗直启）、`HostTaskRegistry` + `config/host-tasks.json`；外部 watchdog 任务删除不重建，脚本 git mv 到 `devtools/` 作开发机手动兜底。新增 T8 启动文件夹自启（零 schtasks、零控制台）、T9 应用内任务管理器面板（未来挂四角壳左下锚位）；总验收顺延 T10。阶段末判据由"仅剩 1 条"改为"**零条**"，T0 守卫白名单同步清空。明确非目标：应用崩溃不自愈（Owner 接受）、v1 仅 agent-server 自动重启、不建四角壳框架。 |
