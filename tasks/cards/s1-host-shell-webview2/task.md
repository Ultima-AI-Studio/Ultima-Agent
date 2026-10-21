# 任务卡：s1-host-shell-webview2

- **task_id**：s1-host-shell-webview2
- **stage**：S1（阶段一 v0.1）
- **标题**：WebView2 嵌入渲染就绪
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为宿主壳 WebView2 渲染层

## goal

在 WinUI3 壳中嵌入 WebView2 控件，加载空页/占位 HTML 渲染成功。禁止：不实现业务页面（后续工单）、不实现悬浮球窗口（T4）、不写 UI 组件树 DSL（v0.4 U15）。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: WebView2 控件嵌入主窗口成功（Runtime 初始化无异常）
- [x] ACCEPT: 加载空页渲染成功（渲染截图/日志可证）
- [x] ACCEPT: 宿主与 WebView2 双向通信通道就绪（WebMessage 往返一次成功）

## dependsOn[]

- s1-host-shell-winui3-init（T2 工程骨架）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\host-shell\`（WebView2 集成代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-host-shell-webview2\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- medium（控件集成 + 通信通道，规则明确）

## category + skill

- category: host-shell · skill: eng.code + eng.ui 协作

## receipt（完成时由 CodeX 回填）

- reviewReason: T3 三项封闭验收均由真实 Release 构建和 WebView2 Runtime 行为证明，提交监督端 W1 独立验收
- stdoutText: PASS — WebView2 Runtime `155.0.4283.62` 初始化；离线占位页渲染；`web-ready → host-ping → web-received:host-ping`
- evidence: `logs/host-shell-repair-20261021T061613/t3-build.log`、`t3-runtime.json`、`t3-webview.json`、`t3-webview-render.png`
- acceptance 逐项核对: WV-01 PASS；WV-02 PASS；WV-03 PASS

## retryCount

- 1（首次编译暴露 WinRT 随机访问流类型不匹配；修正后 0 warning / 0 error）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| WV-01 控件嵌入 | WebView2 控件嵌入主窗口 | Runtime 初始化无异常 | 运行日志 |
| WV-02 空页渲染 | 加载空页/占位 HTML | 渲染成功 | 渲染截图 |
| WV-03 双向通信 | WebMessage 往返一次成功 | 宿主↔Web 通信通 | 往返记录 |

## 2026-10-21 W1 恢复追加证据

- `logs/w1-host-resume-20261021T024845Z/t3-webview/t3-webview-webview.json`：Runtime `155.0.4283.62`、离线渲染成功、`web-ready → host-ping → web-received:host-ping`、externalRequests=0。
- `t3-webview-render.png` 仅为 WebView2 `CapturePreview` 组件证据；本轮未执行桌面截图，也不据此宣称桌面视觉通过。
- 宿主 PID 58236 原生 exit 0，见同目录 `host-result.json`。
