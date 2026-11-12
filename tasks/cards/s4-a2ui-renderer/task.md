# 任务卡：s4-a2ui-renderer
- **task_id**：s4-a2ui-renderer
- **标题**：A2UI 组件 renderer active 化（M08 残余）
- **优先级**：50（中）
- **reasoningEffort**：low
- **category**：core　**skill**：engineering
- **依赖**：无（src/window 既有）
- **登记核验**：已查注册表与产品对齐报告（product-alignment-20261027.md 缺口 N4）；src/window/offline_renderer.py 已实现 Text/Row/Column/List/Card 安全离线渲染（CR-02 核心，未上壳）；a2ui_validator.py 已实现 schema 校验；组件目录 component_directory.json 中控件组件 registered 非 active（renderer pending:T2）。

## goal
A2UI 组件 renderer active 化（M08 残余）：
1. 既有 Text/Row/Column/List/Card 渲染保留（已 active）；
2. 新增控件组件安全 renderer：Button / Slider / TextField / Modal / AudioPlayer——action 事件回调化（不执行真实副作用）、AudioPlayer 仅接受 asset:local 受控引用、无任意样式注入；
3. Ultima 自定义组件安全渲染：UltimaWindow / UltimaSwitch / UltimaProgress / UltimaListCard / UltimaOrb / UltimaSensorCard / UltimaStatusTag（基于 component_directory.json 已登记 schema）；
4. registry.md 组件状态回填（renderer 状态 active 化）。

**禁止**：
- 禁止执行真实副作用 action（仅事件回调）；
- 禁止放开资源引用（asset 仅 local 受控）；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：控件组件 renderer 可用（Button/Slider/TextField/Modal/AudioPlayer）
- [ ] ACCEPT-2：Ultima 自定义组件 renderer 可用（七组件）
- [ ] ACCEPT-3：非法输入/越权 action/非受控 asset 被拒
- [ ] ACCEPT-4：既有回归不倒退（test_a2ui_validator / test_text_core / test_combo_a2ui / test_combo_orchestrator 全绿）
- [ ] ACCEPT-5：registry.md 状态回填（renderer active）
- [ ] ACCEPT-6：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data / docs）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：A2UI 组件 renderer active 化（M08 残余，中） |
