# 落地文件清单

- NEW_FILE `src/host-shell/UltimaAgent.HostShell.sln`：x64 Debug/Release 解决方案。
- NEW_FILE `src/host-shell/UltimaAgent.HostShell/UltimaAgent.HostShell.csproj`：net8 WinUI 3 unpackaged self-contained x64 工程，锁定 Windows App SDK `1.8.260921001`。
- NEW_FILE `src/host-shell/UltimaAgent.HostShell/{App.xaml,App.xaml.cs,MainWindow.xaml,MainWindow.xaml.cs,RuntimeEvidence.cs,app.manifest}`：启动入口、主窗口占位、运行证据与 PerMonitorV2 声明。
- NEW_FILE `src/host-shell/UltimaAgent.HostShell/Assets/{HarmonyOS_Sans.ttf,HarmonyOS_Sans_SC.ttf}`：从权威品牌库复制的打包字体资产，源库未修改。
- NEW_FILE `src/host-shell/README.md`：构建入口与宿主薄壳边界。
- NEW_FILE `logs/host-shell-repair-20261021T061613/{t2-build.log,t2-runtime.json,t2-main-window-render.png,t2-uia-tree.json}`：最终构建与真实 GUI 证据。
- NEW_FILE `docs/reports/evidence/stage1-host-shell/T2-winui3-init.md`：T2 Gate。
- MODIFY_FILE `docs/reports/stage1-host-shell-20261021.md`：登记 T2 PASS。
- MODIFY_FILE `tasks/cards/s1-host-shell-winui3-init/task.md`：回填 receipt/retryCount。

`bin/obj` 为任务卡声明的正常构建侧效应。未复制 Topo 宿主代码，未加入业务智能、WebView2 或悬浮球。


## 重启后最终证据

- `docs/reports/evidence/w1-post-reboot-closeout-20261021/`：维护、正负向、源/产物绑定及清理证据副本。
- `docs/reports/evidence/w1-independent-20261021/round4-post-reboot/`：独立验收。
- 本任务产品实现未在本轮变更，旧文件和失败证据保留。
