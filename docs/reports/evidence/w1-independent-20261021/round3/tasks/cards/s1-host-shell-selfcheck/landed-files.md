# 落地文件清单

- NEW_FILE `scripts/selfcheck-host-shell.ps1`：隐藏构建、产品启动、窗口检出、正常退出、WinEvent 监听、可见窗口枚举与进程身份保护。
- NEW_FILE `logs/selfcheck-host-shell-2026-10-21.md`：人读自检报告。
- NEW_FILE `logs/selfcheck-host-shell-2026-10-21.json`：结构化全链证据。
- NEW_FILE `logs/host-shell-repair-20261021T061613/{t5-build.log,t5-runtime.json,t5-floating-ball-ready.json,t5-floating-ball.png}`：最终构建和产品运行证据。
- NEW_FILE `logs/host-shell-repair-20261021T061613/t5-*-attempt*.{md,json,log,png}`：失败/报告修正轮原样保留，未用于最终 PASS。
- NEW_FILE `docs/reports/evidence/stage1-host-shell/T5-selfcheck.md`：T5 Gate。
- MODIFY_FILE `docs/reports/stage1-host-shell-20261021.md`：登记 T5 PASS/W1 待验。
- MODIFY_FILE `tasks/cards/s1-host-shell-selfcheck/task.md`：回填 receipt/retryCount。

自检没有启动队列引擎或语音链路，没有读取进程命令行或凭证正文。
