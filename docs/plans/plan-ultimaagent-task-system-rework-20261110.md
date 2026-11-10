# 方案 · UltimaAgent 任务系统改造

> 版本 v1.0 ｜ 起草 2026-11-10 ｜ 起草时 HEAD `90a4a9d563cb9321211e8eebd24adcd83800d2b0`
> 依据：G-PLAN-001（先方案后工单）、G-ORCH-001（主脑只传需求、外脑出方案与工单）
> 产出方：本地主脑三阶段（DeepSeek），run = 本文件第 0 节所记目录
> 事实来源：需求 §2（实测）；本方案不含代码改动，只到方法层

## 0. 运行与取证

- 需求文件：`tasks/queue/request-ultimaagent-task-system-rework-20261110.md`（含 §7 需求方裁决）
- 主脑 run：`tasks/queue/runs/wo-ultimaagent-20261110-0036-task-system-rework-r3-20261110T155000629Z`
- 三阶段 verdict：decompose COMPLETED / work_order COMPLETED / schedule COMPLETED
- 主脑参数：`S-REVIEW.max_tokens` 8192（默认 4096 会截断 work_order 阶段，已实测）

## 1. 阶段一：需求理解与歧义关闭（decompose）

```text
REQUIREMENT UNDERSTANDING

Restating the requirement in my own words:

UltimaAgent has a home-grown task system (queue cards + dispatch + deterministic verification + LLM audit gate + freeze-to-tag) that has accumulated structural defects over 30+ orders. The owner wants a one-time consolidation of that system into a clean, long-running kernel — NOT new features — delivered in this order: (1) rebuild the task system itself, (2) use the rebuilt system to walk the "stuck points" from the beginning, (3) then proceed order-by-order. This requirement covers only step (1): the system rework. Its problem families are: state has no single authoritative source (two Markdown tables, hand-edited, mutually inconsistent, and the slot mechanism keys off a hand-maintained field); the freeze gate is structurally unreachable (demands a clean working tree while the repo has 560 pre-existing uncommitted entries); the audit gate rejects on fixed character limits (a constant-tuned band-aid that recurs as audited object sizes change); order cards can be internally contradictory with no pre-dispatch detection (producing false FAILs); the script family has 4 overlapping freeze scripts (two differing by one underscore) plus 19 one-off dispatch scripts and ~60 prompt snapshots piled in the formal directory; and `S-REVIEW.max_tokens=4096` truncates `work_order` stage output. Non-goals: no change to the seven-stage G-TASKFLOW-001 definition, no change to AUDIT_SLOT_LIMIT default of 2, no gate relaxed to "skip", no third-party framework, no touching UltimaManager, no cleaning the 560 uncommitted entries. Deliverables: a plan under `docs/plans/` per G-PLAN-001, then a three-section work-order card that passes both `validate_work_order.py` (DoR) and `verify-order.py`.

Ambiguities that would change scope or acceptance (I list them; most are already closed by §7/§8, and I record the closure so it is auditable):

1. Freeze gate definition — CLOSED by §7.1: scope to this order's write-domain whitelist (`git status --porcelain -- <write-domain>` must be empty), plus reverse check that actual changed paths ⊆ whitelist. Not a skip.
2. State authority — CLOSED by §7.2: new JSON is the sole authority; both Markdown tables become script-generated read-only views with a "generated, do not hand-edit" header; one-time migration imports disk-actual state (0030/0033/0035 at their real states, no re-audit, no re-judgment); rollback = restore timestamped snapshots + delete JSON; slot counting reads JSON.
3. Audit incompleteness criterion — CLOSED by §7.3: inject full content; split at object boundaries when over model input limit; require sha256 per object from the executor; `incomplete` only when actually-injected bytes < sha256-attested bytes, with an itemized missing list; `visible` must be an enumerable coverage list, not a bare negation.
4. Brain parameter — CLOSED by §7.4: `S-REVIEW.max_tokens` 4096 → 8192 as a floor; per-stage differentiation is left to the plan.
5. Verification self-reference (dependency loop A) — CLOSED by §7.5: T0 produces only a baseline snapshot (HEAD, sha256+bytes of the four scripts, sha256+lines of the two MD tables), changes no state source and no judgment logic; each T from T1 onward records both pre-change and post-change machine-check results, and any divergence between the two must be explicitly reported or that T is incomplete.
6. Self-check tooling loop (dependency loop B) — CLOSED by §7.6: until T3 completes, self-checks use the old gate; after T3's completion commit, the new gate; the boundary commit is recorded in the T0 snapshot.
7. Write-domain granularity — CLOSED by §7.7: write domain expressed as file path + symbol anchor + change intent; no signatures or line numbers required; no widening after executor backfill.
8. Schema/path of JSON authority, freeze-script consolidation count and surviving name, archive location for one-off scripts and prompt snapshots, and the self-consistency check item list — EXPLICITLY DELEGATED to the plan by §8; not to be asked back.
9. Facts not covered by §2 (specific function signatures, line numbers, existing test coverage) — may only be written as "取证方法 / 待执行端回填", never as conclusions.

Genuinely open: whether §7.1 or §7.2 is infeasible. This is the only permissible question-back, and only with a stated infeasibility reason plus an alternative — no unilateral reselection.

---

DECOMPOSITION

The plan is a plan-then-card deliverable, so I decompose into (a) plan-authoring work items and (b) the resulting work-order stage structure that the plan must define. I separate the two because the card's T-stages are an output of the plan, but their dependency skeleton and write-domain non-overlap can be verified now.

Phase P — Plan authoring (lands in `docs/plans/`, per G-PLAN-001)

- P1. Goals, scope freeze, non-goals restated from §3/§4 with the §7 rulings folded in as fixed inputs (not open items). Domain: `docs/plans/`.
- P2. Write-domain declaration (file path + symbol anchor + intent) covering: the JSON authority module; the migration script; the view generators for both MD tables; the slot-counting change in `dispatch-work-order.py`; the audit judgment change in `audit-work-order.py`; the freeze definition change in `freeze-work-order.py`; the pre-dispatch self-consistency check; the freeze-script consolidation/archival; the one-off script/prompt archival; `src/brain/slot_adapter.py` `S-REVIEW.max_tokens`. Domain: `docs/plans/`.
- P3. Acceptance criteria per §7 ruling (each problem family maps to a checkable acceptance), plus the dual-path pre/post evidence rule from §7.5. Domain: `docs/plans/`.
- P4. Risk register: rollback for §7.2 (snapshot+delete-JSON), the §7.5/§7.6 dependency-loop handling, migration idempotency, reverse-check false negatives. Domain: `docs/plans/`.
- P5. Emit the three-section card (files / what to write / acceptance / prohibitions), T0→Tn, each T with a closed acceptance checklist, per §5.2 and §7.5/§7.6. Domain: `docs/plans/` + the card file the plan designates.

Phase S — Structure the card must carry (plan-defined, verified here for dependency and non-overlap)

- S0 (T0): baseline snapshot only — no state-source change, no judgment-logic change. Records HEAD, four script sha256+bytes, two MD table sha256+lines, and the T3 boundary commit placeholder per §7.6. Write domain: snapshot artifact only.
- S1: JSON authority + migration (imports disk-actual state; 0030/0033/0035 placed directly, no re-audit). Depends on S0. Must precede S2 because the views and slot counting read the JSON.
- S2: MD view generators (both tables become derived) and slot-counting switch to JSON in `dispatch-work-order.py`. Depends on S1.
- S3: audit judgment replacement in `audit-work-order.py` (sha256-attested, boundary-split, enumerable coverage). Depends on S0 baseline; independent of S1/S2 by write domain. This T's completion commit is the §7.6 cutover boundary.
- S4: freeze-gate redefinition in `freeze-work-order.py` (write-domain-scoped porcelain + reverse subset check). Depends on S0; consumes the write-domain whitelist which is a plan artifact (P2), so depends on P2, not on S1–S3.
- S5: pre-dispatch card self-consistency detection. Depends on S0; touches `dispatch-work-order.py`, which S2 also touches — this is the one genuine overlap that must be serialized (S5 after S2) OR written into distinct symbol anchors and the plan must state which. I flag this as the overlap requiring explicit ordering.
- S6: freeze-script consolidation (4→N, one surviving name) and archival of 19 one-off dispatch scripts + ~60 prompt snapshots. Depends on S4 (only merge after the surviving freeze logic is the redefined one), else the merge would fold in the old definition.
- S7: brain parameter `S-REVIEW.max_tokens` 4096→8192 floor in `src/brain/slot_adapter.py`. Write domain `src/brain/` does not touch `scripts/`; independent, may run in parallel with S1–S6.
- S8: end-to-end dual-path reproducibility of both paths, with pre/post evidence per §7.5 and divergence reporting. Depends on all of S1–S7.

DEPENDENCY AND WRITE-DOMAIN VERIFICATION

- S0 → everything: correct, T0 is the baseline prerequisite, and it is constrained to produce no logic change, satisfying loop A.
- S1 → S2: correct, views and slot counting cannot read a JSON that does not yet exist.
- S3 independent of S1/S2: write domains differ (`audit-work-order.py` vs `dispatch-work-order.py` + view modules), so this is a valid parallel branch; only constraint is S3's completion commit defines loop B's cutover, which the plan must record into the S0 snapshot slot.
- S4 depends on P2 (write-domain whitelist) not on S1–S3: correct, but the whitelist must be frozen before S4, so P2's closure is a hard predecessor of S4.
- S2 and S5 both touch `dispatch-work-order.py`: this is the single real write-domain overlap. It cannot be parallelized as stated. Resolution offered to the plan: either (a) serialize S5 after S2, or (b) assign disjoint symbol anchors (slot-counting symbols vs self-consistency-check symbols) and require the plan to assert the anchors are disjoint with the executor backfilling exact anchors. I recommend (a) for simplicity; the plan decides.
- S6 depends on S4: correct and necessary — merging freeze scripts before the gate redefinition lands would ship the old unreachable definition under a consolidated name.
- S7 parallel with S1–S6: correct, `src/brain/` disjoint from `scripts/` and `tasks/`.
- S8 last: correct, it validates the whole.

Non-overlap summary: with the S2/S5 serialization (or anchor-split) applied, every other pair of stages has disjoint file-path write domains. No stage writes outside its declared files; archival in S6 is a move-only operation on `tasks/queue/` and must be stated as such so it does not collide with S1/S2's view generation under `tasks/queue/`.

Caveats I must state honestly rather than paper over: exact symbol anchors, existing test coverage, and the concrete `audit-work-order.py`/`freeze-work-order.py` internals are NOT covered by §2, so per §6 they can only be surfaced as "取证方法 / 待执行端回填". I have therefore not asserted them as facts. The plan I would hand to the executor must fill these via a取证 step at T0, and per §7.7 the write domain may be stated by path + symbol anchor + intent but must not widen after backfill. Within those constraints nothing in §7.1 or §7.2 appears infeasible: §7.1 is a scope-narrowing of an existing porcelain check plus a subset assertion, both mechanically expressible; §7.2 is a new JSON file plus generators plus a one-time importer with a snapshot rollback, all local and dependency-free — so I have no infeasibility claim to raise.

VERDICT: COMPLETED
```

