# wo-ultimaagent-20261113-0058 · 值冲突收敛报告

> 状态：T1–T6 自检通过；独立复核无 Critical / Important；待 Owner 审阅  
> 执行日期：2026-11-13  
> 边界：不改 `config/voice-next/live.json`；不写 §二十五／§二十六；不访问或写入 `H:\UltimaAI\UltimaAgentNext`；不 commit / push / tag；不改队列状态。

## 0. 预检与裁定

- `docs/INDEX.md` 已先读；本单本地产品权威源为 `docs/specs/next-感知交互参数基线-20261113.md` 及卡片列出的配套文件。
- 停线章节核对：§14.1、§16.2、§16.4、§17.2.3 均存在且编号未变。§16.4 原为“运行态回读”，本单在该节内新增预算公式，未制造重复编号。
- 变更前目标文件 SHA-256：基线 `F055AA60EBFBCA07B0B261782EE45BE0F1B64308C5ED9818104007D78E5F39B1`；详解页 `7F812641D576EFF55805AF63AFA538B1184CC5044940CFC5EE835EF964030002`；架构树 `C01C512709377CE8367FFCEA44E148B41089AC47D353D8A1A9707D1DE20F82A8`；插件分类 `26BC9D0207A36A8213AAA3588FB729E38AE90E4FBBF86290EA8BE1619D0F2F97`；双域规范 `0F1A87AE45B8EA137F23050C9A9FA6D0999F94E9EB1D5C1CA71A0FA4A712D1B0`；v1 冻结文件 `2CACDE1D0DED2F700CAEF95BDB3C78B8154FE85C25EE68EE3B1FBB9519059ED3`。

| 裁定 | 选中案 | 依据 | 影响面 |
|---|---|---|---|
| D-04 | A：动态 `input_budget` | §16.2 的 4096 是 Owner 定值；动态预算可在不改冻结参数、不编造新目标值时消除溢出 | 基线 §16.4 的调用预算与回读解释；§16.2 数值不变 |
| D-05 | B：不保证不丢 | 全卷满/离线时没有持久介质；保守默认不得新增应急介质承诺 | 基线 §17.2.3 的 CAPACITY_ALERT 行为 |
| D-06 | B：根崩溃需用户重启 | §15.5 已接受 Job 收全树、下次登录恢复；A 会新增宿主重入机制承诺 | 架构树 Shell 自愈节点 `desc` |
| D-08 | A：单用户·单显示端，多端后置 v1.x | 0056 C-13 已给最小修法；保留节点但不声称当前已有消费者 | 架构树“多端调度”节点 `desc` |

## 1. T1 · E-02 上下文预算

### 改前

- 基线 §16.2 变更前 L748：`n_ctx = 4096`；§16.3 变更前 L773：输入预算 `4000`；profile 最大输出为 `512`。
- §16.4 只有 `/props` 回读，没有预算公式或 profile 量化表。
- RED 断言：`formula_present=False`、`five_col_present=False`、`conflict_math_present=False`。

### 改后

- §16.4.1 明确复算 `4000 + 512 = 4512 > 4096`，固定输入 `4000` 降为冲突事实，唯一生效公式为 `input_budget(profile) = n_ctx - max_output(profile) - template_overhead`。
- 五列表覆盖 `decision` / `dialog`；`template_overhead` 逐请求由真实 tokenizer 计数，不写死。
- A 案 `status=selected`；B 案 `status=rejected`，未实测内存增量与首 token 延迟记 `TBD-D04`；附录 A 已登记一行。
- §16.2 的 `n_ctx = 4096` 原行未改。

### 依据与影响

- 依据：工单 §0.1 裁定优先级、R-56/§16.2 既有定值、0056 E-02 的输入+输出溢出证据。
- 影响：调用层由固定输入上限改为按 profile/模板动态预算；不改变模型定值，不新增 v1 产品承诺。

### T1 Gate 证据

- GREEN：`formula_count=1`；`conflict_math_count=1`；`five_col_header_count=1`；`decision_row_count=1`；`dialog_row_count=1`。
- 互斥与定值：`d04_exact_count=1`；`a_selected_count=1`；`b_rejected_count=1`；`n_ctx_original_line_count=1`。
- 附录：`appendix_tbd_count=1`。
- 结论：`T1_GATE=PASS`。

