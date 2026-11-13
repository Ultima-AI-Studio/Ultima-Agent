# 主脑独立验收记录 · wo-ultimaagent-20261113-0054（安装包 Phase 3 生命周期切换）

> 验收人：主脑（独立复核，不采信 worker 自证）
> 验收时间：2026-11-13
> 工单卡：`tasks/queue/wo-ultimaagent-20261113-0054--installer-phase3-cleanup-warmring.md`（SHA256 `366E0CBA4951DC8B66A4026782607D17001A726D245F81F5DE95DFDF0CF021A6`）
> 运行记录：`tasks/queue/runs/wo-ultimaagent-20261113-0054-20261113T023840201172Z`
> 交付提交：`22560d41c6814f5c45f8cc945f8a0ec53c32884f`

---

## 1. 结论

**PASS（可冻结）。** T10 七条判据逐条独立复跑全绿，无阻塞缺陷。两处口径需在验收记录中更正（不构成打回）：

1. 提交 `22560d41` 现已在远端分支上 —— **非 worker 自行 push，而是后续主脑 docs 提交以其为祖先连带推送**；卡 T10「不得 push」的意图（禁止 worker 主动外发）未被违反。
2. 卡 T10 指定的语音参数对照基准 `docs\specs\kws-wakeup-params-baseline.md` **已于 2026-11-11 归档**，实际有效基准应改为 `docs\specs\voice-next-product-baseline.md` + `config\voice-next\live.json`。

---

## 2. Gate 逐条复跑结果（主脑本机实跑，非引用 worker 日志）

| # | 判据 | 命令 | 主脑实跑结果 |
|---|---|---|---|
| 1 | HostShell Release 构建 0 警告 0 错误 | `dotnet build src\host-shell\UltimaAgent.HostShell\UltimaAgent.HostShell.csproj -c Release` | **0 警告 0 错误**，BUILD_EXIT=0（`TreatWarningsAsErrors` 生效） |
| 2 | Phase 2 回归 | `tools\test-jobkill.ps1` | `TEST_JOBKILL_RESULT=PASS criteria=1,2,3,4,5`，EXIT=0；五判据逐条 PASS（含判据4 真实 UnhandledException 路径、判据5 WM_CLOSE 正常关 state=stopped） |
| 3 | 用户包零计划任务 | `tools\check-shipped-tasks.ps1` | `SHIPPED_TASKS_RESULT=PASS`，EXIT=0 |
| 4 | 开机自启入口 | `tools\test-phase3-autostart.ps1` | `AUTOSTART_RESULT=PASS`，EXIT=0；TASKS_BEFORE=0 / TASKS_AFTER=0、快捷方式幂等=1、移除后=0、`VISIBLE_CONSOLE_WINDOW_COUNT=0`、截图 SHA256 `39862DD7…4F53BA2` |
| 5 | 机器态零残留（独立复核） | `schtasks /query /fo csv /nh` 全表 | 全表 **378 行**，`UltimaAgent` 前缀 **0 条**；启动文件夹无 `.lnk` |
| 6 | Python AST 3/3 | 专用解释器 `tools\venv-openjarvis\Scripts\python.exe` | `AST_OK=3/3`（`devtools\watchdog.py`、`devtools\tracker-live.py`、`src\voice-next\preload.py`） |
| 7 | 未触碰面零 diff | `git show --name-only 22560d41` | `src\brain\providers`、`dist\release-assets.json`、`src\voice-next\launch.py`、`scripts\start-agent-server.ps1` **均不在改动清单**；`launch.py` SHA256 = `46941A1BD043C268707AF2536C2F4E5B755729E8476E1D3BD0D4E80E9D7ADD01`（与卡要求一致） |
| 8 | 报告 + 证据齐备 | 文件系统 | `docs\reports\stage-installer-phase3.md`（6010 B，七段齐全）；`docs\reports\evidence\installer-phase3\` 顶层 **44** 项，`total-gate.txt` 165 行 |
| 9 | 无第三方依赖引入 | `total-gate.txt` | `DEPENDENCY_AUDIT=PASS new_nuget=0 new_pip=0 new_frontend_or_cdn=0` |

## 3. 提交面核查

| 项 | 值 |
|---|---|
| 提交 | `22560d41`（父 `2ed1c517`，作者 ArkExlabs，2026-11-13 12:46:07 +0800） |
| 改动规模 | 322 文件：`docs/reports` 304、`src/host-shell` 8、`config/host-tasks.json` 1、`devtools` 2、`installer\shipped-tasks.json` 1、`tools` 3、`docs/tracker` 1、`reports/queue-observer` 1 |
| 远端状态 | 是 `HEAD` 与 `origin/codex/voice-fsmn-new-path` 的**共同祖先**，ahead/behind = 0/0 |
| 推送归因 | **非 worker 推送**：`22560d41` 为后续主脑 docs 提交（`c1eca911` 等）的祖先，push 连带上传 |
| 冻结 tag | 本记录产出后打 `wo-ultimaagent-20261113-0054-frozen-20261113` |

## 4. 关键实现核查（静态）

| 项 | 实测 |
|---|---|
| Guardian 常量 | `ProcessHost\GuardianService.cs`：`CheckInterval=20s`、`Cooldown=300s`、`LaunchFailLimit=3`、探活 `http://127.0.0.1:8756/health` |
| 无控制台 | `ChildProcessSupervisor.cs` L218-219 `UseShellExecute=false, CreateNoWindow=true`；`ReadinessProbe.cs` L140-141 同 |
| 托管任务表 | `config\host-tasks.json` 仅两条：`agent-server`（policy=guardian, 20/3/300）、`voice-launcher`（policy=manual） |
| 用户包声明 | `installer\shipped-tasks.json`：`schema=ultimaagent-shipped-tasks/v1`、`shipped_tasks=[]` |
| 语音参数 | `config\voice-next\live.json` 未被本提交触碰（threshold=0.25、keyword=幂幂、command_wait=5s、end_silence=0.8s、worker_timeout=90s 全部保持） |

