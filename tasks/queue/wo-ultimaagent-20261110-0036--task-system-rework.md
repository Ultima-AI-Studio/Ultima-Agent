# Codex 工单 · 0036 任务系统改造（队列 / 派发 / 校验 / 审计 / 冻结核收敛）

> 版本：v1.0 ｜ 状态：可开工 ｜ 适用工具：Codex
> 链路：`wo-ultimaagent-20261110-0036`
> 前置：方案已落档并冻结（`docs/plans/plan-ultimaagent-task-system-rework-20261110.md`）
> 执行端：Codex
> 方案依据：`docs/plans/plan-ultimaagent-task-system-rework-20261110.md`
> 锁定 revision：`90a4a9d563cb9321211e8eebd24adcd83800d2b0`
> 工作目录锁定：`H:\UltimaAI\UltimaAgent`
> 用法：按 T0→T7 顺序逐条执行，Gate PASS 并冻结后再进下一条，禁止跳序、禁止并行改写域。

---

## 0. 本单定位

本单改造的是「任务系统自身」，不是任何一张业务工单。目标是把队列卡 + 派发 + 确定性校验 + LLM 审计门 + 冻结打 tag 这一套，收敛成可长期运行的干净内核：状态有唯一权威源、门禁定义与真实仓库状态相容、每个脚本职责单一、遗留件清理干净、端到端双路径可复现。

**不新增功能**。所有改动只为消除需求 §2 记录的七类结构性问题。

---

## 1. 范围冻结

**本阶段只做**
1. 建一份 JSON 状态权威源，一次性导入现状，两张 Markdown 表改为脚本派生只读视图。
2. 名额判定改读 JSON，不再依赖人工维护的 markdown 字段。
3. 重定义冻结门：只校验本单写域内干净，并加反向防漏（实际改动路径 ⊆ 写域白名单）。
4. 审计判定去掉固定字符数否决，改为全文注入 + 对象边界拆分 + sha256 字节对账 + 可枚举覆盖清单。
5. 派发前增加卡面结构性自洽检测（互斥 Gate 类矛盾可拦）。
6. 4 个冻结脚本归一为单入口；`tasks/queue/dispatch-wo-*-now.py` 与 `tasks/queue/dispatch-*-prompt.txt` 全部归档（数量以归档前实测为准，卡面不写死）。
7. `S-REVIEW.max_tokens` 由 4096 提到不低于 8192。
8. 端到端双路径复现，改造前后两档留证。

**本阶段不做（Non-goals）**
1. 不改 G-TASKFLOW-001 七环节定义。
2. 不改 `AUDIT_SLOT_LIMIT` 默认值 2。
3. 不放宽任何门禁为「跳过」，不允许 `check=False` 式降级。
4. 不引入第三方编排框架，不装新外部服务。
5. 不动 UltimaManager 作为可选监督工具的定位。
6. 不清理仓库里既有的未提交条目（数量以 T0 快照实测为准，卡面不写死具体数字；本单开工前实测为 porcelain 565 条，排除本单三个输入文件后 562 条），本单只让门禁与之相容。
7. 不重审、不改判 0030 / 0033 / 0035，迁移按磁盘实际状态直接落库。
8. 不改 `src/host-shell`、`Topo Backup`、`data`、`logs`、`models`、`TTS`、`dist`、`Temp`、`legacy-topo`、`tools`、`libs`、`artifacts`、`bin`、`obj` 下任何内容。

---