## 2. 阶段二：工单结构与 DoR 自检（work_order）

```text
## G-ORCH 阶段 3 工作：工单（Work Order）自检与就绪判据

### 前置说明（角色与能力边界）

本文件由独立 G-ORCH 阶段 3 代理产出。该代理**无仓库访问、无 shell、无文件系统**，仅依据需求文本进行逻辑自检。因此本文件**不产出**：

- 具体实现代码、函数签名、行号；
- 对未在需求 §2 中给出实测事实的对象的结论；
- 任何声称「已验证仓库现状」的表述。

本文件产出：工单的可判定结构、六项定义就绪（DoR）门禁的逐项自检结果、阻塞项清单。

---

### A. 输入完整性核对

| 需求要素 | 状态 | 备注 |
|---|---|---|
| 目标与顺序 | 已给出 | §0、§1 |
| 事实基线 | 已给出并声明为实测 | §2（可引用） |
| 范围（8 问题族） | 已给出 | §3 |
| 非目标（6 条） | 已给出 | §4 |
| 交付期望 | 已给出 | §5 |
| 事实层声明 | 已给出 | §6（不覆盖项须写成取证方法） |
| 需求方裁决（冻结门/状态源/审计判据/主脑参数/依赖环 A/B/写域粒度） | 已全部定案 | §7（不得回问） |
| 方案自决项 | 已列出 | §8 |
| 回问例外 | 仅 §7.1/§7.2 不可行时 | §8 末句 |

结论：**输入完整，不存在需回问的未决项。** §7.1 与 §7.2 在本代理的判断下**不构成实现不可行**：§7.1 的「`git status --porcelain -- <写域路径>` 为空 + 改动路径 ⊆ 写域」在 git 语义上可判定；§7.2 的「JSON 权威源 + 两张 md 派生」是常规单向派生，无循环依赖。故不触发 §8 的例外条款。

---

### B. 工单结构草图（仅结构，不含实现）

为判定六项 DoR 门禁，先给出工单的**阶段骨架**（T0→Tn）。骨架只声明每 T 的**对象、写域锚、验收口径、禁止项**，不声明改法。

- **T0 — 基线快照（只读，不改任何判定逻辑）**
  - 对象：`git rev-parse HEAD`；`verify-order.py` / `validate_work_order.py` / `audit-work-order.py` / `freeze-work-order.py` 各自 sha256 与字节数；两张 md 表的 sha256 与行数；T3 完成 commit 的分界占位。
  - 写域：新增快照产物文件（路径由方案定）。
  - 禁止：改任何状态源、改任何判定逻辑、改门禁。
- **T1 — 状态单一权威源 + 双表派生**（对应 §3.1、§3.7、§7.2）
  - 写域锚：新建 JSON 权威源路径（方案定）；`tasks/queue/index.md` 与 `global-queue-index.md` 的生成器；`verify-order.py` / `dispatch-work-order.py` 读取路径。
  - 迁移：0030/0033/0035 按 §7.2 实际状态直接落库，不重审不改判；迁移前两表带时间戳快照，回滚=还原快照+删 JSON。
  - 禁止：人工双写、把 md 表继续当权威、借迁移重审既有单。
- **T2 — 名额机制去脆性**（§3.2）
  - 写域锚：`dispatch-work-order.py` 中 `AUDIT_SLOT_LIMIT` 相关名额判定的**数据来源**（仍读 JSON，不改默认值 2）。
  - 禁止：改限额默认值、依赖人工维护字段。
- **T3 — 冻结门新定义**（§3.3、§7.1）
  - 写域锚：`freeze-work-order.py` 中「工作树全净」判据替换为「写域内 `git status --porcelain -- <写域>` 为空」+「实际改动路径 ⊆ 写域白名单」反向防漏。
  - 禁止：放宽为跳过、把判定范围之外的条目纳入冻结判定。
  - 完成 commit 即依赖环 B 的分界（§7.6），需写入 T0 快照。
- **T4 — 审计判定去常量依赖**（§3.4、§7.3）
  - 写域锚：`audit-work-order.py` 中 `CARD_INJECTION_LIMIT` / `EVIDENCE_INJECTION_LIMIT` 相关判定链（L423–424 附近语义）；`incomplete`/`visible` 判定改为基于 sha256 字节对账与覆盖清单。
  - 禁止：保留「超固定字符数即否决」、把 `visible` 写成 `not incomplete` 的裸否定。
- **T5 — 卡面自洽性检测**（§3.5）
  - 写域锚：`validate_work_order.py` 新增结构性矛盾检测项（检测项清单由方案定）。
  - 禁止：把检测结果写成结论性改写卡面。
- **T6 — 脚本群收敛**（§3.6、§8）
  - 写域锚：4 个冻结脚本归并决定（保留名由方案定）；19 个 `dispatch-wo-*-now.py` 与约 60 个 `dispatch-*-prompt.txt` 归档位置（方案定）。
  - 禁止：删除前不留回滚路径、保留仅差下划线的两个名字共存。
- **T7 — 主脑参数**（§2.7、§7.4）
  - 写域锚：`src/brain/slot_adapter.py` 的 `S-REVIEW.max_tokens` 4096 → 8192（下限）。
  - 禁止：低于 8192、按阶段区分时下探到 8192 以下。

（T 的分组可按方案再拆分，但**任何拆分不得减少上述对象覆盖**。）

---

### C. 六项定义就绪（DoR）门禁逐项自检

> 以下六项为本代理采用的 DoR 门禁。每项均给出**可判定判据**与**本工单当前自检结论**。

**G1 — 目标单一且可验收**
- 判据：存在一句话目标，且对应至少一条可机检验收项。
- 自检：目标 =「把任务系统收敛为可长期运行的干净内核」；每条 T 均挂至少一条验收项（写域内 status 为空、JSON 落库可读、sha256 对账、8192 生效等）。→ **PASS**。

**G2 — 范围冻结且写域可判定**
- 判据：写域以「文件路径 + 符号锚 + 改动意图」表述，且不含行号/改法（§7.7）；写域外对象不出现。
- 自检：B 节各 T 的写域锚均落在 §2 已实测存在的对象上（脚本文件、两张 md、`slot_adapter.py` 的 `S-REVIEW.max_tokens`），均为「路径+符号+意图」粒度，未给行号与改法。→ **PASS**（具体锚名待执行端回填，回填后不得扩大——已在 B 节声明）。

**G3 — 事实与推断分离**
- 判据：凡 §2 未覆盖的现状，只以「取证方法」出现并标注「待执行端回填」；不出现精确代码或臆断结论。
- 自检：本文件所有对象均引自 §2 或 §7；未对函数签名、行号、既有测试覆盖下结论；B 节锚点为「语义锚点」而非实现细节。→ **PASS**。

**G4 — 非目标不被违反**
- 判据：对 §4 六条非目标逐条给出「本工单不触碰」的显式声明。
- 自检：不改七环节定义 / 不改 `AUDIT_SLOT_LIMIT=2` / 不放宽为跳过 / 不引第三方编排 / 不动 UltimaManager 定位 / 不清理 560 条既有改动——均已在 B 节「禁止」栏或 A 节显式列为不触碰。→ **PASS**。

**G5 — 依赖环消解已声明**
- 判据：依赖环 A（工具自指）与依赖环 B（自检手段）均有显式处置，且处置可事后核验。
- 自检：依赖环 A = T0 只产基线快照、T1 之后每 T 双档留证、不一致须显式上报（§7.5）；依赖环 B = T3 完成 commit 为分界写入 T0 快照（§7.6）。两项均在 B 节 T0/T3 落位且可核验。→ **PASS**。

**G6 — 不可行例外已被检查且未触发**
- 判据：若 §7.1 或 §7.2 实现不可行，须写明理由与替代且不改选（§8 末句）；否则视为未触发。
- 自检：A 节已判定 §7.1（git 语义可判定）、§7.2（单向派生无环）均可行，未触发例外，未自行改选。→ **PASS**。

六项 DoR 门禁：**6/6 PASS**。

---

### D. 待执行端回填清单（不视为阻塞，属设计内留白）

以下为 §6/§7.7 允许的留白，回填后**写域不得再扩大**：

1. JSON 权威源的具体路径与 schema（§8 自决）。
2. 4 个冻结脚本归并为几个、保留名（§8 自决）。
3. 一次性脚本与提示词快照的归档目录（§8 自决）。
4. 卡面自洽性检测的具体检测项清单（§8 自决）。
5. 各 T 写域锚点的函数名/常量名精确名称（§7.7 允许，待回填）。
6. T3 完成 commit 的哈希（T0 快照产出后回填）。

---

### E. 阻塞项

**无阻塞项。** 未发现需回问 §7.1/§7.2 不可行的情形；六项 DoR 门禁全部 PASS。

---

VERDICT: COMPLETED
```

