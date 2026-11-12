# 任务卡：s3-browser-channel
- **task_id**：s3-browser-channel
- **标题**：浏览器自动化通道（托管浏览器/CDP + 只读红线）
- **优先级**：60（P2）
- **reasoningEffort**：medium
- **category**：exec　**skill**：engineering
- **依赖**：s3-bus-kernel、s3-guard-resident（闸门稳定后）
- **登记核验**：已查注册表，无现有通道；依据 docs/research/agent-capability-notes-localdesktop-20261026.md OpenClaw/Open Interpreter §⑤、Manus §⑤（双浏览器策略）、Agent-Reach 只读红线

## goal
浏览器通道 M13：
1. 托管浏览器/CDP 双轨接入（页面观察、元素定位、操作执行）；
2. 登录态会话隔离（与用户日常浏览器隔离，不共享登录态）；
3. 只读红线：不发帖/评论/点赞/私信/代登录/索要密码；动作前闸门判定；
4. 与总线挂接（经 L3 适配器，动作留痕）。

**禁止**：
- 禁止代登录/索要密码/发帖等越界动作；
- 禁止触碰用户日常浏览器数据；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：托管浏览器/CDP 可导航、可观察、可操作（白名单站点）
- [ ] ACCEPT-2：会话隔离生效（独立 profile）
- [ ] ACCEPT-3：只读红线动作被闸门拒绝并留痕
- [ ] ACCEPT-4：动作全程审计留痕
- [ ] ACCEPT-5：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：浏览器自动化（P2） |