## 2. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `tasks/queue/runs/<本单 run>/baseline-snapshot.json`（新增） | 快照字段齐全、零状态源与判定逻辑改动、可复核 |
| T1 | `tasks/queue/queue-status.json`（新增）+ `scripts/render-queue-views.py`（新增）+ `scripts/dispatch-work-order.py` + `scripts/verify-order.py` | 0030/0033/0035 落库值与裁决一致；两表标「勿手改」；名额判定无 markdown 文本依赖 |
| T2 | `scripts/freeze-work-order.py` | 写域内非空即拒、越界即拒、写域外既有条目不参与判定（数量取 T0 实测） |
| T3 | `scripts/audit-work-order.py` | `incomplete` 仅在注入字节 < sha256 字节时成立；`visible` 可枚举 |
| T4 | `scripts/validate_work_order.py` | 已知自洽单命中 0；构造的互斥 Gate 样本被拦下 |
| T5 | `scripts/freeze-approved-v01.py`、`scripts/freeze-approved-v03.py`、`scripts/freeze_work_order.py`、`tasks/queue/dispatch-wo-*-now.py`、`tasks/queue/dispatch-*-prompt.txt` | 只留单名冻结入口；归档后正式目录无遗留；下划线孪生名不再共存 |
| T6 | `src/brain/slot_adapter.py` | `S-REVIEW.max_tokens` ≥ 8192 生效；work_order 阶段长输出不截断 |
| T7 | `tasks/queue/runs/<本单 run>/`、`docs/plans/plan-ultimaagent-task-system-rework-20261110.md`、本卡回填位 | DoR 通过 `validate_work_order.py`、机检通过 `verify-order.py`、双路径可复现、两档不一致已上报 |

---

## 3. 任务明细

### T0 · 基线快照（只读，不改任何判定逻辑）

**文件**：
1. `tasks/queue/runs/<本单 run>/baseline-snapshot.json`（唯一新增产物，路径由执行端定并回填本卡）
2. 不改动任何既有 `.py` / `.md` / `.json` 文件

**写什么**：
1. 记录 `git rev-parse HEAD` 的完整哈希。
2. 记录四个脚本各自的 sha256 与字节数：`scripts/verify-order.py`、`scripts/validate_work_order.py`、`scripts/audit-work-order.py`、`scripts/freeze-work-order.py`。
3. 记录两张状态表的 sha256 与行数：`tasks/queue/index.md`、`H:\UltimaAI\_shared\queue\global-queue-index.md`。
4. 记录 `src/brain/slot_adapter.py` 中 `S-REVIEW` 的 `max_tokens` 生效值（改造前应为 4096）。
5. 留一个 `t3_cutover_commit` 占位字段，初值 `null`，在 **T3 完成后**回填其完成 commit——它是依赖环 B 的分界（改造期用旧门、验收期用新门）。口径以需求 §7.6 为准：分界点是 T3 完成 commit，不是 T2。
6. 快照文件里显式声明：本 T 不触碰任何状态源、不改任何判定逻辑。

**验收（Gate T0）**：
1. 执行 `python -c "import json,sys;json.load(open(sys.argv[1]))" <快照路径>`，输出无异常、exit 0，证明文件可被 `json.load` 解析。
2. 用 `python` 检查六个 sha256 字段，输出全部非空且为 64 位十六进制，命令 exit 0。
3. 读取 `max_tokens` 字段，输出值为 4096，与改造前基线一致。
4. 执行 `git status --porcelain -- <T0 写域>`，输出为空，即只新增快照文件、未修改既有文件。
5. 读取 `t3_cutover_commit` 字段，输出存在且值为 `null`。
6. 执行 `python -m pytest scripts\tests -o addopts= -p no:cacheprovider -q`，输出 6 failed / 45 passed，与基线一致。

**禁止**：
1. 禁止在本 T 内改动任何脚本、任何状态表、任何门禁逻辑。
2. 禁止把快照写成结论性判断（例如宣称某门禁「不可用」）。
3. 禁止顺手修其他 T 的问题。

**Gate 结果**：PASS（commit `9cf482051b90526cfb4d8ea7f067522f97189693`）；证据：`tasks/queue/runs/wo-ultimaagent-20261110-0036-20261110T162813293712Z/baseline-snapshot.json`。

### T1 · 状态单一权威源 + 双表派生 + 名额改读 JSON

**文件**：
1. `tasks/queue/queue-status.json`（新增权威源；**沿用 `tasks/queue/index.md` 表头已宣称的「状态聚合镜像 = queue-status.json」这个名字**——该名此前只被文档宣称、磁盘上并不存在，本单把它做实，不得另造第三个名字；schema 由执行端定并回填本卡）
2. `scripts/render-queue-views.py`（新增生成器，最终文件名可回填但须落在 `scripts/` 下）
3. `tasks/queue/index.md`（改为派生输出）
4. `H:\UltimaAI\_shared\queue\global-queue-index.md`（改为派生输出）
5. `scripts/dispatch-work-order.py`（名额判定数据来源）
6. `scripts/verify-order.py`（登记读取路径）

