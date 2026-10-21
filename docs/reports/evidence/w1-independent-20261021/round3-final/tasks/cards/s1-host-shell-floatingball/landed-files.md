# 落地文件清单

- NEW_FILE `src/host-shell/UltimaAgent.HostShell/FloatingBallEvidence.cs`：悬浮球占位渲染、Presenter 配置、系统 Caption 拖动区、DPI 尺寸与运行证据。
- MODIFY_FILE `src/host-shell/UltimaAgent.HostShell/MainWindow.xaml.cs`：接入 T4 浮球模式，保持 T2/T3 验证路径。
- NEW_FILE `logs/host-shell-repair-20261021T061613/probes/t4-drag-probe.ps1`：真实物理鼠标拖动与位置保持探针。
- NEW_FILE `logs/host-shell-repair-20261021T061613/{t4-build.log,t4-runtime.json,t4-floating-ball-ready.json,t4-drag-evidence.json,t4-floating-ball.png}`：最终构建、窗口、拖动、DPI 与截图证据。
- NEW_FILE `logs/host-shell-repair-20261021T061613/t4-*-attempt*.{log,json,png}`：失败/中间尝试原样保留，未用于 PASS。
- NEW_FILE `docs/reports/evidence/stage1-host-shell/T4-floatingball.md`：T4 Gate。
- MODIFY_FILE `docs/reports/stage1-host-shell-20261021.md`：登记 T4 PASS。
- MODIFY_FILE `tasks/cards/s1-host-shell-floatingball/task.md`：回填 receipt/retryCount。

未加入四状态动画、语音交互、小组件或业务智能。
