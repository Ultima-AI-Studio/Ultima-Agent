# 落地文件清单

- MODIFY_FILE `src/host-shell/UltimaAgent.HostShell/UltimaAgent.HostShell.csproj`：显式锁定缓存 WebView2 SDK `1.0.3179.45`。
- MODIFY_FILE `src/host-shell/UltimaAgent.HostShell/MainWindow.xaml.cs`：嵌入 WinUI WebView2 控件并保持 T2 原生占位验证分支。
- NEW_FILE `src/host-shell/UltimaAgent.HostShell/WebViewEvidence.cs`：Runtime 初始化、离线 `NavigateToString`、真实截图与 WebMessage 往返证据。
- NEW_FILE `logs/host-shell-repair-20261021T061613/{t3-build.log,t3-runtime.json,t3-webview.json,t3-webview-render.png}`：最终构建和运行证据。
- NEW_FILE `logs/host-shell-repair-20261021T061613/t3-build-attempt1-failed.log`：首次流类型编译失败的保留证据。
- NEW_FILE `docs/reports/evidence/stage1-host-shell/T3-webview2.md`：T3 Gate。
- MODIFY_FILE `docs/reports/stage1-host-shell-20261021.md`：登记 T3 PASS。
- MODIFY_FILE `tasks/cards/s1-host-shell-webview2/task.md`：回填 receipt/retryCount。

未实现业务页面、UI DSL、意图/编排/记忆/模型推理或 T4 悬浮球行为。


## 重启后最终证据

- `docs/reports/evidence/w1-post-reboot-closeout-20261021/`：维护、正负向、源/产物绑定及清理证据副本。
- `docs/reports/evidence/w1-independent-20261021/round4-post-reboot/`：独立验收。
- 本任务产品实现未在本轮变更，旧文件和失败证据保留。
