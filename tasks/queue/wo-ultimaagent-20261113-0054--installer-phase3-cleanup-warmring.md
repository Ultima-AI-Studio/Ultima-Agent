# Codex 工单 · 安装包主线 Phase 3（清计划任务 + 首启样式）

> 版本：v1.0 ｜ 状态：可开工（前置：Phase 2 已冻结 `9febf442` / tag `wo-ultimaagent-20261112-0052-frozen-20261113`）
> 适用工具：Codex（推理档位 high）｜ 复杂度：M ｜ 主技能：eng.infra + eng.ui（审计独立：eng.audit）
> **行数口径**：本卡所有"行数/行号"按含空行（raw）计；引用他人文件优先给**符号名**而非行号（PID/行号必漂移）
> 范围依据：`docs/plans/plan-ultimaagent-monolith-installer-lifecycle-provider-20261112.md` §Phase 3（L422–427）
> **本卡已按 2026-11-13 现场实测校准；方案原文 5 处失真见 §0.6，按本卡执行，勿按方案原文执行**
> 写入域：`installer/`、`tools/`、`devtools/`、`reports/queue-observer/`（仅建任务调用点）、`src/host-shell/UltimaAgent.HostShell/`（App.xaml.cs、MainWindow.xaml.cs、OrbLiveRenderer.cs、Assets/orb.html）、`src/voice-next/preload.py`（仅 docstring）、`docs/reports/`、计划任务（本卡 §0.2 点名清单）

---

## 0. 阶段 3 现场冻结（实测 2026-11-13）

### 0.1 仓库基线
- 分支 `codex/voice-fsmn-new-path`，HEAD `24e3d46c`（Phase 2 冻结收口提交），Phase 2 代码 `9febf442`
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
| 11 | `UltimaAgent-Watchdog` | **Running** / ONLOGON | `tools\venv-openjarvis\Scripts\pythonw.exe scripts\watchdog-loopguard.py` | 现役守护（守 8756 agent_server） | **T2 迁 devtools 后重建（同名、单条）** |
| 12 | `UltimaAgentTrackerLive` | Disabled / 每日 17:56 | `tools\venv-openjarvis\Scripts\pythonw.exe scripts\tracker-live.py` | 开发工具（北极星 live） | **T4 迁 devtools + 删任务** |

阶段末判据：`schtasks /query` 中 `UltimaAgent` 前缀**仅剩 1 条** `UltimaAgent-Watchdog`，且 `Task To Run` 含 `devtools\watchdog.py`；其余 11 条不存在。

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

