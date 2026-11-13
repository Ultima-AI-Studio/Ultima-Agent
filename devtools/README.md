# UltimaAgent developer tools

用户安装包必须保持零计划任务。开机自启只允许使用启动文件夹中的 `UltimaAgent.lnk`，不得通过 `schtasks` 注册任何 UltimaAgent 任务。

`devtools/watchdog.py` 仅用于未启动 HostShell、需要手动调试 voice 栈的开发机场景，禁止在用户安装包中注册或启动。开发机若手动执行其 `--install`，交付前必须执行 `--uninstall` 并确认 `UltimaAgent-Watchdog` 已不存在。
