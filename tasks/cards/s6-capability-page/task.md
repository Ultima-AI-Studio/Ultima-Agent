# 任务卡：s6-capability-page
- **task_id**：s6-capability-page
- **标题**：能力清单指令页（双界面线同源呈现，B 类）
- **优先级**：80（P1）
- **reasoningEffort**：medium
- **category**：core　**skill**：engineering
- **依赖**：s4-a2ui-renderer（active_renderer 可用）；s5-external-executor（能力盘点含外部路由）
- **登记核验**：已查注册表与产品对齐报告（product-alignment-s4-20261027.md §五维度4）；s2-capability-overview 工单为"14B 语音自述工具"，本工单做"同源数据源 + 双界面呈现"，数据权威=manifest，s2 工具后续可读同一 manifest，不重复建工具；docs/plans/capability-list.md 为规划文件（要建什么），本工单盘的是"已建什么"。

## goal
能力清单指令页（解决"不知道 Agent 能干什么"）：
1. 新建同源数据源 `sync/capability-manifest.json`：从真实验收证据盘点（product-alignment-s4 报告 §二矩阵 + registry + tasks.json 已完成状态），每项含 id / 名称 / 说明 / 可呼唤短语（语音）/ 可下达指令（文本）/ 状态 / 入口模块 / 证据路径；不含未实现/未注册能力（防夸大）；
2. 新增 `src/brain/capability.py`：load_manifest（读同源数据源）、summarize（语音摘要文本）、to_a2ui_messages（转 A2UI messages，组合窗口 A2UI 链路消费）、render_capability_page（走 ActiveRenderer 输出安全 HTML，零 JS CSP）；
3. 语音意图：`src/brain/intent.py` 新增 CAPABILITY_INTENT + parse_capability_intent（"你有什么能力/能做什么/有哪些功能/你会什么/有哪些技能"），`src/brain/reporter.py` 消费输出摘要播报（悬浮球侧）；
4. 组合窗口侧：render_capability_page 产出的安全 HTML 可直接进组合窗口 WebView2（同源数据）。
   
**禁止**：
- 禁止把未注册/未实现/阶段预留的能力写成"可用"（预留标规划中）；
- 禁止改冻结组件（daemon 零改动；仅新增意图规则与消费分支）；
- 禁止向 fileDomain 之外写文件；
- 禁止任意样式注入（走 active_renderer schema 白名单）。

## acceptance[]
- [ ] ACCEPT-1：capability-manifest.json 已落盘，盘点项与对齐报告矩阵一致，含真实证据路径
- [ ] ACCEPT-2：load_manifest 可读；缺失/损坏文件确定性报错
- [ ] ACCEPT-3：summarize 输出结构化中文摘要（总数/类别/示例可呼唤）
- [ ] ACCEPT-4：to_a2ui_messages 通过 a2ui_validator.validate_batch（final=True）校验，render_capability_page 输出无脚本 CSP 安全 HTML
- [ ] ACCEPT-5：parse_capability_intent 命中/不命中边界正确（"你有什么能力"命中，"查询任务状态"不命中且不影响 task_status）
- [ ] ACCEPT-6：reporter 消费 capability.query 输出摘要文本；既有任务状态查询不受影响（回归）
- [ ] ACCEPT-7：回执完整（receipt.json + ReceiptValidator + tasks.json 置 COMPLETED）

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / sync / tasks / docs）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：能力清单指令页（双界面线同源呈现，B 类） |
