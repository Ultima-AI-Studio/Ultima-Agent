# 验收证据

## Gate

- Decision: `PASS`
- Build: `0 warnings / 0 errors / exit 0`
- Runtime: `WEBVIEW2_READY / runtime 155.0.4283.62 / exit 0`

## acceptance[]

- PASS：WinUI 主窗口内 WebView2 控件真实初始化；`t3-webview.json` 的 `initialized=true`，`t3-runtime.json` 含非零 HWND。
- PASS：离线 `NavigateToString` 占位页导航成功；`navigationSucceeded=true`、`externalRequests=0`。
- PASS：`t3-webview-render.png` 显示锁定深色页面、标题、状态与消息返回；SHA-256 `8b718796b77eabb453774bdbe126fa2c1ee6765115a5ff328442b74ac39c8773`。
- PASS：真实双向 WebMessage 顺序为 `web-ready`（Web→Host）、`host-ping`（Host→Web）、`web-received:host-ping`（Web→Host）。

## 自核闭环

首次编译将 .NET `FileStream` 传入要求 WinRT `IRandomAccessStream` 的 API 而失败；失败日志保留为 `t3-build-attempt1-failed.log`。改用 `InMemoryRandomAccessStream` 后重新构建为 0 warning / 0 error，未放宽门槛。


## 2026-10-21 维护重启后独立收口

Owner授权维护重启已实际完成；原59328创建身份已不存在，原生枚举与直接内核查询交叉确认，系统清理门解除。正式入口新正向PASS/exit0、缺Runtime负向FAIL/exit1，0警告/0错误、额外窗口0、当前开机后的后台身份保留。独立第四轮验收允许工单内部收口；最终证据见 `docs/reports/evidence/w1-post-reboot-closeout-20261021/` 与 `docs/reports/w1-independent-acceptance-20261021.md`。旧派发exit125/BLOCKED和历次失败保留。内部tag为wo-s1-host-shell-done；v0.1仍待Owner单独审批。
