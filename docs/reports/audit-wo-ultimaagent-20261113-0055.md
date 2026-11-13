# wo-ultimaagent-20261113-0055 · Next 设定基线独立审计

## 1. 结论

**有条件 PASS**。

T1 结构 Gate 与 T3 树 Gate 通过；T2 的 10×7 矩阵、10 行判定和 4 组反向全文计数完整；T4 的 9 条抽验均已分类。审计发现 **4 个当前 MED**：2 个呈现件参数/口径冲突、1 个盘点同步口径缺失、1 个可机检性定义不足；另保留 **1 个 LOW 历史记录**。最高严重度为 **MED**，不存在 HIGH、结构性损坏或无法确定权威源的冲突，故不写无条件 PASS，也不触发停线。

“有条件”的含义仅是：在冻结前应按发现项补齐**判据/引用口径**并重跑相应审计；本报告不修改被审文件，也不替产品选择新参数。

## 2. 发现清单

| 编号 | 严重度 | 状态 | 位置 | 独立复核事实 | 证据 | 最小判据口径建议 |
|---|---|---|---|---|---|---|
| F-001 | LOW | 历史记录／已解除停线 | 工单旧 v1.0 行数硬值；当前工单 §0/T1 | 前轮因卡面写死 1525 行而停线；当前卡已改为脚本复算，T1 当前值 `line_count=1524`、LF。易变计数差异不再是结构停线项。 | `structure.json: line_count/eol`；当前工单 §0 第 1 项、T1 | 继续保持“行数由脚本复算，不在卡面写硬值”。 |
| F-002 | MED | 当前 | `docs/tracker/北极星架构树.html` L218 | 架构树把唤醒阈值写成现行 `0.25`；F1/F2/F5/F7 的 Next 当前口径均为 `0.30`，且其余 `0.25` 命中都能归为 v1、默认、历史或他参数。 | `t2_matrix.md` M2；反向 `0.25` 计数 10，其中真冲突 1 | 节点不自行固化第二份值；显示“Next 当前值从基线 §一回读”，并让展示与回读值一致。 |
| F-003 | MED | 当前 | `docs/tracker/next-基础能力架构-20261113.html` L292、L361–L373 | 同一页面先写主脑“不可换型”，后写“主脑可替换”及完整下拉/隐私闸/回滚口径；无法作为单一口径阅读。 | `t2_matrix.md` M8 | 把 L292 的判据收窄为“不可被 skill 指派／不登记进模型库”，主脑换型只引用该页 §09 与基线 §二十三。 |
| F-004 | MED | 当前 | `docs/plans/next-基础能力盘点与缺口清单-20261113.md` §1.2 L66 | 工单指定该行同步 M10，但只出现 Console 与 8756；未出现“与 `queue_engine` 同 pid、壳经 8756 读只读视图、四项调用=0”的完整门。没有相反值，属于引用件缺失。 | `t2_matrix.md` M10 | 在该格只增加对基线 §24.1 的完整 Gate 引用，或逐项列出同 pid／只读视图／四项=0；不新增产品值。 |
| F-005 | MED | 当前 | 基线 §15.7／§19.7／§24.5 各前 3 条 | 9 条中可直接稳定机检 2、需补夹具/范围/oracle 的半机检 6、依赖人工语义的不可机检 1；“可机检”标题不能证明判据已经可直接执行。 | `t4_gradability.md` 9 行分类及汇总 | 为半机检条目固化夹具 ID、扫描根/API 禁表、时钟和证据源；为“词义唯一”固定 5 个位置与正/禁词 oracle。 |

当前发现合计：**MED 4、LOW 1、HIGH 0**。T2 的不一致格为 **3**；F-005 是独立的 T4 可判定性发现，不重复计入 T2。

## 3. T1 · 结构审计

**PASS**。本轮按续行契约直接读取既有 `structure.json`，不重跑分析。

- 结构：24 章，编号严格 `1..24`；110 个二级节；章序、节序、跨章归属、附录位置、代码围栏、§18 连续性六项 Gate 全为 `true`。
- 附录：唯一“附录 A · 变更记录（全量）”位于 L1500；末章 §二十四标题在 L1438，附录在其后且为最后一个 `##`。
- §18 连续性：`18.1…18.8` 行号依次为 L959/L969/L991/L1004/L1029/L1038/L1045/L1049；18.8 后首个 `##` 为 §十九（L1064）。
- 待定词：14 个命中＝已有解释 9＋显式暂定 3＋运行时算值 2；无解释待定 0。
- 代码围栏：2 个，L846/L859，未闭合数 0。
- 文本：`line_count=1524`；EOL=LF（LF 1524、CRLF 0、CR 0）；UTF-8 文本 SHA-256=`f055aa60ebfbca07b0b261782ee45be0f1b64308c5ed9818104007d78e5f39b1`。

证据：`docs/reports/evidence/audit-0055/audit_structure.py`、`docs/reports/evidence/audit-0055/structure.json`。

## 4. T2 · 一致性矩阵

**证据 Gate PASS；内容不一致 3 处，最高 MED**。

- 10×7＝70 格，已填 70 格；10 个指标判定行齐备。
- 一致：M1、M3、M4、M5、M6、M7、M9，共 7 组。
- 不一致：M2、M8、M10，共 3 组／3 格，分别对应 F-002、F-003、F-004。
- 权威源之间无法选边的冲突 0；因此未触发停线条件 2。
- 注册分类文件作为 M8 补充源单独核对，未擅自扩成 10×8；其职责是 Tools/Skills/Plugins 分类，未复述 M8 整组参数不另计不一致格。

### 4.1 四组反向计数

计数范围固定为矩阵 F1–F7，UTF-8 全文逐行扫描，行内重复按出现次数计。

