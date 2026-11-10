# Codex 工单 · 阶段2（G-TASKFLOW-001 工单契约机器可校验化 + 通用冻结门）

> 版本：v1.0 ｜ 状态：可开工（前置：0030 验收通过，WIP 已清零）｜ 适用工具：Codex（gpt-5.6-sol / reasoning=high）
> 链路：`wo-ultimaagent-20261108-0031`（承接审计 `docs/reports/audit-module12-20261108.md` 模块2 P1+P2）
> 方案依据：`docs/plans/agent-m2-workorder-contract-plan-20261108.md`（G-PLAN-001，方案随单落盘）
> 工作目录锁定：`C:\Users\Administrator\.codex\worktrees\ultimaagent-m2-workorder-20261108`
> 锁定 revision：commit `163df2c0b044945b01ebd395cb2743bb3676eda9`，分支 `codex/m2-workorder-contract-20261108`
> 执行端：`H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe`（Python 3.13.16），禁止默认 Python312
> 用法：按 T0→T4 顺序逐条执行，每 T 的 Gate PASS 后提交再进下一条；**不自判通过**，最终判「待独立复审」

---

## 0. 范围冻结

**本阶段只做**

1. 新建 `docs\specs\work-order.schema.json`（JSON Schema draft 2020-12），把 `tasks\queue\wo-*.md` 工单卡结构固化为可机校验契约。
2. 新建 `docs\specs\work-order-contract.md`，人读契约 + 与老 `tasks\queue_engine\card_contract.py` 体系的边界说明。
3. 新建 `scripts\validate_work_order.py`：校验任意 `wo-*.md`，输出 PASS/FAIL + 错误清单 + JSON 报告。
4. 在 `scripts\dispatch-work-order.py` 派发前接 DoR 硬门，加 `--skip-dor` 逃生阀并强制留痕。
5. 新建 `scripts\freeze_work_order.py`：把 `freeze-approved-v01.py` / `v03.py` 抽象为参数化通用冻结门，行为口径对齐前两者。
6. 配套测试与结果报告。

**本阶段不做（Non-goals）**

