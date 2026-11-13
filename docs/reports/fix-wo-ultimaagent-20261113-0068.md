# wo-ultimaagent-20261113-0068 · 骨架冲突与主链半堵修复报告

## §1 概览

- 工单：`wo-ultimaagent-20261113-0068`。
- 执行顺序：T1→T6；每完成一 T 立即更新本报告。
- 0067 结论回读：**有条件通过（修复后再冻结）**；0057 实测已堵 8／半堵 3／未堵 0，且原 T3.4、T6.1、T6.2、T6.3 为确定性 FAIL。
- 七项映射：F-1＝S-002；F-2＝S-003/U-01；F-3＝G-03/U-02；F-4＝C-17/U-04；F-5＝G-05/U-03；F-6＝S-001 与 0057 T3.4/T6.3；F-7＝0057 T6.2。0067 把 F-6/F-7 合并归 U-07，本卡将其拆为两项；无实质口径差异。
- T1 只建立 T0 快照与八段报告，不写修复内容。

## §2 T0 快照

### 2.1 文件基线

| 文件 | T0 SHA256 | 行数 | 字节数 |
|---|---|---:|---:|
| `docs/specs/next-感知交互参数基线-20261113.md` | `3FE9B80F25E0B75E42191C8C6343AF98EA4B51BA529457F97A48C9770A894C52` | 1792 | 141820 |
| `docs/tracker/北极星架构树.html` | `DC32D2B15405A8690CD34AC61A825506B381F3402D3773F67F9F66071ECDACA3` | 476 | 53787 |

T0 时基线已有 0057 的既存工作树差异（§15.2.1 一行与 §25 全章）；架构树无目标文件工作树差异。本单以当前字节为 T0，不覆盖既存改动。

### 2.2 七处基线锚点原文

1. §14.3，T0 L510：`4. **队列唯一状态源不变**：tasks/queue/queue-status.json 仍只由状态机写（现有"直接写 state 仅 state_machine.py 一处"铁律继续有效）；其他组件问任务态只问 Console，不直连 Manager。`
2. §19.3，T0 L1127：`| Python 引擎（queue_engine） | 只读写八态与迁移结果 | 引擎不决定优先级、不改系统档位 |`
3. §15.2.1，T0 L571–585：标题为`迁移表（fail-closed，未列出的迁移一律拒）`；现有数据行依次为 `QUEUED`、`EXECUTING`、`EXECUTING→CANCELLED`、`SELF_CHECK`、`AUDIT`、`COMPLETED`、`FAILED`、`BLOCKED`、`CANCELLED`；唯一进 `BLOCKED` 的运行失败路径为 T0 L581 `FAILED→BLOCKED` 且 `retryCount ≥ 2`。
4. §25.3，T0 L1580–1598：`context.compose 是唯一装配入口`；现有七区为 `system/policy/memory.hot/habit/session.recent/tool.schema/user.turn`，只引用 §16.4 的动态总预算，超预算事件为 `context_over_budget`，外发隐私引用 §23.6。
5. §25.9，T0 L1731–1737：唯一公式为 `operation_id = sha256(turn_id|step_id|tool_id|args_hash)`；末句为`具体静态保留期记 TBD-G05-RETENTION`。
6. §25.11，T0 L1753–1763：三类副作用为 `reversible/irreversible/external_billing`；末句规定补偿失败直接落 `BLOCKED` 并记 `compensate_failed`，但无 compensator 签名表或补偿 receipt 字段表。
7. 附录 A，T0 L1767–1792：标题与两列表头存在；末条为 T0 L1792 的“设定收口审计（结构与双源修复）”，尚无 0057 行。

逐字原文与完整行段保存在 `docs/reports/evidence/fix-0068/t0-manifest.txt`；全文副本用于 T6 diff-only 回放。

### 2.3 架构树两个「任务编排」节点

- T0 L201（Core）：`<span class="desc">多步任务规划与执行顺序控制</span>`。
- T0 L283（Console）：`<span class="desc">派发 / 优先级 / 依赖；九点位 4–9 是八态投影</span>`。

### 2.4 T0 证据

