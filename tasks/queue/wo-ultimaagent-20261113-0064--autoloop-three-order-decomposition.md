# Codex 工单 · wo-ultimaagent-20261113-0064（Autoloop 三单拆解）

> 版本：v1.0｜状态：可开工｜执行端：Codex｜推理强度：high
> 依据：`docs/plans/next-autoloop-融合实施方案-20261113.md`（v0.3，含 §10 三方对照裁定）
> 参考（只读，不得改写）：`docs/reports/review-autoloop-机制借鉴研究-deepseek-20261113.md`、`docs/reports/review-autoloop-融合方案A案-deepseek-20261113.md`、`docs/reports/plan-autoloop-deepseek-独立方案-20261113.md`
> 执行序：独立单，可与 0057 收口并行；**不依赖 0059 执行**

---

## 0. 现状校准（不要重新判断这些事实）

| 事实 | 值 |
|---|---|
| 0057（主链 11 条） | state=`audit`，自检 PASS，`READY_FOR_OWNER_REVIEW`；**未审计、未提交、未打 tag，即未冻结** |
| 0058（值冲突 9 条） | 已执行、已提交 `37e9cf28`、已 tag，队列 state=`audit` |
| 0059（跨域 16 条） | 未执行，卡已审卡通过（0060 r4），**16 条是封闭清单，不得重拆或缩范围** |
| 方案 v0.3 | 已提交 `e5653451`；A′ 已选定（`session_id` 进 §27.4；`cancel_observe` 切进 §25.10） |
| §二十五 | 已写 §25.1–§25.11（基线 1792 行），写入域归 0057 |
| §二十六 | 空，归 0059 |
| §二十七 | 空，本批可用 |

**本单只产出「卡」，不产出「实现」**：三张卡交 Owner 与独立审计过 0060 式审卡后才允许派发。

---

## 1. 范围冻结

**只做（全部为新建文件）**
1. `tasks/queue/wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md` —— P0「唯一写入口三件套」执行卡
2. `tasks/queue/wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md` —— P1「§二十七 三机制」执行卡
3. `tasks/queue/wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md` —— §25.10 补 `cancel_observe` 小单执行卡
4. `docs/plans/next-autoloop-三单拆解-20261113.md` —— 拆解报告（主文归属表／依赖图／DoR 与 INVEST 自检／延后清单）
5. `docs/reports/decompose-wo-ultimaagent-20261113-0064.md` —— 本单执行报告

**不做**
- 不改基线任何章节、不改 `queue-status.json`、不改任何 tracker HTML、不改 0057／0058／0059／0060 的卡与报告。
- 不写实现代码、不建 inbox 目录、不写 `queue-writer.py`（那是 0061 的活）。
- 不派发、不 commit／push／tag；不访问 `H:\UltimaAI\UltimaAgentNext`；不调 UltimaManager 18766。

**写入域（allowlist，越界即失败）**
1. 上述 3 张新卡（`tasks/queue/` 下）
2. `docs/plans/next-autoloop-三单拆解-20261113.md`
3. `docs/reports/decompose-wo-ultimaagent-20261113-0064.md`

---

## 2. 任务清单

| 任务 | 关闭 | 产出 | 机检锚点 |
|---|---|---|---|
| T1 | 依据与冲突 | 拆解报告「依据清单」「冲突清单」两节 | 两表均存在，每条冲突有处置句 |
| T2 | P0 | 0061 卡 | 六段齐全；每 T 四段齐全；无 volatile 计数 |
| T3 | P1 | 0062 卡 | 三机制各有白名单＋规则＋负例；`cancel_observe` 明确不在本卡 |
| T4 | §25.10 补丁 | 0063 卡 | 三值判定表＋四条 Gate＋口径纪律 |
| T5 | 总验收 | 报告定稿＋交叉自检 | 主文归属表唯一；Gate 并集覆盖方案；INVEST／DoR 逐单打勾 |

---

## 3. 任务明细（三段式）

### T1 · 依据清单与冲突清单
**文件**：`docs/plans/next-autoloop-三单拆解-20261113.md`（新建，本节为前两节）
**写什么**
1. 「依据清单」表：列 5 条来源，每条给 `文件路径`＋`章节号或行区间`＋`本单从哪里取用`（来源＝方案 v0.3、三份 DeepSeek 文本、0056 报告、0057 已写的 §25 现文、`scripts/dispatch-work-order.py` 参数表）。
2. 「冲突清单」表，**必须覆盖下面 6 条**，每条给「冲突 → 处置」，处置只能选「按方案 v0.3 执行／标为不在本批／依赖某单冻结后执行」三类：
   - a. `cancel_observe` 写 §25.10 还是 §27.1（DeepSeek 第三稿主张 §27，我方定 §25.10）；
   - b. 0059 的 16 条是否重拆（禁止重拆）；
   - c. 0057 未冻结时 0063 能否开工（不能，须等冻结 tag）；
   - d. `unknown` 一词语义唯一性（只保留「观测失败」一义；「接单超时」改名 `claim_timeout` 并列入延后）；
   - e. 卡面禁止写死计数（DoR 会以 `W_VOLATILE_COUNT_WRITTEN` 拒派）；
   - f. `queue-writer.py` 引入后与 `dispatch-work-order.py` 的关系（前者唯一写者，后者改为调用）。
