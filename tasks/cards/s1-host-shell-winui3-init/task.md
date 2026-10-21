# 任务卡：s1-host-shell-winui3-init

- **task_id**：s1-host-shell-winui3-init
- **stage**：S1（阶段一 v0.1）
- **标题**：WinUI3 工程初始化（宿主壳工程骨架）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为宿主壳工程骨架（自研，不采 Top 代码 legacy-topo M7 只读）

## goal

初始化 WinUI3 宿主壳工程骨架：解决方案结构、项目引用、App 启动入口、主窗口占位。禁止：不嵌入 WebView2（T3）、不实现悬浮球（T4）、不复用 Top 宿主代码（legacy-topo M7 只读，只借鉴架构经验）。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 工程可构建（dotnet build 零错误零警告）
- [x] ACCEPT: App 启动入口存在并可运行（空主窗口显示）
- [x] ACCEPT: 解决方案结构符合 architecture.md 宿主壳分层

## dependsOn[]

- s1-host-shell-envcheck（T1 环境门全绿后）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\host-shell\`（宿主壳工程）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-host-shell-winui3-init\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（工程骨架搭建，多文件结构）

## category + skill

- category: host-shell · skill: eng.code（智能工程师）+ eng.ui 协作（窗口骨架）

## receipt（完成时由 CodeX 回填）

- reviewReason: 新建独立 WinUI 3/.NET 8 unpackaged self-contained x64 宿主薄壳；固定 Windows App SDK 1.8.260921001；真实构建、启动、HWND/UIA 与应用内像素渲染均通过。
- stdoutText: T2 完成，Release x64 构建 0 warning / 0 error；主窗口 WINDOW_READY、真实占位渲染可见、退出码 0。
- evidence: `logs/host-shell-repair-20261021T061613/t2-build.log`；`t2-runtime.json`；`t2-main-window-render.png`；`t2-uia-tree.json`；`docs/reports/evidence/stage1-host-shell/T2-winui3-init.md`
- acceptance 逐项核对: 工程可构建 PASS；App 入口与主窗口真机运行 PASS；宿主薄壳分层 PASS。

## retryCount

- 2（上限 2；已在限内闭环）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| WI-01 解决方案结构 | 创建 WinUI3 解决方案骨架 | 结构符合 architecture.md 分层 | 目录树 |
| WI-02 项目引用 | 宿主壳项目依赖引用正确 | 引用无缺漏 | 构建输出 |
| WI-03 App 启动入口 | App 类 + 主窗口占位 | 可运行、空主窗口显示 | 运行截图 |
| WI-04 构建零警告 | dotnet build 零错误零警告 | 构建全绿 | 构建输出 |

## 2026-10-21 W1 恢复追加证据

- 最终完整 Release/`win-x64` 构建（未使用 `NoWarn`）：`logs/w1-host-resume-20261021T024845Z/t3-final-build-attempt2/build.log`，编译器 0 warning / 0 error。
- 原生窗口全链复验：`t3-selfcheck-equivalent-attempt2/result.json`，宿主 PID 49364、HWND 3809162、原生 exit 0。
- root 已有宿主自身窗口捕获证明深色背景、标题及“宿主壳已就绪”；本轮未重做桌面截图，最终显示仍留 root 复核。


## 2026-10-21 维护重启后独立收口

Owner授权维护重启已实际完成；原59328创建身份已不存在，原生枚举与直接内核查询交叉确认，系统清理门解除。正式入口新正向PASS/exit0、缺Runtime负向FAIL/exit1，0警告/0错误、额外窗口0、当前开机后的后台身份保留。独立第四轮验收允许工单内部收口；最终证据见 `docs/reports/evidence/w1-post-reboot-closeout-20261021/` 与 `docs/reports/w1-independent-acceptance-20261021.md`。旧派发exit125/BLOCKED和历次失败保留。内部tag为wo-s1-host-shell-done；v0.1仍待Owner单独审批。
