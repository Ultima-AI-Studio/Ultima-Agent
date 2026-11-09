# G-ORCH 契约缺口 · DeepSeek 方案（外部意见，原文未编辑）

- 日期：2026-11-09
- 来源：DeepSeek `deepseek-chat`（`src/brain/orchestrator.call_deepseek`）
- 提示词包：`Temp\gorch-issues-package.md`（5565 字符）
- 用量：in 2950 / out 3552 tokens
- 性质：**外部意见，不是决策**。采纳前需 Owner 复核，采纳后按 G-TASKFLOW-001 转工单执行。

---

## 1. 结论

- **不同源，分开处理。** 问题 1 是"必填字段缺席"，问题 2 是"枚举值未收敛"。用同一套 schema 校验器兜两者，等于把"必填性"和"词表收敛"耦合成一个闸门，任一改动都要重新论证另一件，可回滚性被破坏。合并会把两个最小改动变成一个中改动。
- **Q1 选 (b)：显式豁免，但豁免必须"可被反向审计"，不能只是布尔开关。** 关键设计：无 ACC 表时不接受单纯的 `no_gates: 理由`，而要求一条**可机检的替代判据**；否则豁免即等于关闸。
- **Q3 选：只收敛 `status` 一张词表，不合并 `result`。** `blocked` 归 `result`（回执态），不归 `status`（工单态）。`done` 与 `closed` 视为同义（同一枚举的别名），由映射函数归一，不改 ccpm。
- **Q4 选：未知 `status` 只跳过该任务并显式报错升级，不整批拒绝。** 三个子命令一致；但"跳过"必须产生一条可被 `gate` 读到的显式失败记录（替代静默跳过），否则违反硬约束 1。
- **Q5 不同源。**
- **需要 Owner 拍板 2 点：** (i) 问题 1 过渡期关闭条件写死为"14 份全部补齐或持有豁免"是否接受；(ii) `blocked` 是否允许出现在 `status`（我建议禁止，只留在 `result`）。

---

## 2A. 问题 1 方案（判据表存在性）

### 口径 (b) 的收紧版

不接受"无表 + `no_gates: 理由`"。改为：**无 ACC 表时，必须有一条 `waiver` 记录，waiver 的内容是一个可被冻结门直接执行的非空判据字段**。即豁免不是"免于校验"，而是"换一条校验"。

**卡级声明**（写在卡所在工单 frontmatter，不放卡标题下——因为卡是批次目录下 `<id>.md`，frontmatter 是唯一已有结构化位）：

```yaml
gate_waivers:
  - card: s1-parser
    because: "该卡为纯文档搬运，无可验收行为"
    instead: "pytest tests/test_parser.py -k indent"   # 必填，非空，且必须能被现存测试收集到
```

**机检判据（冻结门内新增，收紧）：**

```
G1-a: 对每张卡：
  rows = acc_rows(card_text)
  if len(rows) == 0:
      w = [x for x in frontmatter.get('gate_waivers', []) if x['card'] == card_id]
      refuse unless len(w) == 1
      refuse unless w[0]['instead'] 是非空字符串且出现在 tests/ 的某个 -k 表达式或某条现有测试路径中
      # 即：豁免值必须能落到一条真实测试，否则视同未豁免
  else:
      # 保持现逻辑，且把 `if gate_ids and (...)` 的短路去掉：
      refuse unless declared_gates == gate_ids == r1 == r2
```

这条改动的实质：把 `if gate_ids and (...)` 改成 `if (...) and (gate_ids or ...)`，并在空表分支插入 waiver 校验。**这是收紧**（空表从"通过"变为"必须持有效 waiver 才通过"）。

### 防"人人写豁免"（关键，机检）

```
G1-b（聚合检测，冻结单卡时不做，冻结整批时做，收紧）:
  batch 内 waiver 数 / 卡总数 <= 0.25
  且 任一单卡 waiver 的 `instead` 不得只指向 "tests/ 里任一测试"，
      必须指向在该卡改动集上会失败的测试（近似实现：instead 里的 -k 表达式
      在去掉该卡产出后 pytest 返回非 0 —— 该项需 stage 级验证，见 Q4 落地）
```

