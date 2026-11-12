# 任务卡：s3-voice-fullchain
- **task_id**：s3-voice-fullchain
- **标题**：语音全链路（VAD 断句 + 打断 + 三态节拍）
- **优先级**：70（P1）
- **reasoningEffort**：medium
- **category**：voice　**skill**：engineering
- **依赖**：s3-bus-kernel
- **登记核验**：已查注册表，l7-voice-entry 已实现（KWS+ASR+TTS 真机通过），本单为链路升级；依据 ADR-005/009、docs/plans/tech-decisions.md TD-03

## goal
语音全链路 M05/M06 升级（保现状可用的前提下增强，不推翻已冻结链路）：
1. VAD 断句（说话停顿自动断句）；
2. barge-in 打断（说话即打断播报）；
3. 三态节拍与在途中止（语音状态可视化联动悬浮球/组合窗口）；
4. 语音/文字同入口验收（同一意图两个入口结果一致）；
5. Pipecat 全链路评估：可行则替换/改造，受阻则按 TD-03 备选自研编排降级（先保 KWS+ASR+TTS 现状可用）。

**禁止**：
- 禁止在未保底时移除现状可用链路；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：VAD 断句在真机可用（长句自动断句）
- [ ] ACCEPT-2：barge-in 打断生效（播报中说话即停）
- [ ] ACCEPT-3：三态节拍与悬浮球/组合窗口状态联动
- [ ] ACCEPT-4：语音与文字同入口结果一致
- [ ] ACCEPT-5：Pipecat 评估结论落档（采用/降级+理由）
- [ ] ACCEPT-6：现状链路回归不倒退
- [ ] ACCEPT-7：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / scripts / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：语音全链路（P1） |
