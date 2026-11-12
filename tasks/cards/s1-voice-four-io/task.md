# 任务卡：s1-voice-four-io

- **task_id**：s1-voice-four-io
- **stage**：S1（阶段一 v0.2）
- **标题**：四 IO 链路（语音进→文字→语音出 + 固定音色）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为语音链路 PoC 的业务闭环（不接队列）

## goal

打通四 IO 链路：语音进（识别）→ 文字（意图中转）→ 语音出（合成，固定音色），演示"查任务状态"语音指令可被识别为文字意图。禁止：不接队列引擎（v0.3 U13）、不实现 L1 意图解析（v0.3 U12）、不做音色训练（v0.2 不做）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 语音"查任务状态"→ 文字意图可识别（真机演示记录）
- [ ] ACCEPT: 文字→语音出闭环（固定音色合成输出）
- [ ] ACCEPT: 四 IO 链路端到端一次成功（语音进→文字→语音出）

## dependsOn[]

- s1-voice-cv3-wiring（T1 CV3 接线）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\voice\`（四 IO 链路）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-voice-four-io\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- medium（链路串联 + 真机验证）

## category + skill

- category: voice · skill: eng.voice（语音/多媒体工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: （待填）
- stdoutText: （待填）
- evidence: 真机演示记录
- acceptance 逐项核对: （待填）

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| IO-01 语音进 | 语音捕获→识别→文字 | 文字意图可识别 | 演示记录 |
| IO-02 文字中转 | 文字→意图→响应 | 中转正确 | 链路日志 |
| IO-03 语音出 | 响应→固定音色合成输出 | 语音出闭环 | 音频输出 |
