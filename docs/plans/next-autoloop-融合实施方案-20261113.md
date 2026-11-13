# Next 引擎 · Autoloop 融合实施方案（v0.3）

> 版本：v0.3（含 §10 三方对照、§11 模块归属；2026-11-14 按 0065 评审改判 §11 两行）｜日期：2026-11-13（v0.3 修订 2026-11-14）｜依据：`docs/plans/next-autoloop-机制借鉴研究-20261113.md` v0.2 ＋ `docs/reports/review-autoloop-机制借鉴研究-deepseek-20261113.md`
> 状态：**方案稿**。评审通过后按 G-PLAN-001 随工单落盘，再拆 0061／0062 派 Codex。
> 定位：本文只回答「按什么顺序、落到哪、怎么验收」，不重复研究稿里的事实核实。

---

## 0. 一句话

**先把「谁写队列」这一个事实钉死，再让三条低代价机制进契约，最后才谈外挂自动化。** 顺序反了（先装 Autoloop 再补对账）就是用未定义的双源换一周速度——这是 DeepSeek 否掉 v0.1 的唯一理由，也是本方案的第一原则。

---

## 1. 范围冻结

**本方案要做**
1. 定义「唯一写入口 + 幂等收件箱 + 对账」三件套的**机制**（不是口号），并给可机检 Gate。
2. 把 **M3（指令数据分离）／M4（跳数＋扇出熔断）／M7（卡片 ask.key 幂等）** 写成基线 §二十七的契约条文，各带负例测试。
3. 把 **M2／M8／M9** 明确降为 v1.1 提案，不进本轮，避免范围膨胀。
4. 给出外挂（Autoloop）接入的**准入条件与禁区**，以及 2 天 spike 的验收口径。

**本方案不做**
- 不改 `config/voice-next/live.json` 任何字段（0058 已核哈希）。
- 不新增任何对用户的产品承诺（`unknown` 态、`hops` 上限都是内部机制）。
- 不整体换 Node 栈、不拷 Autoloop 源码（只借机制；MIT 只解决版权，不解决专利与 TS→Python 等价性）。
- 不碰 0057 正在写的 §二十五、不抢 0059 待写的 §二十六。
- 不在本轮做事件溯源全量、不做交付流水线、不做「暂停是日志事实」层。

---

## 2. 阶段与依赖（三阶段，串行）

| 阶段 | 做什么 | 前置 | 写域 | 冲突风险 |
|---|---|---|---|---|
| **P0 钉事实** | 收件箱目录 + `claim_id` 发号规则 + `scripts/reconcile-inbox.py` + 队列卡新增 `claim_id` 字段 | 无（但**改派发器须等 0057 收口**） | `tasks/queue/inbox/`、`scripts/reconcile-inbox.py`（新文件）、`tasks/queue/queue-status.json` | 低（新文件为主）；派发器改动推后 |
| **P1 进契约** | 基线新增 §二十七（M3／M4／M7 三条）＋ 三份负例测试 | 0057、0059 均收口（同一文件写域空出） | `docs/specs/next-感知交互参数基线-20261113.md` §二十七、`scripts/tests/` | 中（必须等两单冻结） |
| **P2 接外挂** | 2 天 spike：Autoloop 装开发机，只读事件、只写 inbox，跑一条「早报式」流水线 | P0 完成且 P1 定稿 | `tasks/queue/inbox/`（只写）、开发机进程 | 高（引入 Node 运行时，见 §7.4） |

**为什么 P0 排第一**：DeepSeek 指出的三处双源（run 状态 vs 八态、回执 vs note、claim 语义叠加），全部发生在「外挂开始写东西」那一刻。P0 没做完就进 P2，双源立刻成立。

---

## 3. P0：唯一写入口三件套（这是本方案的地基）

### 3.1 机制条文（写进后续工单，不改基线）

