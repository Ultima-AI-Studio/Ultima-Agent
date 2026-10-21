# 完成语

T5 宿主壳一键自检已完成：隐藏构建→启动产品 GUI→检出非零 HWND→定时正常退出全链 PASS；构建进程 `MainWindowHandle` 全程为 0，WinEvent 事件钩子与 25 ms 可见顶层窗口枚举确认意外窗口 0；报告和 JSON 已落盘并独立回读。

## 2026-10-21 正式入口续修（历史结果保留）

当前交付改用 `scripts/selfcheck-host-shell.py` 与 `scripts/HostSelfcheck/`。原PowerShell启动在本机挂起，不能继续作为现行可用入口。新入口正向PASS/exit0、缺Runtime负向FAIL/exit1；WinEvent加完整进程树枚举额外窗口0，监控故障结构化失败回归2/2通过。第三轮独立验收U05功能PASS；旧自检pwsh59328内核未退出，整单W1仍BLOCKED，不据此代签工单或版本冻结。
