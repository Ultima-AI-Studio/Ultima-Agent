# 任务卡：s1-voice-cv3-wiring

- **task_id**：s1-voice-cv3-wiring
- **stage**：S1（阶段一 v0.2）
- **标题**：CV3 接线（CosyVoice3 合成 + sherpa-onnx 识别/VAD）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为语音链路 PoC 的模型接线（权重已装，环境门已核）

## goal

接通 CV3 语音能力：CosyVoice3 文本合成语音 + sherpa-onnx 语音识别/VAD，真机可用（识别/合成往返各一次成功）。禁止：不实现四 IO 业务链路（T2）、不实现音色定制训练（v0.2 明确不做）、不接队列（v0.3）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: CosyVoice3 合成真机可用（文本→音频文件生成成功）
- [ ] ACCEPT: sherpa-onnx 识别真机可用（音频→文本识别成功）
- [ ] ACCEPT: VAD 边界定位可用（静音切分有效）
- [ ] ACCEPT: 真机往返日志（合成→播放→识别→文本 闭环一次成功）

## dependsOn[]

- s1-host-shell-envcheck（CV3 权重/运行库环境已核；版本级前置 v0.1 冻结登记于工单总卡，F3 修正）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\voice\`（语音接线模块）
- `H:\UltimaAI\UltimaAgent\models\voice\`（权重引用，只读）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-voice-cv3-wiring\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（模型 API 接线 + 真机调通，多依赖）

## category + skill

- category: voice · skill: eng.voice（语音/多媒体工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: （待填）
- stdoutText: （待填）
- evidence: 真机往返日志
- acceptance 逐项核对: （待填）

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| CV-01 合成接线 | CosyVoice3 文本→音频 | 合成成功、可播放 | 音频文件+日志 |
| CV-02 识别接线 | sherpa-onnx 音频→文本 | 识别成功 | 识别日志 |
| CV-03 VAD 边界 | 静音切分有效 | 边界定位准确 | 切分输出 |
| CV-04 真机往返 | 合成→播放→识别→文本闭环 | 闭环一次成功 | 往返日志 |