## 2. 九条处置账本

| 编号 | 状态 | 改前 | 改后 | 依据 |
|---|---|---|---|---|
| E-02 | 已处置（T1） | 4000 输入 + 512 输出 > 4096 | §16.4 动态预算公式，D-04 选 A | §16.2 定值优先；保守不抬 `n_ctx` |
| E-03 | 已处置（T4a） | Middleware 节点把双层沙箱整体写在自身工具集 | Shell `desc` 明确负责 Job Object；Middleware `desc` 只保留平台无关 `fileDomain` | R-79 两层沙箱；跨端 Middleware 禁 Windows-only 依赖 |
| E-04 | 已处置（T2） | 全卷不可写仍承诺排队无丢失且审计照写 | D-05 选 B：不保证不丢，审计失败记唯一事件并继续服务 | 无持久介质不能保证队列/审计；禁止新增应急区承诺 |
| E-05 | 已处置（T3） | §14.1 单库硬顶/逐出/卸载清空与多卷无上限/保留互斥 | 三项历史值保留但各加 `[obsolete]`，分别指向 §17.2.3、§17.2.3、§16.1 | R-66 多卷模型、§16.1 默认保留为现行口径 |
| E-06 | 已处置（T4a） | 详解页两句把全部进程/Console 留在客户端域 | 壳与呈现在客户端域；Console/queue_engine 在 Python 引擎域同 pid | R-78/§24.1 迁域裁决 |
| E-07 | 已处置（T5a） | “任一插件可停”与渲染/安装不可缺互斥 | §三表新增 `lifecycle`，逐件映射三枚举；“任一可停”仅指 `disableable` | 运行必需、可停、仅安装期三种生命周期不可混用 |
| E-08 | 已处置（T4b） | “守护自愈”节点未区分子进程与 Shell 根进程 | D-06 选 B：仅子进程可恢复，根进程崩溃需用户重启 | §15.5 已接受根崩溃后全树退出；不新增宿主重入承诺 |
| E-09 | 已处置（T4c） | R-29 三职责与 §16 `decision` 五用途被并列解释为两套主脑职责 | 双域规范 §11.3.1 建 8 行唯一现行表；§16.5 旧表 obsolete 指向本表 | R-29 上位边界、R-34 外脑审/主脑只执行本地 tag |
| C-13 | 已处置（T5b） | 多端调度向多用户设备/显示端投递，但 v1 无消费者 | D-08 选 A：收窄为单用户·单显示端，多端后置 v1.x | 0056 C-13 最小修法；保留节点但不承诺当前多端能力 |

## 3. T2 · E-04 全卷满承诺

### 改前

- 基线 §17.2.3 变更前 L904：所有冷卷红或离线时仍写“采集排队（入库任务排队等待，不丢、不失败）”，同时要求检索与对话照常；0056 E-04 指出任务队列与审计追加都没有可写介质。
- RED：`old_phrase_count=1`、`selected_count=0`、`rejected_count=0`、`if_d05_count=0`、`journal_unavailable_full_doc_count=0`、`capacity_number_count=0`。

### 改后

- A 案 `status=rejected`：仅记录 `emergency_journal` 的触发/回灌流程，不给容量数字，不形成承诺。
- B 案 `status=selected`：逐字采用固定替换文本“采集任务排队等待，不保证不丢；审计写入失败记事件并继续服务”，事件统一为 `journal_unavailable`。
- `CAPACITY_ALERT` 行改为引用唯一 selected 分支；检索/对话与界面提示保持原规则。

### 依据与影响

- 依据：D-05 选 B；保守默认“不新增产品承诺”；所有卷不可写时不存在持久化队列与审计追加的物理条件。
- 影响：仅收窄全卷不可写时的保证；不修改水位、卷模型、检索延迟或 NAS 边界。

### T2 Gate 证据

- 首次检查发现 `CAPACITY_ALERT` 行重复写入字面 `status=selected`，导致节内 selected 计数为 2；根因是运行行重复了机器状态字段。最小修正为改写成“按本节已选 B 案处置”，A/B 块内容不变。
- GREEN 复跑：`old_phrase_count=0`；`selected_count=1`；`rejected_count=1`；`if_d05_count=2`；`a_block_capacity_number_count=0`；`b_block_capacity_number_count=0`；`fixed_text_count=1`；`journal_unavailable_full_doc_count=1`。
- 结论：`T2_GATE=PASS`。