- 不改 `tasks\queue_engine\card_contract.py` 的 `validate_card` / `check_version_gates`，老 `tasks\cards\` 体系保持原样，两套并存。
- 不改任何存量 `wo-*.md` 工单卡正文（存量卡只作正向回归样本；若与 schema 冲突，**改 schema 不改卡**）。
- **不真正打 git tag**：T3 只交付实现并跑 `--dry-run`，实打 tag 由主脑/Owner 在验收后执行。
- 不恢复 18766 登记接口、不改 `GlobalQueueRegistrar`、不改 `queue.py` 与 0030 已验收的 `src\brain\orchestration\ledger\**`。
- 不改 `docs\tracker\北极星上线任务清单.html` 与 `scripts\tracker-live.py`（主脑专属写权）。
- 不改 `H:\UltimaAI\UltimaManager` 下任何文件（只读参照）。
- 不引入新的第三方依赖；schema 校验用已装的 `jsonschema 4.26.0`，YAML 用已装的 `PyYAML 6.0.3`，解析 md 用标准库。
- 不跑全量 pytest（基线缺未提交的 `__init__.py` / `registry.py`，全量必红）；只跑本单新增测试与指定回归集，并如实声明。

---

## 1. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `docs\specs\work-order.schema.json`、`docs\specs\work-order-contract.md` | schema 通过 `jsonschema` 自校验；契约文档四层字段齐全 |
| T1 | `scripts\validate_work_order.py`、`tests\test_validate_work_order.py` | 存量卡 ≥6 张全部 PASS；4 类负样本全部 FAIL 且定位到行 |
| T2 | `scripts\dispatch-work-order.py`（小改）、`tests\test_dor_gate.py` | 负样本派发被拒 exit=2 且无 run 目录；`--skip-dor` 留痕 |
| T3 | `scripts\freeze_work_order.py`、`tests\test_freeze_work_order.py` | dry-run 对 0030 输出完整 gate JSON，`git tag --list` 前后一致 |
| T4 | 总验收 | 全部新增测试绿 + 本工单卡自身过 validator + stage2-frozen 报告 |

---

## 2. 任务明细

### T0 · 工单卡契约冻结

**文件**：
- `docs\specs\work-order.schema.json`（新建）
- `docs\specs\work-order-contract.md`（新建）

**写什么**：
1. schema 用 JSON Schema draft 2020-12，`$id` 设为 `https://ultima.local/schemas/work-order.schema.json`，`title` 写明"UltimaAgent wo-*.md 工单卡契约 v1"。
2. 定义四层字段：L1 头部（`title` 前缀 `# Codex 工单 · `、`version`、`status`、`tool`）；L2 锁定（`link`、`prereq`、`workdir`、`revision`、`usage`、`plan_ref`、`runtime`）；L3 骨架（`scope_do`、`scope_not_do`、`task_table`、`task_details`）；L4 明细（每 T 四段 `files` / `writes` / `gate` / `forbidden`）。
3. `status` 枚举：`可开工`、`排队中`、`待开工`、`已冻结`、`已完成`；派发态子集另在契约文档中说明由 validator 强制。
4. `revision` 用正则 `^[0-9a-f]{7,40}$` 约束。
5. 契约文档写清：四层字段含义、跨层一致性规则（T 集合相等、编号连续、Gate 必须含可验证动词、`scope_not_do` 不得为空）、与 `card_contract.py` 的边界（老体系管 `tasks\cards\`，新契约管 `tasks\queue\wo-*.md`）、以及 schema 与 validator 的分工（schema 管结构，validator 管跨层语义）。
6. 契约文档末尾附"存量卡兼容策略"：以 schema 迁就存量为原则，逐条列出为兼容存量而放宽的规则及理由。

**验收（Gate T0）**：
1. `python -c "import json,jsonschema; s=json.load(open(r'docs\specs\work-order.schema.json',encoding='utf-8')); jsonschema.Draft202012Validator.check_schema(s); print('OK')"` 输出 OK。
2. `work-order-contract.md` 四层字段逐层出现，`##` 小节数 ≥5。
3. 契约文档列出 ≥6 张存量卡名与各自的兼容处理结论。

**禁止**：
- 不把 schema 写成"仅供参考"的注释性文档；必须是可被 `jsonschema` 直接加载的合法 schema。
- 不引入 `$ref` 外部文件（单文件自包含）。
- 不定义本单不校对的字段（避免 schema 与 validator 两张皮）。

---

### T1 · validator 实现

**文件**：
- `scripts\validate_work_order.py`（新建）
- `tests\test_validate_work_order.py`（新建）

