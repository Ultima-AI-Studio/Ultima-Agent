# 验收证据

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
