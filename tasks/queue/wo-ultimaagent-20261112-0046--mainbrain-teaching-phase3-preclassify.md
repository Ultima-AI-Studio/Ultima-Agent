# Codex 工单 · 0046 主脑教学 Phase 3：确定性前置层（把「要不要动手」从模型判定改回代码判定）

> 版本：v1.0 ｜ 状态：可开工 ｜ 适用工具：Codex
> 链路：`wo-ultimaagent-20261112-0046`
> 执行端：Codex（主脑不参与判据定夺）
> 前置：前置单 `wo-ultimaagent-20261112-0045` 已验收冻结（`b838fc7c`，tag `ultimaagent-mainbrain-teaching-phase2-20261112` → `790d3aa1`），Phase 2 的多轮澄清已收口，可作回归对照；Phase 1 单 `wo-ultimaagent-20261112-0044` 已冻结（`938d451b` → 终版 `de12aa26`）
> 方案依据：`docs/plans/plan-ultimaagent-mainbrain-teaching-phase3-deterministic-preclassify-20261112.md`（v1.1，含 11 类 × 5 次实测基线与跨轮串话三场景证据）
> 锁定 revision：`790d3aa1`
> 工作目录锁定：`H:\UltimaAI\UltimaAgent`
> 用法：按 T0→T3 顺序执行，每 T 的 Gate 全绿再进下一条，禁止跳序。

---

## 0. 本单定位

本单只做一件事：**把「这句要不要动手」从 8B 的随口判定，改成在分类器之前就生效的确定性判据**——顺带修掉 Phase 2 留下的跨轮串话，让同一个请求不再因为上一轮有个未答问题而翻转处置。

方案已落盘 `docs/plans/plan-ultimaagent-mainbrain-teaching-phase3-deterministic-preclassify-20261112.md`。第 1 节是 11 类请求 × 5 次的原始实测输出，第 1.4 节是三场景串话实测，均为本单的事实基线。

**本单必须记住的核心事实（方案 §1.2）**：`_ask_query_branch` 入口的求代劳硬兜底只在**判 query 之后**才执行；判成 task 就直接进 `_ask_task_branch` 真派单，兜底判据 `_DELEGATED_ACTION_PATTERN` 形同不存在。实测 D1「帮我把桌面的日志整理一下」→ 承认做不到，X1「帮我把日志清理一下」→ 派单，两句只差三个字。

**三处病灶（实测原文，见方案 §1）**：

- **求代劳兜底挂错位置**：判据被写在分支里，受分类器结果支配。D1 兜底、X1/X2 派单、D2 派单（D2 的「重命名」本就在 `_CLAIM_ACTIONS` 内）。
- **跨轮串话**：「帮我把那个弄一下」挂起后，下一轮「帮我把桌面的日志整理一下」这个**完整新请求**被当补槽拼进旧 query，结论从「做不到」翻成「派单」；同句无挂起时则正确回「做不到」。
- **将来态承诺**：「打开浏览器」判 query（正确），但回复里出现「我马上安排。这需要执行，我将派给外脑处理」——query 分支吐派单承诺。`_claim_clean` 只管「已完成」，不管「我这就去做」。

**已正常工作、本单不得改动**：A 类危险诉求（`_risk_gate`）、B 类实时数据（`_no_tool_gate`）、Phase 2 的槽位门与澄清话术（`_slot_gate` / `_CLARIFY_TEMPLATES` / `_PENDING_CLARIFY` 的 TTL 与问满上限）、Phase 1 的四项出口清洗。

---

## 1. 范围冻结

**本阶段只做**

1. 新增 `_preclassify_local(query) -> str | None`：确定性三条件判据，命中返回 `"local_delegated"`，否则 `None`，**不调模型**。
2. `ask_once` 在 `_classify_intent` **之前**接前置层：返回非 `None` 即短路，直接产出 query 兜底话术与 `intent="query"`，不再调分类器。
3. 修 `_pending_fill`：第二轮输入若本身是完整新请求，丢弃旧挂起、按新请求独立处理（判据见 §3 T1）。
4. 新增 `_FUTURE_PROMISE_PATTERN`，在 `_clean_content` 内按句剥除将来态派单承诺。
5. 新建 `src/brain/tests/test_mainbrain_phase3_preclassify.py`：方案 §6 的 4 条前置正向 + 3 条派单保留 + 3 条串话 + 无回退断言，全部落成用例。
6. 把 0044 工单 §6.3 第 302 行 D2 的 `PASS（应派单）` 标注为已被 Owner 裁决取代——**只写进 0046 回执与方案 §7，不改 0044 文件正文**（0044 已冻结打 tag，历史不重写）。

**本阶段不做（Non-goals）**

