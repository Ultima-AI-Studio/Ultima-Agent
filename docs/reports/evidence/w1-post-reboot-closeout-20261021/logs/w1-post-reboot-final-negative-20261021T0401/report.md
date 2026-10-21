# 宿主壳最终自检

- 结论：失败
- 构建：通过，0 warning / 0 error
- 启动与窗口：失败
- 原生退出：失败，exit 1
- 本轮进程树额外可见窗口：0
- 后台开发进程创建身份：通过，10/10 保留
- 桌面截图：未执行；悬浮球图像仅来自 WebView2 CapturePreview。

这是执行端自检证据，不代表 root 已完成最终鼠标拖动或 W1 签署。
正式scripts入口复核：FAIL；WinEvent与枚举样本24，额外窗口0。源码与产物哈希见entry-result.json。