1. **单一写入口**：`tasks/queue/queue-status.json` 仍是唯一可写队列，且**只允许 `scripts/queue-writer.py` 一个进程写**（`dispatch-work-order.py` 改为调 writer，不再直写）；任何外部组件（含 Autoloop、未来的调度中间层）**只能写 `tasks/queue/inbox/`**，不得直写队列、不得直写 `docs/reports/fix-*`。机检：`grep -r "queue-status.json" scripts/` 只允许命中 `queue-writer.py` 与 `reconcile-inbox.py`。
2. **回执即文件**：一条回执 = `tasks/queue/inbox/<claim_id>.json`，字段最小集 `claim_id / work_order / outcome / summary / session / usage / events / written_at`。
3. **幂等消费**：队列侧消费者按 `claim_id` 去重；同一 `claim_id` 重复投递只处理第一次，其后记 `duplicate` 并丢弃。
4. **一次事务并入**：并入队列状态、写队列 `note`、登记报告指针，三件事在一个事务内完成（JSON 队列用「临时文件 + 原子替换 + 处理标记」实现，不引入数据库）。
5. **对账独立**：`scripts/reconcile-inbox.py` 只读不比写，输出差异表；**差异非零只告警，不自动改队列**（防止脚本自己成为第二个写者）。
6. **claim 归属**：派发前由队列发 `claim_id` 并写进卡面；重派换新 `claim_id`，旧 id 的回执进 `rejected`，不进 `done`。
7. **审计输入隔离**：外挂层与其适配层**禁写** `docs/reports/audit-*`、`docs/reports/evidence/`；`fix-*` 报告只允许由队列消费者按回执生成。

### 3.2 对账脚本口径（`scripts/reconcile-inbox.py`）

| 检查项 | 判据 | 差异时的动作 |
|---|---|---|
| 孤儿回执 | inbox 有 `claim_id`，队列无对应 `work_order` 记录 | 告警，列出文件 |
| 孤儿卡 | 队列 `dispatched_at` 非空但 inbox 无回执且超过阈值 | 告警，标 `suspect_lost` |
| 重复回执 | 同 `claim_id` 出现 ≥2 个文件 | 告警，保留最早、其余标 `duplicate` |
| 状态不一致 | 回执 `outcome=done` 但队列 state 非 `audit/closed` | 告警，不自动改 |
| 未消费积压 | inbox 中 `written_at` 早于 24h 仍未处理 | 告警，计入「注意力预算」 |

- 输出：`--json` 机读 + 人读表；退出码 `0=无差异`、`1=有差异`（供 CI 与派发前检查用）。
- **开源排查结论**：无现成开源件能读我们自研 JSON 队列与 inbox 命名规则，本脚本为必要自写，控制在 80 行以内、零第三方依赖。

### 3.3 Gate P0（全绿才进 P1）
- [ ] `inbox/` 目录存在且有 `.gitkeep`；`README` 一句说明「只写不读」。
- [ ] 造 3 条测试回执（正常 / 重复 `claim_id` / 孤儿 `claim_id`），`reconcile-inbox.py` 分别输出 `0 / 1 / 1`，且人读表能指出具体文件。
- [ ] 队列卡新增 `claim_id` 字段，`queue-status.json` 179 条全部通过 schema 校验（缺字段即 `1`）。
- [ ] 派发前检查接入 `reconcile-inbox.py --json`，差异非零时派发器拒派。

---

## 4. P1：三条机制进 §二十七（各带负例）

| 编号 | 条文要点 | 落点 | Gate（可机检） |
|---|---|---|---|
| §27.1 M3 指令数据分离 | 事件字段只允许 `id/type/subject/summary/detail/link/hops`；`subject` 限 `[A-Za-z0-9#._:/@-]`，`link` 限纯 ASCII；`summary/detail` 只落资料文件**不进提示词**；`access/cwd` 等执行上下文一律拒收，由本地补 | 基线 §27.1 ＋ `scripts/tests/test_event_schema.py` | 负例：投递含 `access` 的事件 → 拒收并返回 `rejected:unknown_field`；投递含 `cwd` → 同；正例：7 字段合规事件 → 通过。断言 3 条 |
| §27.2 M4 熔断 | `hops` 缺省 0；回执事件 `hops = 本轮最大 + 1`；`hops ≥ 8` 只记录不派活；**同轮扇出上限 3**，超出截断并告警 | 基线 §27.2 ＋ `scripts/tests/test_hop_ttl.py` | 构造 9 层链：第 1–8 层派活、第 9 层仅日志，断言派活调用次数 = 8；构造同轮 5 个下游，断言只派 3、告警 1 次 |
| §27.3 M7 卡片幂等 | 卡片带 `ask.key`（事项标识，非随机 id）；同 key 未关闭时不再发第二张；`fyi` 类卡片不带按钮、点击不产生回答 | 基线 §27.3 ＋ `scripts/tests/test_card_idempotent.py` | 同 key 连发 3 次 ask，断言卡片行数 = 1；关闭后再发 = 2；`fyi` 点击不产生 `resolve` 记录 |

