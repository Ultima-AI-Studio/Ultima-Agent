# 任务卡：s9-channel-breadth
- **task_id**：s9-channel-breadth
- **标题**：渠道铺开（C 类 · 渠道注册表与多通道适配）
- **优先级**：80（P1）
- **category**：core　**skill**：engineering
- **依赖**：s3-ime-bridge（M24 WAL/Outbox/审批两端已建）
- **依据**：jarvis-reverse-architecture M24 渠道连接器；对齐报告维度 1 渠道铺开

## goal
渠道铺开（复用既有 WAL/Outbox 与审批机制，不另起炉灶）：
1. 渠道注册表 ChannelRegistry：register/list/get 通道适配器（id/名称/类型/方向/状态）；
2. 多通道适配：新增 本地通知（local_notify，桌面播报）+ 邮件 Outbox（mail_outbox 占位适配器，
   出站走既有 Outbox 写入，入站走既有 WAL）；
3. 与既有 ime_bridge 协同：审批两端同弹复用 ApprovalCoordinator，红线复用 REDLINE_CHANNEL；
   通道适配器统一接口：ingest（入站→WAL）/ dispatch（出站→Outbox）。
   
**禁止**：不代登录/不索要密码/审批不绕过；不接真实外部账号（适配器为可接线占位，真实凭证走凭证中心）。

## acceptance[]
- [ ] ACCEPT-1：ChannelRegistry 注册/列出/获取适配器（含 id/类型/方向/状态）
- [ ] ACCEPT-2：本地通知适配器 ingest/dispatch 走 WAL/Outbox，出站条目可读
- [ ] ACCEPT-3：邮件 Outbox 占位适配器注册可用（出站入 Outbox、入站入 WAL，不真发信）
- [ ] ACCEPT-4：审批接线：高危 dispatch 走 ApprovalCoordinator 超时取消 fail-safe；红线拒绝
- [ ] ACCEPT-5：回执完整（ReceiptValidator 0 issues + tasks.json COMPLETED）

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src/brain/channel + tests + tasks）