- `docs/reports/evidence/fix-0068/t0-baseline.txt`：SHA256 与基线 T0 一致，1792 行。
- `docs/reports/evidence/fix-0068/t0-architecture-tree.txt`：SHA256 与架构树 T0 一致，476 行。
- `docs/reports/evidence/fix-0068/t0-manifest.txt`：七处锚点与两节点逐字清单。
- Gate T1：八段标题顺序齐；两文件哈希/行数齐；七处锚点与两节点原文/行号齐；T0 副本可读。结论：`PASS`。

## §3 F-1／F-2（T2）

### 3.1 RED（修复前）

- `rg -n --fixed-strings '只由状态机写' <baseline>`：命中 1（T0 L510）。
- `rg -n 'Python 引擎.*不写.*queue-status\.json' <baseline>`：命中 0；T0 L1127 仍是“只读写八态与迁移结果”。
- `rg -n '补偿失败.*先落.*FAILED.*retryCount' <baseline>`：命中 0；T0 L1763 仍是补偿失败直接落 `BLOCKED`。
- 方案甲的 `SELF_CHECK/AUDIT→BLOCKED` 行：命中 0。

### 3.2 F-1 写口唯一化

1. §14.3：
   - 改前 T0 L510：`4. **队列唯一状态源不变**：tasks/queue/queue-status.json 仍只由状态机写（现有"直接写 state 仅 state_machine.py 一处"铁律继续有效）；其他组件问任务态只问 Console，不直连 Manager。`
   - 改后现行 L510：`4. **队列单一语义源与唯一写口**：队列状态语义由 state_machine 唯一定义；queue-status.json 落盘唯一由 queue-writer 执行（唯一写者）；其他组件只读投影，不直写该文件，也不直连 Manager。`
   - 结论：`state_machine` 只定语义，`queue-writer` 是唯一落盘写者；未引入第二写者。
2. §19.3：
   - 改前 T0 L1127：`| Python 引擎（queue_engine） | 只读写八态与迁移结果 | 引擎不决定优先级、不改系统档位 |`
   - 改后现行 L1127：`| Python 引擎（queue_engine） | 只读八态投影与迁移结果；不写 queue-status.json | 引擎不决定优先级、不改系统档位 |`
   - 结论：Console 边界明确为只读投影与迁移结果，不写队列文件，与 §15.2.1 消费者映射“不改 `queue-status.json` 业务语义”一致。

### 3.3 F-2 补偿迁移合法化

- 选择：**方案乙**。
- 理由：复用 §15.2.1 已有且唯一的 `FAILED→BLOCKED` 路径与 §21.6 的 `retryCount ≥ 2` 门，不扩张 fail-closed 迁移表，改动面最小。
- 否决方案甲：会新增 `SELF_CHECK→BLOCKED`、`AUDIT→BLOCKED` 两条直达路径，扩大状态机表面积；本单无需新增路径即可闭合。
- 改前 T0 L1763：`任一必需补偿失败时，队列落 BLOCKED，记录唯一事件 compensate_failed……`
- 改后现行 L1763：`任一必需补偿失败时，先落 FAILED 并记录唯一事件 compensate_failed；达到 §21.6 既有门 retryCount ≥ 2 后，才按 §15.2.1 的唯一合法迁移落 BLOCKED。……`
- §15.2.1 T0 L571–585 与现行逐行比较：`transition_diff_count=0`；“fail-closed，未列出的迁移一律拒”仍命中 1，其他迁移门禁未放宽。

### 3.4 Gate T2

```text
authority_old_writer_phrase=0
new_writer_role_line=1
console_no_write_line=1
option_b_count=1
option_a_rows=0
fail_closed_count=1
transition_diff_count=0
baseline_lines=1792
```

搜索范围说明：生效口径扫描 `docs/specs` 与 `docs/tracker`，排除任务卡、修复报告和不可变 T0 证据中的历史原文；这些留证文本不构成现行权威口径。Gate T2：`PASS`。

## §4 F-3／F-4（T3）

### 4.1 RED（修复前）

T0 扫描结果：compose 请求表 0、compose 返回表 0、三类要求的失败码 0、`compensator` 签名 0、补偿 receipt 字段表 0。

### 4.2 F-3 `context.compose` 请求表（现行 L1584–1601）