## 4. T3 · E-05 容量与卸载口径

### 改前

- §14.1 变更前 L446：30k/60k 条与 150MB/300MB 被写成现行硬顶，超限逐出最旧；L460/L461 把硬顶逐出和卸载清空作为验收门。
- RED：`obsolete_count=0`、`arrow_count=0`、`hard_cap_current_line_count=2`、`uninstall_empty_count=1`。

### 改后

- 历史数值及旧验收行原位保留，但明确“作废，不生效”。
- 三条 `[obsolete]` 分别标记单库硬顶、库内删除、卸载门；每条恰一个 `→ §`，前两条指向 §17.2.3，卸载门指向 §16.1。

### 依据与影响

- 依据：R-66/§17.2.3 已用多卷模型取代单库硬顶；§16.1 规定用户数据/权重默认保留。
- 影响：只废止旧物理容量/删除/卸载门；SQLite/FTS5/向量后端技术、迁移校验与隐私门保留。

### T3 Gate 证据

- GREEN：`obsolete_count=3`；`obsolete_arrow_counts=1,1,1`；`obsolete_targets=17.2.3,17.2.3,16.1`。
- 章节与历史保留：`chapter_17_2_3_exists=True`；`chapter_16_1_exists=True`；`active_capacity_heading_count=0`；`historical_values_retained=True`。
- 结论：`T3_GATE=PASS`。

## 5. T4a · E-03 / E-06 拓扑与域

### 改前

- 架构树变更前：Shell“进程树托管”提到 Job Object，但 Middleware 工具节点仍把 `sandbox（双层：Job＋写域白名单）` 整体列入自身；其 `desc` 未限制为 `fileDomain`。
- 详解页变更前 L147：`进程全部在客户端域，引擎域零 Windows-only 依赖`；L238：`进程留在客户端域是刻意选择`。
- RED：`job_object_full_doc_count=1`、`middleware_filedomain_only_count=0`、`shell_process_sandbox_count=0`、`stale_all_client_count=1`、`new_l147_count=0`、`stale_l238_count=1`、`new_l238_count=0`。

### 改后

- Shell“进程树托管”节点 `desc`：`Shell 进程沙箱负责 Job Object`；Middleware 工具节点 `desc`：只保留平台无关 `fileDomain`，进程级沙箱归 Shell。
- 详解页两句分别改为：`壳与呈现在客户端域，Console/queue_engine 在 Python 引擎域同 pid`；`进程留在客户端域是刻意的——但仅指壳与呈现`。

### 依据与影响

- 依据：R-79 将进程级 Job 与目录级 `fileDomain` 分层；R-78/§24.1 已裁定 Console 与 `queue_engine` 同 pid。
- 影响：只收敛模块归属与两句域说明，不改端口、进程参数、八态或实现。

### T4a Gate 证据

- GREEN：`job_object_node_count=1`（节点行 233）；`shell_parent_anchor_line=228`；`job_node_has_shell_process_sandbox=True`；`middleware_filedomain_only_count=1`。
- 详解页：`stale_all_client_count=0`；`new_l147_count=1`；`stale_l238_count=0`；`new_l238_count=1`。
- 结论：`T4a_GATE=PASS`。

## 6. T4b · E-08 Shell 自愈

### 改前

- 架构树“守护自愈”节点只写 Guardian 探活与 `agent-server` 自动重启，未区分子进程恢复和根进程恢复；节点没有 D-06 或 A/B 状态字段。
- RED：`guardian_node_count=1`、`d06_count=0`、`selected_count=0`、`rejected_count=0`、`old_desc_count=1`、`selected_b_text_count=0`。

### 改后

- 同一 `desc` 中保留两案：A `status=rejected`（宿主重入拉起未采用）；B `status=selected`（仅子进程可恢复，根进程崩溃需用户重启）。
- Guardian 的既有 20s/3 次/300s 参数保留；未写基线任何章节。

### 依据与影响

