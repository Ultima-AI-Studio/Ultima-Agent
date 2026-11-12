# 任务卡：s7-bond-deepen
- **task_id**：s7-bond-deepen
- **标题**：羁绊深化（C 类 · 阶段二羁绊系统收口）
- **优先级**：80（P1）
- **category**：core　**skill**：engineering
- **依赖**：s3-bond-system（M18 底座已建）
- **依据**：form-expansion-plan-20261024.md §3.4 阶段二验收口径；jarvis-reverse-architecture M18

## goal
羁绊系统深化（对齐阶段二三验收项，全部落到既有 BondSystem 上，不另起炉灶）：
1. 关系记忆沉淀：add_note（kind=note，沉淀用户偏好/互动史字段齐全，可查询 get_notes）；
2. 距离档位可回退：close_intimate_tier（亲密→专业，留痕）；切换生效即表达变化（state_axis 已供消费）；
3. 跨形态共享：state_axis 已返回 tier/address/tone/honesty，补齐 relation 记忆快照供多端读取一致。
   
**禁止**：不做疲劳/无聊模拟、不做进化矩阵/衰减数值；不拟人化情感表述。

## acceptance[]
- [ ] ACCEPT-1：add_note 沉淀偏好/互动史（kind=note），字段齐全（ts/kind/detail/scope）
- [ ] ACCEPT-2：get_notes 可查询（全量 + 按 kind 过滤）
- [ ] ACCEPT-3：close_intimate_tier 档位回退生效且留痕；未开放亲密时回退报确定性错误
- [ ] ACCEPT-4：state_axis 含关系记忆快照（notes 数量/tier/address/tone），跨形态读取一致
- [ ] ACCEPT-5：回执完整（ReceiptValidator 0 issues + tasks.json COMPLETED）

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src/brain/persona + tests + tasks）