| 字段 | 类型 | 必填 | 取值来源 | 缺省行为 |
|---|---|---|---|---|
| `turn_id` | `string` | 是 | §25.1 `turn.envelope` | 缺失即拒绝 |
| `trace_id` | `string` | 是 | §25.1 与 §21.4 既有观测链 | 缺失即拒绝 |
| `profile` | `decision \| dialog` | 是 | §16.2 已登记 profile | 缺失或枚举外取值即拒绝 |
| `target` | `local \| external` | 是 | §23.2 当前主脑条目类型 | 缺失即拒绝；`external` 必过 §23.6 三闸 |
| `memory_required` | `boolean` | 否 | 当前意图是否要求命中记忆 | 默认 `false` |
| `partitions.system` | `object[]` | 是 | 已冻结的系统指令与运行边界 | 缺失即拒绝 |
| `partitions.policy` | `object[]` | 是 | 治理⑤当前生效规则及版本引用 | 缺失即拒绝 |
| `partitions.memory.hot` | `object[]` | 否 | Memory 本轮热记忆切片 | 默认 `[]`；`memory_required=true` 且为空时返回 `NO_AVAILABLE_MEMORY` |
| `partitions.habit` | `object[]` | 否 | 本轮唯一一次 `habit.read` | 默认 `[]` |
| `partitions.session.recent` | `object[]` | 否 | 当前会话最近回合 | 默认 `[]` |
| `partitions.tool.schema` | `object[]` | 否 | 注册分类 §② 当前候选工具 schema | 默认 `[]` |
| `partitions.user.turn` | `object[]` | 是 | 当前用户原始回合与结构化意图 | 缺失即拒绝 |

封闭关系：七个 `partitions.*` 与 T0 L1584–1592 的七区逐一对应；未知键拒绝，未增加第八区。

### 4.3 F-3 `context.compose` 返回表（现行 L1603–1614）

| 字段 | 类型 | 必返 | 契约 | 关联失败码 |
|---|---|---|---|---|
| `ok` | `boolean` | 是 | 仅成功装配为 `true` | 任一失败均为 `false` |
| `payload` | `object \| null` | 是 | 成功时为送入主脑的装配结果；失败时为 `null` | 三类失败均适用 |
| `included_partitions` | `string[]` | 是 | 实际进入 payload 的分区名 | 无 |
| `trimmed_partitions` | `string[]` | 是 | 按本节既有第 1→4 位规则被裁的分区名 | `CONTEXT_OVER_BUDGET`（超预算） |
| `input_tokens` | `integer` | 是 | 隐私裁剪后由实际 tokenizer 计量 | `CONTEXT_OVER_BUDGET` |
| `budget_ref` | `string` | 是 | 固定引用 §16.4，不内嵌第二公式或预算数值 | `CONTEXT_OVER_BUDGET` |
| `trace_id` | `string` | 是 | 原样回带请求值 | 三类失败均适用 |
| `error_code` | `NONE \| CONTEXT_OVER_BUDGET \| NO_AVAILABLE_MEMORY \| PRIVACY_DENIED` | 是 | 成功／超预算／无可用记忆／§23.6 隐私拒写 | 失败时只取后三值之一 |

对应关系：预算与 token 只消费 §16.4；七区与截断顺序只消费 §25.3 原表；`target` 与 `PRIVACY_DENIED` 只消费 §23.6；`turn_id/trace_id` 复用 §25.1/§21.4。没有第二预算公式，`input_budget(profile) =` 全文声明数仍为 1。

### 4.4 F-4 `compensator` 签名表（现行 L1795–1806）

签名：`compensator(side_effect_id, before_ref, after_ref, compensation_key) -> (compensation_receipt_ref, result)`。

| 方向 | 字段 | 类型 | 必填 | 契约／幂等要求 |
|---|---|---|---|---|
| 入参 | `side_effect_id` | `string` | 是 | 对应 `side_effects[]` 中的副作用标识 |
| 入参 | `before_ref` | `string` | 是 | 原 `reversible` 项的 before 引用 |
| 入参 | `after_ref` | `string` | 是 | 原 `reversible` 项的 after 引用 |
| 入参 | `compensation_key` | `string` | 是 | 由原 operation 标识派生；同键重放不得再次执行副作用 |
| 返回 | `compensation_receipt_ref` | `string` | 是 | 指向补偿 receipt；同一补偿键始终返回原引用 |
| 返回 | `result` | `compensated \| compensate_failed` | 是 | 与 receipt 的 `result` 逐字一致；重复请求返回原结果 |