**写什么**：
1. 建 JSON 权威源，字段至少覆盖：工单号、state、audit_passed、派发时间、审计 run、冻结 commit、备注。
2. 一次性迁移：0030 → `blocked`；0033 → `audit_passed=true` 且 `state=blocked`；0035 → `audit_passed=true` 且 `state=blocked`；其余工单按磁盘实际状态原样导入（含本单自身当前的登记状态），逐单照搬，不重审、不改判。各 state 的计数以迁移前快照实测为准，**卡面不写死具体数字**——写死分布会让迁移 Gate 恒不可判。
3. 迁移前把两张 md 表原样另存带时间戳快照，写清回滚步骤（还原快照 + 删除 `queue-status.json`）。
4. 两表改为生成器输出，表头加「由脚本生成，勿手改」标注。
5. `dispatch-work-order.py` 的名额判定（`AUDIT_SLOT_LIMIT` 相关查表与降级分支）数据来源改为读 `queue-status.json`；限额默认值 2 不变。
6. `verify-order.py` 的登记读取改为读 `queue-status.json`。
7. 迁移须幂等：重复执行不产生重复行、不改变已落库值。

**验收（Gate T1）**：
1. 执行 `python -c` 读取 `queue-status.json`，输出 0030/0033/0035 三条的 state 与 audit_passed，与 §2 裁决逐字段一致。
2. 执行 `python -c` 统计全表 state，输出分布与迁移前快照实测的分布逐状态一致、差异为 0（卡面不写死具体计数，一律以迁移前实测为准）。
3. 重跑生成器后对两表与 `queue-status.json` 逐行对账，输出差异为空；任一表出现手工编辑痕迹即判 FAIL 并记录该行。
4. 迁移命令连续执行两次，第二次执行后 `git status --porcelain -- <迁移写域>` 输出未新增条目。
5. 把某单在 `queue-status.json` 中置为 `audit` 后执行名额判定，输出名额计数值变化（记录改前改后两个数），证明不再依赖 markdown 文本。
6. 执行 `git status --porcelain -- <T1 写域>`，输出为空。

**禁止**：
1. 禁止把 md 表继续当权威源，禁止双写。
2. 禁止改 `AUDIT_SLOT_LIMIT` 默认值。
3. 禁止借迁移重审 0030/0033/0035 或改其结论。
4. 禁止删除迁移前快照。

**Gate 结果**：PASS（commit `03d8df297e9a89d9ee9f51cef07bfc13dfd4e698`）；证据：`tasks/queue/runs/wo-ultimaagent-20261110-0036-20261110T162813293712Z/t1/pre-change.json`、`tasks/queue/runs/wo-ultimaagent-20261110-0036-20261110T162813293712Z/t1/post-change.json`。

### T2 · 冻结门重定义（写域内干净 + 反向防漏）

**文件**：
1. `scripts/freeze-work-order.py`（冻结前置判定）
2. `tasks/queue/runs/<本单 run>/baseline-snapshot.json` 只读、不改动（`t3_cutover_commit` 由 T3 回填，本 T 不得提前写入）

**写什么**：
1. 把「工作树必须全净」替换为「本单写域内干净」：判定命令为 `git status --porcelain -- <写域路径>`，非空即拒绝。
2. 增加反向防漏：冻结时校验「本单实际改动路径 ⊆ 写域白名单」，越界即拒绝——不得靠白名单漏写蒙混。
3. 写域外的未提交条目完全不参与冻结判定，包括 T0 快照实测到的全部既有条目（卡面不写死数量，一律以 T0 实测为准）。
4. 保留原 `audit_passed is True` 与拒绝 truncated 材料的要求，不减少判定强度。
5. 本 T 不触碰 `baseline-snapshot.json` 的 `t3_cutover_commit` 字段（由 T3 回填），只在 Gate 校验它仍为 `null`，证明 T2 没有越界提前切换分界。