## 5. Worker 自证与实测的一致性

| Worker 声明 | 主脑复核 |
|---|---|
| T0–T10 全过 | ✅ 一致（复跑全绿） |
| `TEST_JOBKILL_RESULT=PASS criteria=1,2,3,4,5` | ✅ 一致 |
| `SHIPPED_TASKS_RESULT=PASS` | ✅ 一致 |
| UltimaAgent 计划任务 0 | ✅ 一致（全表 378 行 0 命中） |
| `AUTOSTART_RESULT=PASS` | ✅ 一致 |
| Guardian 强杀 21.8 秒恢复且无控制台 | ✅ 证据在案：`total-gate.txt` `FORCED_KILL_RECOVERY_SECONDS=21.8` + `GUARDIAN_EVENT kind=restart/kind=probe_ok` + `t2-guardian-restart-no-console-pass.png` |
| Python AST 3/3 | ✅ 一致 |
| 首帧中位数 471ms | ✅ 证据在案（458/471/479，limit 1500，T5 冷启基线 1530/444/488） |
| 越界声明「无」 | ✅ 未触碰面 diff 为空，改动全部落在卡声明域内 |
| 「未 push 未打 tag」 | ⚠️ 未自行 push 属实（无 tag 亦属实），但提交已因后续 docs 提交连带在远端 —— 归因已查明，不判违规 |

## 6. 遗留与移交

| 项 | 处置 |
|---|---|
| 卡 T10 语音对照基准指向已归档文件 | 本记录更正为 `voice-next-product-baseline.md` + `config/voice-next/live.json`；卡的 `docs\specs\kws-wakeup-params-baseline.md` 引用属**过期路径**，后续卡模板需避免再引用归档路径 |
| `tasks/queue/index.md` / `queue-status.json` 当前仍为 modified | 由调度器自身写入（0054 状态 executing→audit），非本工单编辑；`total-gate.txt` 中「clean at current HEAD」的表述在此后不再成立，判定为**系统持续写入**而非越界 |
| Phase 4 接线点 | `AutostartEntry`（启动文件夹，零 schtasks），`.iss` 只读 `shipped-tasks.json` 不写入 |
| 面板 → 四角壳左下锚位 | 对接契约已在阶段报告标注，属 Next/壳层范畴，不在本阶段 |

---

**冻结决定：PASS，打 tag `wo-ultimaagent-20261113-0054-frozen-20261113`，队列状态回写 frozen / audit_passed=true。**
