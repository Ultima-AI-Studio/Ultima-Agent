# 任务卡：orb-w4-edge-dock

- **task_id**：orb-w4-edge-dock
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：贴边回收细条 + 滑回
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 贴边回收实现

## goal

拖动球体到屏幕左右边缘贴边成细条，hover 滑回；回收用鼠标状态 + 计时器驱动（非激活后 Deactivated 事件不可靠）；面板/菜单打开时暂停回收，弹出给 grace time。禁止：不实现面板（W4 T3）、不实现动效（W5）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 左右边缘贴边成细条
- [ ] ACCEPT: hover 滑回
- [ ] ACCEPT: 面板打开暂停回收 + grace time

## dependsOn[]

- orb-w4-drag（拖动就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\interaction\`（贴边代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w4-edge-dock\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（贴边状态机）

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
| U-01 贴边 | 边缘贴边细条 | 生效 | 截图 |
| U-02 滑回 | hover 滑回 | 生效 | 截图 |
| U-03 暂停 | 面板打开暂停回收 | 生效 | 测试日志 |
