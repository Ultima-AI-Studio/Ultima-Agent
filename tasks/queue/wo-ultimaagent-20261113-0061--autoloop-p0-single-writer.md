# Codex 工单 · wo-ultimaagent-20261113-0061（Autoloop P0 唯一写入口三件套）

> 版本：v1.0｜状态：待审卡｜执行端：Codex｜推理强度：high  
> 方案依据：`docs/plans/next-autoloop-融合实施方案-20261113.md` §3、§8、§10  
> 前置：不依赖 0057 冻结；须先经 Owner 与独立审计完成 0060 式审卡，审卡通过后方可派发  
> 本单不改基线，不代表可开工。

## 1. 范围冻结

**只做**

- 新建 `tasks/queue/inbox/`，保留 `.gitkeep`，README 用一句话说明“外部组件只写 inbox，不读写队列”。
- 新建 `scripts/queue-writer.py`，作为 `tasks/queue/queue-status.json` 的唯一写者，提供原子替换、`claim_id` 去重与 `--selftest`。
- 新建 `scripts/reconcile-inbox.py`，只读比较 inbox 与队列，覆盖孤儿回执、孤儿卡、重复回执、状态不一致、未消费积压；支持 `--json`。
- 为 `queue-status.json` 的新派发记录增加 `claim_id` 并更新相应 schema 校验；仅新单使用，存量记录不批量改写。
- 将 `scripts/dispatch-work-order.py` 的队列写入路径收敛为调用 writer；现有 CLI 参数表保持不变，其他派发逻辑不变。

**不做**

- 不改 `docs/specs/next-感知交互参数基线-20261113.md` 或其他基线章节。
- 不做 Autoloop 外挂接入，不引入 M2/M5/M6/M8/M9，不新增产品承诺。
- 不提供绕过 writer 的降级裸写，不让 reconcile 自动修复队列。
- 不批量补写存量 `claim_id`，不改变 `config/voice-next/live.json`。

## 2. 任务清单

| 任务 | 文件 | 关闭判据 |
|---|---|---|
| T1 | `tasks/queue/inbox/.gitkeep`、`tasks/queue/inbox/README.md` | inbox 写入边界清楚，目录可随仓库保留 |
| T2 | `scripts/queue-writer.py`、writer 测试 | 唯一写入、原子替换与 `claim_id` 幂等可机检 |
| T3 | `scripts/reconcile-inbox.py`、reconcile 测试 | 只读对账、JSON 输出与退出码契约可机检 |
| T4 | 队列 schema、`scripts/dispatch-work-order.py`、相关测试 | 新单 `claim_id` 生效，派发器只经 writer 写入且参数表不变 |
| T5 | 本单全部写域与测试 | 唯一写者搜索、行为用例、回归与写域差值均通过 |
| T6 | renderer migrate 收口、两个存量测试接口对齐 | 写 authority 仅 queue-writer；12 项存量失败转通过，断言不减少 |

## 3. 任务明细

### T1 · inbox 边界与保留文件

**文件**：`tasks/queue/inbox/.gitkeep`、`tasks/queue/inbox/README.md`

**写什么**

1. 建立 inbox 目录并用 `.gitkeep` 保留空目录。
2. README 明确：外部组件只可投递 `<claim_id>.json`；不得读取或写入 `queue-status.json`，不得写 `docs/reports/fix-*`。
3. README 指向 writer 与 reconcile，不在此重复定义字段或消费规则。

**验收（Gate T1）**

1. 两个文件存在、可读；README 含“只写 inbox”“不得直写队列”的可搜索语句。
2. README 对 `claim_id`、writer、reconcile 的指针与方案 §3.1 一致。
3. `git diff --name-only` 以执行前 T0 快照为准，未出现本单写域外的新路径。

**禁止**：不得在 README 另立队列状态机、回执字段主文或产品承诺；不得让外部组件读取队列后自行决策写回。

### T2 · 唯一 writer 与幂等写入

**文件**：`scripts/queue-writer.py`、writer 单元测试

**写什么**

1. writer 成为 `queue-status.json` 唯一写者：锁内读回、校验预期版本、写同卷临时文件、刷新并原子替换；任一步失败都保留原文件并返回非零。
2. 按 `claim_id` 幂等消费；首次投递落盘，重复投递返回首次结果并记 duplicate，不产生第二份有效队列变更。
3. `--selftest` 在隔离临时目录覆盖正常写入、重复投递、原子替换失败保护，不触碰真实队列。
4. writer 拒绝缺失/空白 `claim_id` 的新派发记录；存量只读回放不触发批量迁移。

**验收（Gate T2）**