**`instead` 指向的测试必须对该卡产出敏感**：这是整条 waiver 从"布尔开关"变成"有效替代判据"的分水岭。实现上不做动态裁剪（成本高），改为**契约断言**：`instead` 表达式的测试在冻结前必须在当前分支跑一次绿；冻结记录里落 `instead_result: pass`，且该结果不得缓存过期（复用现有 `frozen_at` + 该测试文件 mtime 判定）。简化为可执行判据：

```
G1-c: 冻结时对每张带 waiver 的卡，执行 instead 指向的 pytest -k，
      结果必须 pass，且 where 测试文件的 git blob sha 与其被 frozen_at 时记录的 sha 一致。
```

**回滚点：** `scripts/freeze-work-order.py` 单文件；`git revert` 该 commit 即恢复旧短路行为，14 份工单行为回到"无表即默认通过"，不破坏其他测试。

---

## 2B. 问题 2 方案（状态词收敛）

### 唯一权威源：`scripts/gorch/status_map.py`（**新增代码文件**，不是"新文档体系"）

只做映射，不改 ccpm，不并行判断。

```python
# 工单 status 的规范集合与别名映射（单一权威）
STATUS_CANON = {'open', 'in-progress', 'closed'}          # 收紧：去掉 in_progress/done/completed 直写
STATUS_ALIASES = {
    'in_progress': 'in-progress',
    'done': 'closed', 'completed': 'closed',
}
RESULT_CANON = {'done', 'blocked', 'failed'}              # 回执层，与 status 分离

def normalize_status(raw):
    s = (raw or '').strip()
    if s in STATUS_CANON: return s
    if s in STATUS_ALIASES: return STATUS_ALIASES[s]
    return None   # 调用方决定处置，见 Q4
```

**关于合并/不合并：**
- **`status` 与 `result` 不合并。** 二者语义不同：`status` 是工单生命周期，`result` 是单次派发结果。合并会把"任务被 block 过一次"误读成"工单永久 blocked"，这在编排层会连累 `depends_on` 判定。
- **`done` 与 `closed` 同义**：映射到 `closed`。理由：`is_done_status` 三者同认，故语义等价；选 `closed` 作为 canon 是与 ccpm `is_done_status` 字面最短吻合，减少映射噪声。
- **`blocked` 只归 `result`，不归 `status`。** 若 Owner 坚持放 `status`，则 `status: blocked` 会被 `normalize_status` 返回 `None` 而按 Q4 处置——不会静默通过。

### 防四面漂移（机检）

```
G2-a: pytest 断言 STATUS_CANON ∪ set(STATUS_ALIASES) 与以下逐条一致：
      - batch_orchestrator 内不再自持 VALID_STATUSES 集合（改为导入）
      - kanban_update 的状态字面量全部经 normalize_status() 归一后再比较
      - is_done_status 的闭包 == STATUS_CANON 中标记为终态的集合（现 = {'closed'}）
G2-b: shell 判定 `grep -rn "'done'\|'completed'\|'in_progress'" scripts/`
      除 status_map.py 外 0 命中（防止直写别名）
G2-c: codex_channel 的 record['result'] 取值 ∈ RESULT_CANON，且不写入 status 字段
```

**收紧**：原来各层各持一套可直写、直比较的字符串，现改为只允许经 `normalize_status` 后再比较；`in_progress`/`done`/`completed` 在 `status` 里从"合法"降为"别名，写入即被归一，原始值不再参与判定"。

---

## 2C. 问题 2 附加：未知状态处置（Q4）

结论：**只跳过该任务、其余继续；但跳过必须写一条显式失败记录，且该记录能被 `gate` 读到并让 `gate` 报非 0。**

- 权衡：ccpm `next.sh` 现状是"非 open 且非空即跳过且不报错"（静默跳过）。纯沿用则违反硬约束 1；整批拒绝则把一个脏任务的损失放大到全批，对一个"潜在、非现实"的风险过度反应。
- 三个子命令一致性：`gate`/`next`/`provision` 均按"跳过单个任务 + 写 `skipped_unknown_status` 记录"处理；`gate` 因为要对外产出判定，要求该记录非空即退非 0。这一条必须写在 `next.sh` 的调用包装层（自建层），不改 `next.sh` 本体。

```
G4-a: 造 status: blocked 的批次 → next/provision 返回 0 且跳过该任务，
      但 batch 输出里出现 skipped_unknown_status: [<task>] 一条；
      gate 读到该条 → 退出码非 0。
G4-b: 该批次中其余 open 任务仍被派发（数一数派发日志条数）。
```