### 4.5 F-4 补偿 receipt 字段表（现行 L1808–1817）

| 字段 | 类型 | 必填 | 契约 |
|---|---|---|---|
| `compensation_key` | `string` | 是 | 与调用入参逐字一致，作为唯一补偿键 |
| `original_run_id` | `string` | 是 | 原 run 标识 |
| `compensator_id` | `string` | 是 | 原 `side_effects[]` 登记的补偿器标识 |
| `result` | `compensated \| compensate_failed` | 是 | 成功或失败的封闭枚举 |
| `evidence_ref` | `string` | 是 | 补偿结果证据引用；失败时指向失败证据 |
| `occurred_at` | `timestamp` | 是 | 补偿结果形成时间 |

对应关系：`side_effect_id/before_ref/after_ref` 逐项对应原 `reversible` 必填证据；`compensation_key` 对应原唯一补偿键；`original_run_id/compensator_id/evidence_ref` 对应原 `compensate_failed` 事件的原 run、失败补偿器与证据；结果枚举复用 `compensated/compensate_failed`。原三类副作用表保持 3 行且未改。

### 4.6 Gate T3

```text
compose_request_heading=1
compose_return_heading=1
CONTEXT_OVER_BUDGET/NO_AVAILABLE_MEMORY/PRIVACY_DENIED=均存在
compensator_signature=1
compensation_receipt_heading=1
budget_formula_declarations=1
unique_compose_entry=1
side_effect_rows=3
baseline_lines=1848
```

Gate T3：`PASS`。

## §5 F-5（T4）

### 5.1 选择与理由

- 先查 §21.6：只定义 `retryCount/reworkCount` 上限，没有时间制保留期。
- 再查 §22.2：T0/现行 L1320–1327 已有“保留与归档（R-74 拍板值）”，其中 L1324 是冻结后任务热留规则，属于可复用现行来源。
- 选择：§25.9 **只引用 §22.2，不复述年限**；唯一数值来源仍在 §22.2。
- 否决“在 §25.9 新增保守值”：已有可复用条款，再写数值会形成第二保留期来源并违反本单禁止项。

### 5.2 改动前后

- 改前 T0 L1737：`……§21.6 只规定 retry/rework 上限，没有时间制保留期，因此本章不伪造时长；账本在关联 retry/rework 尚未终结时不得清理，具体静态保留期记 TBD-G05-RETENTION。`
- 改后现行 L1769：`……§21.6 只规定 retry/rework 上限，没有时间制保留期；账本在关联 retry/rework 尚未终结时不得清理。关联任务冻结后的静态保留期只认 §22.2“保留与归档”现行规则，本节不复述年限或另立数值。`

### 5.3 Gate T4

```text
tbd_in_baseline=0
retention_pointer_in_25_9=1
year_values_in_25_9=0
section22_t0_diff_count=0
budget_formula_declarations=1
baseline_lines=1848
```

说明：任务卡、0067 审计、T0 证据与本报告会保留 `TBD-G05-RETENTION` 的历史原文；Gate 的清零对象是现行生效基线。Gate T4：`PASS`。

## §6 F-6／F-7（T5）

### 6.1 F-6 架构树两个节点

1. Core「任务编排」节点：
   - 改前 T0 L201：`<span class="desc">多步任务规划与执行顺序控制</span>`。
   - 改后现行 L201：`<span class="desc">多步任务规划（只产出步骤与依赖声明，派发顺序与优先级归 Console）；plan schema 见 §25.5</span>`。
2. Console「任务编排」节点：
   - 改前 T0 L283：`<span class="desc">派发 / 优先级 / 依赖；九点位 4–9 是八态投影</span>`。
   - 改后现行 L283：`<span class="desc">消费 §25.5 的步骤与依赖声明；派发顺序与优先级归 Console；九点位 4–9 是八态投影</span>`。