3. 末尾给「本批不做」清单：M2 全量事件溯源／M8 日志事实层／M9 交付流水线／M5 五字段回执／M6 止损退避，各一行理由。
**验收（Gate T1）**：两表存在且非空；冲突表条目覆盖 a–f 六个字母各一行；「本批不做」清单条数与方案 §7 表一致（以方案表实际行数为准，不写死数字）。
**禁止**：不得把冲突清单写成讨论散文；不得在处置栏写「视情况」。

### T2 · 0061 卡（P0 唯一写入口三件套）
**文件**：`tasks/queue/wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md`
**写什么**
1. 卡头：版本、状态「待审卡」、执行端 Codex、推理强度 high、依据＝方案 §3，并写明「本单不改基线」。
2. §1 范围冻结：只做四件——`tasks/queue/inbox/` 目录与 `.gitkeep`＋一行 README；`scripts/queue-writer.py`（唯一写者，含原子替换与 `claim_id` 去重）；`scripts/reconcile-inbox.py`（只读对账，五类差异）；`queue-status.json` 记录增 `claim_id` 字段（仅新单使用，存量不批量改写）。不做的：不改基线、不改派发器参数表以外的逻辑、不做外挂接入。
3. §2 任务清单：T1 inbox 与 README；T2 writer（含 selftest 子命令）；T3 reconcile（`--json`，退出码 0/1）；T4 `claim_id` 字段与 schema 校验；T5 总验收。
4. §3 每 T 三段式：`**文件**`／`**写什么**`（编号断言）／`**验收（Gate T#）**`／`**禁止**`。
5. Gate 必须包含这四条可机检断言：
   - 三例回执（正常／重复 `claim_id`／孤儿 `claim_id`）分别令 `reconcile-inbox.py --json` 的 `diff` 为 0／非 0／非 0；
   - `grep -r "queue-status.json" scripts/` 只命中 `queue-writer.py` 与 `reconcile-inbox.py`；
   - `reconcile-inbox.py` 全文不含写 `queue-status.json` 的语句（只读性断言）；
   - `writer` 重复投递同 `claim_id` 只落一次，`selftest` 退出码 0。
6. §4 DoR 五项自检、§5 禁止项、§6 给执行端的粘贴模板。
**验收（Gate T2）**：六段标题齐全（范围冻结／任务清单／任务明细／DoR／写域／禁止）；每个 T 具备 `**文件**`、`**写什么**`、`**验收（Gate T#）**`、`**禁止**` 四段；卡面不含「恰好 N 行／处／列」写法；上述四条断言逐条出现在 Gate 段；明确写「不依赖 0057 冻结」。
**禁止**：不得把 writer 的「降级裸写」写进卡（方案 §8 已否）；不得要求改 `dispatch-work-order.py` 现有参数。

### T3 · 0062 卡（P1 §二十七 三机制）
**文件**：`tasks/queue/wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md`
**写什么**
1. 卡头声明：前置＝0057 与 0059 **均已冻结**；执行时机＝两单冻结后；本卡写域仅 §二十七。
2. §27.1 = M3 指令数据分离：事件字段白名单（`id/type/subject/summary/detail/link/hops`）、`subject` 与 `link` 字符集、`summary/detail` 只落资料文件不进提示词、`access`／`cwd` 拒收并返回 `rejected:unknown_field`。
3. §27.2 = M4 熔断：`hops` 缺省与递增规则、`hops ≥ 8` 只记录不派活、**同轮扇出上限 3**（超出截断并告警）。
4. §27.3 = M7 卡片幂等：`ask.key` 语义（事项标识非随机 id）、同 key 未关不发第二张、`fyi` 无按钮且点击不产生 `resolve`。
5. §27.4 = `session_id` 一等字段（仅此一项）；**明确写「`cancel_observe` 不在本卡，落 §25.10，由 0063 负责」**，防止同一契约两处定义。
6. 每节给「字段表／映射规则／负例断言」三件套；负例断言必须是可构造、可断言的（拒收 1 条 `access` 事件；9 层链第 9 层派活次数为 0；同 key 连发后卡片行数不变）。
**验收（Gate T3）**：§27.1–§27.4 四节全部存在且各含字段表、规则、负例；卡内 `cancel_observe` 只以「不在本卡」形式出现；前置检查写成可执行步骤（读队列 state 与 tag 存在性）；无 volatile 计数写法。
**禁止**：不得把 M2／M8／M9／M5／M6 的条文塞进本卡；不得改 §25／§26。