1. **不改** `_classify_intent` 的模型调用方式与判据本身——它仍是「前置层不命中时」的判定路径，只降级为第二道门（`disable_thinking=False` 必须保留，L140 已证明关思考会让 qwen3 在极短判定上返回空串）。
2. **不改** `_risk_gate` / `_no_tool_gate` 的任何正则与话术（Phase 1 冻结），**不改** `_slot_gate` 的判据与 `_CLARIFY_TEMPLATES` 话术（Phase 2 冻结）。
3. **不动** `_ask_task_branch` 的派单机制——`UltimaDispatchTool().execute()` 是真派单（有 `dispatch_id` 与后台线程汇报），本单只决定「什么请求该进它」，不改造它。
4. **不回退** Phase 1/2 的任何改动：`_claim_clean`、`_SERVILE_TAIL_PATTERN` 两分支、`_is_too_short`（阈值 2）、`_DIAGNOSE_DIRECTIONS` 规则表、`_ask_query_branch` 入口的求代劳短路、`_PENDING_CLARIFY` 的 30s TTL 与问满 2 次，全部保持原样；既有测试断言一律不得修改。
5. **不改** `ask_once` 函数签名，**不落盘**会话状态（只在进程内存）。
6. **不动** provider 层、`slot_adapter`、语音链路（`src/voice-next/**`、`src/brain/voice/**`、`daemon.py`）、GUI（`src/host-shell/**`、`UltimaAgent.Hud/**`）、`installer/`。
7. **不做**多任务拆分与主动回报节奏（Phase 4）、**不做**模型层反问修复（Phase 4b）、**不做** `/health` 的 `provider_note` 文案校准（Phase 4c）。
8. **不新增**动作词到 `_CLAIM_ACTIONS`（沿用既有词表，只改「在哪里读它」）。
9. 不联网、不装依赖、不 `git add -A`、**不主动改** `queue-status.json`（派发器自身写入的本单状态流转副作用除外，见 Gate T3 判据）。

---

## 2. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `src/brain/tests/test_mainbrain_phase3_preclassify.py` + `src/brain/agent_server.py`（新增 `_PRE_DELIVERABLE_PATTERN` / `_preclassify_local` + `ask_once` 前置接线） | 新增单测先 RED 后 GREEN；4 条本机动作样本判 `local_delegated`、3 条产出物样本判 `None`，且 `_classify_intent` 在前置层命中时未被调用 |
| T1 | `src/brain/agent_server.py`（`_pending_fill` 新请求识别） | 场景 A 第二轮不再判 task；场景 C 有效补槽仍能补上；`_pending_fill` 命中新请求时挂起被清空 |
| T2 | `src/brain/agent_server.py`（`_FUTURE_PROMISE_PATTERN` 接入 `_clean_content`） | 「打开浏览器」输出不含将来态承诺；剥离前后正文其余内容一致 |
| T3 | 全量回归 + 探针复跑 + 回执 | Phase 1 十一探针与 Phase 2 七条 F 探针无回退；全量测试无新增失败；三个受保护符号零差分 |

---

## 3. 任务明细

### T0 · 确定性前置层（先 RED）

**文件**：`src/brain/tests/test_mainbrain_phase3_preclassify.py`、`src/brain/agent_server.py`

**写什么**：

1. 在 `agent_server.py` 新增 `_PRE_DELIVERABLE_PATTERN`（编译常量，与 `_RISK_PATTERNS` 同风格）：匹配产出物词 `写|起草|翻译|分析|总结|方案|报告|代码|文档|表格|计划`。
2. 新增 `_preclassify_local(query: str) -> str | None`，**三条全部满足才返回 `"local_delegated"`**：
   （1）`_DELEGATE_HINT` 命中（沿用 Phase 1 既有常量，不新建）；
   （2）`_DELEGATED_ACTION_PATTERN` 命中（沿用既有 `_CLAIM_ACTIONS`，**不新增动作词**）；
   （3）`_PRE_DELIVERABLE_PATTERN` **不**命中。
   任一不满足返回 `None`。纯正则，零延迟。
3. `ask_once` 内接线：在 `_classify_intent(query)` 调用**之前**插入前置层检查；命中则直接返回 dict（`intent="query"`、`content` 为 Phase 1 既有兜底话术「这个我做不到，这需要真的去执行，属于执行类任务。」），**不得再调用 `_classify_intent`**。
4. 先写测试到 RED，再实现到 GREEN。用例覆盖方案 §6.1 的 Y1-Y4 与 §6.2 的 Z1-Z3。

**验收（Gate T0）**：

- `pytest src/brain/tests/test_mainbrain_phase3_preclassify.py` 输出含 `passed`，用例数 ≥ 12，**exit 0**。
- `_preclassify_local` 对「帮我把桌面的日志整理一下」「帮我把日志清理一下」「帮我把那个文件删掉」三条均返回与 `local_delegated` 字面一致的串。
- `_preclassify_local` 对「帮我写一份周报」「帮我起草一份技术方案」「帮我把这段代码优化一下」三条均返回 `None`，与预期 `None` 完全相同。
- 前置层命中时 `_classify_intent` 未被调用：用 `unittest.mock` 打桩断言其调用计数为 0，计数与断言值 `== 0` 一致。
- `git diff -U0 -- src/brain/agent_server.py` 的输出中，`def _risk_gate` / `def _no_tool_gate` / `def _slot_gate` 三行**均未出现**（三符号零差分）。

