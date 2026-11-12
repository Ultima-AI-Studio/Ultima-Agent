# 验收证据 · s3-websearch-upgrade（检索增强（M14））

- **task_id**：s3-websearch-upgrade
- **状态**：COMPLETED
- **验收时间**：2026-10-27

## ACCEPT 清单
| 项 | 结果 | 证据 |
|---|---|---|
| ACCEPT-1 | PASS | 多引擎编排：primary 可用即用 primary（test_multi_engine_orchestration） |
| ACCEPT-2 | PASS | 降级标记：primary 失败自动 fallback + degraded + 原因（test_fallback_and_degraded_flag） |
| ACCEPT-3 | PASS | SSRF 防护：内网/回环/链路本地/元数据地址（127/192.168/169.254.169.254/localhost/10.x）全拒（test_ssrf_guard） |
| ACCEPT-4 | PASS | 来源标记：结果带 engine；检索中 SSRF 目标被剔除 blocked_count 计数（test_source_marked_and_ssrf_blocked_in_search） |
| ACCEPT-5 | PASS | 回执落盘经 ReceiptValidator 复核 0 issues；tasks.json 置 COMPLETED |

## 产出文件
- `src/brain/search/upgrade.py`、`src/brain/search/__init__.py`
- `src/brain/search/tests/test_websearch_s3.py`（4/4 OK）
- `tasks/cards/s3-websearch-upgrade/acceptance-evidence.md`、`receipt.json`

## 边界未触碰
- 未改既有 ultima_web_search 工具契约；未向 fileDomain 之外写文件。