- 依据：D-06 选 B；§15.5 已明确根壳崩溃时 Job 收全树、下次登录恢复。选 A 会新增尚未设计/实测的宿主重入机制承诺。
- 影响：删除根进程“常驻自愈”的暗示，只保留子进程恢复能力；不改 Guardian 参数。

### T4b Gate 证据

- GREEN：`guardian_node_count=1`；`d06_count=1`；`selected_count=1`；`rejected_count=1`；`a_text_count=1`；`b_text_count=1`。
- “常驻自愈”检查：拒绝块 0，选中块 0；没有把该词留在未选方案。
- 结论：`T4b_GATE=PASS`。

## 7. T4c · E-09 主脑职责

### 改前

- Owner 日志 R-29 定三类：查询、本地事务管理、汇报，并禁止方案拆解/验收/冻结判定；基线 §16 `decision` 又列意图判定、路由、工具参数、审计判定、摘要压缩五用途。
- 双域规范原无主脑职责表；基线 §16.5 三层表也没有替代链。
- RED：`unique_duty_table_heading_count=0`、`ownership_column_count=0`、`baseline_165_obsolete_pointer_count=0`、`r29_three_phrase_in_dual_count=0`。

### 改后

- 双域规范新增 §11.3.1 唯一现行表，8 行恰为 R-29 三项与 §16 五项的并集；每行都有“归属层（主脑/外脑/中间层）”。
- 路由归中间层，审计判定归外脑；意图/工具参数/摘要分别作为查询、本地事务、汇报的子项，主脑仍不做方案拆解、不验收、不签冻结。
- 基线 §16.5 原三层表就地标 `[obsolete → 本表]`，保留历史但不再作为职责定义。

### 依据与影响

- 依据：R-29 是既有上位职责边界；R-34 已定外脑审核、主脑只在审核 PASS 后执行本地 tag。
- 影响：统一职责判定来源；不改变 §16 profile 参数，不新增执行接口。

### T4c Gate 证据

- GREEN：`definition_heading_count=1`；`duty_union_row_count=8`；`ownership_column_count=1`；`rows_with_three_columns=8`。
- 归属分布：主脑 6、外脑 1、中间层 1；`baseline_165_obsolete_pointer_count=1`；`obsolete_arrow_to_table_count=1`。
- 结论：`T4c_GATE=PASS`。

## 8. T5a · E-07 插件生命周期

### 改前

- §三只有必装/选装与“停用后是否可降级”，没有逐件生命周期；必装行称渲染/安装不可缺，§四纪律又称任一插件停用后仍能跑。
- RED：`lifecycle_header_count=0`、三枚举计数均 0、`any_can_stop_limited_count=0`、`plugin_row_count=2`。

### 改后

- 仅在 §三插件表增加 `lifecycle` 列；必装 11、选装 9 与插件 ID 不变。
- 枚举严格为 `disableable` / `runtime_required` / `install_time_only`；表头同句限定“任一可停”仅适用于 `disableable`。
- 渲染/语音/SQLite 主链列为 `runtime_required` 并写明停用后健康门失败；Inno 安装器列为 `install_time_only`；其余可降级或选装件列为 `disableable`。

### 依据与影响

- 依据：E-07 要求逐件可判；运行期必需、可降级与只在安装事务中需要的组件生命周期不同。
- 影响：只增表列，不改插件数量、ID、安装档位或产品默认启用项。

### T5a Gate 证据

- GREEN：`lifecycle_header_count=1`；`plugin_row_count=2`；`lifecycle_nonempty_rows=2`；`six_column_rows=2`。
- 枚举与数量：`enum_set=disableable,install_time_only,runtime_required`；必装插件 ID 11；选装插件 ID 9。
- 限定与后果：`any_can_stop_limited_count=1`；`runtime_failure_consequence_count=1`。
- 结论：`T5a_GATE=PASS`。

## 9. T5b · C-13 多端调度

### 改前

- 架构树“多端调度”节点 `desc` 为“向多用户设备 / 显示端投递”，没有当前消费者、版本标记或 D-08 状态。
- RED：`multi_node_count=1`、`d08_count=0`、`selected_count=0`、`rejected_count=0`、`old_multiuser_count=1`、`v1x_count=0`。

### 改后