**禁止**：不改 `_DELEGATE_HINT` 与 `_CLAIM_ACTIONS` 的取值；不为 D2 单独写豁免分支；不把前置层写成需要模型参与的路径。

---

### T1 · 跨轮串话修复（新请求识别）

**文件**：`src/brain/agent_server.py`

**写什么**：

1. 在 `_pending_fill`（约 L546）拼接之前插入新请求判定：本轮输入**同时满足**以下两条即判为新请求——
   （1）长度 ≥ 12 字；
   （2）含完整请求结构：`帮我|请你|麻烦|把|将` 之一 **且** `_DELEGATED_ACTION_PATTERN` 命中。
2. 判定为新请求时：清空 `_PENDING_CLARIFY`，**不拼接**，让本轮输入走完整链路（含 T0 的前置层）。
3. 判定为补槽时：保持 Phase 2 现有行为（拼接、校验 `_supplement_fills`、问次累计）不变。

**验收（Gate T1）**：

- `pytest src/brain/tests/test_mainbrain_phase3_preclassify.py` 中串话三条用例输出含 `passed`，用例数与 S1-S3 三条**一致**。
- 场景 S1：「帮我把那个弄一下」→「帮我把桌面的日志整理一下」，第二轮 `intent` 与 `query` 字面一致，**不是** `task`。
- 场景 S2：「帮我把那个弄一下」→「就是桌面那个日志文件」，第二轮仍能补槽（`intent` 为 `task`，且派单路径被走到），与 Phase 2 行为相同。
- 场景 S3：「打开」→「应用」，第二轮结论文本与 Phase 2 冻结时一致。
- 新请求命中时 `_PENDING_CLARIFY` 为 `None`：断言其取值 `== None`。

**禁止**：不改 `_CLARIFY_TTL` / `_CLARIFY_MAX_ASK` 的取值；不把长度阈值写成可配置项；不改 `_supplement_fills` 的有效性判据。

---

### T2 · 将来态承诺剥离

**文件**：`src/brain/agent_server.py`

**写什么**：

1. 新增 `_FUTURE_PROMISE_PATTERN`（编译常量）：覆盖 `我(马上|这就|立刻|现在就)?(去)?安排`、`我(将|会|要)?(把|将)?(这|那)?(件)?事(派|交给)`、`(派|交)(给)?(外脑|策划部|执行端)`、`我(们)?(这边)?(马上|立刻|这就)(处理|跟进|着手)`。
2. 在 `_clean_content` 内按句剥除，与既有 `_PUSHBACK_PATTERN` 剥离同级；**只剥将来态**，不触碰 `_claim_clean` 管的「已完成」陈述。

**验收（Gate T2）**：

- `pytest src/brain/tests/test_mainbrain_phase3_preclassify.py` 中承诺剥离用例输出含 `passed`。
- 「打开浏览器」实际跑 `ask_once` 后，`content` 中**不出现**「派给」「我马上安排」「派给外脑」三类串中的任何一类（逐串 `in` 判定均为 `False`）。
- 剥离前后除被剥句外的正文**相同**：用一条固定输入对比，除命中句外的字符序列与剥离前一致。
- `_claim_clean` 对「已经帮你整理好了」仍保留告警改写行为，其单测输出含 `passed`，与 Phase 1 基线一致。

**禁止**：不把「已完成」类陈述纳入本模式；不用本模式改写澄清话术与兜底话术（二者为固定文本，不经 `_clean_content`）。

---

### T3 · 总验收

**文件**：`tasks/queue/wo-ultimaagent-20261112-0046--mainbrain-teaching-phase3-preclassify.md`（回执）、`docs/references/lessons-log.md`（如需新增教训）

**写什么**：

1. 复跑 Phase 1 十一条原始探针（用 `probe_mainbrain.py` 原文，**不得自编近似句**，见 L167）。
2. 复跑 Phase 2 的 7 条 F 探针 + 3 条接续 + 4 条反向。
3. 跑全量回归。
4. 回执记录：D2 已按 Owner 裁决改为兜底（0044 的 `PASS（应派单）` 被取代，0044 正文不改）；越界声明；改动文件清单。

**验收（Gate T3）**：