**这是放宽**（该任务从"整批拒绝"变为"跳过"）**并用收紧的显式记录补偿**。

---

## 3. 逐项判据（编号，可执行）

- **G1-a**（收紧）：`acc_rows(card)==[]` 的卡必须有且仅有一条 `gate_waivers` 命中，且 `instead` 非空且能解析到 `tests/` 下真实测试路径；否则冻结拒绝。
- **G1-b**（收紧）：`len(waivers)/len(cards) <= 0.25` 于批次级；超阈拒绝整批冻结。
- **G1-c**（收紧）：带 waiver 卡的 `instead` 测试冻结时必须 pass，且测试文件 blob sha == 冻结时记录 sha，否则拒绝。
- **G1-d**（放宽，仅针对过渡期）：见 Q2，现存 14 份工单按其 `frozen_at` 早于 `WAIVER_EPOCH` 一律视为"隐含持有效 waiver"，仅冻结记录不重跑。
- **G2-a**（收紧）：`batch_orchestrator` 不再持有自己的状态集合；`pytest` 断言其内部无状态字面量直比较。
- **G2-b**（收紧）：`grep -rn "'done'\|'completed'\|'in_progress'" scripts/ --exclude=status_map.py` 命中数 = 0。
- **G2-c**（收紧）：`codex_channel` 写 `result` 值 ∈ `RESULT_CANON`，且不写 `status`。
- **G2-d**（收紧）：`normalize_status('blocked') is None`，断言 `blocked` 不得出现在任何工单 `status`。
- **G4-a**（放宽+补偿）：`status: blocked` 批次 → `next`/`provision` 退出 0，输出含 `skipped_unknown_status`，`gate` 见到该条即退非 0。
- **G4-b**（收紧）：`gate` 对"存在 skipped_unknown_status 的批次"必须非 0，且输出该任务名。

---

## 4. 落地顺序与回滚

| 步 | 文件/动作 | 类型 | 完成判据 | 回滚点 |
|---|---|---|---|---|
| 1 | 新增 `scripts/gorch/status_map.py`（只加文件，无人调用） | 中性 | G2-a 的空断言可跑 | 删文件，零影响 |
| 2 | `batch_orchestrator` 改为导入 `normalize_status` 与 canon | 收紧 | 176 测试全绿 + G2-b | revert 该 commit，恢复自持 `VALID_STATUSES` |
| 3 | `kanban_update` 状态比较经 `normalize_status` | 收紧 | G2-b/G2-a | revert |
| 4 | 自建层加 `next.sh` 包装：未知 status → 跳过 + 写 `skipped_unknown_status` | 放宽+补偿 | G4-a/G4-b（造 blocked 批次） | 去掉包装，恢复整批拒绝 |
| 5 | `freeze-work-order.py`：`if gate_ids and (...)` → 空表分支接 waiver | 收紧 | G1-a/G1-b/G1-c | revert 单文件，回到短路 |
| 6 | 冻结门加过渡期豁免：`frozen_at < WAIVER_EPOCH` 的 14 份跳过 G1-a~c | 放宽（过渡） | **14 份真实工单解析 0 误伤**；`pytest` 176 全绿 | 去掉 epoch 分支，回到旧行为（等于全禁 14 份，不引入新风险） |
| 7 | 关闭过渡期（Owner 拍板时）：移除 epoch 分支 | 收紧 | 14 份全部补齐 waiver 或补 ACC 表 | 反向 revert epoch 分支 |

**确认"不误伤 14 份"的具体判据：**

```
pytest tests/ -k freeze && python -c "..."   # 对 14 份逐一 freeze，断言均返回 0（过渡期），
                                              # 且输出里 WAIVER_EPOCH 未命中的卡数为 0
```

---

## 5. 风险与"不做什么"

**最可能翻车的两处：**

1. **G2-b 的宏层 grep 会误报**——`kanban_update` 内部可能有合理的 `'done'` 字面量（如展示用）。提前发现办法：步 2 前先跑一次 grep，把每处命中人工分型（判定参与 / 展示），只对"参与判定"的收紧，展示层允许直写但在测试里钉死。**这是"收紧"唯一需要预分类的地方，不做预分类会砸测试。**

2. **G1-c 的 sha 绑定**——测试文件被无关 PR 改动（格式化）会让所有持 waiver 的卡冻结失败。提前发现：在步 5 落地前，对现存 14 份跑一次 G1-c 的 dry-run，记录 sha 是否都在近期被改过；若历史改动频繁，把 sha 绑定退化为"容忍 mtime 变化、只要求测试仍收集到"（属于对 G1-c 的放宽）。

