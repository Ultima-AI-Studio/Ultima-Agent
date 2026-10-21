# 工单②：S1-Host-Shell（宿主壳）

- **工单 ID**：wo-s1-host-shell · 2026-10-16 · 主脑立项
- **版本归属**：v0.1 环境基线（本工单覆盖 U01-U05；U06-U09 队列引擎属工单①）
- **依赖**：工单①（wo-s1-queue-engine）并行推进（同属 v0.1，互不阻塞）
- **L3 结果（要什么）**：宿主壳可用——环境门全绿、WinUI3 工程可构建、WebView2 渲染就绪、悬浮球占位可拖动、一键自检脚本跑通；成为语音/窗口/主脑的承载壳。
- **L3 Gate**：工单②内部 DoD PASS（5 任务全过 + 总验收）——版本冻结归版本级（工单①+② 全过后触发 v0.1-frozen）

## 0. 范围冻结

- 本工单只做：宿主壳五任务（环境门/工程骨架/WebView2/悬浮球/自检脚本）
- 本工单不做：队列引擎（工单①）、语音链路（v0.2）、组合窗口渲染（v0.4）、业务 UI 范式设计（ui-kit-standard 冻结，只落地壳）

## 1. 任务清单（T ↔ U 映射表）

| 任务 ID | 标题 | 对应验收单元 | 验收门 |
|---|---|---|---|
| T1 s1-host-shell-envcheck | 环境门 9 项核对 | U01 | 宿主阶段开工门全绿（environment-spec §7.1） |
| T2 s1-host-shell-winui3-init | WinUI3 工程初始化 | U02 | 工程可构建零警告 |
| T3 s1-host-shell-webview2 | WebView2 嵌入渲染 | U03 | 空页渲染成功 |
| T4 s1-host-shell-floatingball | 悬浮球占位窗口 | U04 | 占位显示可拖动 |
| T5 s1-host-shell-selfcheck | 壳自检脚本 | U05 | 自检跑通 |

**写入域（fileDomain）**

| 任务 | 精确写入域 |
|---|---|
| T1 s1-host-shell-envcheck | `H:\UltimaAI\UltimaAgent\logs\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-host-shell-envcheck\` |
| T2 s1-host-shell-winui3-init | `H:\UltimaAI\UltimaAgent\src\host-shell\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-host-shell-winui3-init\` |
| T3 s1-host-shell-webview2 | `H:\UltimaAI\UltimaAgent\src\host-shell\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-host-shell-webview2\` |
| T4 s1-host-shell-floatingball | `H:\UltimaAI\UltimaAgent\src\host-shell\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-host-shell-floatingball\` |
| T5 s1-host-shell-selfcheck | `H:\UltimaAI\UltimaAgent\scripts\`；`H:\UltimaAI\UltimaAgent\logs\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-host-shell-selfcheck\` |

**推理强度（reasoningEffort）**：工单级 `medium`；逐任务以任务卡为准：T1 `low`，T2 `high`，T3-T5 `medium`。

**依赖图**：T1 → T2 → T3 → T4；T5 依赖 T2/T3/T4（并联收口）

## 2. 任务明细

每张任务卡见 `cards/<task_id>/task.md`（11 字段齐全）。

## 3. 总验收（工单 DoD，非版本冻结）

- [ ] 全部 5 任务 PASS（T1-T5）
- [ ] T↔U 映射核对：U01-U05 全部覆盖
- [ ] 壳自检端到端 PASS（build → launch → window → exit）
- [ ] 关联文档同步（docs/README 权威清单登记工单②）
- [ ] 冻结基线标记：工单② 内部 tag `wo-s1-host-shell-done`（版本 tag v0.1-frozen 待工单①+② 全过后由版本级触发）

## 4. 验收要点（打勾清单）

- [ ] 前置：宿主阶段环境门全绿（U01；environment-spec §7.1，Owner 已批准阶段拆分）
- [ ] 每任务回执三件套（I1）
- [ ] 提交前自核闭环（§8）
- [ ] 失败回执结构化（I3）；证据不明确 fail-closed（B1）
- [ ] 开发与审计技能分离

## 变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.1 | 2026-10-20 | AUDIT-S1-FIX：工单①/②依赖口径统一为同属 v0.1 并行、互不阻塞 |
| v1.0 | 2026-10-16 | 初版：工单② 宿主壳 5 任务 + T↔U 映射 + 依赖图 + 总验收 |
| v1.2 | 2026-10-21 | Owner 直接批准按阶段拆分 T1：WinUI/.NET/WebView2 为宿主开工门；语音和任务管线验收留在原工单，不改变其 Gate。 |