**P1 禁止项**：不得顺手写 §27.4 事件溯源、§27.5 交付流水线（那是 v1.1）；不得改 §25/§26 任何一行；不得改 `dispatch-work-order.py` 的既有参数表（只允许加 `claim_id`）。

---

## 5. P2：外挂 spike 的准入与验收

**准入（缺一不进）**
1. P0 的 Gate 全绿、`reconcile-inbox.py` 已接进派发前检查。
2. 外挂进程只持有 inbox 的写权限；`docs/reports/`、`docs/specs/` 对它只读。
3. 明确「外挂挂了怎么办」：挂掉 = 回到人工派发，队列不受影响（不需要回滚）。

**spike 验收口径**
- 一条「早报式」流水线跑通：定时事件 → 规则 → 派活 → 回执落 inbox → 消费者并入队列 → `reconcile-inbox.py` 输出 `0`。
- 人为制造两种故障：① 杀掉外挂进程；② 手写一条重复 `claim_id` 回执。断言：队列状态无分叉、对账能指出差异。
- 记录运行成本：进程常驻内存、单轮 token、续接首轮的重放 token（DeepSeek 要求写明，不许对外说「零消耗」）。

**2 天不出结论就停**：spike 只回答「这套外挂能不能不污染队列」，不回答「要不要长期用」。

---

## 6. M1 的分歧与二轮评审结论（A 已改为 A′）

DeepSeek 首轮主张首批只做 M3/M4/M7，我方主张 M1 会话字段要进首批。**二轮把 A 案单独送审后，它判定「A 按现文不成立——那只是把 E-01 改名」，并给出改法。** 以下是改条件后的 A′，与保守的 B 并列，你拍一个即可。

原文：`docs/reports/review-autoloop-融合方案A案-deepseek-20261113.md`

| 选项 | 范围 | 好处 | 代价 |
|---|---|---|---|
| **A′（推荐，已按 DeepSeek 二轮评审改条件）** | ①§27.4 只写 M1 会话字段（信封带 `session_id`）；②**切小单**改 §25.10，补取消观测值 `cancel_observe ∈ {running, not_running, unknown}`，仅挂 run 层 | 把 E-01 由「静默留洞」改成「显式挂起 + 告警」，审计上可辩护 | 多约 15 行＋4 条 Gate＋1 轮 0057 返工审计；**且只能称「显式挂起」，不得称「已解 E-01」** |
| **B（DeepSeek 首轮口径）** | P1 只做三条；M1 进 v1.1 | 范围最小、最快收敛 | E-01 仍是 BLOCKER，取消表对「取消时已无进程」的 run 无定义 |

**A′ 的四条硬条件（缺一即退回 B）**
1. `unknown` 是**判定结果**，不是状态：「3s ack 窗口结束，既未收到 cancel_ack，也未取得 `ActiveProcesses==0` 强杀凭据」；`not_running`＝取消触发时即无活动进程、无在途 ack 义务，直接落 `CANCELLED`，不占窗口。
2. **不落 `CANCELLED`**：`unknown` 时 run 保持最后事实状态，只向队列投影 `CANCELLED_PENDING`（队列侧标记，非八态）。
3. **解除规则**：下一轮对账或再次取消取得 `ActiveProcesses==0` 凭据 → 转 `running` 并落 `CANCELLED`；连续 3 轮仍 `unknown` → 人工介入告警，脚本不改队列。
4. **Gate 四条**：a）ack 超时＋强杀后 `ActiveProcesses!=0` → `unknown` 且未落 `CANCELLED`；b）取消时无进程 → `not_running` 直落 `CANCELLED`；c）`unknown` 连续 3 轮 → 告警且队列未被脚本改动；d）八态状态图 diff 为空。

