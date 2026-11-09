# 修复：后台周期性弹出控制台窗口（2026-11-09）

## 现象

屏幕上每隔几分钟就连续闪出 6 个控制台窗口，反复不断，看起来像有任务在周期性派发/跟踪。

## 排查过程

| 步骤 | 动作 | 结果 |
|---|---|---|
| 1 | 猜"G-ORCH 批次还在跑" | 普查无 `bash`/`codex`/`wt` 存活，批次早已结束 |
| 2 | 查 6 个常驻 `conhost.exe` 的父进程 | ArmouryCrate / ollama / verge-mihomo / Codex 扩展的 cmd / agent_server / 我的 shell，全是长驻宿主，不是新弹出 |
| 3 | 90 秒进程采样 | 只抓到自己的 shell，无周期进程（**周期比采样窗口长，漏掉了**） |
| 4 | 采样延长到 330 秒覆盖完整 5 分钟周期 | 19:36:04 抓到真凶 |

## 根因

`scripts/tracker-live.py` 的 `process_start()` 为取一个 pid 的启动时间，起一个完整 PowerShell：

```python
subprocess.check_output(["powershell", "-NoProfile", "-Command",
                         f"$p=Get-Process -Id {pid} ..."])
```

刷新逻辑固定取最近 6 条，每条调一次：

```python
for it in items[:6]:
    it["alive"] = alive(it["pid"], ...)
```

计划任务 `UltimaAgentTrackerLive` 每 5 分钟拉起一次（repeat `PT5M`）。三个条件叠加 = **每 5 分钟连续 6 个窗口**。这些 `powershell.exe` 既无 `-WindowStyle Hidden` 也无 `CREATE_NO_WINDOW`，每次调用都新建 conhost。

实测抓到的现场（19:36:04—19:36:06）：

```
pythonw.exe  tracker-live.py            ← 计划任务（父 svchost）
powershell.exe  $p=Get-Process -Id 19292   ← 窗口 1
powershell.exe  $p=Get-Process -Id 12460   ← 窗口 2
powershell.exe  $p=Get-Process -Id 34552   ← 窗口 3
```

## 修复

1. **`scripts/tracker-live.py`** —— `process_start()` 改为直接调 kernel32 读进程创建时间，不再起子进程：

   `OpenProcess(0x1000, ...)` + `GetProcessTimes(...)` 取 FILETIME，`ticks/1e7 - 11644473600` 换算 UTC 后转 CST，与原 `datetime.fromisoformat` 口径一致。

2. **`scripts/gorch/batch_orchestrator.py`** —— 新增 `_NO_WINDOW = 0x08000000 if sys.platform == 'win32' else 0`，7 处 `subprocess.run/Popen`（bash 判定、wt switch / merge / remove、git branch / rev-parse）全部带上 `creationflags=_NO_WINDOW`。此前只有 `codex_channel.py` 设了，派发一批要调十几次子进程，本身也会连续闪窗。

3. **`scripts/gorch/kanban_update.py:135`** —— 看板刷新 fallback 的 `Popen` 补 `creationflags=0x08000000`。

## 验证

| 项 | 结果 |
|---|---|
| 三文件 `py_compile` | 通过（rc=0） |
| `test_gorch_batch_orchestrator.py::test_conflict_blocked_when_other_in_progress` 单条 | 1 passed / 1.75s |
| `tracker-live.py` 真跑一次 | rc=0，`live-data.js` 正常更新（19:41:19），已退出 pid 正确判 `running:false` |
| 脚本内 PowerShell 残留 | grep 仅剩 docstring 说明文字，无调用 |
| 独立 probe 对比 ctypes 与旧法 | ctypes 返回正确启动时间（对 `$PID` 校验一致） |

## 后续处置：计划任务已禁用（2026-11-09 19:53）

修复后经 Owner 判断，该任务保留价值过低：它唯一的产物是 `docs/tracker/live-data.js`，唯一消费方是本地看板 `北极星上线任务清单.html`（打开时才读），而"现在哪张工单在跑"这个信息用 5 分钟粒度自动备料并不必要。**已禁用，不是删除**：

- 处置：`Disable-ScheduledTask -TaskName UltimaAgentTrackerLive`，State 由 `Ready` → `Disabled`
- 禁用前最后一轮 19:51:03 正常写入（证明修复在真实周期上有效，且该轮无任何 powershell 子进程）
- 任务定义与 `scripts/tracker-live.py` 全部保留，需要时恢复：

  ```powershell
  Enable-ScheduledTask -TaskName UltimaAgentTrackerLive
  ```

- 也可随时手动生成一次最新快照：`tools\venv-openjarvis\Scripts\python.exe -B scripts\tracker-live.py`
- 关闭后看板的"当前焦点任务"会停留在占位文案（页面已注明"live-data.js 未加载不等于任务在跑"），属预期。

## 遗留

- `powershell.exe` 在我这个沙箱 shell 的 PATH 里不可用（`Get-Command powershell` 无结果），但计划任务环境（svchost → 系统 PATH）可用。这是环境差异，不是缺陷；但说明**"在我这里测不出来"不能推出"不会弹窗"**。
- 其它 pythonw 常驻进程（watchdog-loopguard、QueueObserver、UltimaManager-Service）本轮未逐一验证是否还有同类无窗标志缺失；它们当前未观测到弹窗。
