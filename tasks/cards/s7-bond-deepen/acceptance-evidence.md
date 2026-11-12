# s7-bond-deepen 验收证据

- 验收人：主脑（豆包直做）
- 验收时间：2026-10-27
- 依据：form-expansion-plan-20261024.md §3.4 阶段二验收口径

## 实现范围（增量，不推倒底座）

`src/brain/persona/bond.py`（s3-bond-system 之上）：
- RelationFact 增加 `scope` 字段（general/preference/interaction，关系记忆字段齐全）；
- `add_note(detail, scope)`：沉淀用户偏好/互动史（kind=note），非法域/空内容报 BondError；
- `get_notes(kind=None, scope=None)`：关系记忆可查询（全量 + 按 kind/scope 过滤）；
- `close_intimate_tier(granted_by="user")`：亲密档回退至专业距离，称呼/口吻复位，留痕（tier_open 记录"回退"）；
- `state_axis()` 增加 `relation_memory` 快照（notes/preferences/interactions/facts 计数），跨形态读取一致。

## 验收项逐条

| 项 | 判定 | 证据 |
|---|---|---|
| ACCEPT-1 add_note 沉淀字段齐全 | 通过 | test_add_note_persists_fields：kind=note，ts/detail/scope 齐全 |
| ACCEPT-2 get_notes 可查询 | 通过 | test_get_notes_filter：全量/kind/scope 过滤正确 |
| ACCEPT-3 档位回退生效且留痕 | 通过 | test_close_intimate_tier / test_close_intimate_tier_without_open |
| ACCEPT-4 state_axis 含记忆快照跨形态一致 | 通过 | test_state_axis_memory_snapshot：重建 BondSystem 读取一致 |
| ACCEPT-5 回执完整 | 通过 | 本文件 + receipt.json，ReceiptValidator 0 issues |

## 测试结果

- 新增：src/brain/persona/tests/test_bond_deepen_s7.py — 6/6 通过
- 回归：test_bond_s3 + test_bond_deepen_s7 — 11/11 通过

## 边界确认

- 未做疲劳/无聊模拟、未做进化矩阵/衰减数值（honesty_boundary 保持）——符合 form-expansion §3.2 轻量边界。
