# s6-capability-page 验收证据

- **task_id**：s6-capability-page
- **验收日期**：2026-10-27
- **验收人**：主脑（豆包直做，无人值守工单，无确认类问询）
- **结果**：通过（全绿）

## 交付物
| 文件 | 作用 |
|---|---|
| sync/capability-manifest.json | 同源能力清单数据源（26 项可用 + 4 项规划中） |
| src/brain/capability.py | load_manifest / summarize / to_a2ui_messages / render_capability_page |
| src/brain/intent.py | 新增 CAPABILITY_INTENT + parse_capability_intent |
| src/brain/reporter.py | 消费 capability.query → 摘要播报（悬浮球侧） |
| src/brain/tests/test_capability_s6.py | 验收测试 11 条 |

## 验收项逐条核对
| 判据 | 结果 | 证据 |
|---|---|---|
| ACCEPT-1：manifest 落盘，盘点与对齐报告一致，含证据路径 | 通过 | 26 项可用（≥24），4 项规划中；每项含 id/name/description/status/module/evidence |
| ACCEPT-2：load_manifest 可读，缺失/损坏确定性报错 | 通过 | test_load_missing_raises / test_load_corrupt_raises |
| ACCEPT-3：summarize 结构化中文摘要 | 通过 | test_summary（总数/可呼唤示例/规划中） |
| ACCEPT-4：A2UI 校验 + 零 JS CSP 安全 HTML | 通过 | test_messages_pass_validation（ULTIMA_CATALOG_ID）；test_render_no_script_csp（script-src 'none'、无 <script>） |
| ACCEPT-5：parse_capability_intent 命中/不命中边界 | 通过 | test_hits 5 例命中；test_miss_task_status_not_capability；test_miss_negation_and_reference |
| ACCEPT-6：reporter 消费能力查询，任务状态不受影响 | 通过 | test_capability_query_returns_summary；test_task_status_unaffected（"任务库为空"） |
| ACCEPT-7：回执完整 | 本文件 + receipt.json + ReceiptValidator + tasks.json COMPLETED | 见 ReceiptValidator 结果 |

## 测试结果
- s6 新增：11/11 全绿
- 回归：
  - src.brain.tests.test_intent：4/4
  - src.brain.tests.test_reporter：7/7（既有）
  - src.window.tests.test_a2ui_renderer_s4：8/8
  - src.window.tests.test_combo_a2ui：4/4
- 合计 34 条全绿，无失败无错误

## 说明
- 能力清单与 s2-capability-overview 工单（语音自述工具）同源：本工单建立的 capability-manifest.json 为数据权威，s2 工具后续可读同一 manifest，不重复建数据。
- 组合窗口侧 render_capability_page 产出可直接进 WebView2；悬浮球侧 reporter 摘要走既有 TTS 播报链路（daemon 零改动）。
- 阶段预留 4 项（M09/M25/M28/M15-MCP）独立分组标"规划中"，不作可用。
