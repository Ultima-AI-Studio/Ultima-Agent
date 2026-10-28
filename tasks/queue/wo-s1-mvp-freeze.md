# 工单⑥：S1-MVP-Freeze（MVP 冻结）

- **工单 ID**：wo-s1-mvp-freeze · 2026-10-16 · 主脑立项
- **版本归属**：v1.0 MVP 冻结（本工单覆盖 U18-U20）
- **依赖**：v0.2 + v0.4 冻结（语音链路 + 组合窗口）
- **L3 结果（要什么）**：MVP 可交付——L7 征询闭环（交付→征询→调整→重呈现）+ 队列调整（插队/改优先级，审计留痕）+ L8 凭证中心与受控执行（状态只报告/操作需授权/越界拦截 100%）；本工单只闭合内部 DoD，版本级待工单⑥+⑦+⑧及项目级四信号全绿后再触发 tag `stage1-v1.0-frozen`。
- **L3 Gate**：工单⑥内部 DoD PASS（工单级）；**`stage1-v1.0-frozen` 由版本级触发 = 工单⑥+⑦+⑧ 全部 DoD PASS + 项目级四信号全绿**

## 0. 范围冻结

- 本工单只做：征询闭环 / 队列调整 / 凭证中心（MVP 收口）
- 本工单不做：新版本功能（迭代二）、音色训练（明确不做）、新 UI 范式（冻结）、多平台适配（迭代）

## 1. 任务清单（T ↔ U 映射表）

| 任务 ID | 标题 | 对应验收单元 | 验收门 |
|---|---|---|---|
| T1 s1-mvp-confirm-loop | L7 征询闭环 | U18 | 征询链路 PASS |
| T2 s1-mvp-queue-adjust | 队列调整（插队/优先级） | U19 | 调整生效、审计留痕 |
| T3 s1-mvp-credential-gate | L8 凭证中心+受控执行 | U20 | 越界拦截 100% |

**写入域（fileDomain）**

| 任务 | 精确写入域 |
|---|---|
| T1 s1-mvp-confirm-loop | `H:\UltimaAI\UltimaAgent\src\brain\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-mvp-confirm-loop\` |
| T2 s1-mvp-queue-adjust | `H:\UltimaAI\UltimaAgent\src\brain\`；`H:\UltimaAI\UltimaAgent\tasks\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-mvp-queue-adjust\` |
| T3 s1-mvp-credential-gate | `H:\UltimaAI\UltimaAgent\src\security\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-mvp-credential-gate\` |

**推理强度（reasoningEffort）**：工单级 `high`；逐任务以任务卡为准：T1 `high`，T2 `medium`，T3 `ultra`（eng.security，需评审背书）。

**依赖图**：T1 → T2 → T3（串行；T3 安全边界收口）

## 2. 任务明细

每张任务卡见 `cards/<task_id>/task.md`（11 字段齐全）。

## 3. 总验收（工单 DoD = v1.0 版本冻结门 + 项目级）

- [x] 全部 3 任务 PASS（T1-T3）✅ 2026-10-28 主脑直做验收回填：confirm-loop（征询闭环 3/3）、credential-gate（L8 凭证中心 4/4）、queue-adjust（队列调整 3/3），专项测试全绿
- [x] T↔U 映射核对：U18-U20 全部覆盖 ✅ T1=confirm-loop、T2=queue-adjust、T3=credential-gate 逐张任务卡验收全绿
- [x] 项目级四信号（product-plan §8）：闭环率 ≥80% / 覆盖 ≥90% / 越界拦截 100% / 诚实边界 100% ✅ 2026-10-28 版本级联合评估全绿（reports/stage1-v1.0-signals-20261028.md）；冻结 tag 仍待工单⑦ PK-03 净机补验后版本级触发
- [ ] 关联文档同步（docs/README 登记工单⑥）⏳
- [ ] 冻结基线标记：工单⑥内部 tag `wo-s1-mvp-freeze-done`（版本 tag 待⑥+⑦+⑧全绿由版本级触发）⏳

## 4. 验收要点（打勾清单）

- [x] 前置：v0.2 + v0.4 冻结 → 2026-10-29 Owner 批准，v0.2-frozen/v0.4-frozen 已打（HEAD d94576d，语义：语音链路/组合窗口）
- [ ] 每任务回执三件套（I1）
- [ ] 提交前自核闭环（§8）
- [ ] 失败回执结构化（I3）；证据不明确 fail-closed（B1）
- [ ] 开发与审计技能分离（T3 eng.security ultra 需评审背书）

## 变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.1 | 2026-10-20 | AUDIT-S1-FIX：工单⑥仅闭合内部 DoD；v1.0 版本 tag 改由⑥+⑦+⑧全绿及项目级四信号共同触发 |
| v1.0 | 2026-10-16 | 初版：工单⑥ MVP 3 任务 + T↔U 映射 + 总验收 |
