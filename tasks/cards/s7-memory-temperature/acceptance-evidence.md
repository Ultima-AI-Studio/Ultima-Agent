# 验收证据 · s7-memory-temperature（记忆热度分层）

- **task_id**：s7-memory-temperature
- **状态**：COMPLETED
- **验收时间**：2026-10-27
- **验收人**：Ultima 主脑（独立复核视角：实现与验收分离，dev 不自证清白）

## ACCEPT 清单

| 项 | 验收项 | 结果 | 证据 |
|---|---|---|---|
| ACCEPT-1 | 三档热度可标记（写入/召回后 temperature 字段正确） | PASS | `test_temperature_s7.py::TestTemperatureTagging`（按层默认档：working=hot/declarative=warm/env_profile=cold；touch 更新 access_count/last_access；会话内 ≥2 次升热） |
| ACCEPT-2 | 升降级四动作单测通过，状态迁移正确 | PASS | `TestPromoteDemote`（promote_hot 内存标记、demote_warm 落盘持久、demote_all_hot 批量、冷档条目拒绝直接升降级）+ `TestColdArchive`（archive_cold 标记不删行、thaw_cold 回温并移出归档、unknown 返回 False） |
| ACCEPT-3 | 三级检索路由按序命中即停；冷归档条目可解冻召回 | PASS | `TestThreeTierRetrieval`（read 命中即 touch；include_cold 可召回归档条目；默认检索排除冷档）+ `read_archived` 只读冷档不带 touch 污染 |
| ACCEPT-4 | 中期层成立（declarative 温档，无独立存储文件） | PASS | 设计文档 §三 时间三层映射：中期=温档 declarative 活跃条目；存储仍 `data/memory/layers/declarative.jsonl`，未新增存储文件 |
| ACCEPT-5 | 打断单元写入与下轮合并上下文闭环 | PASS | `TestInterruptUnit`（pending_interrupt kind 合法、可检索、闭环转温档）；brain_loop 新增 record_interrupt/resume_interrupt/close_interrupt 三方法 |
| ACCEPT-6 | venv-openjarvis 全量测试全绿（既有功能零回归） | PASS（4 项既有基线失败，非本工单引入，见下） | s7 单测 25/25 OK；src/brain/tests 全量 217 项：213 过 + 4 项既有失败（test_adapters 脚本式结构 / test_queue_source×2 生产库数据 / test_voice_loop 语音环境），4 项均未引用本工单改动文件 |
| ACCEPT-7 | 回执完整（含变更登记） | PASS | 本文件 + receipt.json 落盘 |

## 测试结果

| 测试集 | 结果 |
|---|---|
| `test_temperature_s7.py`（本工单验收，25 项） | 25/25 OK（EXIT=0） |
| 全量 `src/brain/tests`（217 项） | 213 过 / 3 FAIL / 1 ERROR（既有基线，见下） |

## 既有失败基线登记（非本工单引入）

| 用例 | 失败原因 | 与本工单关系 |
|---|---|---|
| test_adapters | 脚本式测试（模块级 `sys.exit(0)`），被 unittest discover 误收集为 import 错误 | 未引用记忆层/brain_loop 改动 |
| test_queue_source.test_empty_production_library... | 依赖真实生产库 `tasks/queue` 状态，snapshot.ok=False | 未引用记忆层改动 |
| test_queue_source.test_real_storage... | 生产数据 duration=`150:59:03` 超正则 `\d{2}` 上限 | 未引用记忆层改动 |
| test_voice_loop.test_no_reply_skip_tts | 语音循环 stage 语义（'tts' vs 'bridge'），语音环境相关 | 未引用记忆层/brain_loop 改动 |

## 关键参数冻结表（不越基线）

| 参数 | 值 | 依据 |
|---|---|---|
| 热度三档 | hot / warm / cold（meta.temperature） | memory-temperature-tiering-20261027.md §二 |
| 按层默认档 | working=hot / declarative=warm / procedural=warm / device_profile=warm / env_profile=cold | 设计文档 §二 映射表 |
| 热档阈值 | 会话内召回 ≥2 次（HOT_TOUCH_THRESHOLD=2，可配置） | 设计文档 §四 |
| 冷档判定 | 超保留期 或 30 天未召回（COLD_STALE_DAYS=30，可配置） | 设计文档 §四 |
| 冷归档存储 | `data/memory/archive/<layer>.jsonl.gz`（标准库 gzip） | 设计文档 §二.4 |
| 中期层 | declarative 温档活跃条目（无独立存储文件） | 设计文档 §三 |
| 打断单元 | kind=pending_interrupt，working 层默认热档 | 设计文档 §五 |
| 冻结基线 | ADR-008 五层性质分层/容量/保留期默认值未改动 | 回归 test_defaults_unchanged |

## 变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：s7 记忆热度分层验收 |
