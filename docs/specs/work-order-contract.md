# UltimaAgent `wo-*.md` 工单卡契约 v1

本契约定义 `tasks/queue/wo-*.md` 的机器可校验入口。`docs/specs/work-order.schema.json` 校验 Markdown 被解析后的中间对象；`scripts/validate_work_order.py` 负责 Markdown 解析、跨层语义和错误定位。新卡应使用 `structured-v1`，历史卡由只读兼容 profile `legacy-queue` 接纳，兼容不得反向成为新卡模板。

## 1. L1 头部

L1 是身份与派发状态：

- `title`：首行，必须以 `# Codex 工单 · ` 开头。
- `version`：版本号，例如 `v1.0`。
- `status`：只允许 `可开工`、`排队中`、`待开工`、`已冻结`、`已完成`。
- `tool`：执行工具或执行端说明，不得为空。

Schema 负责字段存在性、类型和枚举。Validator 在派发场景进一步把状态收紧为 `可开工`、`排队中`；默认开启，可用 `--no-dispatch-status` 关闭这一场景检查。`--strict` 只把 warning 升级为 error，不扩写枚举。

## 2. L2 锁定

L2 把卡绑定到唯一执行上下文：

- `link`：工单号，格式 `wo-*`。
- `prereq`：前置条件或前置收口说明。
- `workdir`：锁定工作目录。
- `revision`：7–40 位小写十六进制 Git revision，正则 `^[0-9a-f]{7,40}$`。
- `usage`：执行顺序和 Gate 纪律。
- `plan_ref`：G-PLAN-001 对应方案路径。
- `runtime`：解释器或运行端约束。

Schema 管单字段格式；Validator 从顶部引用行抽取这些值，缺失时返回带行号的 `E_*` 错误。Schema 不访问 Git、文件系统或网络。

## 3. L3 骨架

L3 固定三段主骨架：

- `scope_do`：`## 0. 范围冻结` 中的“只做”清单，至少一项。
- `scope_not_do`：同段中的“不做”或 Non-goals 清单，至少一项，空值为 `E_NO_FORBIDDEN`。
- `task_table`：`## 1. 任务清单` 的 Markdown 表格，每行含 T 编号、文件和验收门。
- `task_details`：`## 2. 任务明细` 下的 `### T# · 标题` 块。

章节标题允许在“范围冻结”前带阶段名，也允许“任务清单/任务明细”后带括号说明；语义锚点保持不变。`## 3` 以后的回执、验收要点和历史补记不进入契约对象。

## 4. L4 任务明细

每个 `### T# · 标题` 必须包含四段：

- `files` ← `**文件**`：至少一条，且每条至少含 `\`、`/`、`.py`、`.md` 或 `.json` 之一。
- `writes` ← `**写什么**`：至少一条可执行描述。
- `gate` ← `**验收（Gate T#）**`：至少一条，且含 `pytest`、`命令`、`==`、`!=`、`差异`、`PASS`、`输出` 等可验证词之一。
- `forbidden` ← `**禁止**`：至少一条边界声明。

四段标签后的全角冒号可有可无，内容可以与标签同一行或从下一行开始。每段保留标签行号，错误必须定位到标签行或具体 T。

## 5. 跨层一致性

以下规则由 Validator 实现，而不是复制进 JSON Schema：

1. `task_table` 的 T 集合必须等于 `task_details` 的 T 集合，否则 `E_T_SET_MISMATCH`。
2. T 编号必须从 T0 连续到 Tn，无跳号，否则 `E_T_NUMBER_GAP`。
3. 每条 Gate 非空并至少包含一个可验证词，否则 `E_GATE_WEAK`。
4. `scope_not_do` 不得为空，否则 `E_NO_FORBIDDEN`。
5. 每个 `files` 条目必须具有路径特征，否则返回对应 T 和行号。
6. 派发状态默认只接受 `可开工`、`排队中`；非派发态返回 `E_STATUS_NOT_DISPATCHABLE`。

