# 验收证据

## Gate

- Decision: `PASS`
- Build: `0 warnings / 0 errors / exit 0`
- Runtime: `FLOATING_BALL_READY / DRAG_PASS / host exit 0`

## acceptance[]

- PASS：运行态 `OverlappedPresenter` 报告 `HasBorder=false`、`HasTitleBar=false`、`IsAlwaysOnTop=true`、`IsResizable=false`；见 `t4-floating-ball-ready.json`。
- PASS：探针使用 `SetCursorPos + LEFTDOWN + 16 步移动 + LEFTUP` 的真实物理鼠标输入，窗口由 `(3522,1770)` 移至 `(3362,1670)`，实际位移 `(-160,-100)`；见 `t4-drag-evidence.json`。
- PASS：松手后等待 1 秒，位置漂移 `(0,0)`，尺寸始终 `270×270`。
- PASS：真机为 144 DPI（150%）；180 逻辑像素×1.5=`270` 物理像素，实测误差 0。
- PASS：`t4-floating-ball.png` 视觉回读显示蓝色圆形占位、品牌 U 标记和绿色就绪点；SHA-256 `21fb8f52dbebb7379bdc24857af26125ba6d07c57a48d306602389bdf524aee2`。

## 自核闭环

1. 初次编译因 lambda 下划线参数被当作变量而非 discard 失败；改为具名参数后 0 warning / 0 error。
2. 初次 WebMessage→`WM_NCLBUTTONDOWN` 路径的真实鼠标位移为 0，未判通过；改用 Windows App SDK `InputNonClientPointerSource` 原生 Caption 区域后，相同输入得到准确位移并保持。
3. 原证据将 Presenter 状态与旧式 Win32 style 位错误合取而误报；最终证据同时保留两组原始值，以 WinUI Presenter 的权威属性判定边框/置顶，未删除误报证据。


## Root 独立修复复验（2026-10-21，非 W1 批准）

最终范围：真实144DPI拖动和位置保持通过；跨DPI/跨屏仍未验证。Caption区域已在尺寸变化时更新；FB-03完整验收保留。

最终报告：`logs/host-shell-reviewfix-20261021T065131/final-report.md`。旧执行端 Gate 为该次历史自检结果，不覆盖本段限制。
