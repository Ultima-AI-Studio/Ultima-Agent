# 任务卡：s1-window-theme-floatball

- **task_id**：s1-window-theme-floatball
- **stage**：S1（阶段一 v0.4）
- **标题**：图波主题 v1 + 悬浮球四状态绑定（倾听/思考/说话/待命）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为组合窗口的主题与悬浮球状态绑定

## goal

落地图波主题 v1（theme-standard）+ 悬浮球四状态绑定：倾听/思考/说话/待命，状态切换正确，窗口与语音同时交付。禁止：不实现新 UI 范式（范式冻结，只落主题）、不实现语音链路（v0.2 已完成，只绑定状态）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 图波主题 v1 落地（theme-standard tokens 生效）
- [ ] ACCEPT: 悬浮球四状态绑定正确（倾听/思考/说话/待命 切换记录）
- [ ] ACCEPT: 窗口+语音同时交付（真机状态切换记录）

## dependsOn[]

- s1-window-composite-render（T2 渲染）
- s1-voice-four-io（v0.2 语音链路，状态源）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\window\`（主题/悬浮球代码）
- `H:\UltimaAI\UltimaAgent\src\host-shell\`（悬浮球宿主集成）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-window-theme-floatball\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（主题 + 状态机绑定）

## category + skill

- category: window · skill: eng.ui（UI 工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: （待填）
- stdoutText: （待填）
- evidence: 真机状态切换记录
- acceptance 逐项核对: （待填）

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| TF-01 主题 tokens | 图波主题 v1 落地 | theme-standard tokens 生效 | 样式核对 |
| TF-02 四状态定义 | 倾听/思考/说话/待命 | 四状态齐全 | 定义核对 |
| TF-03 状态绑定切换 | 悬浮球四状态绑定正确 | 切换正确 | 真机记录 |
| TF-04 双交付 | 窗口+语音同时交付 | 同时交付 | 真机记录 |