T0→现行逐行比较：`tree_changed_lines=201,283`，`tree_line_count_delta=0`；`git diff --no-index --unified=0` 仅有两个单行 hunk。Core 旧句“多步任务规划与执行顺序控制”命中 0；两个「任务编排」节点含 `§25.5` 的命中数为 2。

### 6.2 F-7 附录 A

- 改前：T0 附录 A L1767–1792 中 0057 变更行命中 0。
- 改后：现行 L1845 新增且仅新增一行：`| 2026-11-13 | **wo-ultimaagent-20261113-0057**：新增 §25.1–§25.11 主链可执行契约，并在 §15.2.1 补 EXECUTING → CANCELLED；来源工单 wo-ultimaagent-20261113-0057。 |`
- 附录 A 精确 0057 行计数：1；日期与来源工单号均为 2026-11-13 / `wo-ultimaagent-20261113-0057`。

### 6.3 0057 收尾闭合

- 0057 T3.4（架构树「任务编排」desc 含 `§25.5`）：**已闭合**，2/2 节点命中。
- 0057 T6.2（附录 A 恰新增 1 行）：**已闭合**，0057 行计数 1。
- 0057 T6.3（架构树 desc 节点改动数＝2）：**已闭合**，现行只改 L201/L283。

### 6.4 Gate T5

```text
core_old_phrase=0
task_nodes_with_25_5=2
tree_changed_lines=201,283
tree_line_count_delta=0
appendix_0057_count=1
baseline_lines=1849
```

Gate T5：`PASS`。

## §7 越界声明

### 7.1 基线七处锚点

| 锚点 | T0→现行 diff-only 结果 | 判定 |
|---|---|---|
| §14.3 | T0 L510→现行 L510，单行替换写口表述 | **在声明域内** |
| §19.3 Console 行 | T0 L1127→现行 L1127，单行替换为只读投影且不写文件 | **在声明域内** |
| §15.2.1 迁移表 | T0 L571–585 与现行逐行差异 0；方案乙不改迁移表 | **在声明域内** |
| §25.3 | T0 L1583 后新增 32 行请求/返回字段表 | **在声明域内** |
| §25.9 | T0 L1737→现行 L1769，单行替换保留期来源 | **在声明域内** |
| §25.11 | T0 L1763→现行 L1795–1819，新增两表并替换补偿失败句 | **在声明域内** |
| 附录 A | T0 L1788 后→现行 L1845，新增 0057 恰 1 行 | **在声明域内** |

基线相对 T0 共 6 个 hunk：§15.2.1 因选方案乙无 hunk，其余 6 个均落在上表允许锚点；越界处数 0。

### 7.2 架构树与报告证据

| 对象 | T0→现行结果 | 判定 |
|---|---|---|
| Core「任务编排」desc | 仅 L201 单行替换 | **在声明域内** |
| Console「任务编排」desc | 仅 L283 单行替换 | **在声明域内** |
| 本报告 | 本单唯一新建报告 | **在声明域内** |
| `docs/reports/evidence/fix-0068/` | 仅三份 T0 证据 | **在声明域内** |

架构树行数不变，逐行差异只含 201、283；其他节点、属性、样式、结构差异 0。队列文件在当前工作树已有 0057/派发相关既存 `M` 状态（0067 已审计记录），本单未调用写接口、未对其应用补丁；0061/0062/0063 卡未写。未执行 `git add/commit/tag/push`，未访问禁区，未调用 18766。

## §8 自证

### 8.1 改动文件清单

- `docs/specs/next-感知交互参数基线-20261113.md`：T0 1792 行、SHA256 `3FE9B80F25E0B75E42191C8C6343AF98EA4B51BA529457F97A48C9770A894C52`；现行 1849 行、SHA256 `07C262EEE47D8EFC568EC2304BC875262D4FAAC82378C4915B84BDF968E36FB7`；行数变化 `+57`。
- `docs/tracker/北极星架构树.html`：T0 476 行、SHA256 `DC32D2B15405A8690CD34AC61A825506B381F3402D3773F67F9F66071ECDACA3`；现行 476 行、SHA256 `8A89AE9AC290DD1F41F5238238202A194A93727D9D34AB89528135B77EC08398`；行数变化 `0`。
- `docs/reports/fix-wo-ultimaagent-20261113-0068.md`：本单唯一新建报告。
- `docs/reports/evidence/fix-0068/t0-baseline.txt`、`t0-architecture-tree.txt`、`t0-manifest.txt`：T0 证据。

