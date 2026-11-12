# s9-channel-breadth 验收证据

- 验收人：主脑（豆包直做）
- 验收时间：2026-10-27
- 依据：jarvis-reverse-architecture M24 渠道连接器；对齐报告维度 1 渠道铺开

## 实现范围（增量，复用既有 ime_bridge，不另起炉灶）

新建 `src/brain/channel/channel_breadth.py`：
- `ChannelRegistry`：通道适配器注册/列出/获取/启停（id/名称/类型/方向/状态）；
- `ChannelDispatcher` 总装：统一 ingest（入站→WAL）/ dispatch（出站→Outbox）；
  复用 WALOutboxStore / ApprovalCoordinator（两端审批超时 fail-safe）/ ChannelRedline（只读红线）；
- 内置占位通道：`local_notify`（本地通知，out，active）+ `mail_outbox`（邮件 Outbox，both，registered，不真发信）；
- 高危 dispatch 走两端审批；红线动作直接拒绝；方向不符确定性报错。

## 验收项逐条

| 项 | 判定 | 证据 |
|---|---|---|
| ACCEPT-1 注册表注册/列出/获取 | 通过 | test_registry / test_defaults_registered |
| ACCEPT-2 本地通知 ingest/dispatch 走 WAL/Outbox | 通过 | test_local_notify_dispatch_outbox / test_ingest_wal |
| ACCEPT-3 邮件 Outbox 占位注册可用（不真发信） | 通过 | test_mail_placeholder |
| ACCEPT-4 审批接线：高危两端审批超时取消；红线拒绝 | 通过 | test_high_risk_approval_and_timeout / test_redline_rejects / test_wrong_direction |
| ACCEPT-5 回执完整 | 通过 | 本文件 + receipt.json，ReceiptValidator 0 issues |

## 测试结果

- 新增：src/brain/channel/tests/test_channel_breadth_s9.py — 9/9 通过
- 回归：test_ime_bridge_s3 + test_channel_breadth_s9 — 12/12 通过

## 边界确认

- 不代登录/不索要密码/审批不绕过（红线复用）；适配器为可接线占位，真实凭证走凭证中心（L8）。