### T4 · 0063 卡（§25.10 补 `cancel_observe`）
**文件**：`tasks/queue/wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md`
**写什么**
1. 卡头声明：前置＝0057 已冻结（`freeze_commit` 非空或冻结 tag 存在）；写域仅 §25.10 段内。
2. 三值表：`cancel_observe ∈ {running, not_running, unknown}`，逐值给判定条件——`not_running`＝取消触发时无活动进程、无在途 ack 义务，直接落 `CANCELLED` 不占窗口；`running`＝ack 窗口内收到 cancel_ack，或强杀后证明 `ActiveProcesses==0`，落 `CANCELLED`；`unknown`＝3s ack 窗口结束既无 ack、也无 `ActiveProcesses==0` 凭据。
3. 投影规则：`unknown` 时 run 保持最后事实状态、**不落 `CANCELLED`**，只向队列投影 `CANCELLED_PENDING`（非八态）。
4. 解除规则：下一轮对账或再次取消取得凭据 → 转 `running` 落 `CANCELLED`；连续 3 轮仍 `unknown` → 告警转人工，脚本不改队列。
5. 四条 Gate：a）ack 超时＋强杀后进程仍在 → `unknown` 且未落 `CANCELLED`；b）取消时无进程 → `not_running` 直落；c）连续 3 轮 → 告警且队列未被脚本改动；d）八态状态图 diff 为空。
6. 口径纪律：对外只能称「E-01 显式挂起」，不得称「已解 E-01」；并把 E-01 三段闭合判据（①真实观测到 `not_running` ∧ ②`running` 态取消在窗口内被受理 ∧ ③告警可触发）写进 Gate，其中 ①② 标 `TBD-RUNTIME`（Next 代码未开工，不得用 ③ 冒充闭合）。
**验收（Gate T4）**：三值表三行齐全且每行有判定条件；`unknown` 相关表述出现「不落 `CANCELLED`」与「`CANCELLED_PENDING`」；解除规则与 3 轮告警各一处；四条款 Gate 齐全；「显式挂起」口径句存在；写域明确「§25.10 原文除新增外 diff 为空」。
**禁止**：不得新增状态机状态；不得改 §25.10 已定的 3s／强杀／`ActiveProcesses==0` 口径；不得把 `cancel_observe` 挂到 step 或 plan 层。

### T5 · 交叉自检与报告定稿
**文件**：`docs/plans/next-autoloop-三单拆解-20261113.md`（补后三节）、`docs/reports/decompose-wo-ultimaagent-20261113-0064.md`
**写什么**
1. 「主文归属表」：每个契约/机制只允许一个主文位置（M3→§27.1、M4→§27.2、M7→§27.3、`session_id`→§27.4、`cancel_observe`→§25.10、writer→0061 卡），并给出「禁止在别处重复定义」一句话。
2. 「依赖图」：0064 →（0061 无前置；0062 前置 0057∧0059 冻结；0063 前置 0057 冻结）→ P2 spike 前置 0061＋0062。
3. 「Gate 覆盖映射表」：方案 §3／§4／§6 的每条 Gate → 落在哪张卡的哪个 T（不得有 Gate 无归属）。
4. 「INVEST 与 DoR 自检」：对三张卡逐单给 Independent／Small／Testable 三问结论与 DoR 五项结论（通过/不通过＋一句理由）。
5. 执行报告：改动文件清单（新建 4 个＋报告 1 个）、每个 Gate 的实际结果、越界声明（无则写"无"）。
**验收（Gate T5）**：主文归属表覆盖 6 项且无重复主文；依赖图四个节点齐；Gate 覆盖映射表无「未归属」行；三张卡各自 DoR 五项均有结论；报告含越界声明与文件清单。
**禁止**：不得自行判三张卡「已审卡通过」（审卡由 Owner 与独立审计做）。

---

## 4. 总验收（DoD）

- 4 个新建文件存在、非空、可读（卡 3 份＋拆解报告 1 份）；报告 1 份。
- 三张卡均可被 `python scripts\validate_work_order.py <卡路径>` 执行（PASS 或给出明确拒绝原因并记录，不得伪造 PASS）。
- 本单自证七项齐全：文件清单／Gate 逐项结果／越界声明／依赖声明／无编造数值／未碰禁写域／报告落盘路径。

---

## 5. 禁止项（全单）

1. 禁止任何「恰好 N 行／N 处／N 列／N 个」写死计数（DoR 会拒派）。
2. 禁止改基线、队列、tracker、既有四张卡与报告。
3. 禁止 commit／push／tag；禁止调 18766。
4. 禁止把三张卡自行标为「可开工」——状态只能写「待审卡」。
5. 禁止在卡里留「视情况」「按最佳实践」这类不可判定表述。

---

## 6. 给执行端的粘贴模板

```
T1 完成：依据清单 X 条、冲突清单 6 条（a–f）、本批不做 X 条
T2 完成：0061 卡（六段／每 T 四段／四条机检断言）
T3 完成：0062 卡（§27.1–§27.4，cancel_observe 仅在"不在本卡"处出现）
T4 完成：0063 卡（三值表／四条 Gate／显式挂起口径）
T5 完成：主文归属表 6 项／依赖图／Gate 覆盖映射无未归属／INVEST 与 DoR 结论
总验收：4 文件存在；validate_work_order.py 结果：<粘贴原文>
```