## 3. 阶段三：排期（schedule）

| order | work_order | depends_on | wip_slot | window | gate |
|---|---|---|---|---|---|
| 1 | WO-T0 基线快照（只读：HEAD、四脚本 sha256/字节数、两表 sha256/行数；写入 T0 快照文件，含 T3 分界声明） | — | 1 | S1 | G0：快照字段齐全、零状态源/判定逻辑改动、可复核 |
| 2 | WO-T1 JSON 权威源 + 双表派生视图 + 名额改读 JSON（含一次性迁移与时间戳快照回滚路径） | WO-T0 | 2 | S1 | G1：0030/0033/0035 落库值与裁决一致；两表标注勿手改；名额判定无 markdown 文本依赖 |
| 3 | WO-T2 冻结门重定义（写域白名单内干净 + 改动路径 ⊆ 写域反向防漏，不放宽为跳过） | WO-T0 | 3 | S1 | G2：越界即拒、写域外 560 条不参与判定；改造前后两档留证 |
| 4 | WO-T3 审计判定去常量依赖（全文注入 / 对象边界拆分 + sha256 / 可枚举覆盖清单） | WO-T1 | 1 | S2 | G3：incomplete 仅在注入字节 < sha256 字节时成立；visible 可枚举；两档留证 |
| 5 | WO-T4 卡面自洽性检测（派发前结构性矛盾检出，检测项清单随方案） | WO-T3 | 2 | S2 | G4：互斥 Gate 类矛盾可拦；两档留证 |
| 6 | WO-T5 脚本群收敛（4 冻结脚本归一、19 个一次性脚本与 ~60 提示词归档、命名不可混淆） | WO-T2, WO-T3 | 3 | S2 | G5：仅保留单名冻结入口；归档后目录无遗留；两档留证 |
| 7 | WO-T6 主脑参数（S-REVIEW.max_tokens ≥ 8192，按阶段区分与否由方案定） | WO-T0 | 1 | S3 | G6：work_order 阶段长输出不截断；两档留证 |
| 8 | WO-T7 端到端双路径复现 + 方案落档 docs/plans/（G-PLAN-001） | WO-T4, WO-T5, WO-T6 | 2 | S3 | G7：DoR 通过 validate_work_order.py、机检通过 verify-order.py；双路径可复现；两档不一致已上报 |