> 落地位置**不是** §27.4：`unknown` 的判据与 §25.10 的 3s ack／强杀／`ActiveProcesses==0` 强耦合，分两节写会造成「判据在一节、观测值在另一节」的新双源。故 §27.4 只放 `session_id`，`unknown` 切小单进 §25.10（§25.10 正是 0057 刚写、尚未冻结的最低成本窗口）。
>
> **口径纪律**：对外只能说「E-01 显式挂起」。`unknown` 不解决「不知道在不在跑」本身——那需要可靠的进程级探活，属 v1.1；把 A′ 说成「已解 E-01」即过度承诺。

---

## 7. 降级与延后（明确写死，防范围膨胀）

| 机制 | 处置 | 触发再议的条件 |
|---|---|---|
| M2 事件溯源（全量） | v1.1 提案；本轮最多做 append-only 日志 + 每日投影快照 | 队列出现「需要历史回溯」的真实事故 ≥2 次 |
| M8 规则即配置＋暂停不补跑 | 只吸「到点跳过、恢复不补跑」语义；不抄「暂停是日志事实」层 | M2 落地后 |
| M9 交付流水线 | v1.1 提案，与 CI 一起议 | 有真实发布节奏后 |
| M5 回执一次生效 | 二期，先砍为 5 字段（`outcome/summary/session/usage/events`） | P1 定稿后 |
| M6 claim 幂等＋止损 | 二期，退避参数固定（5min 起翻倍、上限 1h、第 10 次 `cancelled`），不做可配 | P0 的 `claim_id` 跑顺后 |

---

## 8. 风险与红线（DeepSeek 提的六条，逐条已接住）

| # | 风险 | 本方案的处置 |
|---|---|---|
| 1 | 队列与外部状态无跨库事务 | 只允许 inbox 一个写点；对账脚本只读告警 |
| 2 | claim 语义叠加、同一份活被两处领走 | `claim_id` 由队列发号；重派换 id；旧 id 回执进 `rejected` |
| 3 | 续接会话上下文重放重新计费 | spike 必须实测并写进报告；对外不说「零 token」 |
| 4 | `hops` 只限深度不限宽度 | §27.2 加同轮扇出上限 3 |
| 5 | 外挂层污染审计输入 | 禁写 `audit-*`／`evidence/`；fix 报告只能由消费者生成 |
| 6 | 引运行时早于审查时点 | spike 前先做 License/依赖/CVE 记录；Node 版本锁死并写进方案附录 |

---

## 9. 待拍点（不回复按默认走）

| # | 待拍 | 默认 |
|---|---|---|
| P1 | M1 走 A 还是 B | **A′**（`session_id` 进 §27.4；`cancel_observe` 三值切小单进 §25.10；只称「显式挂起」） |
| P2 | 首批工单怎么拆 | **0061＝P0 三件套**（可立即派发，不动基线）；**0062＝P1 §二十七**（等 0057／0059 收口后派）；**0063＝§25.10 补 `cancel_observe`**（小单，等 0057 冻结后切） |
| P3 | spike 做不做 | **做**，P1 定稿后 2 天 |

---

## 10. DeepSeek 自出方案的对照裁定（三稿）

原文：`docs/reports/plan-autoloop-deepseek-独立方案-20261113.md`。它这次交的是方案不是评审，**有三条真东西，也有三个硬错**。逐条裁定如下。

### 10.1 采纳（并入本方案）