### 0.5 watchdog 职责与迁移约束
- 脚本头声明（`scripts\watchdog-loopguard.py`）：守 8756 端口 agent_server（无监听/不健康自动拉起，连续失败 3 次冷却），日志 `data/logs/watchdog.log` + `watchdog-events.jsonl`
- 自带 `--install` / `--uninstall`，**硬编码任务名 `UltimaAgent-Watchdog`** 与脚本路径（在文件尾部的 schtasks 调用处）
- 迁移风险：脚本内所有基于 `__file__` / `os.path.dirname` 的相对路径会因 `scripts\` → `devtools\` 位移而错位 → T2 必须逐项核查修正，并以"日志仍有新增"做实证
- 用户硬要求：**看门狗必须无窗后台运行** → 迁移后仍用 `pythonw.exe`，不得改前台/可见窗口

### 0.6 方案原文失真清单（本卡已校准，勿按方案原文执行）

| 方案原文 | 实测真相 | 本卡处置 |
|---|---|---|
| `dist/release-assets.json` 的 `shipped_tasks` 置空 | 该文件 922B，顶层键仅 `version/package/package_signature/manifest/manifest_signature/publisher_config/remote_upload_pull_status`，**无 `shipped_tasks`**；全仓检索仅方案文档自身出现该词 | T0 新建 `installer\shipped-tasks.json` 作唯一声明载体 + 守卫脚本（偏差理由见 §6） |
| UI 可交互时 `status.json` `state="warm"` | 真实状态机 `warming→ready→capturing→processing→speaking/acknowledging/stopped/error`，**无 `warm`** | 判据改 `state=="ready"` 或 `warm_progress==100` |
| `OrbLiveRenderer` 内 `EnableWarmRing` 开关旁路 | 全仓不存在该标识 | T6 新建开关（默认 true，`ULTIMA_HOST_WARM_RING=0` 旁路） |
| 冷启动"当前约 4.2s" | 无计时证据：`data\logs\orb-live-loop.txt` 最后写入 2026-10-26，无任何启动耗时埋点 | T5 先埋点、测改前基线（3 次），T7 用改后实测判 |
| `scripts\watchdog-loopguard.py` 移到 `devtools\watchdog.py` | `devtools\` 目录**不存在**；`installer\` 亦不存在 | T2/T4 建目录并同步自注册路径 |

### 0.7 UI 现状（T6 改造面）
- `src\host-shell\UltimaAgent.HostShell\MainWindow.xaml.cs`（7046B）：`InitializeComponent()` 后顺序 `await` 三个渲染器（`ComboWindowRenderer` → `OrbLiveRenderer` → `OrbBallRenderer`）；**无 ReadyState 订阅、无启动计时**
- `src\host-shell\UltimaAgent.HostShell\OrbLiveRenderer.cs`（11215B）：`RunAsync(...)` 内常驻循环每 250ms 轮询 `data\host\orb_command.json`，`seq` 递增即 `PostWebMessageAsString` 推送；已有 `ReadyMessage = "orb-ready"`
- `src\host-shell\UltimaAgent.HostShell\Assets\orb.html`：存在，已处理 `orb-ready`/`drag-start`/`orb-error`；**无 ring/progress 元素**
- `data\voice-next\status.json` 真实字段（实测样本）：`pid/run_id/keyword/state/ready/warm_progress/model/threshold/input_gain/.../worker_pid/worker_ready/tts_backend/tts_cv3_pending/last_error`；`warm_progress` 取 0/25/50/75/100（Phase 2 已落）

---

## 1. 任务清单

| 任务 | 文件 | 验收门（一句话） |
|---|---|---|
| T0 | 新建 `installer\shipped-tasks.json`、`tools\check-shipped-tasks.ps1` | 声明 `shipped_tasks=[]`；守卫脚本可判 PASS/FAIL，退出码正确 |
| T1 | 计划任务（§0.2 第 2–10 项，10 条）+ `reports\queue-observer\` 唯一建任务调用点 | 10 条零残留；调用点补自清扫；前后快照证据 |
| T2 | `scripts\watchdog-loopguard.py` → `devtools\watchdog.py` + `devtools\README.md` | 任务唯一且指向 devtools；日志有新增；pythonw 无窗 |
| T3 | 任务 `UltimaAgent-Preload`；`src\voice-next\preload.py`（仅 docstring） | 任务零命中；逻辑 diff 为 0；坏路径证据在案 |
| T4 | `scripts\tracker-live.py` → `devtools\tracker-live.py`；任务 `UltimaAgentTrackerLive` | 任务零命中；旧路径引用零命中；AST 通过 |
| T5 | `src\host-shell\UltimaAgent.HostShell\App.xaml.cs` | `startup-timing.json` 四时点齐全；改前基线 3 次 |
| T6 | `OrbLiveRenderer.cs`、`Assets\orb.html`、`MainWindow.xaml.cs` | 环随 `warm_progress` 变化；开关可旁路；既有视觉零改动 |
| T7 | 新建 `tools\test-phase3-firstframe.ps1` + 证据 | 3 次冷启动 `first_frame` 中位数 ≤1500ms |
| T8 | 总验收 | build 0/0 + Phase 2 `test-jobkill` 回归 PASS + 任务面 PASS + 未触碰面为 0 |

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
  "note": "用户安装包不得创建任何计划任务；本文件是唯一权威声明，Phase 4 的 .iss 只读不写。开发机任务白名单见 devtools/README.md。"
}
```
2. `tools\check-shipped-tasks.ps1`：①断言 `shipped_tasks` 为空数组；②枚举 `schtasks /query /v /fo csv` 中 `UltimaAgent` 前缀任务，与白名单（仅 `UltimaAgent-Watchdog`，且 `Task To Run` 必须含 `devtools\watchdog.py`）逐条比对，多一条或少一条均 FAIL；③输出 ASCII `SHIPPED_TASKS_RESULT=PASS|FAIL` 并配退出码 0/1
3. `devtools\README.md`（若 T2 未建则本 T 先建）：写清"开发机白名单 = `UltimaAgent-Watchdog`（devtools\watchdog.py）；用户包 = 零任务"
**验收（Gate T0）**：
- 脚本可运行：`powershell -NoProfile -File tools\check-shipped-tasks.ps1` 在 T1–T4 未完成时输出 `FAIL`（预期）、T8 时输出 `PASS`
- `git diff --stat -- dist\release-assets.json` 为空
**禁止**：不得给带签名的 `release-assets.json` 塞非签名语义字段；不得让守卫脚本自动删/自动修任务（只读判定）

