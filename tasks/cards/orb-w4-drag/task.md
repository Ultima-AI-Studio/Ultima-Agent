# 任务卡：orb-w4-drag

- **task_id**：orb-w4-drag
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：鼠标拖动 + 位置保持
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 拖动交互实现

## goal

鼠标按下拖动球体、松手位置保持；多 DPI 下位置不偏移。禁止：不实现贴边（W4 T2）、不实现面板（W4 T3）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 鼠标拖动生效、松手位置保持
- [ ] ACCEPT: 多 DPI 下不偏移
- [ ] ACCEPT: 真机截图/位置日志可证

## dependsOn[]

- orb-w1-ball-window（球窗就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\interaction\`（拖动代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w4-drag\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（拖动 + DPI）

## category + skill

- category: orb-interaction · skill: eng.win（Win32 工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: 待回填
- stdoutText: 待回填
- evidence: 待回填
- acceptance 逐项核对: 待回填

## retryCount

- 0

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| U-01 拖动 | 拖动 + 位置保持 | 拖动生效 | 位置日志 |
| U-02 DPI | 多 DPI 无偏移 | 通过 | 真机测试 |
| U-03 截图 | 真机截图 | 可证 | 截图 |
