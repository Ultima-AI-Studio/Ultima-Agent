# Codex 工单 · 0037 队列体检判据独立审计与修正

> 版本：v1.0 ｜ 状态：可开工 ｜ 适用工具：Codex
> 链路：`wo-ultimaagent-20261111-0037`
> 执行端：Codex（独立只读审计 + 有界修正，不经主脑判断）
> 前置：无（独立审计单，不依赖任何未冻结前置）
> 方案依据：`docs/plans/plan-ultimaagent-queue-doctor-criteria-audit-20261111.md`
> 锁定 revision：`9cfc7fa655747d205279dd4bfde13aae790fd650`
> 工作目录锁定：`H:\UltimaAI\UltimaAgent`
> 用法：按 T0→T4 顺序执行，每 T 的 Gate 全绿再进下一条，禁止跳序。

---

## 0. 本单定位

本单审的是**体检判据本身准不准**，不是队列里的数据对不对。

背景事实（可作为反例样本使用，无需重新发现）：2026-11-11 新增 `scripts/queue-doctor.py`，首跑报 92 条 P0。复核活跃窗口 12 条，**其中 10 条是判据造出来的假缺口**——本仓冻结 tag 大量采用语义命名（`ultimaagent-audit-hardening-20261108`、`ultimaagent-kws-user-entry-20261101`、`ultimaagent-middleware-v1-20261103` 等），而判据只认「tag 名以工单号开头」，把「已经打过」判成「没打」。后续虽已补了 note-token 兜底，但那只是补了**假阳性这一头**；**假阴性（现实不满足却判通过）从未被系统检查过**。

本单要求从两头夹：

- **假阳性**：现实已满足，判据报缺。会制造无用工作量，并让人不再信任体检结果。
- **假阴性**：现实不满足，判据报通过。会让真问题长期隐身。**这头更危险，优先审。**

---

## 1. 范围冻结

**本阶段只做**

1. 逐条枚举 `scripts/queue-doctor.py` 现行全部判据（P0 / P1 / LEGACY 降级各档），为每条写出：断言什么事实、用什么信号、该信号可否被伪造或漏读。
2. 对每条判据构造**假阳性样本**与**假阴性样本**各至少 1 例，样本必须来自真实仓数据或最小可复现夹具。
3. 把「按命名/按约定匹配」的判据改为「按事实存在」判定，并为每条判据输出 `evidence` 字段（说明它凭什么这么判）。无 evidence 的判据视为未实现。
4. 补齐 `scripts/tests/test_queue_doctor.py`，每条判据至少 1 正 1 负，本轮已知的 10 条假阳性必须成为回归用例。
5. 改造前后对全库各跑一次，输出对比账（消失项 / 新增项分别列出），新增项若为真问题必须如实保留，不得为凑数删除。

**本阶段不做（Non-goals）**

1. 不改 `tasks/queue/queue-status.json` 里任何业务数据，包括 `legacy` / `legacy_reason` / `state`。
2. 不放宽任何判据使 P0 归零。P0 数量是结果，不是目标。
3. 不改 `scripts/verify-order.py`、`scripts/verify-mechanism-change.py` 的任何判据。
4. 不改 `scripts/dispatch-work-order.py`、`scripts/freeze-work-order.py`、`scripts/validate_work_order.py`。
5. 不清理 18 张未入库卡、11 个孤儿 run 目录、4 条过期 blocked 理由——这些属数据处置，本单只负责把它们**判准**。
6. 不引入第三方依赖，不联网。

---

## 2. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `tasks/queue/runs/<本单 run>/criteria-inventory.md`（新增） | 现行判据逐条列出，无遗漏、无归并 |
| T1 | 同上文件追加反例段 | 每条判据正负样本各 ≥1，样本可复现 |
| T2 | `scripts/queue-doctor.py` | 全部判据带 evidence；命名类判据已改造 |
| T3 | `scripts/tests/test_queue_doctor.py`（新增） | 每条判据 1 正 1 负全绿；10 条已知假阳性被覆盖 |
| T4 | `tasks/queue/runs/<本单 run>/before-after.md`（新增）+ 本卡回填位 | 全库前后对比账完整；`--strict` 行为可解释 |

---

## 3. 任务明细

### T0 · 判据清单与信号可信度

**文件**：`tasks/queue/runs/<本单 run>/criteria-inventory.md`（新增，run 目录由派发器给出，不得自造）