- A 案 `status=selected`：`单用户·单显示端（多端为 v1.x）`；B 案 `status=rejected`：移除节点并记附录 A（未采用）。
- 节点保留，`desc` 中 D-08 只出现一次；没有为 rejected 的 B 案写附录记录。

### 依据与影响

- 依据：D-08 选 A；0056 C-13 已给“v1 收窄单用户显示端”的最小修法，符合保守默认且不增加消费者假设。
- 影响：当前产品面只承诺单用户单显示端；多端能力明确后置 v1.x，不改执行端编排。

### T5b Gate 证据

- GREEN：`multi_node_count=1`；`d08_count=1`；`selected_count=1`；`rejected_count=1`；`old_multiuser_count=0`；`selected_a_text_count=1`；`rejected_b_text_count=1`。
- 结论：`T5b_GATE=PASS`。

## 10. T6 · 总验收

### 10.1 参数 allowlist

| 参数 | 文件 | 允许变更 | 实际 diff | 裁决编号 |
|---|---|---|---|---|
| `n_ctx` | 基线 §16.2 / §16.4 | 仅 B 案可改目标值；A 案只增动态公式 | D-04 选 A；§16.2 `n_ctx=4096` 行 0 diff，§16.4 新增公式 | D-04 |
| 全卷满承诺句 | 基线 §17.2.3 | A 应急日志或 B 不保证不丢，二选一 | D-05 选 B；旧“不丢、不失败”删除，A/B 状态互斥、事件唯一 | D-05 |
| `lifecycle` | 注册分类 §三插件表 | 仅新增列与三枚举、停用后果 | 表头与两数据行变更；插件数量/ID 未变 | 不适用（E-07） |
| 主脑职责表 | 双域规范 §11.3.1；基线 §16.5 | 8 行唯一表；旧表 obsolete 指向 | 双域新增 15 行；§16.5 新增 1 条 obsolete 指针 | 不适用（E-09） |
| 节点 `desc` / 域说明 | 架构树 4 节点；详解页 L147/L238 | Job 归 Shell、Shell 自愈、多端版本、两句迁域 | 树 4 节点各 1 行；详解页恰 2 行 | D-06 / D-08（E-03/E-06 依 R-79/R-78） |

### 10.2 Git diff 清单

| 文件 | 实际变更位置 | 行级统计 |
|---|---|---:|
| `docs/specs/next-感知交互参数基线-20261113.md` | §14.1、§16.4、§16.5、§17.2.3、附录 A；§16.2 原行未改 | +40 / -4 |
| `docs/tracker/next-基础能力架构-20261113.html` | 变更前 L147、L238 两句 | +2 / -2 |
| `docs/tracker/北极星架构树.html` | 进程树托管、守护自愈、Middleware 沙箱、多端调度 4 个节点 `desc` | +4 / -4 |
| `docs/plans/next-注册分类-tools-skills-plugins-20261113.md` | §三插件表 4 行 | +4 / -4 |
| `docs/specs/next-双域分离与开工设置规范.md` | §11.3.1 主脑职责表一处 | +15 / -0 |
| `docs/reports/fix-wo-ultimaagent-20261113-0058.md` | 本报告（新文件） | 新文件 |

产品文件合计：`65 insertions / 14 deletions`。报告不计入产品 diff。

### 10.3 九项映射（9/9）

| 编号 | 唯一落点 |
|---|---|
| E-02 | 基线 §16.4.1 |
| E-03 | 架构树 Shell“进程树托管”与 Middleware 工具节点 `desc` |
| E-04 | 基线 §17.2.3 |
| E-05 | 基线 §14.1 |
| E-06 | 详解页变更前 L147/L238 |
| E-07 | 注册分类 §三插件表 |
| E-08 | 架构树“守护自愈”节点 `desc` |
| E-09 | 双域规范 §11.3.1；基线 §16.5 obsolete 指针 |
| C-13 | 架构树“多端调度”节点 `desc` |

### 10.4 六条 Gate 自证