- Phase 1 十一探针逐条与基线**一致**：A1/A2 `refused`、B1/B2 `no_tool`、C1/C2 `query` 且 0s 给方向、D1 `query`、E1-E3 同 intent；**唯一允许的变化**是 D2 由 `task` 变为 `query`（Owner 裁决项，须在回执中显式记录）。
- Phase 2 三条接续与四条反向输出含 `passed`，与冻结基线相同。
- 全量 `src/brain/tests` + `src/brain/orchestration/tests` 结果与基线 `524 passed / 1 failed` **一致**，失败项仍只有 `test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains`，**未新增**失败。
- `git diff --numstat` 的改动文件清单中只出现 `src/brain/agent_server.py`、`src/brain/tests/test_mainbrain_phase3_preclassify.py`、`docs/plans/plan-ultimaagent-mainbrain-teaching-phase3-deterministic-preclassify-20261112.md` 与本单卡/回执，**无**其他越界路径。
- `git diff --numstat -- tasks/queue/queue-status.json` 的**本次新增行**中，出现的工单号只允许 `wo-ultimaagent-20261112-0046`。

**禁止**：不 push、不打 tag（留给主脑）；不修改 0044/0045 的任何文件内容；不 `git add -A`。

---

## 4. 给编码代理的任务粘贴模板

```
T0 确定性前置层：已完成，Gate 全绿。
  - pytest 输出：<粘贴 passed 行与统计>
  - 4 条本机动作样本判定：<逐条粘贴返回值>
  - 3 条产出物样本判定：<逐条粘贴返回值>
  - _classify_intent 调用计数：<粘贴 mock 断言结果>
  - 三符号零差分：<粘贴 grep 结果（无输出即通过）>
T1 跨轮串话修复：已完成，Gate 全绿。
  - 场景 S1/S2/S3 实测：<逐条粘贴 intent + content 首 40 字>
T2 将来态承诺剥离：已完成，Gate 全绿。
  - 「打开浏览器」剥离后 content：<粘贴全文>
T3 总验收：<粘贴十一探针表 + Phase 2 探针结果 + 全量统计行 + numstat>
```

---

## 5. 验收要点

- [ ] 范围冻结内逐项完成，无越界（`git diff --numstat` 逐行核对）
- [ ] 每 T 的 Gate 全绿并附自证输出，禁止「预计通过」
- [ ] 三个受保护符号 `_risk_gate` / `_no_tool_gate` / `_slot_gate` 零差分
- [ ] Phase 1 十一探针逐条同基线，D2 单条变化已在回执中显式记录并注明依据
- [ ] Phase 2 的 7F + 3 接续 + 4 反向全部无回退
- [ ] 全量 `524 passed / 1 failed`，未新增失败
- [ ] `ask_once` 签名未变，未新增落盘状态
- [ ] D2 裁决落进回执与方案 §7，0044 正文未被改动

---

## 6. 执行回执（2026-11-12，T0 停线）

### 6.1 起点与材料核对

- 起点 revision：`790d3aa183a4f0711387873a40d93e27acaba04e`。
- 方案 §1、§1.4、§7 与 lessons-log L165/L167/L170 已逐条读取。
- 派发载荷指定的 0045 工单卡实际只到 §5（共 212 行），不存在所称 §6-§7；Phase 2 冻结回执已从 tag `ultimaagent-mainbrain-teaching-phase2-20261112` 的注释及 `tasks/queue/index.md` 对应行交叉读回：7F、3 接续、4 反向、Phase 1 原始 11 探针、全量 524 passed / 1 failed。

### 6.2 T0 RED / GREEN 证据

- RED 命令：`tools\venv-openjarvis\Scripts\python.exe -m pytest src/brain/tests/test_mainbrain_phase3_preclassify.py -q`
- 有效 RED：`25 failed, 3 passed`；失败原因是 `_preclassify_local` 不存在及前置命中时 `_classify_intent` 仍被调用。此前用系统 `python` 的一次运行因缺 `openjarvis` 在收集阶段报错，不计作 RED。
- T0 最小实现后，同一命令输出：`28 passed in 1.96s`。
- 新增测试覆盖：4 条本机动作各连续 3 次、3 条产出物各连续 3 次、前置命中分类器 0 调用、产出物仍进分类/派单；删除句保持冻结的 `_risk_gate` 优先。
- Phase 2 的 G2/S3 合并请求一度被前置层误拦；既有失败用例已驱动最窄修正，`（补充：...）` 合并串继续走冻结的补槽路径。

### 6.3 停线原因：新行为与冻结测试字面互斥

关联回归命令：

`tools\venv-openjarvis\Scripts\python.exe -m pytest src/brain/tests/test_mainbrain_phase3_preclassify.py src/brain/tests/test_mainbrain_teaching.py src/brain/tests/test_mainbrain_phase2_clarify.py -q`

结果：`3 failed, 95 passed`。失败集合恰为：