| 它给的 | 为什么收 | 落到哪 |
|---|---|---|
| **E-01 三段闭合判据**：Gate 通过只证明「取消失败有记录」，不证明「取消可达」；闭合＝①`not_running` 在真实运行中被观测到 ≥1 次 ∧ ②`running` 态下取消请求在 ack 窗口内被受理 ∧ ③`unknown` 连续 3 轮告警可触发 | 这是三轮里唯一把「什么叫修好了」说清的判据，且可机检 | §27.4 Gate 升级为三段式；本轮 Next 代码未开工，①②标 `TBD-RUNTIME`，禁止用 ③ 冒充闭合 |
| **单向写入口收敛到单文件** `scripts/queue-writer.py`，并用 `grep -r "queue-status.json" scripts/` 只命中 writer 与 reconcile 做机检 | 把「单一写入口」从口号变成一条可执行的搜索断言 | §3.1 第 1 条；P0 Gate 增列 |
| **砍运行时形态**：不搬 SQLite／SSE／cron／多通道，只借「事实日志＋幂等收件箱＋单向写入口」 | 与我方「借机制不借实现」一致，且明确写了砍的理由 | §7 已覆盖，补一句「运行时形态不搬」 |

### 10.2 驳回（并写清理由）

| 它的写法 | 错在哪 | 处置 |
|---|---|---|
| 「§25.10 已冻结在 0057 自检 PASS 的文本里，所以不能动，改新增 §27.1」 | **前提错误**：0057 只到「自检 PASS＋READY_FOR_OWNER_REVIEW」，**未独立审计、未提交、未打 tag**，根本没冻结。基于错误前提做的「推翻第二轮」不成立 | 维持 A′：`cancel_observe` 仍切进 §25.10（判据与观测值同节，避免跨节双源）；若 0057 已冻结则改 §27，但那要等真冻结 |
| §27.1 判定规则：`not_running`＝窗口结束且 `ActiveProcesses==0`；`running`＝窗口结束且 `ActiveProcesses>0`；`unknown`＝窗口结束且 `==0` 不成立 | **逻辑倒置**：进程还在（`>0`）说明取消没生效，它却判 `running` 并随后落 `CANCELLED`。真正该判的是「ack 是否收到、强杀后是否证明 `==0`」，不是「进程数大于零」 | 沿用 A′ 的四条硬条件，不采用它的三值判据 |
| §27.2 又把 `unknown` 定义成「接单程序 5 分钟未回执」 | **同一文件里 `unknown` 两义**（§27.1 是观测失败、§27.2 是接单超时），自己制造了它上一轮批判的那种双源 | 本轮只保留一个 `unknown`（观测失败）；「接单 5 分钟未回执」改名 `claim_timeout`，进二期 M6 |
| 单 C 从 0059 的 16 条里「挑 6 条写 §二十六，其余 10 条占位」 | **擅改 0059 范围**：0059 的 16 条是 0060 审卡通过的封闭清单，挑 6 条等于就地缩范围，违反「验收封闭、清单外走变更」 | 0059 维持 16 条不动；跨域单不重拆 |
| 「一周可机检」第 1 条 `grep -c "§25" ≥ 11`、`queue-writer --selftest` 等计数型 Gate | 正撞 `W_VOLATILE_COUNT_WRITTEN`（它自己刚被告知这条禁令，仍写死计数）；且①②依赖真实运行，Next 代码未开工，一周内不可能观测到 | Gate 改为「存在性/差值为空/断言条数」三类，不写死计数；运行类判据一律标 `TBD-RUNTIME` |

### 10.3 三方对照（一句话）

| 稿 | 它的价值 | 它的缺陷 |
|---|---|---|
| DeepSeek 评审一 | 拆穿「不共享库≠无双源」，给出三处双源与堵法 | 把「M1 进首批」判成可后置，低估 E-01 |
| DeepSeek 评审二 | 指出 `unknown` 缺判定主体/时点/Gate，是改名不是补洞 | 建议切 §25.10 时误以为它已冻结（这是它第三稿推翻自己的根因） |
| **DeepSeek 自出方案** | **E-01 三段闭合判据**＋**writer 单点 grep 机检**（这两条已采纳） | 判定规则倒置、`unknown` 双义、擅改 0059、计数 Gate、依赖未开工的运行态 |
| 本方案 v0.3 | 冻结面前提先核实、判据与观测值同节、Gate 全部可机检或显式 `TBD` | 仍缺真实运行观测（同 DeepSeek，无解，只能标 TBD） |

---

## 11. 模块归属（基础能力六块里挂哪儿）

