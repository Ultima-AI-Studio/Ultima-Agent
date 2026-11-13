# DeepSeek 独立方案 · Autoloop 融合（不是评审，是它自己写的方案）

> 生成通道：DeepSeek API（deepseek-chat）｜时间：2026-11-13 23:44
> 说明：本文件为外部模型**自出方案原文**，未经删改。它前两轮评审与我方方案在 `review-autoloop-机制借鉴研究-deepseek-20261113.md`、`review-autoloop-融合方案A案-deepseek-20261113.md`。

---

# Next 引擎 · Autoloop 融合方案

## 0 一句话方案

只借 Autoloop 的**事实日志＋幂等收件箱＋单向写入口**三件机制，把 0057 主链 11 条 BLOCKER 落成可审计契约；`unknown` 不进八态、只做 run 层投影；三张单收口，其余砍掉。

**我改了哪条判断**：第二轮说「落点切小单改 §25.10」——推翻。§25.10 已冻结在 0057 自检 PASS 的文本里，再动它等于让 0057 重审。改为**新增 §27.1–§27.4 承载 cancel_observe 与 unknown**，§25.10 一字不改，只在 §27.1 声明「§25.10 的 `cancel_outcome` 是终态，§27 的 `cancel_observe` 是过程观测，二者不互斥」。理由：冻结面越小，审计越独立。

## 1 范围冻结

**做**：
1. 新增 §27.1–§27.4（cancel_observe／unknown／事实日志／对账）。
2. 0057 的 §25.1–§25.11 提交＋冻结 tag。
3. 队列单向写入口 `scripts/queue-writer.py`＋幂等收件箱表。
4. 跨域 16 条中与主链强耦合的 6 条写进 §二十六，其余 10 条挂 §二十七 占位。

**不做**：
1. 不引入 SQLite／SSE／cron／多通道（Autoloop 的运行时形态不搬）。
2. 不改 `n_ctx=4096`、不改 `live.json`。
3. 不做 M2 全量、M8 日志形态、M9 过度设计（维持第一轮判断）。
4. 不新增用户可见承诺（E-04 满卷语义只写「拒绝并记录」，不写「排队不丢」）。
5. 不动八态迁移表 §15.2.1。

## 2 工单拆分（3 张）

### 单 A：0057 冻结（收口单）
- **目标**：§25.1–§25.11 过独立审计并打冻结 tag。
- **前置**：0058 已提交；0057 自检 PASS 记录在案。
- **写域**：`docs/specs/next-感知交互参数基线-20261113.md` §25 段；`docs/reports/audit-0057-*`（**仅审计侧写**）。
- **Gate 全绿**：①独立审计报告 PASS 且审计者≠0057 作者；②`git tag freeze-0057` 存在且指向含 §25 全文的 commit；③`live.json` 哈希与冻结值一致；④卡面无 `W_VOLATILE_COUNT_WRITTEN` 命中。
- **禁止项**：开发侧不得创建/修改 `docs/reports/audit-*`、`evidence/`；不得改 §25 正文以外的章节。

### 单 B：§27 契约（新增单）
- **目标**：写 §27.1–§27.4，含 cancel_observe、unknown、事实日志、对账。
- **前置**：单 A 冻结 tag 存在。
- **写域**：基线文档 §27 段；`scripts/queue-writer.py`（新建）；`tasks/queue/inbox/`（新建目录）。
- **Gate 全绿**：①§27 四条各有字段表＋映射规则＋Gate 段；②`queue-writer.py` 单测覆盖「重复投递同 idempotency_key 只写一次」；③对账脚本 `scripts/reconcile-queue.py` 对 179 条记录跑出 0 差异或差异清单入 `evidence/reconcile-*.json`（**由审计侧生成**）；④§25.10 文本 diff 为空。
- **禁止项**：不得改 §25 任何字；不得让 `dispatch-work-order.py` 直写 `queue-status.json`（必须经 writer）；不得在卡面写死计数。

### 单 C：跨域 6 条（§二十六）
- **目标**：16 条中挑 6 条与主链强耦合的写进 §二十六，其余 10 条在 §二十七 列标题占位。
- **前置**：单 B 的 §27 已冻结。
- **写域**：基线文档 §二十六、§二十七。
- **Gate 全绿**：①6 条各带「上游契约编号→本域字段→下游消费点」三段；②§二十七 10 条仅标题＋「待 0060」标记，无正文；③审计侧确认 6 条与 §25／§27 无字段名冲突。
- **禁止项**：不得把 10 条占位写成半成品正文；不得新增 §25 引用。

## 3 契约条文草案

### §27.1 cancel_observe（过程观测）
字段：`run_id`、`cancel_requested_at`、`ack_window=3s`、`cancel_observe ∈ {running, not_running, unknown}`、`observed_at`、`consecutive_unknown_rounds`。
判定规则：
- `not_running`：ack 窗口结束且 `ActiveProcesses==0`。
- `running`：ack 窗口结束且 `ActiveProcesses>0`。
- `unknown`：ack 窗口结束且 `ActiveProcesses==0` **不成立**（即查询本身失败/超时/进程表不可读）。
投影规则：`cancel_observe=unknown` 连续 3 轮 → 告警事件 `CANCEL_OBSERVE_UNKNOWN`；**不写八态**，仅在 run 层投影 `CANCELLED_PENDING`。
Gate：单测覆盖三态各一例＋连续 3 轮告警一例；`cancel_observe` 不出现在 `queue-status.json` 任何字段。