### 8.2 逐 T Gate

| T | 命令／核验摘要 | 结果 |
|---|---|---|
| T1 | 八段标题计数 8；两份全文副本可读且哈希等于 T0；七处锚点＋两节点行号齐 | PASS |
| T2 | `authority_old_writer_phrase=0`；新角色句 1；Console 不写句 1；方案乙 1／方案甲 0；fail-closed 1；迁移表差异 0 | PASS |
| T3 | 请求/返回表各 1；三失败码齐；compensator 签名 1；receipt 表 1；预算公式声明 1；副作用类别 3 | PASS |
| T4 | 基线 TBD 0；§25.9 指针 1；§25.9 年限数值 0；§22 相对 T0 差异 0 | PASS |
| T5 | Core 旧句 0；两节点含 §25.5＝2；树只改 201/283；附录 0057 行＝1 | PASS |
| T6 | 26 项自动验收全部为 True，`failed_checks=0`；七锚点越界 0；抽检回读 8 条一致 | PASS |

### 8.3 反例检查

```text
第九态：eight_states_exact=True
八态实测：QUEUED,EXECUTING,SELF_CHECK,AUDIT,COMPLETED,FAILED,BLOCKED,CANCELLED
第二写者：old_writer_phrase_zero=True；writer_role_one=True；console_no_write_one=True
第二预算公式：budget_formula_single=True
第二保留期数值：retention_pointer_one=True；retention_value_zero_in_25_9=True；retention_tbd_zero=True
Core 旧“执行顺序控制”：core_old_phrase_zero=True；task_nodes_25_5_two=True
F-2 双路径：option_b_one=True；option_a_zero=True
```

搜索对象为现行生效基线与架构树；任务卡、审计报告、本报告和 T0 证据保留的历史原文不冒充现行口径。

### 8.4 抽检回读（8 条）

| # | 坐标 | 原文摘要 | 结论 |
|---:|---|---|---|
| R1 | 基线 L510 | `state_machine` 唯一定义状态语义，`queue-writer` 是落盘唯一写者 | 一致 |
| R2 | 基线 L1127 | Console 只读八态投影与迁移结果，不写 `queue-status.json` | 一致 |
| R3 | 基线 L571/L581/L1819 | fail-closed 仍在；`FAILED→BLOCKED` 须 `retryCount ≥ 2`；补偿失败先落 `FAILED` | 一致 |
| R4 | 基线 L1584/L1603/L1614 | compose 请求/返回两表存在，三类失败码齐 | 一致 |
| R5 | 基线 L1769 | §25.9 只认 §22.2，未复述年限 | 一致 |
| R6 | 基线 L1795/L1808 | compensator 签名与补偿 receipt 字段表均存在 | 一致 |
| R7 | 架构树 L201/L283 | Core 只产步骤/依赖，Console 管派发顺序/优先级；两处均引 §25.5 | 一致 |
| R8 | 基线 L1845 | 附录 A 的 0057 行日期、摘要、来源工单号齐 | 一致 |

### 8.5 F-1～F-7 结论

- F-1：队列状态语义与落盘写口已唯一化，**已闭合**。
- F-2：采用方案乙，经 `FAILED` 与 `retryCount ≥ 2` 到 `BLOCKED`，**已闭合**。
- F-3：`context.compose` 请求/返回字段与三类失败码齐，**已闭合**。
- F-4：`compensator` 签名和补偿 receipt 字段齐，**已闭合**。
- F-5：§25.9 只引用 §22.2，TBD 清零且无第二数值，**已闭合**。
- F-6：Core/Console 编排边界与 §25.5 指针一致，**已闭合**。
- F-7：附录 A 已补 0057 恰一行，**已闭合**。

T6_GATE=PASS
READY_FOR_INDEPENDENT_AUDIT
