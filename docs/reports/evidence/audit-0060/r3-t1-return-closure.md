# 0060-r3 · T1 十行打回闭环

> 审计对象：0057/0058/0059 v1.2；仅复核 0060-r2 的 10 行最小打回清单。

## 输入确认

| 单 | 头部编号数 | SHA-256 |
|---|---:|---|
| 0057 | 11 | `B0489165999AC0512A99EB05D5010992A10E704D367309C742BCC640D885C0B5` |
| 0058 | 9 | `48E9BFA7EB61C6B361CAAEC058856F23A29D2EE31B33E9B43C445A4EB6D3CFE8` |
| 0059 | 16 | `70AA6CA1AC9D0DDCF84C4883ED1BF9D628BD063AE6E8A838601C82409324F0DB` |

三单头部声明仍为 11/9/16；按本轮边界不重算已确认的 36/36 覆盖。

## 十行闭环表

| # | r2 打回行 | v1.2 原文片段 | 判定 | 仍缺什么 / 一句话修法 |
|---:|---|---|---|---|
| 1 | 0057 T3 字段计数 | Gate T3：`顶层字段 5 个`＋`steps[] 子字段 6 个` | 闭 | 无；字段集合与计数已逐字一致。 |
| 2 | 0057 T4 receipt | 写项：`dispatch.receipt` 含 `exit/artifacts[]/side_effects[]/usage/idempotency_key` 五字段；Gate：`idempotency_key` 在 request 与 receipt 两处 | 闭 | 无；schema 与 Gate 已对齐。 |
| 3 | 0057 T6 全称 diff 门 | `唯一例外＝D-01 选 A 时 §15.2.1 的 1 行迁移`，并给出集合放行条件 | 闭 | 无；r2 指出的 §15.2.1 条件例外已补（附录 A 的另一处冲突另列 T2 新问题）。 |
| 4 | 0058 T1 D-04 偷填 | D-04：B 案目标值`由 D-04 一并决定，本单不得先写任何具体值`；T1：`n_ctx 目标值写 D-04 占位` | 闭 | 无；仍出现的 4096/4000/512/4512 均是现状复算值，不是 D-04 的待裁目标值。 |
| 5 | 0058 T2 状态机检 | 顶部：`未裁决 → 对应 Gate 判 SKIP`；Gate T2：每块首行只许 `status=selected` 或 `status=rejected`，且全文`恰有一处 selected` | **未闭** | 缺 `pending` 分支且未裁决时仍被强制选案；修法：允许两块 `status=pending`，未裁决时 Gate SKIP，裁决后才要求恰一 selected、一 rejected。 |
| 6 | 0058 T4b 写域＋状态机检 | 文件已改为`架构树“Shell 自愈”节点 desc（不写基线任何章节）`；但写项同时写`status=selected\|rejected`、`未裁决…仅一 selected`与`裁决前 status=pending` | **未闭** | §15 越界已闭，但状态集合与未裁决分支仍互斥；修法：把块首行允许值统一为 `pending\|selected\|rejected`，并将“仅一 selected”限定为裁决后。 |
| 7 | 0058 T4c §16.5 | allowlist 含`§16.5`；T6 diff 门也含`§16.5` | 闭 | 无；写项、总 allowlist 与 diff 门一致。 |
| 8 | 0058 T5b 二选一无裁决 | 新增 `D-08`；T5b 写`未裁决时 pending、Gate 判 SKIP`且禁止执行者自选 | 闭 | 无；裁决来源和 pending 分支均已补。 |
| 9 | 0059 T4d 步骤数 | 任务表、写项、Gate、粘贴模板均为五步 `prepare→copy→verify→swap→retire` | 闭 | 无；copy/verify 已统一拆步。 |
| 10 | 0059 T6 全称门 | `唯一例外＝附录 A 恰 1 行`；放行集合为`§二十六 ∪ {附录 A 该 1 行}` | 闭 | 无；全称门与附录写项已对齐。 |

## T1 结论

10 行中 **8 行闭、2 行未闭**。未闭均在 0058 的待裁分支状态标记：T2 没有 `pending`，T4b 的正文仍把 `pending` 与“仅一 selected”并置。两行都不是“只有人读”的问题，而是卡面条款会让状态 Gate 在未裁决态无法一致执行。