**写什么**：
1. CLI：`python scripts/validate_work_order.py <card.md> [--json] [--strict] [--schema <path>]`。
2. 对外接口：`validate(card_path, *, strict=False, schema_path=None) -> Report`，`Report` 含 `status`（`PASS`/`FAIL`）、`card`、`order`、`errors[]`、`warnings[]`；`errors` 每项含 `code`、`line`（能定位到时）、`message`。
3. 解析流程：读 md → 按 `^## ` 切段 → 解析 L1/L2 头部键值 → 解析任务清单表格行 → 解析每个 `### T# ·` 明细块的四段 → 组装 dict → 交 `jsonschema` 校验结构 → 再跑跨层语义校验。
4. 跨层语义校验（schema 表达不了，必须实现）：T 集合相等、T 编号从 T0 连续无跳号、每条 Gate 非空且含可验证动词（`pytest`/`命令`/`==`/`!=`/`差异`/`PASS`/`输出` 等）、`scope_not_do` 非空、`files` 段每条至少含一个路径特征（`\` 或 `/` 或 `.py` 或 `.md` 或 `.json`）、`status` 在派发态子集内（该检查由调用方按场景开关，默认开启但 `--no-dispatch-status` 可关）。
5. 错误码用字符串常量表（如 `E_MISSING_SECTION`、`E_T_SET_MISMATCH`、`E_T_NUMBER_GAP`、`E_GATE_WEAK`、`E_NO_FORBIDDEN`、`E_STATUS_NOT_DISPATCHABLE`、`E_REVISION_FORMAT`、`E_NO_PLAN_REF`），便于测试断言。
6. 退出码：PASS=0，FAIL=1；`--json` 时 stdout 只输出 JSON（人类可读信息走 stderr）。
7. 无网络、无文件写入、无副作用；import 时不执行任何 IO。

**验收（Gate T1）**：
1. `pytest tests\test_validate_work_order.py -o addopts= -q` 全绿，用例数 ≥8。
2. 对 `tasks\queue\` 下全部现存 `wo-*.md`（≥6 张）逐个跑 validator，**全部 PASS**，结果写入 `docs\reports\wo-ultimaagent-20261108-0031-t1-regression.json`（每张卡的 order/status/errors/warnings）。
3. 4 类负样本（临时造在 `tests\fixtures\` 或 tmp_path）全部 FAIL，且 `errors` 里能定位到具体行号或具体 T 号：①删掉"不做"节；②任务清单 T 集合与明细不一致；③某 T 缺 `**禁止**`；④`status` 写成 `执行中`。
4. `--json` 输出可被 `json.loads` 解析，且 `status` 字段与退出码一致。

**禁止**：
- 不修改任何存量 `wo-*.md` 让它们"变合规"。
- 不把校验降级成"只检查文件存在"。
- 不在 validator 里硬编码某张特定卡的名字或内容。
- 不用 `try/except: pass` 吞掉解析异常（异常必须转成 `errors` 项）。

---

### T2 · 派发前 DoR 硬门

**文件**：
- `scripts\dispatch-work-order.py`（小改，只加 DoR 接线与 `--skip-dor`）
- `tests\test_dor_gate.py`（新建）

**写什么**：
1. 在 `main()` 里解析出工单号与卡路径后、真正起 `codex` 进程前，调用 `validate_work_order.validate(card_path)`。
2. FAIL 且未给 `--skip-dor`：打印完整 errors（含 code/line/message），`exit 2`，**不得创建 run 目录、不得写 dispatch-record.json、不得起进程**。
3. 给 `--skip-dor`：放行，但 `dispatch-record.json` 必须新增 `"dor_skipped": true` 与 `"dor_errors": [...]`（原样记录），便于事后审计。
4. PASS 时 `dispatch-record.json` 新增 `"dor_status": "PASS"`。
5. 卡路径解析顺序：优先 `tasks\queue\<order>*.md`（用 order 前缀 glob，取唯一命中；多命中即报错），其次显式 `--card`。
6. 不改动原有 lock、run 目录命名、codex 参数、状态推进逻辑。

**验收（Gate T2）**：
1. `pytest tests\test_dor_gate.py -o addopts= -q` 全绿，用例数 ≥5。
2. 负样本卡派发：`exit=2`，且 `tasks\queue\runs\<order>` 下**未新增**目录（前后目录数一致）。
3. 正样本卡 + `--dry-run-dor`（或等价测试钩子）：能走到"将派发"分支且 `dor_status=PASS` 被写出（测试用临时目录，不真起 codex）。
4. `--skip-dor` 路径：`dor_skipped=true` 且 `dor_errors` 非空被记录。
5. 原派发流程的行为差异说明写进结果报告（列出新增字段与新增退出码 2）。

**禁止**：
- 不得把 DoR 检查做成"警告继续跑"。
- 不得在 `--skip-dor` 时静默跳过而不写记录。
- 不得改动 `dispatch-work-order.py` 里与状态机、lock、run 目录相关的既有逻辑。
- 不真起 `codex.exe` 做验收（测试必须能离线跑完）。

---

### T3 · 通用冻结门

**文件**：
- `scripts\freeze_work_order.py`（新建）
- `tests\test_freeze_work_order.py`（新建）

**写什么**：
1. CLI：`python scripts/freeze_work_order.py --order <wo-xxx> --baseline <sha> --tag <tag> --evidence "<glob>" [--gate-json <path>] [--dry-run] [--approve-text "<owner 原话>"] [--known-limit "<文本>"]`。
2. 校验链按顺序，任一失败即 `exit 3` 并打印失败项：
   - `git rev-parse HEAD` == `--baseline`
   - `git diff --name-only` 为空、`git diff --cached --name-only` 为空
   - `git tag --list <tag>` 为空
   - `--evidence` 每个 glob 命中的文件全部存在且非空
   - 命中的 `*.json` 里若存在 `status` 字段须为 `PASS`，若存在 `all_technical_pass` / `all_*pass` 须为 `true`（大小写不敏感匹配 `pass`/`true`）
3. 生成 gate JSON：`{gate, decision, approved_by, approved_at, order, baseline_commit, evidence:[{path,sha256}], approval_text, scope, known_limit, schema_version}`，写入 `tasks\queue\gates\<tag>.json`。
4. `--dry-run`：只打印将执行的动作清单与 gate JSON 全文到 stdout，**不写文件、不打 tag**。
5. 非 dry-run：写 gate JSON 后 `git tag -a <tag> <baseline> -m "<message 含 gate json sha256>"`（用 `subprocess` + `creationflags=0x08000000`，与本仓既有脚本一致），打完后断言 `rev-parse <tag>^{}` == baseline。
6. 与 v01/v03 的口径对照表写进结果报告：逐项列出"v01/v03 做了什么 / 本脚本对应哪个参数或默认行为"。

**验收（Gate T3）**：
1. `pytest tests\test_freeze_work_order.py -o addopts= -q` 全绿，用例数 ≥6。
2. 对 0030 的 worktree 跑 dry-run：`--order wo-ultimaagent-20261108-0030 --baseline a4d968af... --tag test-dryrun-only --evidence "docs\reports\wo-ultimaagent-20261108-0030*" --dry-run`，输出含完整 gate JSON；执行前后 `git tag --list` 完全一致（无新增）。
3. 负面用例：baseline 不符 → exit 3；tag 已存在 → exit 3；证据缺失 → exit 3。三条各有用例。
4. `--dry-run` 下确认 `tasks\queue\gates\` 目录**未新增文件**（前后文件数一致）。
5. 对照表覆盖 v01/v03 的全部关键断言（≥6 项）。

**禁止**：
- 不得在本单执行期间真打任何 tag（验收只用 `--dry-run`）。
- 不得删除或修改 `freeze-approved-v01.py` / `v03.py` / `readback-approved-v01.py` / `readback-approved-v03.py`。
- 不得把 `--dry-run` 实现成"先写后删"。
- 不得在 gate JSON 里伪造 `approved_by`（必须来自 `--approve-text` 或默认标注 `owner` 且 `approval_text` 如实记录）。

---

### T4 · 总验收

**文件**：
- `docs\reports\wo-ultimaagent-20261108-0031-result.md`（新建）
- `docs\reports\wo-ultimaagent-20261108-0031-t1-regression.json`（T1 产出）

**写什么**：
1. 结果报告按六段写：范围与改动清单 / 各 T Gate 逐项结果（含命令与输出摘要）/ 正负样本矩阵（卡 × 结论 × 错误码）/ 与 v01/v03 冻结门口径对照表 / 越界声明 / 已知限制。
2. 已知限制必须写：基线缺未提交 `__init__.py` / `registry.py` 导致全量 pytest 红，本单只跑指定范围；未真打 tag；未改存量卡；schema 为兼容存量放宽了哪些规则。
3. 越界声明：明确写"无"，或列出实际越界项与原因。

**验收（Gate T4）**：
1. 本单新增测试全绿：`pytest tests\test_validate_work_order.py tests\test_dor_gate.py tests\test_freeze_work_order.py -o addopts= -q`，passed 数与用例声明一致。
2. 0030 的 31 项 ledger 测试仍全绿（`pytest tests\test_ledger_schema_check.py tests\test_ledger_store.py tests\test_ledger_registrar.py src\brain\orchestration\tests\test_register_control_m29.py -o addopts= -q`）。
3. **本工单卡自身过 validator**：`python scripts\validate_work_order.py tasks\queue\wo-ultimaagent-20261108-0031--m2-workorder-contract.md` 输出 PASS（自举校验）。
4. 全量 `wo-*.md` 回归 JSON 存在且张数 ≥6、全部 PASS。
5. `git status --porcelain` 干净；提交数 ≥4（T0-T3 各一）；无删除测试（`git diff <baseline> HEAD --diff-filter=D --name-only` 为空）；无 `skip`/`xfail` 逃逸（新增测试文件内 grep 为空，测试函数名除外需在报告说明）。

**禁止**：
- 不伪报全量 pytest 通过。
- 不在报告里省略未做的项。
- 不把"计划要做"写成"已完成"。

---

## 3. 给编码代理的任务粘贴模板

```
T# <标题>：已完成，Gate 全绿
- 改动文件：<逐条>
- 验收命令与输出：<命令 + 关键输出行>
- 越界：无
```

总验收：

```
新增测试：<passed 数>
0030 回归：31 passed
本卡自举校验：PASS
存量卡回归：<N> 张全 PASS
git tag 前后一致：是
```

---

## 4. 验收要点

- [ ] 范围冻结内逐项完成，无越界（对照"本阶段不做"逐条核）
- [ ] 每 T Gate 全绿 + 自证完整（命令与输出，不接受"预计通过"）
- [ ] 关联文档同步：schema ↔ 契约 ↔ validator ↔ 报告四处口径一致
- [ ] 阶段报告产出 → 主脑独立复核 → 冻结

---

## 5. 开源替代排查（DoR 第 6 项 · G-OSS-001）【REVISE 补票 2026-11-08】

> 补票原因：派发时本卡缺此段，④ 准入判 DoR 第 6 项不满足。补写不涉及代码。
> verdict：`OSS_WRAPPER`　｜　checked_at：2026-11-08　｜　target：自研范围仅"按行切节取字段"一层

### 5.1 能力域与候选

| 子能力 | 候选 repo | License | 结论 |
|---|---|---|---|
| JSON Schema 校验 | `python-jsonschema/jsonschema` | MIT | **USE_OSS**（已用 4.26.0，venv 实测） |
| YAML 读取 | `yaml/pyyaml` | MIT | **USE_OSS**（已用 6.0.3，venv 实测） |
| Markdown 按行切节 | `executablebooks/markdown-it-py` | MIT | NO_OSS |
| 同上 | `lepture/mistune` | BSD-3-Clause | NO_OSS |
| 同上 | `jhamner/python-frontmatter` | MIT | NO_OSS |
| 工单卡模型校验 | `pydantic/pydantic` | MIT | NO_OSS |
| 同上 | `pyeve/cerberus` | ISC | NO_OSS |
| git tag 冻结 | `git` CLI | GPL-2.0 | **USE_OSS**（subprocess 调用） |

> 候选项未纳入依赖；stars 与 last_commit 未逐一联网核实（本单在离线环境执行）。License 取自各 repo 公开声明。

### 5.2 NO_OSS 的 why_not（点名到 repo）

- **markdown-it-py / mistune**：输出通用 AST，不保留"字段在第几行"。本 validator 每条错误必须带 `line`（`E_*` 报告契约），通用 parser 给不出行号，机检无法定位。
- **python-frontmatter**：只解析 `---` 包裹的 YAML front-matter。`wo-*.md` 用的是 `> 版本：…` 引用行 + `## 节` 结构，不是 front-matter，格式不匹配。
- **pydantic / cerberus**：用 Python 类或 dict 定义规则，无法直接加载 `docs/specs/work-order.schema.json`（draft 2020-12）。改用它们等于把已冻结的契约再翻译一遍，产生第二份真相，违反横切①单一权威源。
- **未自研 md parser**：切节取字段只用标准库 `re` 按行扫描（`validate_work_order.py` 内约 40 行），低于引入 AST 库的维护成本，不构成"自研能力"。

### 5.3 结论

- 校验引擎全部现成库：jsonschema（schema 校验）+ PyYAML（配置）+ git CLI（tag 冻结）。
- 唯一自写层是"按行切节取字段"，因通用库拿不到行号；why_not 已列，不触 G-OSS-001 反例清单。
- 无 `NO_OSS` 的能力域整体。

### 5.4 固定输出契约

`{domain, candidates[{repo, license, last_commit, stars}], verdict, target, why_not, checked_at}`

本条实例：`domain=work-order-contract`、`verdict=OSS_WRAPPER`、`checked_at=2026-11-08`。

