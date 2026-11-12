# 验收证据 · s3-device-profile（设备档案层（M15））

- **task_id**：s3-device-profile
- **状态**：COMPLETED
- **验收时间**：2026-10-27

## ACCEPT 清单
| 项 | 结果 | 证据 |
|---|---|---|
| ACCEPT-1 | PASS | 四实体档案模型可读写持久化（重建读回）（test_four_entities_rw） |
| ACCEPT-2 | PASS | 可控性三独立：不可达全拒/无凭证不可控/sensor 类型不可控制（防误控）（test_controlability_three_independent） |
| ACCEPT-3 | PASS | MCP 适配器框架：插件经 endpoint() 取配置，换 server 只改配置（test_mcp_adapter） |
| ACCEPT-4 | PASS | 前置检查链：档案→凭证→可控性 分阶段拒绝（test_provision_chain） |
| ACCEPT-5 | PASS | 单协议试点（matter）：不可达设备如实报告不编造（test_single_protocol_pilot） |
| ACCEPT-6 | PASS | 回执落盘经 ReceiptValidator 复核 0 issues；tasks.json 置 COMPLETED |

## 产出文件
- `src/brain/iot/device_profile.py`
- `src/brain/iot/tests/test_device_profile_s3.py`（5/5 OK）
- `tasks/cards/s3-device-profile/acceptance-evidence.md`、`receipt.json`

## 边界未触碰
- 未一次性全量接入协议；可控性判定前置；未向 fileDomain 之外写文件。