**写什么**：

1. 以代码为准（不凭 `.md` 文档描述），逐条列出 `diagnose()` 内产生的每一个 issue 类型，按 P0 / P1 / LEGACY 降级分组。
2. 每条填四栏：断言的事实 / 使用的信号（具体到函数与字段） / 该信号在什么情况下会**误报** / 在什么情况下会**漏报**。
3. 明确标出哪些判据属于「按命名或约定的字符串匹配」（这是本单的主要嫌疑对象），哪些属于「按文件/进程/远端状态实测」。
4. 给出每条判据的**可证伪条件**：构造什么样本能让它必然报出、构造什么样本能让它必然沉默。

**验收（Gate T0）**：
- 判据条目数 == 代码中实际 issue 类型数（逐一对账，多一条或少一条都不合格）。
- 每条四栏均非空，无「待定」「视情况」等模糊表述。
- `FROZEN_WITHOUT_TAG`、`AUDIT_WITHOUT_RUN`、`STALE_BLOCKER`、`ORPHAN_RUN` 四条均存在可证伪条件，缺一即不合格。

**禁止**：不得按 `index.md`、`queue-status.json` 的字段名反推判据（那会正好复制判据自身的假设）。

---

### T1 · 反例枚举（本单核心）

**文件**：`tasks/queue/runs/<本单 run>/criteria-inventory.md`（追加「反例」段）

**写什么**：

1. 每条判据至少 1 个**假阳性**样本：现实已满足，判据仍报缺。样本必须写明具体工单号 / tag 名 / run 目录名，且可在当前仓复现。
2. 每条判据至少 1 个**假阴性**样本：现实不满足，判据仍报通过。构造方式二选一——真实仓中确有此情形，或用夹具造出该情形并说明构造方法。
3. 已知的 10 条假阳性（12 条活跃 P0 中除 0025、0028 外的部分，对应 `ultimaagent-audit-hardening-20261108` 等语义命名 tag）**必须**在表中出现，并标为「历史已发生」。
4. 对每条假阴性，写明它若长期隐身会造成什么后果（一句即可，不写方案）。

**验收（Gate T1）**：
- 每条判据正负样本各 ≥1，缺一即不合格。
- 假阳性样本中至少 5 条可当场用 `git tag --list` / `ls runs/` 复现并贴出命令与输出。
- 假阴性样本必须贴出实际运行**输出**证明判据在该样本下沉默，不接受推断。

**禁止**：不得只列假阳性就收工；不得用「理论上可能」代替实际样本。

---

### T2 · 判据改造

**文件**：`scripts/queue-doctor.py`

**写什么**：

1. 把所有「按命名/约定字符串匹配」的判据改为「按事实存在」判定。已知必改项：
   - tag 存在性：优先从该单的 run 证据（`runs/<order>/*/dispatch-record.json` 或冻结回执）中取实际 tag，再与 `git tag --list` 求交；note-token 兜底保留，但该结果必须标 `confidence: low` 并在输出中区分。
   - run 存在性：以 `runs/<order>/` 目录存在且含 `dispatch-record.json` 为准，不以 note 文本或 `audit_run` 字段空否为准。
   - blocked 理由过期：不得按关键词判过期，改为对该理由做「当前是否仍成立」的实测（例如理由声称存在未提交改动，就去查当前是否真有）；无法实测的理由输出 `unverifiable` 而非判过期。
2. 每条 issue 增加 `evidence` 字段：写明判定依据（命中的文件路径、tag 名、commit、命令输出摘要之一）。
3. 保持 CLI 契约不变：`--json` / `--strict` / `--out` 行为、退出码 0/1/2 语义，一处不得改。
4. 若某条判据经 T0/T1 审计后确认无法可靠判定，允许降级为 `unverifiable` 独立分类，但**不得直接删除判据**，且必须在 T4 对比账中列明。

**验收（Gate T2）**：
- 所有 issue 均带非空 `evidence`。
- `grep` 确认无「以工单号开头」这类前缀匹配逻辑残留在 tag 判定路径上。
- `--strict` 对同一仓、同一时刻的两次连续运行结果完全一致（无抖动）。
- 对 0025（有 tag）、0026（语义命名 tag）两张单，`FROZEN_WITHOUT_TAG` 报出条数 == 0，且 evidence 指向的真实 tag 名与 `git tag --list` 的 grep 输出一致。

