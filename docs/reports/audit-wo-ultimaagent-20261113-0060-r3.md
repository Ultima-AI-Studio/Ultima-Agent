# wo-ultimaagent-20261113-0060 · 第 3 轮 v1.2 重审

> 状态：已完成（静态审单）  
> 审计对象：wo-ultimaagent-20261113-0057 / 0058 / 0059 v1.2  
> 审计范围：只复核第 2 轮 10 行打回、改动引入的新矛盾、31 条 Gate 可判性及 D-01～D-08；不重算已确认的 36/36 覆盖。

## 1. 结论

**不通过。最高严重度：BLOCKER。**

1. 第 2 轮最小打回清单的 10 行中，**8 行闭、2 行未闭**。未闭均在 0058：T2 的未裁决态没有 `pending` 且被强制恰一 `selected`；T4b 同时要求 `selected|rejected`、未裁决 `pending` 和“仅一 selected”。
2. v1.2 另有 **4 个新矛盾（BLOCKER 2、HIGH 2）**：0057 T4 的 3/5 步分裂、0057 T6 漏放行附录 A、0057 T3 回执模板残留 7 字段、0058 T1 同时强制和禁止具体数值。
3. 31 条 Gate 均有字段集合/计数/顺序/正则/diff 等脚本锚点，**31 可机检、0 只能人读**；但其中 **6 条被卡面其他条款抵消**，不能据此放行。
4. `D-01`～`D-08` 均为真占位，**8/8 未偷填待裁具体数值**。
5. 三单头部编号数仍为 **0057=11、0058=9、0059=16**；不重算 36/36。第 1 轮已闭的主文分工与 D 编号唯一性未见回归。

因此：**0057/0058/0059 不得进入执行，需修卡后再审。**

## 2. 审计输入指纹

| 单 | 头部编号数 | SHA-256 |
|---|---:|---|
| 0057 v1.2 | 11 | `B0489165999AC0512A99EB05D5010992A10E704D367309C742BCC640D885C0B5` |
| 0058 v1.2 | 9 | `48E9BFA7EB61C6B361CAAEC058856F23A29D2EE31B33E9B43C445A4EB6D3CFE8` |
| 0059 v1.2 | 16 | `70AA6CA1AC9D0DDCF84C4883ED1BF9D628BD063AE6E8A838601C82409324F0DB` |

## 3. T1 · 10 行打回闭环

| # | 单号 + T + v1.2 原文片段 | 判定 | 仍缺什么 / 一句话修法 |
|---:|---|---|---|
| 1 | 0057 T3：`顶层字段 5 个`＋`steps[] 子字段 6 个` | 闭 | 无；字段集合与计数一致。 |
| 2 | 0057 T4：receipt 含`exit/artifacts[]/side_effects[]/usage/idempotency_key`五字段；Gate 要求 request/receipt 两处都有幂等键 | 闭 | 无；schema 与 Gate 一致。 |
| 3 | 0057 T6：`唯一例外＝D-01 选 A 时 §15.2.1 的 1 行迁移` | 闭 | 无；r2 指出的 §15.2.1 例外已补，附录 A 冲突另列新问题。 |
| 4 | 0058 T1：D-04 B 案`目标值由 D-04 一并决定，本单不得先写任何具体值` | 闭 | 无；4096/4000/512/4512 是既有事实与复算，不是 D-04 目标值。 |
| 5 | 0058 T2：顶部`未裁决 → Gate 判 SKIP`；Gate 只许`selected/rejected`且`恰有一处 selected` | **未闭** | 补 `pending`；未裁决时两块 pending 并 SKIP，裁决后才要求一 selected、一 rejected。 |
| 6 | 0058 T4b：文件已是`架构树节点 desc（不写基线）`；写项仍并列`status=selected|rejected`、`仅一 selected`、`裁决前 pending` | **未闭** | 将允许值统一为 `pending|selected|rejected`，并把“仅一 selected”限定在裁决后。 |
| 7 | 0058 T4c：§16.5 已同时进入执行 allowlist 与 T6 diff 门 | 闭 | 无；写域与总门一致。 |
| 8 | 0058 T5b：新增`D-08`，未裁决`pending`且 Gate SKIP，禁止执行者自选 | 闭 | 无；裁决来源与分支门齐。 |
| 9 | 0059 T4d：任务表/写项/Gate/模板均为`prepare→copy→verify→swap→retire`五步 | 闭 | 无；步骤数一致。 |
| 10 | 0059 T6：`新增行 ⊆ §二十六 ∪ {附录 A 该 1 行}` | 闭 | 无；全称门已含唯一例外。 |

T1 详细证据：`docs/reports/evidence/audit-0060/r3-t1-return-closure.md`。

## 4. T2 · 新问题与回归

### 4.1 新问题