**验收（Gate T2）**：
1. 构造写域内存在未提交修改的样本后执行冻结，输出拒绝且 exit code 非 0。
2. 构造「写域内干净、写域外存在与 T0 实测同量级脏条目」的样本后执行冻结，输出放行并记录冻结 commit，证明与真实仓库状态相容。
3. 构造实际改动路径中有 1 条不在白名单的样本后执行冻结，输出拒绝并记录越界路径。
4. `audit_passed is not True` 的单执行冻结，输出拒绝（未减少判定强度）。
5. truncated 材料执行冻结，输出拒绝。
6. 读取 `t3_cutover_commit` 字段，输出仍为 `null`，证明 T2 未提前回填该分界。

**禁止**：
1. 禁止放宽为跳过检查。
2. 禁止把写域外的条目纳入冻结判定。
3. 禁止改动 `verify-order.py` 的判定逻辑（只允许 T1 已改的读取路径）。

**Gate 结果**：PASS（commit `fbd685659f1c36a735281710161d7b52cb078c8f`）；证据：`tasks/queue/runs/wo-ultimaagent-20261110-0036-20261110T162813293712Z/t2/pre-change.json`、`tasks/queue/runs/wo-ultimaagent-20261110-0036-20261110T162813293712Z/t2/post-change.json`。

### T3 · 审计判定去常量依赖

**文件**：
1. `scripts/audit-work-order.py`（`CARD_INJECTION_LIMIT` / `EVIDENCE_INJECTION_LIMIT` 相关判定链、`incomplete` / `visible` 判定）
2. `tasks/queue/runs/<本单 run>/baseline-snapshot.json`（回填 `t3_cutover_commit`）

**写什么**：
1. 注入被审对象完整内容，不再按固定字符数截断。
2. 单对象超模型输入上限时，按对象边界拆分注入，并要求执行端为每个对象提供 sha256。
3. `incomplete` 仅在「实际注入字节 < 该对象 sha256 对应字节」时成立，且须附具体缺项清单。
4. `visible` 不再等于 `not incomplete` 的裸否定，须给出可枚举的覆盖清单。
5. 保留两轮同身份模型、两轮都须 PASS 的既有结构，不减少轮次。
6. 本 T 完成 commit 回填进 T0 快照的 `t3_cutover_commit` 字段——这是依赖环 B 的正式切换点（以需求 §7.6 为准，分界是 T3 完成 commit）。

**验收（Gate T3）**：
1. 用一个 12,000–40,000 字符之间的被审对象执行审计，输出 `incomplete` 为空、`visible` 为可枚举清单——修复 0033 那类死结。
2. 用一个超模型输入上限的对象执行审计，输出按对象边界拆分的记录，缺项清单计数可枚举到具体对象名。
3. 构造「注入字节 < sha256 字节」样本执行审计，输出 `incomplete` 成立且缺项指向该对象。
4. 检查 `visible` 输出类型，为列表或含明细字段的结构，非单个布尔。
5. 用 0033 / 0035 两个既有 run 离线重放，输出结论与改造前一致，或差异项逐条记录并说明。
6. 比对 `t3_cutover_commit` 值与本 T 完成 commit，输出一致。

**禁止**：
1. 禁止保留「超固定字符数即否决」。
2. 禁止把 `visible` 写成 `not incomplete` 的裸否定。
3. 禁止减少审计轮次或放宽 PASS 条件。

**Gate 结果**：PASS（T3 切换 commit `26bcb9dc26659ae11a7986ef4bb4522ba8103842`；后续元数据提交仅回填该既成 hash）；证据：`tasks/queue/runs/wo-ultimaagent-20261110-0036-20261110T162813293712Z/t3/pre-change.json`、`tasks/queue/runs/wo-ultimaagent-20261110-0036-20261110T162813293712Z/t3/post-change.json`。

### T4 · 卡面自洽性检测（派发前）

**文件**：
1. `scripts/validate_work_order.py`（新增结构性矛盾检测项）