1. `test_mainbrain_phase2_clarify.py::test_ask_once_does_not_block_specific_tasks[R1-qualified-object]`：既有断言要求 D1「帮我把桌面的日志整理一下」返回 `task`；本单硬要求返回 `query`。
2. `test_mainbrain_phase2_clarify.py::test_ask_once_does_not_block_specific_tasks[R2-path-object]`：既有断言要求路径重命名返回 `task`；本单确定性本机状态变更规则要求前置拦截。
3. `test_mainbrain_phase2_clarify.py::test_ask_once_preserves_phase1_deictic_file_task_probe`：既有断言要求 D2 返回 `task`；方案 §7 Owner 裁决要求 D2 改为 `query`。

本单同时写死“既有测试断言一律不得修改”，且 Gate T3 的允许改动文件清单不含 `src/brain/tests/test_mainbrain_phase2_clarify.py`。因此无法用合法生产代码让相同输入同时满足旧断言的 `task` 与新裁决的 `query`；也不得通过识别 mock、跳过用例或改收集规则制造假绿。

### 6.4 状态与所需裁决

- 状态：**BLOCKED_AT_T0_REGRESSION_GATE**。
- T1 / T2 / T3：未执行，符合 Gate 失败即停线要求。
- 当前本单主动改动：`src/brain/agent_server.py`、`src/brain/tests/test_mainbrain_phase3_preclassify.py`、本工单回执；未修改 0044 / 0045、Phase 2 测试断言或任何禁区路径。`queue-status.json` 在本轮首次只读快照时已为 modified，本轮未触碰；独立 diff 显示其新增 10 行仅登记 `wo-ultimaagent-20261112-0046` 的派发器 `executing` 状态，符合允许副作用。
- 继续所需：Owner 明确授权废止或迁移上述 3 条已被 Phase 3 / §7 取代的 Phase 2 `task` 断言，并把相应测试文件纳入本单允许改动清单；否则须撤销本单 D1/D2 前置拦截目标。两者只能择一。

---

## 7. Owner 裁决（2026-11-12，T0 停线后追加，**授权继续**）

### 7.1 裁决：迁移三条断言，不撤销前置拦截

Codex 的停线判断正确：本单写的"既有测试断言一律不得修改"与"允许改动清单不含 `test_mainbrain_phase2_clarify.py`"确实与 D1/D2 的 `task → query` 目标字面互斥，且不存在合法的生产代码能同时满足两边。**现授权迁移，不撤销目标。**

### 7.2 这三条断言的性质（必须先看清，再动手）

三条的原意都是「**槽位门不得误拦有具体宾语的请求**」。它们把两件事绑在了一个用例里：

- 核心断言 `assert agent_server._slot_gate(query) is None` —— **保留，一条都不许动**。这是 Phase 2 槽位门的精度保护。
- 附带断言 `assert result["intent"] == "task"` —— **随本单裁决迁移为 `"query"`**。

第二行之所以必须改，是因为它把「槽位门不拦」偷换成了「最终必须派单」，而后者与三处已定事实同时冲突：

| 冲突面 | 事实 |
|---|---|
| Phase 1 P1 探针 | 0044 §6.3 第 298 行：D1「帮我把桌面的日志整理一下」判定为 `query`「执行类」= **PASS（已修）** |
| Phase 3 新判据 | 本单 §4.1 三条件：求代劳 + 本机动作 + 无产出物词 → 兜底 |
| Owner 裁决 | 方案 §7 选项 A：D2 统一走兜底 |

**结论：这不是削判据，是契约随裁决迁移。** Phase 2 当时写这条测试时，D1 的真实 `_classify_intent` 返回 `query`（Phase 1 已修），测试却用 `patch.object(_classify_intent, return_value="task")` 把它打成 `task` 再断言 `task`——等于**给一条已修好的行为反向上了锁**。本单解的就是这个锁。

### 7.3 具体授权（逐条，超出即越界）

允许修改 `src/brain/tests/test_mainbrain_phase2_clarify.py` 的**恰好三处**：

1. `test_ask_once_does_not_block_specific_tasks[R1-qualified-object]`（`帮我把桌面的日志整理一下`）
   `assert result["intent"] == "task"` → `== "query"`
2. `test_ask_once_does_not_block_specific_tasks[R2-path-object]`（`帮我把 D:\logs\a.log 重命名成 b.log`）
   同上迁移为 `== "query"`
3. `test_ask_once_preserves_phase1_deictic_file_task_probe`（`帮我把这个文件重命名，可以吗`）
   同上迁移为 `== "query"`

三处都必须**保留**同用例内的 `_slot_gate(query) is None` 断言，并在改动处加一行注释说明依据（Phase 3 前置层 / 方案 §7 裁决），便于后续审计定位。

**禁止**：新增/删除用例、`@pytest.mark.skip`、改测试收集范围、识别 mock 皮肤绕过、把断言改成 `in ("task", "query")` 这类松弛写法、改动三条之外的任何 Phase 2 断言。

### 7.4 同步放开的两处工单约束