VERDICT: COMPLETED

## 4. 编号统一说明（本方案对主脑产物的唯一一处裁定）

主脑三阶段各自编号不一致：decompose 用 S0–S8（9 段）、work_order 用 T0–T7（8 段）、schedule 用 WO-T0~WO-T7（8 段）。
为遵守 Owner「不要多套规则」的要求，**工单卡统一采用 8 段 T0–T7**，次序取 schedule（依赖最正确）：

| 统一编号 | 对应 decompose | 对应 schedule | 内容 |
|---|---|---|---|
| T0 | S0 | WO-T0 | 基线快照（只读） |
| T1 | S1+S2 | WO-T1 | JSON 权威源 + 迁移 + 双表派生成器 + 名额改读 JSON |
| T2 | S4 | WO-T2 | 冻结门重定义（写域内干净 + 反向防漏） |
| T3 | S3 | WO-T3 | 审计判定去常量依赖 |
| T4 | S5 | WO-T4 | 卡面自洽性检测 |
| T5 | S6 | WO-T5 | 脚本群收敛与归档 |
| T6 | S7 | WO-T6 | 主脑参数 ≥8192 |
| T7 | S8 | WO-T7 | 端到端双路径复现 + 本方案落档确认 |

## 5. 需求原文（作为方案输入留档）

