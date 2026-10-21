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
