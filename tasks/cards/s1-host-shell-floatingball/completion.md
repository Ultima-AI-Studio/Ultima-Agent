# 完成语

T4 悬浮球占位窗口已完成：Windows App SDK Presenter 运行态确认无边框、无标题栏、置顶且不可缩放；真实物理鼠标序列拖动窗口 `(-160,-100)`，松手 1 秒后位置保持；144 DPI 尺寸换算精确匹配，并取得真实 WebView2 像素截图。


## 2026-10-21 维护重启后独立收口

Owner授权维护重启已实际完成；原59328创建身份已不存在，原生枚举与直接内核查询交叉确认，系统清理门解除。正式入口新正向PASS/exit0、缺Runtime负向FAIL/exit1，0警告/0错误、额外窗口0、当前开机后的后台身份保留。独立第四轮验收允许工单内部收口；最终证据见 `docs/reports/evidence/w1-post-reboot-closeout-20261021/` 与 `docs/reports/w1-independent-acceptance-20261021.md`。旧派发exit125/BLOCKED和历次失败保留。内部tag为wo-s1-host-shell-done；v0.1仍待Owner单独审批。