| Gate | 自证结论 |
|---|---|
| T1 | 公式/复算/五列表各 1；decision/dialog 各 1；D-04 1；原 `n_ctx` 行 1 |
| T2 | 旧承诺 0；selected/rejected 各 1；`IF D-05=` 2；事件 1；新增容量数字 0 |
| T3 | obsolete 3；每行箭头 1；目标章节 17.2.3/17.2.3/16.1 均存在 |
| T4 | T4a Job 节点 1 且父链 Shell、详解旧句 0/新句各 1；T4b 状态互斥；T4c 定义 1/职责 8/obsolete 指针 1 |
| T5 | T5a lifecycle 三枚举且 11/9 不变；T5b 节点 1、状态互斥、选中 A 含 v1.x |
| T6 | 综合脚本 16 项全 True、failed_count=0；diff 范围与冻结哈希通过；独立复核另见收尾记录 |

### 10.5 越界声明

- 越界：无。
- 未改 §二十五／§二十六；未改队列状态；未 commit / push / tag。
- 未访问或写入 `H:\UltimaAI\UltimaAgentNext`。
- `config/voice-next/live.json` 变更前 SHA-256 为 `2CACDE1D0DED2F700CAEF95BDB3C78B8154FE85C25EE68EE3B1FBB9519059ED3`；最终复跑必须相同。
- 工作树原有大量与本单无关的已修改/未跟踪文件；本单未触碰，T6 仅以本单 5 个产品文件与 1 个报告文件为核对集合。

### 10.6 遗留

- `TBD-D04`：B 案（已拒绝）的 KV cache 内存增量与首 token 延迟区间尚无同模型/量化/硬件/prompt 夹具的复现实测；不得当作已测值。该遗留不阻塞已选 A 案。

### 10.7 T6 Gate 证据

- 核心章节存在、T1、T2、T3、T4a、T4b、T4c、T5a、T5b、报告形状、变更文件集合、hunk 范围、v1 哈希、§25/§26 禁写、D 标记 20 字检查、`git diff --check` 共 16 项全部为 `True`。
- hunk：基线 `446,451,460,778,787,889,904,1521`；详解页 `147,238`；架构树 `233,274,286`（首 hunk 含相邻的进程树托管与守护自愈两节点）。
- v1 冻结文件最终 SHA-256：`2CACDE1D0DED2F700CAEF95BDB3C78B8154FE85C25EE68EE3B1FBB9519059ED3`，与变更前一致；Git diff 为空。
- D 标记后 20 字均无具体数字：D-04/D-05/D-06/D-08 全通过。
- `failed_count=0`；`FINAL_GATE=PASS`。

## 11. 独立复核与收尾

### 11.1 复核结论

- 只读独立复核：`Ready for owner review? Yes`。
- Critical：0；Important：0；Minor：2。
- 独立复核确认：20/20 插件 ID 各映射一次；职责表 8 行；obsolete 指向 3/3；唯一 Job Object 父链含 Shell；T2 状态/事件计数通过；五个变更前哈希与 HEAD 一致；冻结配置哈希一致。

### 11.2 Deferred minors

1. 架构树 Middleware 节点名称仍保留历史总称 `sandbox（双层：Job＋写域白名单）`；现行 `desc` 已明确 Middleware 只拥有 `fileDomain`、进程沙箱归 Shell。因本单写域只允许目标 `desc`，不改名称；代价是只扫标题的读者仍可能误读。
2. §16.4 量化表“是否合法”列可进一步改成“仅当预算非负且实际输入不超过预算”；当前上文已写送入硬条件并禁止负预算请求，因此不阻塞本次公式收敛。代价是脱离上文单独引用表格时，条件性不够醒目。

### 11.3 Final rulings

- 本单 Gate PASS 只代表文档口径与 diff 门通过，不代表 Next 运行吞吐、延迟、恢复或插件停用行为已实测；若把文档 PASS 当运行验收，会夸大交付状态。
- 不修改 Middleware 节点名称或注册分类 §四正文：二者不在明确写入域；现行 `desc` 与 §三 `lifecycle` 列承担本单收敛。若该范围判断错误，代价是旧标题/旧纪律句仍可能被孤立摘录。
- 独立复核只能证明当前文件哈希、diff 与写入集合；“执行期间未访问其他目录/未做 Git 写操作”由执行记录与本报告越界声明负责。若声明不实，现有 diff 无法反证历史动作。

READY_FOR_OWNER_REVIEW