1. 对同一 `claim_id` 重复投递，队列有效记录集合在首次投递后不再变化，duplicate 证据存在。
2. `python scripts/queue-writer.py --selftest` 退出码为 `0`，且测试使用隔离路径。
3. 注入替换失败后，原队列字节哈希与 T0 快照一致，临时文件不会被误认成正式队列。
4. 缺失或空白 `claim_id` 的新单被 fail-closed 拒绝，存量记录保持原样。

**禁止**：不得提供“writer 失败时由派发器直接裸写”的分支；不得跳过锁内版本复核、schema 校验或原子替换。

### T3 · 只读 reconcile 与差异分类

**文件**：`scripts/reconcile-inbox.py`、reconcile 单元测试

**写什么**

1. 只读比较 inbox 与队列，报告孤儿回执、孤儿卡、重复回执、状态不一致、未消费积压；不得自动修改任一输入。
2. `--json` 输出稳定顶层对象，至少含 `diff` 与按类别分组的证据；无差异退出 `0`，有差异或输入不可判定退出 `1`。
3. 差异项携带可定位的 `claim_id`、`work_order` 与文件路径；时间阈值从既有配置/常量入口读取，不在测试中依赖当前生产数量。
4. 测试夹具分别构造正常、重复 `claim_id`、孤儿 `claim_id`，不使用真实 inbox。

**验收（Gate T3）**

1. 正常夹具运行 `reconcile-inbox.py --json` 时 `diff` 为 `0`；重复 `claim_id` 与孤儿 `claim_id` 夹具运行时 `diff` 均非 `0`，且输出能定位具体夹具文件。
2. 无差异退出码为 `0`；有差异退出码为 `1`；JSON 可被标准解析器读取。
3. `reconcile-inbox.py` 全文不含写入、替换或删除 `queue-status.json` 的语句；运行前后输入文件哈希逐项一致。
4. 输入损坏或读取失败时 fail-closed，输出可诊断错误且不改队列。

**禁止**：不得让 reconcile 调用 writer 修复差异；不得把差异非零自动转换为队列状态；不得把 stdout 以外的审计落盘伪装成只读。

### T4 · 新单 claim_id 与派发器收敛

**文件**：`scripts/queue-writer.py` 内的记录校验（现行无独立 queue-status JSON schema，记录结构由 `schema_version` 门与内联校验保证，claim_id 校验加在此处）、`scripts/dispatch-work-order.py`、相关单元测试

**写什么**

1. schema 对新派发记录要求非空 `claim_id`；存量兼容规则有明确判定边界，不批量重写历史记录。
2. 派发前由队列侧发放 `claim_id`；重派使用新值，旧值回执归 rejected，不进入 done。
3. `dispatch-work-order.py` 从直写改为调用 writer；保留现有参数名、必填性、取值域和默认值，不新增 `claim_id` CLI 参数。
4. 调用 writer 失败时派发 fail-closed，保留可审计错误，不启动执行进程。

**验收（Gate T4）**

1. 新单缺失/空白 `claim_id` 的 schema 校验失败；带有效值通过；存量夹具逐项保持原表示。
2. 重派后新旧 `claim_id` 可区分，旧值回执不会进入 done。
3. 对比 T0 参数快照，`dispatch-work-order.py --help` 的既有参数名、必填性、取值域和默认值逐项一致。
4. 模拟 writer 失败，断言派发器返回非零且未启动 worker、未改队列。

**禁止**：不得改现有 CLI 参数表；不得在派发器保留第二条队列写路径；不得把 `claim_id` 与 `session_id` 合并。

### T5 · 总验收

**文件**：本单允许写入的全部实现、测试与收件箱说明文件，以及执行报告 `docs/reports/exec-wo-ultimaagent-20261113-0061.md`

**写什么**

1. 汇总执行 T1–T4 Gate，保存命令、退出码与隔离夹具路径。
2. 搜索全部 scripts 写入引用，证明队列写入口已收敛；复跑队列引擎与派发器相关回归。
3. 对照执行前 T0 快照核验写域，记录任何预存差异但不得覆盖。

**验收（Gate T5）**

1. 对 `scripts/` 做**写入口扫描**（匹配指向 `queue-status.json` 的 `open(...,w)`、`os.replace`、临时文件原子替换等写动作）：写者仅允许 `queue-writer.py`；`reconcile-inbox.py`、`queue-doctor.py`、`render-queue-views.py`、`verify-order.py`、`dispatch-work-order.py` 等只读引用不在此列，保存原始输出。若环境使用 `rg`，须执行语义等价命令。
2. `reconcile-inbox.py` 只读性断言通过；正常／重复 `claim_id`／孤儿 `claim_id` 的 `diff` 结果分别为 `0`／非 `0`／非 `0`。
3. writer 对同一 `claim_id` 的重复投递只产生首次有效落盘，`--selftest` 退出码为 `0`。
4. 相关回归全部通过；失败即本单不通过，不得以局部 Gate 代替总验收。
5. 写域差值与本卡 §5 allowlist 逐项一致；`config/voice-next/live.json` 和基线文档哈希相对 T0 不变。