依据：`docs/tracker/next-基础能力架构-20261113.html` §02（六块：Core／Senses.Voice／Shell／Surface／Memory／Middleware，模块数**仍是六块**）＋ 基线 §二十一 归属定案（R-68~R-73）。

**一句话：主体挂 Middleware，但整份方案不归任何单独一块——必须按四条切开放，否则会出现「一个方案两个主文」的老毛病。**

| 方案部分 | 归属模块 | 依据 | 落点 |
|---|---|---|---|
| P0 三件套（`inbox/`、`queue-writer.py` 唯一写者、`reconcile-inbox.py`、`claim_id`） | **Middleware · queue_engine**（票据与八态唯一写权） | 六块里「执行端与票据、八态定义权在此层（不是 Console）」 | 0061；inbox／reconcile 是 queue_engine 的**子件**，不新增模块 |
| P1 M3 指令数据分离（字段白名单、`summary/detail` 不进提示词、`access/cwd` 拒收） | **Middleware · delegation**（派发 ABI 入口）主体；**治理⑤ · 防投毒**只出约束声明 | 外部事件进引擎的边界就是 delegation；防投毒属横切治理层，不承载实现 | 0062 §27.1 |
| P1 M4 跳数 8 ＋ 同轮扇出 3 | **Console · 任务编排** | 「还能不能再派活」是编排策略，不是执行器职责 | 0062 §27.2 |
| P1 M7 `ask.key` 卡片幂等 | **Console · task_store**（持久幂等主体）＋ **Core · clarify**（问题与事项键的生产者）＋ **Surface · task_manager_panel**（只读呈现） | 0065 §3.4 改判：未关闭查重与关闭账是有持久状态的卡片账，归 Core 会造第二套卡账、归 Surface 违反「只画、不管」 | 0062 §27.3 |
| P1 `session_id` 一等字段 | **Core ↔ Senses.Voice** 对话信封（主文已在 §25.1） | 会话边界属对话域，§27.4 只登记字段不重定义 | 0062 §27.4 |
| P2 `cancel_observe`／`CANCELLED_PENDING` | **Middleware · queue_engine** 的 run 取消投影／票据子件（观测主体）＋ **Shell**（终止凭据来源）＋ **Middleware · state_machine**（只守八态门） | 0065 §3.6 改判：三值本身是 run 层观测结果、不是第九种状态，挂 state_machine 会把观测值写成状态；§25.10 主文不动 | 0063 |

**改判采纳记录（2026-11-14，据 0065 独立评审）**：上表 M7 与 `cancel_observe` 两行由「Core＋Surface」「state_machine＋Shell」改判为上文所写，依据见 `docs/reports/review-autoloop-module-placement-0065.md` §3.4／§3.6；其余四行经评审维持。0065 结论等级＝有条件通过，未决项 U-01～U-04 已全部在本轮闭合。

**两条硬约束（写方案不是为了加模块）**
1. **不新增第七块**：`inbox`／`reconcile`／`writer` 都是 queue_engine 的子件；登记进能力注册表即可，基础能力模块数维持六块（页面口径不许改）。
2. **写口在 Middleware、读视图在 Console**：R-74 已定「任务库是 Console 的账」，但队列**写入口**必须在 `queue_engine`。两者不是双源——Console 只读消费、不得写 `queue-status.json`。这条正是本方案 §3.1 在模块层的对应表述，也是审卡时要机检的一条。

**§二十七 标题建议**（给 0062 用）：`§二十七 事件入口、编排熔断与票据幂等（Middleware.delegation / Console.orchestration / Core.clarify）` —— 标题里带模块，审计才能一眼对到六块。

---

## 附：来源

- 机制与协议事实：`https://raw.githubusercontent.com/KKKKhazix/agent-autoloop/main/docs/protocol.md`
- 评审一：`docs/reports/review-autoloop-机制借鉴研究-deepseek-20261113.md`
- 评审二：`docs/reports/review-autoloop-融合方案A案-deepseek-20261113.md`
- DeepSeek 自出方案：`docs/reports/plan-autoloop-deepseek-独立方案-20261113.md`
- 研究稿 v0.2：`docs/plans/next-autoloop-机制借鉴研究-20261113.md`
