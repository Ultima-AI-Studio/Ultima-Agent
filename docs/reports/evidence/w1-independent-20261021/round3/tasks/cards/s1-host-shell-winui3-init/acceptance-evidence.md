# 验收证据

## Gate

- Decision: `PASS`
- Build: `0 warnings / 0 errors / exit 0`
- Runtime: `WINDOW_READY / native HWND != 0 / exit 0`

## acceptance[]

- PASS：解决方案与工程真实构建；`logs/host-shell-repair-20261021T061613/t2-build.log`。
- PASS：App 启动入口与 960×640 主窗口真实运行；`t2-runtime.json`。
- PASS：应用内像素截图显示锁定深色背景与原生占位；`t2-main-window-render.png`，SHA-256 `d57a9f4f46f9b888bf50f4f90f58eca003e86496907c909d6d6b94e790a50681`。
- PASS：独立 UI Automation 树含可见 Window/Pane 与两个 TextBlock（“Ultima Agent”“宿主壳已就绪”）；`t2-uia-tree.json`。
- PASS：工程只含启动、原生渲染与协议边界声明，无意图/编排/记忆/模型推理实现。

## 自核闭环

1. 初次编译因 `LibraryImport` 需要 unsafe 失败；改为最小 `DllImport`，未放宽编译门。
2. 外部 PrintWindow/CopyFromScreen 对 WinUI 合成层返回白图；显式挂载 Content 后，UIA 读回证明内容可见，并用应用内 RenderTargetBitmap 获得真实像素证据。
3. 最终重新构建仍为 0 warning / 0 error；失败日志和不完整截图均保留，未用于 PASS。


## Root 独立修复复验（2026-10-21，非 W1 批准）

独立复验：移除 NETSDK1198 屏蔽后实际0警告0错误；窗口/UIA/控件渲染通过，桌面显示仍未确证，不把白色系统抓屏丢弃。

最终报告：`logs/host-shell-reviewfix-20261021T065131/final-report.md`。旧执行端 Gate 为该次历史自检结果，不覆盖本段限制。