| 反向词 | 命中 | 历史/边界/他参数 | 真冲突 | 结论 |
|---|---:|---:|---:|---|
| `0.25` | 10 | 9 | 1 | F6 L218 为真冲突；其余是 v1 边界、外部默认、历史或 VAD 他参数。 |
| `1.5s` | 8 | 8 | 0 | 5 个他参数/pre-roll，3 个已作废历史冷却值。 |
| `11434` | 1 | 1 | 0 | 唯一命中明确写“不作主脑后端”。 |
| `250 MB`（含 `250MB`） | 9 | 9 | 0 | 均处于旧建议或 R-66/R-80 覆盖链。 |

完整证据：`docs/reports/evidence/audit-0055/t2_matrix.md`、`docs/reports/evidence/audit-0055/t2_matrix.json`。

## 5. T3 · 树与模块口径审计

**PASS**。本轮按续行契约直接读取既有 `tree.json`，不重跑分析。

- 节点：`node_count=113`、`raw_li_node_count=113`。
- 标签：`ul 29/29`、`li 113/113`、`div 144/144`；差值均为 0；`parser_errors=[]`。
- P1 主脑父链（深度 5）：`UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 1. Core（编排与裁决） → 主脑（可替换推理后端）`，不在“能力”组内。
- P2 五原则父链：五条均在 `本体 → 引擎 → 基础能力 → 治理与约束⑤ → 行为学原则` 下，叶节点深度 6；感官分工、理解先于行动、复述确认、记忆分层、不打扰与反馈闭环 5/5 通过。
- P3 三抽屉：`本体 → 引擎 → 外部能力（容器 · 三抽屉）` 的直接子节点为“能力库 Skill／插件 Plugin／模型库 Provider”；主脑正向条目 0。
- P4：任务库父节点为 Console；日志库父节点为治理与约束⑤。
- P5 温度三层链：`本体 → 引擎 → 基础能力 → 5. Memory → writer · poison_guard · store_backend · temperature_tier · volumes`；热 500MB、温 2GB、定值、冷路径可指定四项检查均为 true。
- A 三类／B 八块／C 七桶口径冲突数 0；`taxonomy_conflict_count=0`；总 Gate `gate_pass=true`。

证据：`docs/reports/evidence/audit-0055/audit_tree.py`、`docs/reports/evidence/audit-0055/tree.json`。

## 6. T4 · 可机检性抽验

**证据 Gate PASS；直接可执行性有 MED 缺口**。

| 抽验 | 可机检 | 半机检 | 不可机检 |
|---:|---:|---:|---:|
| 9 | 2 | 6 | 1 |

- 可机检：§24.5 的“Console/queue_engine 同 pid 与壳树 Console=0”、沙箱越界写拒绝＋审计有行。
- 半机检：§15.7 前 3 条、§19.7 前 2 条、§24.5 第 2 条，共 6 条；均有客观目标，但缺固定夹具、扫描范围、时钟或证据源。
- 不可机检：§19.7“词义唯一”抽查 5 处；原文没有固定样本和语义 oracle。

9 条原文、判定方法和最小判据改写见 `docs/reports/evidence/audit-0055/t4_gradability.md`。

## 7. T5 · 总验收与反向断言

| 验收项 | 结果 | 证据 |
|---|---|---|
| T1 结构 | PASS | `structure.json gate_pass=true`；24 章／110 节／附录 1／untriaged 0／围栏未闭合 0。 |
| T2 矩阵 | 证据 Gate PASS；内容有条件 | 70/70 格、10/10 判定、4/4 反向组；3 个 MED 不一致格。 |
| T3 树 | PASS | `tree.json gate_pass=true`；113 节点、标签平衡、5 组父链通过、三口径冲突 0。 |
| T4 可判定性 | 证据 Gate PASS；内容有条件 | 9/9 分类；2 可／6 半／1 不可。 |
| 总结论 | **有条件 PASS** | 当前最高严重度 MED；HIGH 0；结构停线项 0。 |

### 7.1 反向断言

- 8 份被审文件的 staged 与 unstaged `git diff --name-only` 均为空；精确路径 `git status --short --untracked-files=all` 也为空。
- 本单写入仅在 `docs/reports/audit-wo-ultimaagent-20261113-0055.md` 与 `docs/reports/evidence/audit-0055/**`；仓库其余既有脏项未整理、未覆盖。
- `tasks/queue/queue-status.json` 在开场已有既存修改；本单未读取、未写入，也不声称其 records 数得到本轮验证。
- 未 commit、未 push、未打 tag、未派发新工单、未访问或改动 `H:\UltimaAI\UltimaAgentNext`。
- 越界声明：无本单造成的写入域越界。

## 8. 未覆盖声明

1. **像素渲染**：未做像素级渲染验证。
2. **产品决策**：未判断产品取值对错，未在冲突项中自行选择新值。
3. **运行期实测值**：未现场实测 `sha256`、`n_ctx`、KWS 曲线或其他待到机/落盘值。
4. **Next 目录**：未访问、创建或改动 `H:\UltimaAI\UltimaAgentNext`。
5. **队列状态**：未验证或更新 `tasks/queue/queue-status.json`，也未复算其 records。

## 9. 交付物

- 主报告：`docs/reports/audit-wo-ultimaagent-20261113-0055.md`
- T1：`docs/reports/evidence/audit-0055/audit_structure.py`、`structure.json`
- T2：`docs/reports/evidence/audit-0055/t2_matrix.md`、`t2_matrix.json`
- T3：`docs/reports/evidence/audit-0055/audit_tree.py`、`tree.json`
- T4：`docs/reports/evidence/audit-0055/t4_gradability.md`
