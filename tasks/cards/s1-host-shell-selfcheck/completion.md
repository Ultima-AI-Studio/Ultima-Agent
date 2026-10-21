# 完成语

T5 宿主壳一键自检已完成：隐藏构建→启动产品 GUI→检出非零 HWND→定时正常退出全链 PASS；构建进程 `MainWindowHandle` 全程为 0，WinEvent 事件钩子与 25 ms 可见顶层窗口枚举确认意外窗口 0；报告和 JSON 已落盘并独立回读。

## 2026-10-21 正式入口续修（历史结果保留）

当前交付改用 `scripts/selfcheck-host-shell.py` 与 `scripts/HostSelfcheck/`。原PowerShell启动在本机挂起，不能继续作为现行可用入口。新入口正向PASS/exit0、缺Runtime负向FAIL/exit1；WinEvent加完整进程树枚举额外窗口0，监控故障结构化失败回归2/2通过。第三轮独立验收U05功能PASS；旧自检pwsh59328内核未退出，整单W1仍BLOCKED，不据此代签工单或版本冻结。


## 2026-10-21 维护重启后独立收口

Owner授权维护重启已实际完成；原59328创建身份已不存在，原生枚举与直接内核查询交叉确认，系统清理门解除。正式入口新正向PASS/exit0、缺Runtime负向FAIL/exit1，0警告/0错误、额外窗口0、当前开机后的后台身份保留。独立第四轮验收允许工单内部收口；最终证据见 `docs/reports/evidence/w1-post-reboot-closeout-20261021/` 与 `docs/reports/w1-independent-acceptance-20261021.md`。旧派发exit125/BLOCKED和历次失败保留。内部tag为wo-s1-host-shell-done；v0.1仍待Owner单独审批。
