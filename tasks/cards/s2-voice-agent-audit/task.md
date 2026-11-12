# 任务卡：s2-voice-agent-audit

- **task_id**：s2-voice-agent-audit
- **标题**：语音兜底 Agent 循环真机听测
- **优先级**：70（P1）
- **reasoningEffort**：low
- **category**：core　**skill**：voice
- **依赖**：无
- **登记核验**：已查注册表，无重复组件；对齐 #87 遗留事项①（interaction 兜底仅文字验证）

## goal（做什么 / 禁止做什么）

**做什么**：对语音链路 Agent 兜底（`interaction.py _try_agent_fallback`）做真机听测闭环并修复发现的问题：

1. 真机场景：唤醒「贾维斯」→ 说一句规则表未命中的话（如"随便聊聊" / "今天有什么新闻"）→ 触发 Agent 兜底 → 14B 回答 → TTS 播报；
2. 验证 5 类输入各 3 轮：闲聊 / 未命中问题 / 工具类问题（查任务、查配置）/ 无效内容 / 空内容——统计兜底触发率、播报成功率；
3. 修复发现的问题：如唤醒灵敏度、播报延迟、14B 回答被 TTS 截断、兜底误触发（把背景音当输入）等；
4. 验证 agent_server 不可达时语音链路降级静默（不报错不崩溃不语音搭话）。

**禁止**：
- 禁止改动唤醒词词条与 KWS 模型；
- 禁止改动 ASR 模型（faster-whisper）与 TTS 引擎（edge-tts）；
- 禁止改动队列引擎；
- 禁止向 fileDomain 之外写文件。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT-1：闲聊类输入 3 轮全部触发 Agent 兜底并正常播报
- [ ] ACCEPT-2：未命中问题类输入 3 轮全部触发兜底并播报
- [ ] ACCEPT-3：工具类输入（查任务状态/查配置）走 Agent 工具调用并播报真实结果
- [ ] ACCEPT-4：无效内容/空内容不触发兜底（保持静默），不误搭话
- [ ] ACCEPT-5：agent_server 停掉时语音链路静默降级，无报错无崩溃
- [ ] ACCEPT-6：发现的缺陷已修复并复验（缺陷记录含 现象/复现/修复/回归）
- [ ] ACCEPT-7：回执完整——receipt 含 reviewReason / stdoutText / evidence / acceptance（含真机听测证据）

## fileDomain[]

- `H:/UltimaAI/UltimaAgent`（src / data / docs）

## receipt（完成时回执）

- reviewReason / stdoutText / evidence / acceptance 逐项核对

## 变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-24 | 初版：语音兜底真机听测（#87 遗留①） |