**禁止**：不得通过放宽条件让某些单「消失」；任何一条判据变松，必须在代码注释中写明理由与代价。

---

### T3 · 用例与守护

**文件**：`scripts/tests/test_queue_doctor.py`（新增）

**写什么**：

1. 每条判据至少 1 条正向用例（该报则报）与 1 条负向用例（不该报则不报）。
2. 本轮 10 条已知假阳性全部转为回归用例（夹具化，不依赖真实仓状态漂移）。
3. `--strict` 退出码语义用例：有 P0 → 2，无 P0 → 0，运行错误 → 1。
4. `LEGACY_` 降级用例：同一问题在 legacy 单上落 P1、在活跃单上落 P0，且前缀正确。

**验收（Gate T3）**：
- `& H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest scripts/tests -o addopts= -p no:cacheprovider -q` 全绿。
- 执行「改回旧写法」命令后，对应负向用例 exit 非 0（反证用例真的在守）。

**禁止**：不得只测 helper 不测 `diagnose()` 主路径。

---

### T4 · 前后对比账与自证

**文件**：`tasks/queue/runs/<本单 run>/before-after.md`（新增）+ 本卡回填位

**写什么**：

1. 改造前基线：先对**未修改的**代码跑一次全库体检，结果落盘。
2. 改造后：同一仓、同一时刻跑一次，结果落盘。
3. 对比账三栏：**消失项**（判据改准后不再报的，逐条给原因）、**新增项**（改造后新暴露的真问题，逐条保留并标真/假）、**未变项**。
4. 结论一句话：现行判据还剩哪些已知不可靠，明确列出。

**验收（Gate T4）**：
- 前后两次运行的记录文件都存在，时间戳与 commit 可对。
- 消失项每条都有「为什么原来误报」的解释，不允许出现「调整后不再报」这类无因结论。
- 本卡回填：`## 回执` 段落填写 run 目录、commit、pytest 结果、前后 P0/P1 数。

**禁止**：不得先改后跑，必须在改之前留下真实基线。

---

## 4. 总验收

1. `python scripts/queue-doctor.py --json` 可解析，每条 issue 带 `evidence`。
2. `pytest scripts/tests` 全绿，且反向验证（改回旧写法必红）已做。
3. 全库前后对比账完整，消失项与新增项都可在仓内复核。
4. 判据清单中每条都有正负样本，无一条只有正向。
5. 数据未动：`git diff HEAD -- tasks/queue/queue-status.json` 为空。

---

## 5. 禁止清单

1. 不得改 `queue-status.json` 任何字段（含 `legacy`、`state`、`note`）。
2. 不得为让 P0 数字好看而放宽判据。
3. 不得改 `verify-order.py` / `verify-mechanism-change.py` / `dispatch-work-order.py`。
4. 不得 `git add -A`，提交必须显式列路径。
5. 不得在干净检出之外宣称验证通过；若本地通过而干净检出失败，按仓库缺口处理并如实上报。
6. 不得只做假阳性一侧就结单。

---

## 回执（执行端填写）

- run 目录：`tasks/queue/runs/wo-ultimaagent-20261111-0037-20261111T025942414734Z`
- commit：实现提交 `300ee2ec22d17f52de04fbf2917d00b2b60923e2`；T4 回执提交见该实现提交之后的本卡历史
- pytest：新增 `scripts/tests/test_queue_doctor.py` 27 passed；全量 `scripts/tests` 104 passed in 7.25s；旧前缀逻辑反向验证 10 failed、exit 1，恢复后全绿
- 改造前 P0/P1：`0 / 153`（`before.json`，`--strict` exit 0）
- 改造后 P0/P1：`2 / 221`（`after.json`，`--strict` exit 2；两条 P0 为 0019/0020 缺机器可读审计 run 的新暴露真缺口）
- 仍不可靠的判据：`CARD_MISSING` 未核卡内身份；note-token tag 兜底仅 `confidence=low`；缺 `dispatch-record.json` 的历史/独立 run 归属只能 `unverifiable`；`STALE_BLOCKER` 除 clean-tree 外多数理由无机器探针；`VIEW_DRIFT` 仍依赖 renderer 自身覆盖面；`LEGACY_` 继承对应基础限制。详见本 run 的 `before-after.md`。