| ID | 严重度 | 单号 + T + 原文片段 | 问题 | 一句话修法 |
|---|---|---|---|---|
| R3-N01 | HIGH | 0057 任务表 T4（L48）：`时序 3 步`；T4 写项/Gate（L112/L118）：五步 `prepare→policy.check→start→stream*→finalize` | 同一时序存在 3/5 两个计数。 | 把任务表 T4 改为“时序 5 步”。 |
| R3-N02 | BLOCKER | 0057 范围（L34）：`§二十五＋附录 A 一行`；T6（L146）放行集合只有 §二十五和条件 §15.2.1，却又要求附录 A 一行 | 强制新增的附录行不在全称门集合，T6 必失败。 | 放行集合加入`{附录 A 恰 1 行}`。 |
| R3-N03 | HIGH | 0057 T3 Gate（L101）：顶层 5＋子字段 6；粘贴模板（L165）：`7字段` | 回执模板仍保留旧 schema 计数。 | 模板改为“顶层 5＋steps 子字段 6”。 |
| R3-N04 | BLOCKER | 0058 T1（L66-L68）要求 4000/512/4512/4096 复算和数值表，又写`本 T 不得出现任何具体数值`；Gate（L72-L74）再要求取数比对 | 同一 T 强制出现又绝对禁止数值。 | 禁令收窄为“B 案不得出现未裁决的 n_ctx 目标值”。 |

### 4.2 已闭项回归

composer、habit caller、dispatch 时序、policy API、取消主文、预算公式的唯一归属均未回归；D 编号仍唯一分配为 0057=`D-01..03`、0058=`D-04/05/06/08`、0059=`D-07`。不展开重报此前已闭问题。

T2 详细证据：`docs/reports/evidence/audit-0060/r3-t2-new-contradictions.md`。

## 5. T3 · Gate 可判性重算

| 单 | Gate 数 | 有脚本锚点 | 只能人读 | 被卡面其他条款抵消 |
|---|---:|---:|---:|---:|
| 0057 | 6 | 6 | 0 | 3（T3/T4/T6） |
| 0058 | 9 | 9 | 0 | 3（T1/T2/T4b） |
| 0059 | 16 | 16 | 0 | 0 |
| **合计** | **31** | **31** | **0** | **6** |

抵消原因：

- 0057 T3：Gate 是顶层 5＋子字段 6，粘贴模板仍写 7。
- 0057 T4：Gate 是 5 步，任务表机检锚点仍写 3 步。
- 0057 T6：Gate 的全称 diff 集合漏掉同卡强制的附录 A 一行。
- 0058 T1：Gate 强制数值复算，同 T 又禁“任何具体数值”。
- 0058 T2：未裁决应 SKIP，却没有 pending 且强制一 selected。
- 0058 T4b：Gate 接受 pending，写项却把块首行值限定为 selected/rejected，并称未裁决时“仅一 selected”。

逐 Gate 31 行证据：`docs/reports/evidence/audit-0060/r3-t3-gate-gradability.md`。

## 6. T4 · D-01～D-08 占位抽查

| 占位 | 判定 | 证据摘要 |
|---|---|---|
| D-01 | 真占位 | 只列取消实现 A/B，无新数值。 |
| D-02 | 真占位 | 只有“秒”单位，无时限值。 |
| D-03 | 真占位 | clarify/refuse 触发线未填。 |
| D-04 | 真占位 | B 案目标值未填；既有 4096 等不是待裁目标。 |
| D-05 | 真占位 | 容量/位置另批，无 MB/GB 数值。 |
| D-06 | 真占位 | 行为 A/B，无数值。 |
| D-07 | 真占位 | 样本量/失败线未填；档位与 24h 引既有 R-56。 |
| D-08 | 真占位 | 节点处置 A/B，未裁决 pending，无数值。 |

结论：**真占位 8/8，假占位 0/8。**

T4 详细证据：`docs/reports/evidence/audit-0060/r3-t4-placeholders.md`。

## 7. T5 · 最小打回清单

| 单号 + T | 打回原因 | 一句话修法 |
|---|---|---|
| 0057 T3 | Gate 与回执模板的字段计数不同 | 模板改为“顶层 5＋子字段 6”。 |
| 0057 T4 | 任务表 3 步与明细/Gate 5 步冲突 | 任务表统一为 5 步。 |
| 0057 T6 | diff 全称门漏放行附录 A | 集合加入附录 A 恰一行。 |
| 0058 T1 | 数值复算与“不得出现任何具体数值”互斥 | 禁令只约束未裁决的 n_ctx 目标值。 |
| 0058 T2 | 未裁决没有 pending，且被强制选案 | 增 pending/SKIP 分支，裁后再要求一选一拒。 |
| 0058 T4b | pending 与 selected/rejected 限定及“仅一 selected”互斥 | 统一三值状态并把一 selected 限定为裁后。 |

## 8. 边界与未覆盖声明

- 未改 0057/0058/0059、队列或其他产品文档；未执行三张修复单。
- 未访问 `UltimaAgentNext`；未 commit/push/tag。
- 写入仅为本报告和 `docs/reports/evidence/audit-0060/r3-*`。
- 未代 Owner 裁决 D-01～D-08。
- 未重算已确认的 36/36；只确认三单头部编号数仍为 11/9/16。

## 9. 交付物

- 主报告：`docs/reports/audit-wo-ultimaagent-20261113-0060-r3.md`
- T1：`docs/reports/evidence/audit-0060/r3-t1-return-closure.md`
- T2：`docs/reports/evidence/audit-0060/r3-t2-new-contradictions.md`
- T3：`docs/reports/evidence/audit-0060/r3-t3-gate-gradability.md`
- T4：`docs/reports/evidence/audit-0060/r3-t4-placeholders.md`

READY_FOR_OWNER_REVIEW