```markdown
# 需求：任务系统改造（UltimaAgent 队列/派发/校验/审计/冻结核自身）

- 项目：UltimaAgent
- 发起：Owner（2026-11-10）
- 通道：A（豆包调度，DeepSeek 出方案与工单，Codex 执行）
- 依据：G-TASKFLOW-001、G-ORCH-001、G-PLAN-001、G-DISPATCH-001

## 0. Owner 原话（原样）

> 「先要把任务系统改造做完，然后从卡点开始从头开始捋，捋顺了之后一个一个开始用新的任务系统去做。」

目标顺序即：**任务系统自身改造 → 用改造后的系统把卡点从头捋顺 → 再逐单推进**。

## 1. 本次要解决什么

UltimaAgent 现在有一套自建的任务系统（队列卡 + 派发 + 确定性校验 + LLM 审计门 + 冻结打 tag），已经跑过 30+ 单。但它是在长期打补丁中长出来的，现在出现四类结构性问题，导致：**冻结门实际不可达、状态没有单一权威源、审计能卡住的点与真正质量无关、脚本群职责重叠且混有历史遗留**。

本次不要新增功能，要**把这套系统收敛成一个可长期运行的干净内核**：状态有唯一权威源、门禁的定义与真实仓库状态相容、每个脚本职责单一、遗留件清理干净、端到端双路径可复现。

## 2. 实测现状（事实层，均由具备仓库访问权的一侧实测，带证据路径）

> 以下为事实，不是推断。方案里凡涉及这些对象的结论必须以此为基线；凡需求未给出现状的项，只能写成「取证方法」，不得写成结论。

### 2.1 脚本群（`H:\UltimaAI\UltimaAgent\scripts\`）

| 脚本 | 体积 | 职责（实测） |
|---|---|---|
| `verify-order.py` | 46,765 B | 确定性校验器，G-ORCH-001 口径的复核主体 |
| `dispatch-work-order.py` | 38,360 B | 派发；含 `AUDIT_SLOT_LIMIT`（默认 2）名额机制（L192）、名额清点与降级（L616–671） |
| `freeze-work-order.py` | 33,069 B | 冻结；重跑确定性检查、要求 `audit_passed is True`（L381）、拒绝 truncated 材料（L584）、要求 clean working tree |
| `audit-work-order.py` | 22,985 B | LLM 审计门；两轮同身份模型；只输出 JSON，**不回写任何登记 state** |
| `validate_work_order.py` | 16,738 B | 工单卡校验（DoR） |
| `gorch_contract.py` | 13,522 B | 契约与阶段门解析（`_STAGE_GATE` / `_STAGE_ITEM` / `stage_gates`） |
| `freeze-approved-v03.py` | 13,039 B | **历史遗留** |
| `freeze-approved-v01.py` | 10,021 B | **历史遗留** |
| `freeze_work_order.py` | 6,558 B | **历史遗留（与 `freeze-work-order.py` 仅下划线之差，极易误用）** |
| `run-gorch.py` | 6,588 B | 编排入口之一 |
| `orchestrate-order.py` | 5,163 B | 主脑三阶段入口（decompose / work_order / schedule） |
| `finalize-reviewed-text-order.py` | 6,646 B | 文本类工单收口 |
| `sync-reviewed-stage1-gates.py` | 4,046 B | 阶段门同步 |
| `read-dispatch-progress.py` | 2,916 B | 进度读取 |
| `stop-finished-owned-dispatch.py` | 3,751 B | 停止已完成派发 |
| `stop-idle-owned-dispatch.py` | 4,074 B | 停止空闲派发 |
| `order_naming.py` | 1,752 B | 工单命名（G-WO-NAME-001） |
| `verify-goal-repair.py` | 3,590 B | 目标修复校验 |

即：**4 个冻结脚本并存**，其中两个仅差一个下划线；冻结逻辑分散在 33 KB 主脚本 + 3 个历史脚本里。

### 2.2 状态存放（这是最硬的问题）

- 工单的 `state` 存在**两份 Markdown 表**里：项目 `tasks/queue/index.md`（18,569 B）与全局 `H:\UltimaAI\_shared\queue\global-queue-index.md`（28,211 行）。
- 两份表**互不一致**：`wo-ultimaagent-20261110-0033` 在全局表有独立行，在项目表**完全没有行**；`0032` 在项目表仍写 `pending`，实际已有合并动作。
- **没有任何脚本回写这些 state**：`audit-work-order.py` 只输出 JSON；`dispatch-work-order.py` 只在派发时写一次；审计通过/未通过都要**人工改 Markdown**。
- 名额机制正是建立在这个人工维护的字段上：`blocking = 全局表中 state 仍为 audit 的工单`。**状态一旦没手改，名额就永远占着**——本轮 0030/0033 就是因此卡住 0035。
- 全表 state 取值实测为：`frozen` 112 / `blocked` 17 / `cancelled` 16 / `audit` 6（已清零）/ `pending` 4 / `closed` 1。

### 2.3 冻结门与真实仓库状态不相容

- `freeze-work-order.py` 要求**工作树无已跟踪文件的修改**，否则拒绝。
- 而本仓当前 `git status --porcelain` 有 **560 条**既有未提交条目（历史执行痕迹、日志、配置、`.superpowers/sdd/*/progress.md` 等），且**不是本次改造产生**。
- 后果：任何单即使 `audit_passed=true` 也**永远冻不了**。0033、0035 都已审计通过，都卡在这里。
- 这不是「仓库脏」的业务问题，而是**门禁定义与工程现实不相容**：一个长期运行的项目仓库不可能保持全净。

### 2.4 审计窗口 vs 被审对象体积（已修一次，但只修了常量）

- `audit-work-order.py` L60 `CARD_INJECTION_LIMIT = 16000`、L61 `EVIDENCE_INJECTION_LIMIT = 40000`（本轮由 12,000 改上来）。
- 判定链 L423–424：`visible = not incomplete`、`passed = pass1 and pass2 and visible`。
- 0033 曾因此**四轮全 PASS 却判 false**：它要审的三个脚本自身 12,773 / 22,701 / 32,535 字符，全超当时 12,000 窗口 → `incomplete_inputs` 永不为空 → `visible` 恒 False。
- 修常量只解决了这一个实例。**这类问题会随被审对象体积变化复发**，需要一个不依赖人工调常量的判定方式。

### 2.5 工单卡自身的缺陷会直接制造假 FAIL

- 0035 的 Gate T7 第 1 条要求「恰 6 条 `=>` 的 status 差分」，第 5 条要求「6 个文件完成提交」——**两条互斥**（提交后路径即从 status 消失）。执行端连续一轮被判 FAIL，第二轮用等价证据替代仍被判「已偏离卡面」。
- 最终靠**在 detached worktree 重建提交前那一刻**才拿到原样证据。
- 即：卡面自相矛盾时，系统没有任何检测，只能靠执行端或审计员事后发现。

### 2.6 一次性脚本未归档

- `tasks/queue/` 根目录有 **19 个 `dispatch-wo-*-now.py`** 一次性派发脚本，以及约 60 个 `dispatch-*-prompt.txt` 提示词快照，全部堆在正式目录里。
- 另有 `tasks/queue/runs/_probe-orchestrate` 空目录、`tasks/queue/_backup`。

### 2.7 主脑参数

- `src/brain/slot_adapter.py` 的 `S-REVIEW.max_tokens` 默认 **4096**；`work_order` 阶段天然需要长输出（0035 的工单阶段实测 3,840 字符已接近上限，0033 类多门工单必然被截）。

## 3. 范围（要改造什么，按问题族列）

1. **状态单一权威源**：审计/校验/冻结的结论必须由脚本写入，Markdown 表只做只读视图或由脚本生成；不得再有「人工改表才能释放名额」。
2. **名额机制去脆性**：名额判定不得依赖人工维护的字段。
3. **冻结门的定义**：把「工作树必须全净」改成与长期运行仓库相容的定义（例如只校验被冻 commit 与被审内容一致、或限定到本单写域），且**不得放宽为跳过检查**。
4. **审计判定去常量依赖**：`incomplete` 与 `visible` 的判定不能是「超固定字符数即否决」。
5. **卡面自洽性检测**：派发前能查出「两条 Gate 要求互斥」这类结构性矛盾。
6. **脚本群收敛**：4 个冻结脚本与 19 个一次性脚本归并/归档，职责单一，命名不可混淆。
7. **双表一致性**：项目表与全局表由同一权威源派生，不允许人工双写。
8. **主脑参数**：`work_order` 阶段的输出上限按实际需要设定。

## 4. 不做（Non-goals）

- 不改 G-TASKFLOW-001 的七环节定义（登记→计划评审→执行→复核→有界修复→验收→冻结）。
- 不改 `AUDIT_SLOT_LIMIT` 的默认值 2（本次只改判据来源，不改限额）。
- 不放宽任何门禁为「跳过」；不允许 `check=False` 式降级。
- 不引入第三方编排框架，不装新外部服务。
- 不动 UltimaManager 作为可选监督工具的定位。
- 不清理这 560 条既有未提交改动本身（那是另一件事，本次只让门禁与之相容）。

## 5. 交付期望

1. 先出**方案**（落 `docs/plans/`，按 G-PLAN-001 随工单留档）：目标、范围冻结、写域、验收口径、风险。
2. 方案定稿后出**工单卡**（三段式：文件 / 写什么 / 验收 / 禁止；T0→Tn；每 T 封闭验收清单）。
3. 工单必须能被 `validate_work_order.py` 通过 DoR，且能通过 `verify-order.py` 机检。

## 6. 事实层声明（给方案编制方）

- 你**无法读取仓库、无法执行命令**。第 2 节给的是实测事实基线，可直接引用；第 3 节给的是问题族，不是解法。
- 凡第 2 节未覆盖的现状（具体函数签名、行号细节、既有测试覆盖），你只能写成「取证方法」并标注「待执行端回填」，**不得写成结论或直接给出精确代码**。
- 若某处事实与你的推断冲突，以第 2 节为准。

## 7. 需求方裁决（2026-11-10，已定，直接作为方案输入，不要再问）

上一版此项空缺导致主脑判 BLOCKED 并拒绝虚构工单。以下裁决全部生效，**不得再作为「未决项」回问**。

### 7.1 冻结门新定义（原 §3.3 目标选定）

**选定：只要求本单写域内干净。**

- 判据：以工单写域白名单为范围，校验 `git status --porcelain -- <写域路径>` 为空，非空即拒绝。
- 写域外的未提交条目**完全不参与冻结判定**，含现有 560 条。
- **反向防漏（必须同时成立）**：冻结时须证明「本单实际改动路径 ⊆ 写域白名单」，越界即拒绝——不得靠白名单漏写蒙混。
- **不得放宽为跳过**：只缩小判定范围，不减少判定强度。

### 7.2 状态权威源（原 §3.1 / §3.7 目标选定）

**选定：新建 JSON 权威源，两张 Markdown 表改为脚本生成的只读视图。**

- 唯一权威是一份 JSON（路径与 schema 由方案定）。
- 项目 `tasks/queue/index.md` 与全局 `H:\UltimaAI\_shared\queue\global-queue-index.md` 改为派生输出，表头标注「由脚本生成，勿手改」。
- 迁移一次性导入现状，取值以**磁盘实际**为准：`0030=blocked`、`0033=audit_passed_true 且 state=blocked`、`0035=audit_passed_true 且 state=blocked`；全局表分布 `frozen 112 / blocked 17 / cancelled 16 / pending 4 / closed 1 / audit 0`。
- **回滚**：迁移前把两张 md 表原样另存带时间戳快照，回滚 = 还原快照 + 删除 JSON。
- 名额判定改为读 JSON，不再读 markdown 文本。
- 0030 / 0033 / 0035 迁移期按上表实际状态直接落库，**不重审、不改判**。

### 7.3 审计判定替代判据（原 §3.4）

不再以固定字符数否决。替代判据：

- 注入被审对象**完整内容**；
- 单对象超过模型输入上限时，按对象边界拆分注入，并要求执行端为每个对象提供 sha256；
- `incomplete` 仅在「实际注入字节 < 该对象 sha256 对应字节」时成立，且须附具体缺项清单；
- `visible` 不再等于 `not incomplete` 的裸否定，须给出可枚举的覆盖清单。

### 7.4 主脑参数基线（原 §2.7）

- `S-REVIEW.max_tokens` 4096 → **8192**，为下限。
- 实测依据：4096 时 `work_order` 阶段 `out_tokens` 触顶 4096、正文 7,300 字符在句中截断；8192 时同阶段正常收尾。
- 是否按阶段区分上限由方案定，但不得低于 8192。

### 7.5 验收工具自指（依赖环 A）

- **T0 只产基线快照**，不改任何状态源、不改任何判定逻辑。
- 快照字段至少含：`git rev-parse HEAD`；`verify-order.py`、`validate_work_order.py`、`audit-work-order.py`、`freeze-work-order.py` 各自的 sha256 与字节数；两张 md 表的 sha256 与行数。
- T1 之后每个 T 的机检**分两档**：改造前版本、改造后版本，两档都留证；两档判定不一致必须显式上报，未上报即视为该 T 未完成。

### 7.6 自检手段依赖环（依赖环 B）

- 改造期（T3 未完成前）自检沿用旧门；T3 完成后切新门。
- 分界以 T3 的完成 commit 为界，写入 T0 快照。

### 7.7 写域粒度授权（解除 §6 与 G2 的冲突）

原 §6 的「不得给出精确代码 / 行号」**不适用于写域声明**。明确允许并只要求：

- 写域按「**文件路径 + 符号锚（函数名 / 类名 / 常量名）+ 改动意图**」表述；
- 不要求给具体改法、函数签名或行号；
- 具体实现由执行端回填，回填后**写域不得再扩大**。

## 8. 交由方案自行决定，不要回问

- JSON 权威源的具体 schema 与路径。
- 4 个冻结脚本归并为几个、保留哪个名字。
- 19 个一次性 `dispatch-wo-*-now.py` 与约 60 个 `dispatch-*-prompt.txt` 的归档位置。
- 卡面自洽性检测的具体检测项清单。

**唯一仍需回问的情形**：若方案认为 §7.1 或 §7.2 的选定目标在实现上不可行，须写明具体不可行理由与替代方案，**不得自行改选**。

```
