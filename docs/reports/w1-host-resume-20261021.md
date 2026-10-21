# W1 宿主壳恢复交接报告 · 2026-10-21

> 工单：`wo-s1-host-shell`  
> 执行端结论：**阻塞（BLOCKED）**。宿主实现、真实构建、WebView2、物理跨 DPI、原生退出和等价零额外窗口自检均已得到运行证据；但本轮固定缓存 `pwsh` 自检进程 PID 59328 仍以 1 个线程被系统枚举，精确终止接口返回互相矛盾的“成功 / 无运行实例 / ESRCH”。在它被独立确认消失前，本工单不能闭合。  
> W1：未签署；Owner 冻结：未签署；未发布、未打 tag、未启动后续工单。

## 1. 范围与边界

- 只执行 `tasks/queue/wo-s1-host-shell.md` 的本轮 W1 恢复，不执行队列引擎、语音、文本或后续工单。
- 未修改 `App.xaml`、`docs/INDEX.md`、W2 报告、`_shared`、全局登记、队列引擎/测试、vault、模型或 Topo Backup。
- 未执行桌面截图、CopyFromScreen、PowerShell UIAutomation、鼠标/键盘输入、系统 DPI 或显示设置修改。
- WebView2 `CapturePreview` 只作为组件渲染证据，不据此宣称桌面视觉通过。
- root 既有 `logs/w1-native-2026-10-21T02-26-42-926Z/native-window.json` 已记录宿主自身窗口内深色客户区、`Ultima Agent` 标题和“宿主壳已就绪”；因此旧桌面白色抓屏不再作为已证实产品显示缺陷，本轮未为其修改资源或外观。

## 2. T0 修改前基线

- 修改前 38 个源码/宿主脚本/五卡文件副本与 SHA-256：`logs/w1-host-resume-20261021T024845Z/before/source-manifest.json`。
- 修改前 WMI 进程基线：`before/process-baseline.json`，字段含 PID、CreationDate、命令行及可执行路径。
- 最终对照的 7 个受保护后台身份全部保持原 PID+CreationDate：UltimaScan 日任务 2 个、watchdog 父进程 1 个、本工单 dispatcher/guardian/Codex 链 4 个；见 `after/process-preservation.json`。
- 等价自检窗口内另核对 30/30 个 Codex/Python/Node/dotnet/Ollama 等创建身份不变；未停止、重启或替换其他后台开发进程。

## 3. T1 真实 DPI 验收仪器

新增 `DpiAcceptanceEvidence.cs`，并以 `ULTIMA_HOST_DPI_ACCEPTANCE=1` 作为唯一入口。默认启动、WebView 模式和普通 FloatingBall 模式不启用该流程。

仪器行为：

1. `EnumDisplayMonitors/GetMonitorInfoW` 读取真实物理屏和工作区。
2. 宿主自身调用 `Microsoft.UI.Windowing.AppWindow.Move` 移动窗口。
3. 每次用 `GetDpiForWindow`、`GetWindowRect` 和当前 Caption 区尺寸回读；连续稳定后保持 1 秒，再次读取漂移。
4. 完成后移动回原屏并恢复原矩形，再保持 1 秒核对恢复漂移。
5. 不发送 `WM_DPICHANGED`，不改变系统 DPI/显示设置。

实际拓扑与授权一致：DISPLAY3 外框 `(0,0)-(3840,2160)`、工作区高 2088、144 DPI；DISPLAY2 外框 `(3840,0)-(6400,1440)`、工作区高 1392、96 DPI；DISPLAY1 外框 `(6400,0)-(8960,1440)`、工作区高 1392、96 DPI。

## 4. T2 首次复现与修复判断

第一次真正启动产品的复现即通过，证据为 `t2-initial-reproduction-attempt3/t2-initial-dpi-acceptance.json`：

| 目标屏 | 实测 DPI | 物理尺寸 | 逻辑尺寸 | Caption 区 | 1 秒保持漂移 |
|---|---:|---:|---:|---:|---:|
| DISPLAY3 | 144 | 270×270 | 180×180 | 270×270 | 全 0 |
| DISPLAY2 | 96 | 180×180 | 180×180 | 180×180 | 全 0 |
| DISPLAY1 | 96 | 180×180 | 180×180 | 180×180 | 全 0 |

恢复到 DISPLAY3 原始矩形 `(3522,1770)-(3792,2040)`，恢复保持漂移全 0。由于尺寸和拖动 Caption 区均随实际 DPI 正确更新，未进入 FloatingBall 产品配置修复分支；逻辑直径仍为工单原型的 180，未重做外观。

两次产品启动前的 launcher 失败均保留：前两种 `cmd /c` 参数组合在宿主启动前被命令行语法拒绝，见 `t2-initial-reproduction/` 与 `t2-initial-reproduction-attempt2/`；第三种直接 EXE 启动持有宿主 PID 56400并成功完成真实复现。