**写什么**：
1. 增加派发前静态检测，能识别互斥型 Gate 矛盾（例如「要求恰 N 条 X」与「要求已完成提交」这类不可能同时成立的两条）。
2. 检测项清单由执行端回填（至少覆盖 0035 T7 那一类：状态差分条数断言 与 完成提交断言 互斥）。
3. 检测结果为报错/警告分级输出，不静默通过。
4. 不得把检测结果写成自动改写卡面。

**验收（Gate T4）**：
1. 用 `tasks/queue/wo-ultimaagent-20261110-0035--voice-baseline-split.md` 执行检测，输出报出 T7 的互斥项并含具体条目定位。
2. 用 `tasks/queue/wo-ultimaagent-20261110-0036--task-system-rework.md` 与 `tasks/queue/wo-ultimaagent-20261110-0033--card-form-unify.md` 执行检测，输出命中计数为 0。
3. 执行 `grep` 检测项清单，输出行数 ≥ 1，证明清单在文件内可枚举（常量表或注释）。
4. 检测前后比对输入文件 sha256，输出相同，证明检测不修改输入。

**禁止**：
1. 禁止把检测做成自动改写卡面。
2. 禁止为通过检测而放宽既有卡的 Gate 条件。
3. 禁止检测项过度泛化到会误伤合法卡的粒度（须以 0036 卡命中 0 为反证）。

### T5 · 脚本群收敛与归档

**文件**：
1. `scripts/freeze-approved-v01.py`（遗留，处置）
2. `scripts/freeze-approved-v03.py`（遗留，处置）
3. `scripts/freeze_work_order.py`（下划线孪生名，处置）
4. `tasks/queue/dispatch-wo-*-now.py`（19 个一次性脚本，归档）
5. `tasks/queue/dispatch-*-prompt.txt`（约 60 个快照，归档）
6. `tasks/queue/archive/20261110-0036/`（归档目录，新增，最终路径可回填）

**写什么**：
1. 4 个冻结脚本归一为单一入口，存活名保留 `scripts/freeze-work-order.py`（已在 T2 改造完成的那个）。
2. 其余三个移入 `tasks/queue/archive/20261110-0036/freeze-legacy/`，并在原位置留一行指向归档路径的说明文件，写清「已归档，勿使用」。
3. 全部 `dispatch-wo-*-now.py` 与全部 `dispatch-*-prompt.txt` 移入同一归档目录（本次归档为 move-only，不改内容），数量以归档前实测为准。
4. 归档后 `tasks/queue` 正式目录不得残留上述文件。

**验收（Gate T5）**：
1. 统计 `scripts/` 下冻结入口，输出计数为 1 且文件名为 `freeze-work-order.py`。
2. 枚举归档目录，输出 3 个冻结遗留 + 全部 `dispatch-wo-*-now.py` + 全部 `dispatch-*-prompt.txt`，计数与归档前实测记录一致（卡面不写死固定数字）。
3. 统计 `tasks/queue` 根目录 `dispatch-wo-*-now.py` 与 `dispatch-*-prompt.txt`，输出计数均为 0。
4. 比对归档前后同名文件 sha256，输出相同，证明归档是 move-only。
5. 执行 `python -m pytest scripts\tests -q`，输出仍为 6 failed / 45 passed，未新增失败。

**禁止**：
1. 禁止直接删除而不留归档与回滚路径。
2. 禁止保留仅差一个下划线的两个名字共存。
3. 禁止改动归档内容本身的语义。

### T6 · 主脑参数

**文件**：
1. `src/brain/slot_adapter.py`（`_DEFAULTS['S-REVIEW']['max_tokens']`）

**写什么**：
1. `S-REVIEW.max_tokens` 由 4096 改为 8192（下限）。
2. 若同时按阶段区分上限，任何阶段不得低于 8192。
3. 在改动处留一行注释写明实测依据：4096 时 `work_order` 阶段 `out_tokens` 触顶 4096、正文 7,300 字符在句中截断；8192 时同阶段正常收尾。

