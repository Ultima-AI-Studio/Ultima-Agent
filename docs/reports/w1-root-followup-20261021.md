# W1 主监督续修回执 · 2026-10-21

W2已独立通过35项/62回归并内部收口。W1第三轮独立结论为U01-U05功能通过、整单BLOCKED；不提交版本冻结审批，不代签Owner。

## 已落地修复

正式交付 `scripts/selfcheck-host-shell.py` 与 `scripts/HostSelfcheck/`，替代本机启动挂起的PowerShell推荐入口。保留旧实现和失败历史。Python入口编译并调用C#真实构建、启动、窗口、原生退出链；复用已独立验收的WindowMonitor观察完整进程树，含WinEvent及枚举。构建摘要严格匹配数字0，监控start/stop错误强制结构化FAIL；两项故障回归通过。独立代码复查没有剩余P1/P2。

正式正向 `logs/w1-delivered-selfcheck-verified-path-positive-20261021T0324/` PASS/exit0；缺WebView2负向 `logs/w1-delivered-selfcheck-verified-path-negative-20261021T0325/` FAIL/exit1，均额外窗口0。两轮source-before及运行后源码哈希一致；QueryFullProcessImageNameW真实读取运行路径，EXE/DLL哈希与最终鼠标会话一致。旧bound-positive的actualProcessExecutable=null失败边界保留，新结果不覆盖它。

最终原生截图 `logs/w1-final-native-2026-10-21T03-08-13-206Z/` 显示深色客户区、标题及中文就绪文字。真实鼠标 `logs/w1-final-mouse-20261021T0313/` 从(90,90)拖到(30,30)逻辑坐标，窗口物理位置移动(-90,-90)，270物理尺寸和144DPI保持，24秒后零漂移，AltF4关闭后没有可见窗口。跨DPI另由宿主真实AppWindow移动验证144/96/96三屏、保持和恢复，不伪造WM_DPICHANGED。

## 派发和阻塞原样保存

真实工程派发PID17252完成报告和全部计划后，最后停在update_plan约十分钟；报告/源码稳定且最终挂起调用不包含源码修改。监督端核验同句柄创建身份后仅结束该工单进程。派发器实际写入exit125、receipt_valid=false、BLOCKED，没有伪造业务完成；证据 `tasks/queue/runs/wo-s1-host-shell-20261021T023427316731Z/`。这证明真实派发接入与失败闭合，不代表该运行成功。

旧自检pwsh59328创建身份134370250506523457仍存在。`logs/w1-host-resume-20261021T024845Z/after/root-kernel-process-state.json`、`root-targeted-cleanup.json`及`root-post-dispatch-exit-kernel-state.json`记录：exitCode1，但内核wait258/exitTime0；同句柄精确TerminateProcess返回AccessDenied5。独立W1审计者再次核实相同结果。不能据此声称已退出，也没有扩大到结束其他开发进程或修改系统。

## 收口条件

处理或经获准维护窗口重启后确认旧pwsh残留消失，复跑正式自检并回读后台身份，再由独立审计签署W1、创建宿主内部tag。W1/W2均完整通过后才提交v0.1冻结审批；当前只保留审批准备材料。未创建v0.1-frozen，未启动等待冻结的后续六工单。