### §27.2 unknown（run 层）
定义：`unknown` 是 run 状态，不是八态之一；语义＝「接单程序 5 分钟未回执」。
映射：run `unknown` → 八态保持 `dispatched` 不变，仅置 `audit_run.unknown_since`。
Gate：`unknown` 字符串不出现在 §15.2.1 迁移表；出现即 Gate 红。

### §27.3 事实日志＋幂等收件箱
- 事实日志：`tasks/queue/facts.jsonl`，字段 `id/type/subject/summary/detail/link/at`，`subject` 仅标识符字符、`link` 仅 ASCII、`summary/detail` 不进提示词。
- 收件箱：`tasks/queue/inbox/<idempotency_key>.json`，同 key 二次投递返回首次结果，不重写。
- 单向写入口：**只有** `queue-writer.py` 可写 `queue-status.json` 与 `facts.jsonl`；`dispatch-work-order.py` 改为调 writer。
Gate：`grep -r "queue-status.json" scripts/` 只命中 writer 与 reconcile；重复投递单测 PASS。

### §27.4 对账
`reconcile-queue.py` 比对 `queue-status.json` × `facts.jsonl` × `inbox/`，输出差异 JSON 到 stdout；审计侧落 `evidence/`。
Gate：179 条基线跑出 0 差异；人为注入 1 条差异能被检出。

## 4 风险与止损

| 风险 | 触发条件 | 动作 |
|---|---|---|
| §27 与 §25.10 语义打架 | 审计报字段冲突 | 回滚单 B，§27.1 改为纯附录不引用 §25.10 |
| writer 成新单点 | writer 崩溃致队列不可写 | 保留 `queue-status.json` 只读快照，writer 失败降级为「拒绝派发＋告警」，不裸写 |
| unknown 被误当八态 | `grep unknown` 命中迁移表 | Gate 红，单 B 打回 |
| 对账差异无法归零 | 179 条中 >0 差异 | 差异清单入 evidence，单 B 不冻结，转 0060 |
| 审计侧越界写开发路径 | `git diff` 显示开发 commit 含 `audit-*` | 该 commit 作废重提 |

## 5 与 §25／§二十六／§二十七 冲突处置

- **§25**：一字不改。§27.1 显式声明「`cancel_outcome`（§25.10 终态）与 `cancel_observe`（§27.1 过程）正交」。
- **§二十六**：单 C 只写 6 条，其余 10 条在 §二十七 占位，避免半成品。
- **§二十七**：原为空，现承载 §27.1–§27.4＋10 条占位标题。

## 6 一周内可机检最小成果

1. `git tag freeze-0057` 存在，`git show freeze-0057:docs/specs/...md | grep -c "§25"` ≥ 11。
2. `python scripts/queue-writer.py --selftest` 退出码 0，含重复投递用例。
3. `python scripts/reconcile-queue.py` 对 179 条输出 `{"diff":0}`。
4. `grep -c "cancel_observe" 基线文档` ≥ 1 且 `grep "cancel_observe" tasks/queue/queue-status.json` 为空。
5. `grep "unknown" §15.2.1 段` 为空。
6. `sha256sum config/voice-next/live.json` 与冻结值一致。

---

## 必答

**a) E-01 闭合判据**：Gate 通过**只证明「取消失败有记录」，不证明「运行中取消可达」**。闭合需三条同时成立：①`cancel_observe=not_running` 在真实运行中至少被观测到 1 次（证明取消路径能走通）；②`running` 态下取消请求能在 ack 窗口内被受理（有回执事实）；③`unknown` 连续 3 轮告警可触发。仅 ③ 成立＝只证明有记录。**判据：E-01 闭合 = ①∧②∧③，缺一不闭合。**

**b) 四者关系表**

| 维度 | 载体 | 取值 | 与其它三者关系 |
|---|---|---|---|
| `cancel_outcome`（§25.10） | 取消请求终态 | `cancelled` 等 | 终态；与 `cancel_observe` 正交，不互斥 |
| `cancel_observe`（§27.1） | run 层过程观测 | `running/not_running/unknown` | 过程；`unknown` 不落八态，只投影 `CANCELLED_PENDING` |
| 幂等键（§25.9） | 收件箱 key | 字符串 | 保证同一取消请求只处理一次；与 observe 无直接映射 |
| 八态（§15.2.1） | 队列状态机 | 8 值 | `unknown` **不是**八态之一；run `unknown` 时八态保持 `dispatched` |

**c) 谁写队列**：只有 `queue-writer.py` 写，**每次派发/回执写 1 次**（幂等键去重后实际落盘 1 次）。出问题由 `reconcile-queue.py` 对账，审计侧落 evidence，开发侧不得写 evidence。

**d) 砍留理由**：砍 SQLite/SSE/cron/多通道（运行时形态不搬，借机制不借实现）；砍 M2/M8/M9（第一轮已判不必）；砍 10 条跨域（半成品比空更危险）。留：事实日志＋幂等收件箱＋单向写入口（三件直接堵双源）、cancel_observe/unknown（E-01 闭合必需）、0057 冻结（主链 11 条 BLOCKER 的收口）。**理由：3 张单能在一周内机检，超过 3 张必然有单卡在「等审计」而非「等开发」。**