**明确不做：**

- 不新建 `docs/` 文档；waiver 语法只活在 YAML 与解析器，不入文档体系。
- 不合并 status 与 result；不合并问题 1 与问题 2 成统一 schema 校验器。
- 不改 ccpm 的 `unmet_deps` / `active_conflicts` / `next.sh` 本体，只接只映射。
- 不要求 Owner 维护任何豁免清单：waiver 由写入方自行声明，聚合阈值 G1-b 由机器算。
- 不把 `status: blocked` 升格为合法 `status`（即使 Owner 拍板同意，也只记为 `result` 或走 G4 的 skip 路径）。
- 不做"冻结时动态执行 `instead` 测试"的复杂化——G1-c 只对带 waiver 的卡跑一次静态 pass + sha 校验。

---

# 附录 · 复核意见（豆包，2026-11-09，供 Owner 讨论，不是决策）

## 可以采纳的 3 点

1. **不同源、分开处理**。两个问题的回滚单位不同（一个在冻结门、一个在判定层），合成一个 schema 校验器会让任一改动都要重新论证另一件。这一条比我原来的"合并成一个契约问题"的判断更实际。
2. **`blocked` 归 `result` 不归 `status`**。这是对的，也纠正了我上一轮的字段混淆——我原话"两套状态词正面对撞"不准确，`blocked` 从来不是工单状态词。
3. **豁免不是"免于校验"，而是"换一条校验"（`instead` 字段）**。"无表 + 写个理由"确实等于关闸；要求豁免必须指向一条真实测试，方向对。

## 需要修正的 4 点

1. **G1-c 的 git blob sha 绑定建议砍掉。** DeepSeek 自己在风险 2 里已经承认"测试文件被格式化就全挂"，退让成 mtime 容忍。那就等于引入一个会失效的新状态位（冻结记录里存 sha），收益很低。**改为**：冻结时只要求 `instead` 指向的测试当前 pass 且能被 pytest 收集到，不绑 sha。

2. **"`instead` 的测试必须对该卡产出敏感"这一层，机检做不到，必须如实标为人工复核点。** DeepSeek 承认做不了动态裁剪，退化成"跑一次绿"——但一个永远绿的测试（`pytest tests/x.py -k not_a_real_test` 也能退出 0）足以骗过豁免。**这是机检的边界**，应该写成"每 N 份 waiver 由 Owner 抽审一次"，不要假装 G1-c 覆盖了它。

3. **G2-b 的 `grep scripts/ 命中 0` 当不了判据。** `kanban_update.py` 有 42KB，内部必然有 `'completed'` 这类 todo 状态字面量（那是看板自己的状态机，不是工单状态）。DeepSeek 在风险 1 里也承认要预分类。**改为**：只对"参与判定"的命中收紧，展示层允许直写但在测试里钉死；预分类结果作为一次性基线落进测试 fixture。

4. **G1-d 的过渡期判定不能用 `frozen_at < WAIVER_EPOCH`。** 它等于让所有历史工单永久免检，且 `frozen_at` 本身是个可能不存在的字段。**改为**：由机器扫现存 14 份工单生成一次显式 id 白名单（脚本落进 tests，不靠人工维护），过渡期只对名单内工单跳过存在性校验；名单一旦不再增长即可关闭。

## 需要 Owner 拍板的 3 点

1. **未知状态词到底"整批拒绝"还是"跳过该任务"。** DeepSeek 选跳过 + 写 `skipped_unknown_status` 记录，但没说清 `next` 返回 0 与 `gate` 返回非 0 时调用方听谁的——这是"带病继续"还是"显式告警"，得你定。
2. **`status` 是否允许出现 `blocked`。** DeepSeek 建议禁止（只留 `result`）。我同意，但这意味着"工单被阻塞"这件事只能落在回执里，工单本身没有表达位置——要不要给工单加一个 `blocked_by` 类字段，是设计选择。
3. **过渡期关闭条件。** DeepSeek 写"14 份全部补齐或持有豁免"，这实际上要求给现存工单补 ACC 表——工作量不小，且这些工单多数已冻结交付。要不要干脆"历史工单永久按白名单豁免、只对新建工单强制"，你定。