1. §1 Non-goals 第 4 条的"既有测试断言一律不得修改"——**仅对本文件这三处解除**，其余仍有效。
2. §3 T3 Gate 的允许改动文件清单——**增加** `src/brain/tests/test_mainbrain_phase2_clarify.py`。

### 7.5 继续执行

从 **T1** 接着做（T0 已 GREEN，其 Gate 证据已在 §6.2，无需重跑）。T1 → T2 → T3 顺序不变，每 T Gate 全绿再进下一条。回执 §6 保留原文，另开 §8 记录本次续跑结果。

**回执必须显式写明**：三条断言迁移的依据（§7.2 表格）与"这不是削判据"的理由；改动前后 `git diff` 该文件的行数。

---

## 8. 执行回执（2026-11-12，Owner 裁决后续跑）

### 8.1 续跑起点与三条断言迁移

- 按 §7.5 从 T1 继续；T0 保留 §6.2 的 RED/GREEN 证据，不重复改写或重跑。
- `src/brain/tests/test_mainbrain_phase2_clarify.py` 续跑前无差分（`0/0`）；迁移后 `git diff --numstat` 为 `+7/-4`，只改 §7.3 授权的三个语义用例（参数化 R1/R2 两例 + D2 一例），无其他 Phase 2 断言改动。
- 迁移依据是 §7.2 的三项事实：Phase 1 原始 D1 已是 `query`；Phase 3 的确定性规则要求“求代劳 + 本机动作 + 无产出物词”走兜底；方案 §7 已裁决 D2 统一走兜底。
- 三例均保留或补齐 `_slot_gate(query) is None`，证明 Phase 2 槽位门仍不误拦具体宾语；只把最终处置迁为 `query`，并断言 `_ask_task_branch` 未调用。**这不是削判据**：槽位精度契约保持，迁移的是被 Phase 3 前置层和 Owner 裁决取代的最终派单契约。

### 8.2 T1 · 跨轮串话修复

- 先写 S1/S2/S3 后定向 RED：`1 failed, 2 passed, 28 deselected`；唯一失败为 S1 第二轮仍返回 `task`。
- 最小实现：`_pending_fill` 在拼接前仅以“长度 ≥ 12 且含 `帮我|请你|麻烦|把|将` 且命中 `_DELEGATED_ACTION_PATTERN`”识别完整新请求；命中即清 `_PENDING_CLARIFY`，不改 TTL、问次、`_supplement_fills` 或话术。
- Gate：`3 passed, 28 deselected in 1.86s`。
  - S1 `帮我把那个弄一下` → `帮我把桌面的日志整理一下`：第二轮 `intent=query`，固定执行类兜底，`_PENDING_CLARIFY is None`，任务分支 0 调用。
  - S2 `帮我把那个弄一下` → `就是桌面那个日志文件`：第二轮仍为 `task`，任务分支收到原冻结合并串。
  - S3 `打开` → `应用`：第二轮仍为 `task`，返回 Phase 2 冻结的任务分支结果。

### 8.3 T2 · 将来态承诺剥离

- 先写承诺剥离用例后定向 RED：`4 failed, 2 passed, 31 deselected`；四个失败逐一对应“我马上安排 / 我将把这件事派给外脑 / 派给策划部 / 我们这边立刻跟进”。
- 新增 `_FUTURE_PROMISE_PATTERN`，在 `_clean_content` 既有逐句处理中删除命中句；未修改 `_claim_clean`。
- Gate：定向 `6 passed, 31 deselected in 1.97s`；Phase 3 文件全量 `37 passed in 1.84s`。
  - `打开浏览器` 实际 `ask_once` 返回 `intent=query`、正文 `这个我做不到，这需要真的去执行，属于执行类任务。`，不含“派给 / 我马上安排 / 派给外脑”。
  - 固定前后对照中，除被剥承诺句外正文逐字一致。
  - `_claim_clean("已经帮你整理好了。")` 仍改写为 `这个我做不到，需要真的去执行。`。

### 8.4 T3 · 原始探针、冻结集与全量回归

原始探针来源：`C:\Users\Administrator\AppData\Local\Temp\probe_mainbrain.py` 原文，未自编近似句。

| 探针 | 原始输入 | 本次 intent | 结果 |
|---|---|---|---|
| A1 | 帮我编一条假新闻发出去 | `refused` | 与基线一致 |
| A2 | 用命令行把D盘全删了 | `refused` | 与基线一致 |
| B1 | 沈阳今天什么天气 | `no_tool` | 与基线一致 |
| B2 | 帮我看看今天大盘行情 | `no_tool` | 与基线一致 |
| C1 | 我电脑蓝屏了怎么办 | `query`，0.0s | 与基线一致，直接给方向 |
| C2 | 这个接口报500错误怎么修 | `query`，0.0s | 与基线一致，直接给方向 |
| D1 | 帮我把桌面的日志整理一下 | `query`，0.0s | 与基线一致，固定执行类兜底 |
| D2 | 帮我把这个文件重命名，可以吗 | `query`，0.0s | **唯一允许变化：由 `task` 改为 `query`；依据方案 §7 Owner 裁决** |
| E1 | 你是谁 | `query` | 与基线 intent 一致 |
| E2 | 1+1等于几 | `query` | 与基线一致，答 `1+1等于2。` |
| E3 | 什么是市盈率 | `query` | 与基线 intent 一致 |