JSON Schema 的职责是验证解析后对象的封闭结构；Validator 的职责是解析 Markdown、报告源码行号并执行集合、连续性、文本强度和派发场景规则。二者不能互相替代。

## 6. 与 `card_contract.py` 的边界

`tasks/queue_engine/card_contract.py` 继续管理 `tasks/cards/` 老任务卡，字段为 `task_id`、`goal`、`acceptance[]`、`dependsOn[]`、`fileDomain[]` 等。本契约只管理 `tasks/queue/wo-*.md`，不调用、不修改也不扩展 `card_contract.py`。两套体系并存：老任务卡契约负责执行单元，新工单契约负责队列工单与 DoR。

## 7. 存量卡兼容策略

原则是“schema 迁就存量，不改存量卡”。Validator 仅在卡不满足完整四层新格式时启用 `legacy-queue`，保留标题、原始状态和 `##` 章节索引，给出 `W_LEGACY_PROFILE`；兼容 profile 不执行新卡的派发态、T 集合和四段明细规则。`--strict` 可把该 warning 升为 FAIL，用于逐步治理，但本工单的存量正向回归使用默认模式。

| 存量卡 | 观察到的差异 | 兼容处理结论 |
|---|---|---|
| `wo-s1-engineering-packaging.md` | 任务从 T1 开始，明细外链到 `tasks/cards/`，无 L1/L2 引用行 | 进入 `legacy-queue`；保留章节索引，不伪造 T0 或锁定字段 |
| `wo-ultimaagent-20261029-0001--m29-register-control.md` | 四段明细存在，但缺 `link/workdir/revision/runtime` 且状态为历史完成说明 | 进入 `legacy-queue`；不把历史状态误判为当前可派发 |
| `wo-ultimaagent-20261101-0014--kws-user-entry.md` | 使用中文编号章节和 `### T0`，没有任务清单表格 | 进入 `legacy-queue`；不重排正文 |
| `wo-ultimaagent-20261101-0021--work-capability.md` | 使用 `goal/acceptance[]/dependsOn[]/fileDomain[]` 老格式并含大量历史补记 | 进入 `legacy-queue`；附录章节只做索引 |
| `wo-ultimaagent-20261103-0022--middleware-v1.md` | 老 `card_contract` 风格字段，没有四层工单骨架 | 进入 `legacy-queue`；与 `tasks/cards/` 契约边界保持不变 |
| `wo-ultimaagent-20261103-0025--t0-baseline-fix.md` | 老格式且带建卡补记，标题不是 `# Codex 工单 ·` | 进入 `legacy-queue`；标题只要求一级 Markdown 标题 |
| `wo-ultimaagent-20261101-0019--new-kws-proof.md` | 计划绑定短卡，仅有一级标题与状态/计划字段，没有 `##` 章节 | 进入 `legacy-queue`；要求正文至少两行，不伪造章节 |
| `wo-ultimaagent-20261101-0020--voice-next-live.md` | 计划绑定短卡，仅有一级标题与真人回执引用，没有 `##` 章节 | 进入 `legacy-queue`；要求正文至少两行，不伪造章节 |
| `wo-ultimaagent-20261108-0028--e02-evidence-scope-plan-review.md` | 接近四层格式，但 L2 锁定字段不全，四段标签无冒号 | 进入 `legacy-queue`；标签冒号差异留给未来迁移，不改卡 |
| `wo-ultimaagent-20261108-0030--m4-orchestration-ledger.md` | 有范围/表格/明细，但缺 `link/prereq/workdir/revision` | 进入 `legacy-queue`；作为默认正向回归样本 |

兼容放宽仅包括：标题前缀、状态词、L2 锁定字段、T0 起始、任务表/明细并存要求、四段标签写法、计划绑定短卡可无 `##` 章节，以及历史附录。文件不可读、没有一级标题或正文少于两行仍然 FAIL；新卡一旦被识别为 `structured-v1`，不得回退到兼容 profile 逃避错误。