## 5. T3 最终运行证据

### 5.1 构建

- 首次含 restore 构建因执行宿主缺 `USERPROFILE`/NuGet 路径而失败：`t3-final-build/build.log`，0 warning / 1 error，原文为 `Value cannot be null. (Parameter 'path1')`。
- 仅补齐构建进程环境后复验：`t3-final-build-attempt2/build.log`，真实 restore + Release `win-x64` 成功，0 warning / 0 error；未使用 `NoWarn`。

### 5.2 WebView2

- 宿主 PID 58236，原生 exit 0。
- Runtime `155.0.4283.62`；离线 `NavigateToString` 渲染成功；`web-ready → host-ping → web-received:host-ping`；外部请求 0。
- 组件预览 SHA-256：`8b718796b77eabb453774bdbe126fa2c1ee6765115a5ff328442b74ac39c8773`。
- 证据：`t3-webview/t3-webview-webview.json`、`t3-webview-runtime.json`、`host-result.json`。

### 5.3 最终物理跨 DPI

`t3-dpi-final/t3-dpi-dpi-acceptance.json` 再次通过：DISPLAY3 144 DPI/270×270；DISPLAY2/1 96 DPI/180×180；逻辑尺寸全为 180×180；Caption 区同步；三处 1 秒漂移全 0；恢复漂移全 0；宿主 PID 57644 原生 exit 0。

### 5.4 build→launch→window→exit 与零额外窗口

固定缓存 `pwsh.exe -NoProfile -NonInteractive` 的既有 `selfcheck-host-shell.ps1` 启动尝试在脚本读取前挂起且没有创建证据目录。没有覆盖该失败；`t3-selfcheck-launcher-attempt1.json`、`t3-selfcheck-targeted-termination.json` 和 `after/residual-pwsh-*.json/txt` 保留全过程。

随后使用仅位于本轮证据目录的 .NET 等价探针执行同一真实链路，最终 `t3-selfcheck-equivalent-attempt2/result.json` 通过：

- build PID 58768，exit 0，0 warning / 0 error，最大主窗口句柄 0；
- 宿主 PID 49364，HWND 3809162，FloatingBall 真实 WebView2 初始化，原生 exit 0，未使用定向杀进程；
- 25 ms `EnumWindows` + Toolhelp32 父链枚举，本轮进程树额外可见窗口 0；宿主主窗口及其按 HWND 历史矩形归属的 WebView2 渲染表面是允许的产品窗口；
- 后台创建身份 30/30 保留；桌面像素未捕获。

探针首次运行的失败同样保留在 `t3-selfcheck-equivalent/result.json`：产品窗口/退出/30/30 均已通过，但探针对乱码构建摘要和 WebView2 移动中瞬时表面归属判定过严。最终探针固定英文构建输出，并只按宿主 HWND 矩形历史验证 WebView2 表面；未放宽为任意后代窗口。

## 6. 当前阻塞与 W1 交接门

### 执行端不能闭合的阻塞

- 固定缓存 `pwsh` PID 59328 由本轮 PID 55476 包装进程启动。根树 `/T /F` 曾返回成功，但 PID 59328 仍被 `tasklist` 和 WMI 枚举；后续精确 `taskkill` 返回“没有正在运行的实例”，Desktop Commander 返回 `ESRCH`。
- 最终 WMI 状态仍显示 `threads=1; handles=458; working_set=69091328`。在该 PID 消失或由 Owner/root 确认其系统终止状态前，不能宣称“仅本轮测试进程已全部退出”。

### 仍由 root/独立验收完成

1. 清理或独立确认 PID 59328 已从 `tasklist`/WMI 消失，再重做最终进程回读。
2. root 通过 Computer Use 在最终构建上复核真实鼠标拖动（含跨 DPI 后拖动区）及最终原生窗口显示；执行端未发送输入，不冒称完成。
3. 独立复核本报告、源码哈希与证据后决定 W1；W2 第二轮 35 项技术通过不替代本门。
4. Owner 冻结、工单行政收尾、tag 与发布均未执行。

## 7. 改动摘要与越界声明

产品源码改动仅为显式验收仪器及读回：新增 `DpiAcceptanceEvidence.cs`；`MainWindow.xaml.cs` 接入显式开关；`FloatingBallEvidence.cs` 暴露实际 Caption 区读回；`src/host-shell/README.md` 记录用法。`App.xaml`、资源、默认模式与 FloatingBall 180 逻辑直径未改。

五张 `s1-host-shell-*` 任务卡只追加本轮证据。正式证据索引及 SHA-256 位于 `docs/reports/evidence/w1-host-resume-20261021T024845Z/`。

越界声明：无。未发布、未打任何 tag、未签 W1、未启动语音/文本/后续工单。