**验收（Gate T6）**：
1. 执行 `python -c "from src.brain.slot_adapter import review_settings;print(review_settings()['max_tokens'])"`，输出 ≥ 8192。
2. 重跑 `work_order` 单阶段，输出 `tokens.out` 不等于 4096 触顶值，且响应含 `VERDICT:` 收尾行。
3. 读取 `S-MAIN` / `S-EXEC` 默认值，输出与改造前一致，证明未改动。
4. 执行 `grep` 改动处注释，输出含实测依据行（含 4096 与 8192 字样）。

**禁止**：
1. 禁止把上限设成低于 8192。
2. 禁止按阶段区分时下探到 8192 以下。
3. 禁止改动 `S-MAIN` / `S-EXEC`。

### T7 · 端到端双路径复现与总验收

**文件**：
1. `tasks/queue/runs/<本单 run>/`（留证）
2. `docs/plans/plan-ultimaagent-task-system-rework-20261110.md`（确认已落档）
3. `tasks/queue/wo-ultimaagent-20261110-0036--task-system-rework.md`（本卡回填位）

**写什么**：
1. 回填 T0–T6 全部「待回填」项到本卡对应位置，回填后写域不得再扩大。
2. 跑端到端双路径：路径 A = 队列卡经 `scripts/validate_work_order.py` → `scripts/dispatch-work-order.py` → `scripts/audit-work-order.py` → `scripts/freeze-work-order.py`；路径 B = 存量已冻结单的冻结复现。
3. 每条 T 的机检按改造前版本与改造后版本各跑一次，两档结果都留证。
4. 两档判定不一致的，逐条显式上报并说明原因；未上报即视为该 T 未完成。
5. 产出本单验收报告，含逐 T Gate 结果、改动文件清单、越界声明。

**验收（Gate T7）**：
1. 执行 `grep` 本卡「待回填」字样，输出计数为 0。
2. 执行 `python scripts\validate_work_order.py tasks\queue\wo-ultimaagent-20261110-0036--task-system-rework.md --strict`，输出 PASS 且 exit 0。
3. 执行 `python scripts\verify-order.py tasks\queue\wo-ultimaagent-20261110-0036--task-system-rework.md`，输出 PASS。
4. 端到端双路径各跑通一次，输出两份 run 目录路径且均存在。
5. 并列展示改造前 / 改造后两档机检结果，差异项计数为 0 或逐条记录并说明。
6. 执行全量 `python -m pytest scripts\tests -q`，输出与基线一致，或差异项逐条记录。
7. 执行 `git status --porcelain -- <本单写域>`，输出为空。

**禁止**：
1. 禁止用「预计通过」替代实际运行输出。
2. 禁止跳过任一条 T 的 Gate 直接做 T7。
3. 禁止把两档不一致静默吞掉。
4. 禁止在 T7 内新增 T0–T6 写域之外的改动。

---

## 4. 执行须知

1. 本单是「改造任务系统自身」的元工单，改造对象包含正在验收本单的工具。为此 T0 只产快照，T1 起每 T 双档留证——这是需求 §7.5 的依赖环消解方案，不是可选项。
2. 写域按「文件路径 + 符号锚 + 改动意图」表述。执行端回填精确符号后，写域不得再扩大。
3. 遇到卡面与实际不符，先报再改，不得自行调整验收口径。
4. 每 T 完成后在本卡对应 T 下追加一行 Gate 结果与证据路径。
5. 卡面不写死任何易变的环境计数（`git status --porcelain` 条数、脚本个数、测试用例数、**队列各 state 的工单计数**等）。凡涉及数量处一律以迁移前 / T0 快照实测为准；实测值与卡面文字不一致时，以实测为准并在 T7 报告差异，**不因此停机**——写死计数当判据本身就是本单要消除的脆性。本单裁决只固定在 0030/0033/0035 三条的 `state`/`audit_passed` 取值上，其余工单逐单照搬磁盘现状。

---

## 5. 待回填位（执行端在 T7 前必须填齐）

1. `queue-status.json` 的最终路径与 schema 摘要。
2. `scripts/render-queue-views.py` 的最终文件名与调用方式。
3. 一次性脚本与提示词快照的归档目录最终路径。
4. 卡面自洽检测的检测项清单。
5. T0 快照文件路径。
6. `t3_cutover_commit` 值。
7. 各 T 写域内精确函数名 / 常量名。