### T1 · 清 10 条一次性遗留 + 根因自清扫
**文件**：计划任务（§0.2 第 2–10 项，共 10 条，**逐条点名**）；`reports\queue-observer\` 下唯一建任务调用点
**写什么**：
1. 先落证据：`schtasks /query /v /fo csv` 中这 10 条完整快照 → `docs\reports\evidence\installer-phase3\t1-tasks-before.json`
2. 逐条 `schtasks /Delete /TN "<精确任务名>" /F`；删除后再快照 `t1-tasks-after.json`
3. 定位"创建一次性任务后不回收"的调用点：`git ls-files reports/queue-observer` + 全目录 `Select-String -Pattern 'schtasks|Register-ScheduledTask|standalone-task.xml'`；**只改那一处**，改为 `try/finally` 自删（若现设计已是常驻则只补自删）；调用点若在未跟踪脚本，允许 `git add -f` 该文件并在阶段报告注明
4. 说明：本次 10 条均 `LastTaskResult=0x0`（或 `0x40010004`）、无下次触发时间，属可安全清除的一次性残留
**验收（Gate T1）**：
- 10 条任务名在 `schtasks /query` 中零命中；`UltimaAgent-Watchdog` / `UltimaAgent-Preload` / `UltimaAgentTrackerLive` **仍在**（证明未误删）
- 改后 runner 跑一次最小用例（有 `--selftest` 则用它）后新增任务数 = 0；证据落 `t1-gate.txt`
**禁止**：不得删 Watchdog/Preload/TrackerLive；不得删 `reports\queue-observer` 任何数据目录；不得清理工作区在途变更

### T2 · watchdog 迁 devtools + 自注册同步（现役守护不断链）
**文件**：`scripts\watchdog-loopguard.py` → `devtools\watchdog.py`（`git mv`）；`devtools\README.md`
**写什么**：
1. 顺序固定：`--uninstall`（先删任务，缩短双起窗口）→ 按命令行精确终止旧 watchdog 进程（命令行含 `scripts\watchdog-loopguard.py` 的那条，实测 pid 11356）→ `git mv` 到位
2. 改脚本：`--install`/`--uninstall` 的 `/TR` 指向 `devtools\watchdog.py`（仍 `pythonw.exe`、任务名仍 `UltimaAgent-Watchdog`、**不新增第二条任务**）；头部用法注释（L13–16 区域）路径同步
3. 逐项核查基于 `__file__` / `os.path.dirname` 的相对路径（日志、事件、状态、被守护目标），按新位置修正；**不得改**守护语义（8756、3 次失败冷却）
4. 重新 `--install` 后 `schtasks /Run`，验证进程/日志/事件
**验收（Gate T2）**：
- `schtasks /query /v /fo csv`：`UltimaAgent-Watchdog` 恰好 1 条且 `Task To Run` 含 `devtools\watchdog.py`
- 新 watchdog 进程命令行含 `devtools\watchdog.py`，进程名 `pythonw.exe`（无窗口）
- 启动后 30 秒内 `data\logs\watchdog.log` 与 `watchdog-events.jsonl` 均有新写入（路径未断）
- `git status` 显示 `scripts\watchdog-loopguard.py` 已 rename，旧路径不存在
**禁止**：不得改守护端口/冷却策略；不得用 `python.exe` 或可见窗口启动；不得留下第二条同名/同职能任务；不得删日志历史

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
**文件**：`src\host-shell\UltimaAgent.HostShell\App.xaml.cs`（唯一代码文件）
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
**文件**：`src\host-shell\UltimaAgent.HostShell\OrbLiveRenderer.cs`、`Assets\orb.html`、`MainWindow.xaml.cs`
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

### T8 · 总验收
**文件**：`docs\reports\stage-installer-phase3.md`、`docs\reports\evidence\installer-phase3\`（本阶段全部证据汇总）
**写什么**：
1. 把 T0–T7 全部 Gate 证据汇总到 `total-gate.txt`（逐项命令 + 关键输出行）
2. 写阶段报告：概览结论 / 逐 T 完成情况 / 问题清单 / 越界声明 / 证据汇总 / 下一阶段前置核验 / 冻结建议
**验收（Gate T8，全绿才可交主脑）**：
- `dotnet build src\host-shell\UltimaAgent.HostShell\UltimaAgent.HostShell.csproj -c Release` → **0 警告 0 错误**
- **Phase 2 回归**：`powershell -NoProfile -File tools\test-jobkill.ps1` → `TEST_JOBKILL_RESULT=PASS criteria=1,2,3,4,5`（Phase 3 改动不得破坏 Job 托管）
- `powershell -NoProfile -File tools\check-shipped-tasks.ps1` → `SHIPPED_TASKS_RESULT=PASS`（任务面仅 Watchdog 一条且指向 devtools）
- Python AST 3/3：`devtools\watchdog.py`、`devtools\tracker-live.py`、`src\voice-next\preload.py`（专用解释器 `tools\venv-openjarvis\Scripts\python.exe`）
- 未触碰面 diff 为空：`src\brain\providers`、`dist\release-assets.json`、`src\voice-next\launch.py`（SHA256 必须仍为 `46941A1BD043C268707AF2536C2F4E5B755729E8476E1D3BD0D4E80E9D7ADD01`）、语音参数（对照 `docs\specs\kws-wakeup-params-baseline.md`）
- 报告 + 证据目录齐备；冻结 tag `wo-ultimaagent-20261113-0054-frozen-<日期>` **由主脑验收后统一打**
**禁止**：不得 push / tag；不得在总验收阶段补做 T0–T7 的改动（发现缺口回退对应 T，不得就地追加）

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
- [ ] §0.2 任务处置表逐条对齐，未误删现役任务
- [ ] 每条 T 有命令级证据，无"预计通过"
- [ ] watchdog 迁移前后不断链（日志有新增、进程无窗口）
- [ ] Phase 2 Job 托管回归 PASS
- [ ] 首启判据用实测数说话，禁止倒推
- [ ] 阶段报告 + 冻结 tag（主脑执行）

## 5. 全局禁止
- 不得触碰 TuppoAvatarLab 进程、Codex 自身进程、本卡写入域之外的用户数据
- 不得删改 `dist\release-assets.json`；不得改 `launch.py`、语音参数、`src\brain\providers`
- 不得用通配符批量删任务；除 T2 同名重建外不得创建**任何新**的 UltimaAgent 计划任务
- 不得 push / 不得打 tag（统一由主脑验收后收口）

---

## 6. 修订记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-11-13 | 初版（实测校准版）。相对方案原文的 5 处校正：①计划任务实测 **12 条**并逐条归因（方案写"无条目"）；②`shipped_tasks` 字段不存在 → **偏差裁决**改用 `installer\shipped-tasks.json` 作唯一载体（理由：`release-assets.json` 带 `package_signature/manifest_signature`，塞非签名语义字段有污染签名清单风险，且 Phase 4 的 `.iss` 可直接消费独立文件）；③`state="warm"` 不存在 → 改 `ready`/`warm_progress==100`；④`EnableWarmRing` 不存在 → 本卡新建；⑤冷启动 4.2s 无证据 → T5 先埋点测基线再判。另新增：Preload 静默失败实证（坏解释器 `WinError 2`）作为切 Preload 的依据；僵尸 HostShell 与 PID 漂移按命令行识别/基线排除。 |