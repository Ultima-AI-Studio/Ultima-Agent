# 任务卡：s1-host-shell-selfcheck

- **task_id**：s1-host-shell-selfcheck
- **stage**：S1（阶段一 v0.1）
- **标题**：壳自检脚本（一键核验壳可起）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为宿主壳一键自检

## goal

实现壳自检脚本：一键核验宿主壳可启动（构建 → 启动 → 窗口出现 → 退出），输出自检报告。禁止：不实现队列引擎自检（工单①）、不实现语音自检（v0.2）、脚本全程无窗口（ops-selfcheck §3）。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 自检脚本跑通（build → launch → window → exit 全链 PASS）
- [x] ACCEPT: 自检报告落盘 logs/selfcheck-host-shell-<date>.md
- [x] ACCEPT: 脚本启动无窗口（CREATE_NO_WINDOW / Hidden）

## dependsOn[]

- s1-host-shell-winui3-init（T2 骨架）
- s1-host-shell-webview2（T3 渲染）
- s1-host-shell-floatingball（T4 悬浮球）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\scripts\`（自检脚本）
- `H:\UltimaAI\UltimaAgent\logs\`（自检报告）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-host-shell-selfcheck\`（任务卡自身）
- （N1 修正：构建产物 obj/bin 属工程既有侧效应，不视为越界；源代码写入仅限以上声明域）

## priority

- 50（默认）

## reasoningEffort

- medium（脚本串联 + 无窗口封装）

## category + skill

- category: host-shell · skill: eng.infra（运维工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: T5 三项封闭验收均由全链运行、WinEvent/窗口枚举和独立报告回读证明，提交监督端 W1 独立验收
- stdoutText: PASS — build 0/0；PID `26556`；HWND `1967896`；exit 0；意外可见窗口 0；既有开发进程身份 16/16 不变
- evidence: `logs/selfcheck-host-shell-2026-10-21.{md,json}`、`logs/host-shell-repair-20261021T061613/t5-build.log`、`t5-runtime.json`、`t5-floating-ball-ready.json`
- acceptance 逐项核对: SC-01 PASS；SC-02 PASS；SC-03 PASS

## retryCount

- 2（首次归属判定把 WebView2 子渲染面误列额外窗口；第二轮修正报告模板字面量并复跑全链）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| SC-01 脚本串联 | build→launch→window→exit 全链 | 全链 PASS | 自检输出 |
| SC-02 零弹窗封装 | 启动点 CREATE_NO_WINDOW/Hidden + 运行期窗口枚举全程计数 0 | 前台零弹窗（闪一下都不行，宿主 GUI 除外） | 窗口枚举输出 |
| SC-03 报告落盘 | 自检报告 logs/selfcheck-host-shell-<date>.md | 报告存在 | 文件核对 |

## 2026-10-21 W1 恢复追加证据

- 固定缓存 `pwsh.exe -NoProfile -NonInteractive` 实际启动后在脚本读取前挂起；仅定向终止本轮 PID 55476→59328 进程树，失败及终止回执保留于 `logs/w1-host-resume-20261021T024845Z/t3-selfcheck-*.json`。
- 未覆盖失败事实；改用本轮证据目录内 .NET 等价探针执行真实 build→launch→window→exit。最终 `t3-selfcheck-equivalent-attempt2/result.json` 为 PASS：0 warning/0 error、宿主 exit 0、本轮进程树额外可见窗口 0、后台创建身份 30/30 不变。
- 探针未截取桌面、未发送鼠标键盘输入；悬浮球图像只用允许的 WebView2 `CapturePreview`。最终鼠标拖动和原生窗口显示仍由 root 独立复核。