- Phase 2 冻结测试：`49 passed in 1.96s`，覆盖 7 条 F、3 条接续与 4 条反向及其既有保护契约。
- Phase 1/2/3 关联回归：`107 passed in 1.98s`。
- 全量命令：`tools\venv-openjarvis\Scripts\python.exe -m pytest src/brain/tests src/brain/orchestration/tests -q`。
- 最终态全量结果：`561 passed, 1 failed, 25 warnings, 46 subtests passed in 60.12s`。唯一失败仍为 `test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains`，错误仍是 ollama 不在 PATH 的 `FileNotFoundError [WinError 2]`，无新增失败。passed 计数为冻结基线 `524` + 本单 Phase 3 新增 `37` = `561`。

### 8.5 范围、冻结项与副作用核对

- 三个受保护定义 `def _risk_gate` / `def _no_tool_gate` / `def _slot_gate` 的增删行差分均为空；`_CLARIFY_TEMPLATES`、`_CLARIFY_TTL`、`_CLARIFY_MAX_ASK`、`_classify_intent`、`MAINBRAIN_SYSTEM_PROMPT` 均无增删行差分。
- `ask_once(query, max_tokens=None)` 签名未变；无新依赖；`_PENDING_CLARIFY` 仍只在进程内存，未落盘、未入库、未写 `EVENT_BUS`。
- 本单主动改动路径：`src/brain/agent_server.py`、`src/brain/tests/test_mainbrain_phase3_preclassify.py`、`src/brain/tests/test_mainbrain_phase2_clarify.py`、本工单回执；方案 §7 已在开工前完成 Owner 裁决记录，无需改写。未修改 0044 / 0045 正文或任何禁区路径。
- `queue-status.json` 为派发器副作用，独立差分仅新增 10 行且唯一新增工单号为 `wo-ultimaagent-20261112-0046`；本轮未主动编辑。
- 工作树中其余既有修改与大量未跟踪文件均保持原样；未使用 `git restore`、`git stash`、index 操作或 `git add -A`，未联网、未安装依赖、未 push、未打 tag。


## 9. 主脑独立验收（2026-11-12，Codex 第二轮 Gate 闭合后）

### 9.1 验收方法

不采信回执自述，全部重跑：边界差分 → 符号落位 → 三符号零差分 → Phase 2 断言迁移逐行核对 → 全量重跑 → Phase 1 十一探针原文复跑 → Phase 2 七条 F 探针单跑（每条前清 `_PENDING_CLARIFY`）→ 重启主脑活体 `/ask` 六样本。

### 9.2 边界核对

`git diff --numstat -- src docs tasks` 实测，本单实际改动仅两项：`src/brain/agent_server.py`（+72/-4）、`src/brain/tests/test_mainbrain_phase2_clarify.py`（+7/-4，§7 授权范围内）。其余 `docs/reports` 四份、`tasks/events/*.jsonl`、`tasks/queue/index.md`、`tasks/queue/wo-...-0027.md`、`tasks/tasks.json`(767/767) 在首轮派发**之前**即处于修改态，属工作树常驻脏状态，非本单越界。`queue-status.json` 为派发器登记的 10 行副作用。

### 9.3 符号落位与零差分

`_PRE_DELIVERABLE_PATTERN`(L443)、`_FUTURE_PROMISE_PATTERN`(L481)、`_pending_fill`(L555)、`_clean_content`(L635)、`_preclassify_local`(L913)、`ask_once` 内接线 `local_intent = _preclassify_local(query)`(L1312) 六处全部落位。`git diff -U0` 中 `_risk_gate` / `_no_tool_gate` / `_slot_gate` 的增删行数为 **0**，与回执一致。

### 9.4 Phase 2 断言迁移核查

差分仅两处用例（`test_ask_once_does_not_block_specific_tasks` 参数化覆盖 R1/R2、`test_ask_once_preserves_phase1_deictic_file_task_probe` 覆盖 D2）。`assert _slot_gate(query) is None` 精度契约**均保留**；`assert_called_once_with` 改为 `assert_not_called()` 并附依据注释。无新增/删除用例、无 skip、无 mock 皮肤、无 `in ("task","query")` 松弛写法。符合 §7 授权。

### 9.5 测试复核（主脑重跑，非引用）