**禁止**：不得以进程启动、脚本存在或部分测试通过宣称完成；不得修改测试来掩盖真实失败；不得自行冻结或更新队列状态。

### T6 · 单写者收口与存量测试对齐（2026-11-14 补充授权）

**文件**：`scripts/render-queue-views.py`（仅 `migrate()` 写路径）、`tests/test_dor_gate.py`、`tests/test_audit_slot_age.py`（仅接口对齐）及其直接测试

**写什么**

1. renderer：删除/改写 `migrate()` 内对 AUTHORITY 的 `_atomic_json` 写——authority 不存在时改为 fail-closed，返回非零并指向 queue-writer，不自行创建 queue-status.json；正常渲染仍只写 index.md。
2. `test_audit_slot_age.py`：把 `_row/_registry` 生成 Markdown 行改为生成现行 JSON-dict（含 `records` 列表），各测试断言意图与数量保持不变。
3. `test_dor_gate.py`：移除对已删 `resolve_work_order_card` 的引用，工单号命名对齐现行契约，DoR 断言意图保持不变。
4. 不放宽任何 fail-closed 门禁，不改断言的业务含义。

**验收（Gate T6）**

1. 隔离复现 `--migrate`：authority 不存在时返回非零且不创建文件；写入口扫描显示写 authority 的仅 `queue-writer.py`。
2. 两个更新后的测试文件全绿；断言数量与意图不减少（对照修复前清单）。
3. 扩展回归中此前 12 项失败转通过，无新增失败。

**禁止**：改测试掩盖真实失败、删断言、改 CLI 参数、触碰写域外文件。

## 4. DoR 自检

| DoR 项 | 待审卡结论 | 依据 |
|---|---|---|
| 范围明确 | 通过 | §1 固定唯一 writer、只读 reconcile、新单 `claim_id` 与排除项。 |
| 依赖明确 | 通过 | 不依赖 0057 冻结；只依赖审卡门与当前队列/schema 可读。 |
| 写域明确 | 通过 | §5 给出实现 allowlist，并要求以 T0 差值复核。 |
| Gate 可执行 | 通过 | 每个 T 均给出输入、命令/行为与 fail-closed 结果。 |
| 回滚/止损明确 | 通过 | 原子替换失败保留原队列，writer/reconcile 失败均禁止派发。 |

> 以上只是卡面 DoR 自检，不等于 Owner/独立审计通过，不构成派发授权。

## 5. 写域

允许写入：

- `tasks/queue/inbox/.gitkeep`
- `tasks/queue/inbox/README.md`
- `scripts/queue-writer.py`
- `scripts/reconcile-inbox.py`
- 与 writer/reconcile/新单 `claim_id` 直接对应的测试文件与 schema 文件
- `scripts/dispatch-work-order.py` 中“调用 writer 替代直写”的最小改动
- 执行报告 `docs/reports/exec-wo-ultimaagent-20261113-0061.md`
- T6 补充授权：`scripts/render-queue-views.py`（仅 `migrate()` 写路径收口）、`tests/test_dor_gate.py`、`tests/test_audit_slot_age.py`（仅接口对齐，禁删断言）

任何新增测试文件须在执行前 T0 记录中声明精确路径；未声明路径拒写。`tasks/queue/queue-status.json` 只可通过 writer 在隔离/验收流程中写入，卡面不得授权人工直改。

## 6. 禁止项

1. 禁改基线、v1 冻结参数、tracker、全局队列主表与其他工单卡。
2. 禁止降级裸写、第二写者、reconcile 自动修复、存量批量改写。
3. 禁止改 `dispatch-work-order.py` 现有参数，不得顺带重构派发流程。
4. 禁止实现 Autoloop 外挂或延后机制，禁止新增产品承诺。
5. 禁止 commit／push／tag，禁止调 18766，禁止访问 `H:\UltimaAI\UltimaAgentNext`。
6. 状态保持“待审卡”；未经过 Owner 与独立审计不得自称可开工。

## 7. 给执行端的粘贴模板

```text
工单：wo-ultimaagent-20261113-0061
T0：revision=<实测>；写域快照=<路径>
T1：inbox 边界=<PASS/FAIL>；证据=<路径>
T2：writer selftest=<退出码>；重复 claim_id=<结果>；原子失败保护=<结果>
T3：reconcile normal/duplicate/orphan=<逐项结果>；只读哈希=<结果>
T4：schema=<结果>；派发器参数差值=<结果>；writer 失败止损=<结果>
T5：唯一写者搜索=<原始输出路径>；回归=<命令与退出码>；越界=<无/说明>
状态声明：仅报告执行事实，不自行冻结、不改队列状态。
```

