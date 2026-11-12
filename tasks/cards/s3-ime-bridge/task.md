# 任务卡：s3-ime-bridge
- **task_id**：s3-ime-bridge
- **标题**：渠道桥接（IM 适配器 + 审批闭环 + 只读红线）
- **优先级**：55（P2）
- **reasoningEffort**：low
- **category**：channel　**skill**：engineering
- **依赖**：s3-guard-resident
- **登记核验**：已查注册表，无现有通道；依据 docs/research/agent-capability-notes-localdesktop-20261026.md OpenClaw §⑥、agent-capability-notes-platform-20261026.md Coze/Manus §⑥

## goal
渠道桥接 M24：
1. IM 适配器（微信/飞书/Discord 等，入站 WAL/出站 Outbox 模式）；
2. 审批两端同弹（高危动作在 IM 端与桌面端同时征询）；超时取消；
3. 只读/不代登录红线；
4. 与主脑回路挂接（经总线）。

**禁止**：
- 禁止代登录/索要密码；
- 禁止绕过审批执行高危动作；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：适配器接入一种渠道（微信或飞书）收发可用
- [ ] ACCEPT-2：审批两端同弹+超时取消验证通过
- [ ] ACCEPT-3：只读红线生效（不代登录）
- [ ] ACCEPT-4：经总线挂接主脑回路
- [ ] ACCEPT-5：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：渠道桥接（P2） |
