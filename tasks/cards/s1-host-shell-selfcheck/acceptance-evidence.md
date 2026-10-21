# 验收证据

现行正式入口：`scripts/selfcheck-host-shell.py`，实际工具源码位于 `scripts/HostSelfcheck/`。维护后最终证据及独立判断见本文件末尾追加记录；历史PowerShell轮次保留。

## Gate

- Decision: `PASS`
- Chain: `build PASS → launch PASS → HWND PASS → exit PASS`
- Zero popup: `unexpectedVisibleWindowCount=0`

## acceptance[]

- PASS：Release x64 真实构建 exit 0、0 warning、0 error；构建 PID `29260`，`CreateNoWindow=true`、`WindowStyle=Hidden`、最大 `MainWindowHandle=0`。
- PASS：宿主 PID `26556` 启动，检测到 HWND `1967896`，6500 ms 后正常 exit 0。
- PASS：运行全程使用 WinEvent `EVENT_OBJECT_CREATE..SHOW` 加 25 ms 顶层可见窗口枚举（1141 个样本）；排除唯一产品 GUI 及几何包含于宿主窗口内的 WebView2 子渲染面后，意外可见窗口为 0。
- PASS：既有 Codex/Python/Node/dotnet/Ollama/Brain/Watchdog 名称集按 PID+启动时间比较，16/16 身份不变；未读命令行或凭证正文。
- PASS：`logs/selfcheck-host-shell-2026-10-21.md` 与 `.json` 均存在、非空、无未解析模板变量，独立回读状态为 PASS。

## 自核闭环

1. 首轮四步链均 PASS，但监听捕获 WebView2 的 `Chrome_WidgetWin_1` 子渲染面；因未有归属证据而按规则先判 FAIL。补记进程祖先、进程名和窗口几何后，仅允许宿主 HWND 与其内部 WebView2 后代渲染面，复跑意外窗口 0。
2. 第二轮运行 PASS，但 Markdown 证据变量被反引号转义为字面量；保留该轮证据，修正模板并第三次完整复跑，最终报告路径与两个 SHA-256 均为实值。


## Root 独立修复复验（2026-10-21，非 W1 批准）

独立负向测试FAIL/exit1，最终正常自检PASS/exit0；意外可见窗口0、既有进程身份13/13保持。失败记录追加保存且不可被READY覆盖。

最终报告：`logs/host-shell-reviewfix-20261021T065131/final-report.md`。旧执行端 Gate 为该次历史自检结果，不覆盖本段限制。

## 2026-10-21 现行入口独立验收

正式Python/C#入口的正向 `logs/w1-delivered-selfcheck-verified-path-positive-20261021T0324/entry-result.json` 为PASS/exit0，缺Runtime负向 `logs/w1-delivered-selfcheck-verified-path-negative-20261021T0325/entry-result.json` 为FAIL/exit1，均意外窗口0。`source-before.json`与运行后源码清单逐字节一致；实际进程路径经QueryFullProcessImageNameW读回，启动EXE/DLL哈希与产物一致。监控异常2项故障回归由独立审计者重跑通过。

独立结论见 `docs/reports/evidence/w1-independent-20261021/round3-final/result.json`：U01-U05功能PASS；整单BLOCKED。旧pwsh59328仍wait258/exitTime0、精确终止AccessDenied5；没有将工具返回成功或exitCode1解释为真实终止。旧PowerShell历史PASS及本轮挂起记录均保留。


## 2026-10-21 维护重启后独立收口

Owner授权维护重启已实际完成；原59328创建身份已不存在，原生枚举与直接内核查询交叉确认，系统清理门解除。正式入口新正向PASS/exit0、缺Runtime负向FAIL/exit1，0警告/0错误、额外窗口0、当前开机后的后台身份保留。独立第四轮验收允许工单内部收口；最终证据见 `docs/reports/evidence/w1-post-reboot-closeout-20261021/` 与 `docs/reports/w1-independent-acceptance-20261021.md`。旧派发exit125/BLOCKED和历次失败保留。内部tag为wo-s1-host-shell-done；v0.1仍待Owner单独审批。