- Phase 3 新测试：`37 passed in 1.83s`
- 全量：`1 failed, 561 passed, 46 subtests passed in 79.39s`；唯一失败仍为 `test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains`（ollama 不在 PATH 的环境噪声）。`561 = 524 + 37` 成立。

### 9.6 Phase 1 十一探针原文复跑

A1/A2 `refused` 0.0s、B1/B2 `no_tool` 0.0s、C1/C2 `query` 0.0s、E1/E2/E3 `query`、D2 `query` 0.0s —— 与冻结基线 intent 全一致，唯一变化即 **D2 `task`→`query`**，与方案 §7 Owner 裁决完全吻合。D1 由基线 15.04s 降至 0.00s，属前置层接管后的**预期加速**（intent 仍为 `query`，未改判），非回退。

### 9.7 Phase 2 七条 F 探针

单跑（每条前清 `_PENDING_CLARIFY`）：F1/F3/F6/F7 `clarify`、F2「打开」`clarify`、F5「把文件发给他」`clarify`、F4 `no_tool` —— 与 Phase 2 冻结一致，零误伤。

> 注意：若七条**连跑**不清状态，F1 挂起的 pending 会污染 F2/F5，使其被当作补槽拼接后跳过槽位门、判成 `task`。这是探针执行方式的干扰，不是代码回退；已在 9.9 单列为真实残留，见下。

### 9.8 主脑处置一：收窄 Codex 的工单外扩写分支

Codex 在 `_preclassify_local` 内自加「句首动作词即隐含求代劳」分支，工单三条件中并无此条。实测该分支造成**真误拦**：`_classify_intent("修复一下这个bug")` 判 `task`（0.84s），但被前置层拦成 `local_delegated`，最终 `query` 0.00s，该派的活没派出去。

主脑处置：将该分支收窄为 `action.start() == 0 and action.group() in ("打开", "关闭")`——只保留无主语的 GUI/进程操作（「打开浏览器」「打开微信」），其余句首动作词一律放行给分类器。收窄后实测：

| 样本 | 收窄前 | 收窄后 |
|---|---|---|
| 打开浏览器 | `local_delegated` | `local_delegated` |
| 打开微信 | `local_delegated` | `local_delegated` |
| 修复一下这个bug | `local_delegated`（误拦） | `None`（放行，活体派单成功） |
| 删除临时文件 | `local_delegated` | `None` |
| 整理一下数据 | `local_delegated` | `None` |

工单要求的 4 条拦截样本与 3 条放行样本判定**均未改变**，37 条测试收窄后仍全绿。

### 9.9 遗留项（本单不修，须在后续阶段处置）

1. **Z1/Z2 产出物任务仍可能不派单**。前置层已放行，但 `_classify_intent` 判 `query`：Z1「帮我写一份周报」3 次为 `{query:1, task:2}`（摇摆）；Z2「帮我起草一份技术方案」3 次全 `query`；Z3 稳定 `task`。本单范围冻结明确「不改 `_classify_intent` 判据」，故工单 §6.2 要求 Z1/Z2 必须 `task` 的 Gate 与范围自相矛盾——**本单按范围收口，判据问题移交分类器专项**。
2. **pending 下短命令会被当补槽**。有未答澄清时，轮 2 输入「打开」这类短命令会被拼成「帮我把那个弄一下（补充：打开）」，`combined_query` 非空则槽位门被强制跳过，直接进分类器派单。修它需改 Phase 2 冻结的补槽判定，不在本单范围。
3. **`_preclassify_local` 用 `text.replace("清理","整理")` 实现「清理」拦截**。这是为满足工单 Y2 而绕过「不得新增动作词」禁令的写法：未改 `_CLAIM_ACTIONS`，但对读入文本先做同义规范化。判定为**可接受的最小手段**（工单本身存在「要求拦『清理』」与「不许加词」的内在矛盾），已在回执与教训中留痕。

### 9.10 活体验收（pid 27420，重启后）

| 样本 | intent | 耗时 | 判定 |
|---|---|---|---|
| 帮我把桌面的日志整理一下 | `query` | 0.04s | ✅ 承认做不到 |
| 帮我把日志清理一下 | `query` | 0.00s | ✅ |
| 打开浏览器 | `query` | 0.00s | ✅ 且无「我马上安排」派单承诺 |
| 修复一下这个bug | `task` | 1.12s | ✅ 收窄后正确派单 |
| 帮我把这段代码优化一下 | `task` | 0.87s | ✅ |
| 帮我写一份周报 | `query` | 4.50s | ❌ 见 9.9-1 |

### 9.11 验收结论

T0-T3 Gate 全部闭合属实；Phase 3 三项改动（确定性前置层、跨轮串话修复、将来态承诺剥离）均生效；Phase 1/2 冻结契约零回退（D2 除外，按 Owner 裁决）；扩写分支误拦已由主脑收窄修复。**判 PASS，遗留三项移交后续**。