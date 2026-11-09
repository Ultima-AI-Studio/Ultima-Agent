# G-ORCH 治理体检报告 · UltimaAgent / G-ORCH 编排体系

- 体检时间：2026-11-09 ｜ 基准：`project-governance-audit` v1（A 类 00–18 + B 类 B1–B6）
- 检查范围：`docs/`（14 子目录、22 个 G-ORCH 相关文件）、`tasks/`、`scripts/gorch/`、`src/brain/slot_adapter.py`、`data/gorch/runs/`（16 批次实测记录）、`config/gorch/`
- 取证方式：清单核对 / 编号一致性 / 交叉引用 Grep 验证 / 参数并排 / 工单四段 / 能力实跑复现
- 未检查项：`libs/memory/mem0` 全量、ccpm 其余 15 脚本、Blender/语音链路、非 G-ORCH 的既有脏改动区（`.superpowers/`、`tasks/queue/`）

---

## 一、总览（结论先行）

**25 行判定（A 类 19 + B 类 6）：✅ 7 绿 / ⚠️ 11 不一致 / ❌ 4 缺 / ➖ 3 不适用**

**治理结论：不 PASS。**

三层原因，按严重度：

1. **P0 · 判据门本身不成立**。`gorch-judgement-baseline-20261109.md` 至今写着「待 Owner 确认后冻结」，而它自述「本轮必须修完」的 L1-02 / L1-03 / L1-04 **三条全部未达标**（本轮实测：四类畸形行 4/4 静默通过、`python3` 仍被接受、`Scripts` 下任意层级仍被接受、skip 政策仍只有合成 XML）。判据没冻结、判据要求没实现，返工上限 2 次的规则就无从生效——这是 11 轮复审反复追同一批问题、每次都能再往下细分的结构性原因。
2. **P0 · 权威文档清单与实际脱节**。G-ORCH 相关 22 个文件里 **20 个未登记**进 `docs/文档库索引.md` / `docs/INDEX.md`（仅 `lessons-log.md`、`config/gorch/README.md` 登记）。契约、判据基线、14 篇报告与计划、4 个脚本、`slot_adapter.py` 全部在清单外。
3. **P0 · 无 ADR、无正式工单**。`tech-decisions.md`、`capability-list.md`、`docs/decisions/*` 对 G-ORCH **零命中**；`tasks/` 下 **0 张** G-ORCH 工单，唯一工单 `WO-README.md` 落在 gitignore 的 `data/gorch/handoff/S7-smoke/batch/`。S1–S7 六个阶段的重大选型（wt 作并发底座、600s 预算、18766→11434、merge target 语义）全部只存在于契约与教训日志，没有决策记录。

**能力验收结论（八跳 + 三插槽 + 并发 + 合并）**：核心链路可跑、可复现，但**并发 3 通道未经验证**，跳 4 未串跑。

| 能力 | 实测证据 | 判定 |
|---|---|---|
| 跳 1 主脑理解（S-MAIN） | 本轮独立复跑 `15.6s / in 170 / out 427 / model qwen3-8b-uncensored:latest`，三条需求全部保留、未加额外内容 | ✅ |
| 跳 2 decompose（DeepSeek） | `run-b/stages/decompose.json` completed，1708 tokens | ✅ |
| 跳 3 Owner 确认 | 设计为人工门，无自动旁路 | 设计内 |
| 跳 4 回传授权条件（S-MAIN） | `call_main()` + 4 条专项单测（未启用抛 `SlotConfigError`、参数透传、key 覆盖等），**未与真实需求串跑** | ⚠️ |
| 跳 5 work_order（DeepSeek） | `work_order.json` completed，926 tokens | ✅ |
| 跳 6 自检（G1–G6） | `schedule.json` completed，491 tokens | ✅ |
| 跳 7 执行（S-EXEC Codex） | `WO-README` run done 133.5s，`config/gorch/README.md` 4209B 落地 | ✅ |
| 跳 8 复核（S-REVIEW DeepSeek） | `review-deepseek.json` PASS，A1/A2/A3 全 ok，in 2071 / out 392 | ✅ |
| 合并 600s 预算 | 真实合并 `rc=0 / 227.4s`，主线 `50af6549→3d0fc8dd`，报告 4020B 落地；`MERGE_TIMEOUT=600` 确认挂在 `batch_orchestrator.py:345`，`WT_TIMEOUT=180` 挂 switch/remove | ✅（单次实证） |
| **并发 3 通道** | 第 1 轮三通道同秒启动但 `out.log` 全是 `[dry-run] 未真实执行 Codex`；第 2 轮 JOB-1/JOB-2 真跑 blocked（241.9s/241.2s，根因为 Codex 连 `chatgpt.com/backend-api/ps/mcp` 超时，非编排缺陷），**JOB-3 未参跑**；第 3 轮 JOB-1/JOB-2 done（70.4s/60.1s）出 15B 产物，**JOB-3 无任何产物**（worktree 仍停 `34c676da`，无 `out-3.txt`） | ⚠️ **2/3 且非同轮** |
| 三插槽可替换 | S-MAIN/S-REVIEW/S-EXEC 全走 `slot_adapter`；换供应商只改配置 3 字段，不改码 | ✅ |

---

## 二、P0 必建缺失（阻塞，先补再开工）

| 缺什么 | 验收判据（怎么算补齐） | 影响 | 修复动作 |
|---|---|---|---|
| **判据门可放行性**（基线未冻结 + L1 三条未达标） | `gorch-judgement-baseline` 状态从「待 Owner 确认后冻结」改为「已冻结 v1」；L1-02/03/04 各补机检断言并实测绿 | 冻结门给出 PASS 也不代表判据被满足；审计结论无锚 | ① 先让 Owner 拍板冻结范围（含 L2-01/02 是否纳入）② 再修三条实现 ③ 复检 |
| **08 权威文档清单与磁盘不一致**（20/22 未登记） | `docs/文档库索引.md` + `docs/INDEX.md` 登记全部 22 个文件，含判据基线、契约、4 脚本 | 新增文档无登记机制 = 双源漂移必然复发；接手者按清单找不全 | 建 G-ORCH 文档区块，逐条登记并注明权威层 |
| **14 ADR 缺**（`tech-decisions.md` 对 G-ORCH 零命中） | 每条决策含 决策/理由/后果 三段 | 五个重大选型无记录，下轮可能重复推翻 | 补 5 条 ADR：wt 并发底座 / 600s 预算 / merge target 语义 / 18766→11434 / bridge 只搬不解析 |
| **18 工单缺**（`tasks/` 0 张，唯一工单在 gitignore 区） | 工单含范围冻结/任务表/总验收/DoD 四段，T 序列不撞号，有禁止清单 | S1–S7 无冻结门可追溯，阶段报告替代不了工单 | 补建 `docs/work-orders/G-ORCH-S{1..7}` 三段式工单（可回溯建，标注口径为"补记"） |
| **L1-04 卡集合解析**（实测 4/4 畸形行静默通过） | 4 类畸形行各一条「必须 ValueError」断言，实测红 | `ACC-1x` 被当合法 gate（`acc_rows` 返回 1 行）、缩进卡行/`T2s1-`/`ACC-X` 均静默漏掉——收据可声明"看到全部行"而实际没看到 | `scripts/gorch_contract.py:25,28,29,85` 收紧：`_TASK_ROW` 允许前导空白后仍须判卡引用；`_ACC_HEAD` 加 `$` 锚定；新增"疑似行未解析即 ValueError"分支 |
| **L1-02 解释器唯一性**（`verify-order.py:318,321` 原样） | `resolve()` 后与注册路径**字符串精确相等**；`python3` 被拒 | `Scripts/` 下任意层级同名 exe 通过；`python3` 通过 → "限定登记 venv"被放宽成"同目录任意层级" | 改为 `str(exe.resolve()) == str(REGISTERED)`，解释器名白名单收敛为 `python.exe` |
| **L1-03 跳过/失败政策**（只有合成 XML 计数） | 全 skip / 混合 skip / xfail / 非 strict XPASS / strict XPASS 五类**各一条真实 pytest 运行**断言 | 被跳过的用例与通过无法区分；`_junit_counts` 自洽 ≠ 真跑 | `tests/test_verify_order.py` 增加 5 条真跑用例（临时 worktree 内置 fixture） |

---

## 三、P1 不一致 / 漂移（需修复并复检）

| 不一致项 | 证据（文件 / 取值） | 影响 | 修复动作 |
|---|---|---|---|
| **教学文档教的是过期值** | `config/gorch/README.md:11,63`、`slots.example.json:11–12` 仍写 `127.0.0.1:18766` + `qwen3:8b`；`slot_adapter.py` 实际 `11434` + `qwen3-8b-uncensored:latest` | 照文档配置 → 端口无落地、模型不存在，`require_main` 抛「未接线」；与已验收的跳 1 直接矛盾 | 改两文件为 11434 + `qwen3-8b-uncensored:latest`；README §5 同步「默认已启用？否」的真实状态 |
| **并发 3 通道声明超出实证** | `MAX_CHANNELS=3`（`batch_orchestrator.py:56`）；`codex_channel.py:129` `--channel 1..6` 仅用于 run-dir 命名与看板标签，通道间能力相同 | 对外说"三通道并发"会被读成已验证能力；JOB-3 无产物 = 三通道从未同轮全部成功 | ① 补一轮三通道真跑并回读 3 份产物 ② 文档改为"同能力最多 3 实例并行"，并注明 2/3 实证 |
| **交叉引用 11 处落点不存在** | `config/gorch/README.md:7`→`slots.json`（确不存在）；`gorch-multi-channel-rollout-plan:75`→`scripts/envcheck.py`、`tests/test_envcheck.py`；`:128`→`scripts/gorch_stage.py`；`lessons-log.md:467`→`src/brain/work_research.py`、`work_navigation.py`；`:575`→`scripts/kanban_update.py`（实际 `scripts/gorch/kanban_update.py`）；`gorch-edict-assembly:18`→`scripts/file_lock.py`、`:19`→`scripts/utils.py`（实际都在 `scripts/gorch/`） | 接手者按引用找不到文件；搬迁后未回改 = 双源 | 按实际位置回改；`slots.json` 在 README 中改为"从 example 复制生成" |
| **A04 参数基线未登记** | `MERGE_TIMEOUT/WT_TIMEOUT/BASH_TIMEOUT/MAX_CHANNELS/BRANCH_PREFIX/WORKTREE_ROOT` 只在代码常量 + 契约散述，`execution-param-contract.md` 无这些项 | 参数改动无单点核对表，跨文档漂移无判据 | 在 `execution-param-contract.md` 增 G-ORCH 参数表（值 / 可设置 vs 写死 / 引用） |
| **A00 架构文件不含 G-ORCH** | `docs/architecture.md` 2557B 对 `gorch/g-orch/插槽/slot` 零命中；分层只在 `batch_orchestrator.py:1–24` 注释 + 契约 §2 | 新人读架构看不到编排层位置 | 在 architecture 增一节「G-ORCH 编排层：六子命令 + 三插槽 + 三通道」 |
| **A06 高危动作无拦截** | `data/gorch/runs/.../stderr.log` 显示 Codex 以 `approval: never` + `sandbox: danger-full-access` 运行 | 与 `Ultima-执行端调度` §四「高危动作即时拦」冲突；执行端可无审批改文件 | 编排层加动作级白名单或 `--ask-for-approval`，并在契约写明边界 |
| **A11 两套状态词** | `codex-channel.json` 用 `done/blocked`；`kanban_update.py:587–593` 用 `completed/in-progress/not-started` | 同一任务在 run 账本与看板状态不可直接对齐 | 建枚举总表，或在契约声明映射规则 |
| **A15 待拍板项未进台账** | 契约 §6 留 1 条（merge target 语义）；另有 5 项待确认（并发 3 / worktrunk 定调 / 审计返工 2 / L2 条目范围 / 判据是否冻结）只在会话中 | 未决项无状态/影响/时间，跨会话丢失 | 建 `docs/decisions/g-orch-open-items.md` 登 OPEN-xx |
| **A16 功能范围未登记** | `capability-list.md` 对 `gorch/g-orch/插槽` 零命中；能力只在 rollout-plan 隐含 | 无 L0–Ln 分层，"本版本不做清单"缺失 | 补 G-ORCH 能力分层：S1–S7 / 八跳 / 三插槽 / 并发 / 合并 / 看板，并写不做清单（如"不自动解析自然语言工单"） |
| **B2 能力→技能路由未成文** | 技能注册表存在（系统侧），但 G-ORCH 内部"哪一步该由哪个执行端/技能承担"只在契约 §2 描述 | 路由规则不可执行，替换执行端需读码 | 建 G-ORCH 路由表：跳 1/4→S-MAIN、2/5→S-REVIEW、6→stage、7→S-EXEC、8→S-REVIEW |
| **lessons-log 结构不统一** | 613 行 / 111332B；L1–L74 连续无跳号，但 **L28 物理位在 L29 之后**（214 vs 208 行）；早期 `### L01 `、近期 `## L70 · ` | 编号规范部分违规（标题层级 h2/h3 混用 + 顺序颠倒） | 统一为 `## Lnn · `，L28/L29 换位 |
| **A07 无发布包清单 / 版本号规则** | 有 `gorch-s6-merge` / `gorch-slot-adapter` / `gorch-s7-bridge` / `gorch-s7-closeout` 四个 tag，无规则文档 | 打 tag 靠惯例，接手不可复现 | 契约增"阶段 tag 命名规则"一节 |

---

## 四、P2 可选项 / 增强

| 建议 | 理由 | 价值 |
|---|---|---|
| 建 G-ORCH 术语表（S-MAIN / S1–S7 / 八跳 / bridge / stage_gate / 回执八字段） | `scripts/gorch/` 下 0 个 `.md`，术语只在契约正文 | 中 |
| `codex-channel.json` 补 schema 文档（A02） | 字段靠读码，跨版本易漂 | 中 |
| 补"启动→运行→关闭 + 容灾"时序（A03） | 现有 `fail-closed` 超时处理，但无成文时序 | 中 |
| 补自检命令文档（A12） | 六子命令有 `--help`，无一条"健康自检"串 | 低 |
| bridge 边界写入功能范围的不做清单 | 现状需人把工单放进批次目录，与"全自动八跳"有张力 | 高（决定验收口径） |

---

## 五、修复建议汇总

- **P0：7 项** → 建议生成 4 张修正工单（见 §六）：①判据冻结+三条 L1 落地 ②文档清单登记 ③ADR+功能范围 ④阶段工单补建
- 本报告自身是第 23 个 G-ORCH 相关文件，按 A08 判据应**随工单 02 一并登记**，不在本报告内自行代登（审计不代改）
- **P1：12 项** → 其中"教学文档过期值"与"并发 3 通道"建议同批处理（都要动 `config/gorch` 与契约，且都要重跑实证）
- **P2：5 项** → Owner 决定

**顺序建议**：先做「文档过期值 + 交叉引用」（1 小时内可闭环，且直接影响别人照着配环境）→ 再做「判据冻结 + 三条 L1」（这是后续所有审计的前提）→ 最后「清单登记 + ADR + 工单」（属补账，可回溯建）。

---

## 六、修正工单（4 张，三段式）

### 工单 G-ORCH-AUDIT-01：冻结判据基线并落地 L1-02/03/04
**范围冻结**：只改 `gorch-judgement-baseline` 状态、`scripts/verify-order.py` 解释器判定、`scripts/gorch_contract.py` 两个解析器、`tests/test_verify_order.py` 与 `tests/test_order_contract.py`。不碰八跳逻辑、不碰 `batch_orchestrator.py`。
**任务表**：
- T1 `verify-order.py:317–323` 改字符串精确相等；解释器名收敛为 `python.exe`；Grep 补 2 条断言（同名不同层级被拒、`python3` 被拒）
- T2 `gorch_contract.py` 收紧：疑似卡行/ACC 行未解析即 `ValueError`；`_ACC_HEAD` 加 `$`；补 4 条畸形行断言
- T3 `test_verify_order.py` 增 5 类 skip/xfail 真跑断言（临时 worktree 内造 fixture）
- T4 基线条目状态由「待 Owner 确认」→「已冻结 v1」，并把 L2-01/02 纳入结果写进文首
**验收（Gate）**：`tools/venv-openjarvis/Scripts/python.exe -m pytest -o addopts= tests/test_verify_order.py tests/test_order_contract.py` 全绿；畸形行 4/4 实测 REFUSE；`python3` 实测 REFUSE
**禁止**：不放宽任何现有断言；不改判据条目语义；不通过"注释说明"替代实现

### 工单 G-ORCH-AUDIT-02：G-ORCH 文档登记与过期值回改
**范围冻结**：只改 `docs/文档库索引.md`、`docs/INDEX.md`、`config/gorch/README.md`、`config/gorch/slots.example.json`、5 处失效引用所在文档。不改代码。
**任务表**：T1 两份索引增 G-ORCH 区块，登记 22 个文件（含权威层标注）→ T2 `README:11,63` 与 `slots.example.json:11–12` 改 11434 + `qwen3-8b-uncensored:latest`，并写清 `enabled` 默认 `false` 的手动开启步骤 → T3 失效引用按实际落点回改（`scripts/gorch/*`、`src/brain/*`）→ T4 `README:7` 的 `slots.json` 改为"从 example 复制"
**验收**：索引中 22 行逐条 `Test-Path` 为真；Grep `18766` 仅剩历史记述 5 处（已在 §四 列为正常留痕）；Grep 失效引用 11 处全部落点存在
**禁止**：不改历史报告中的记述性 18766；不动 `data/gorch/`

### 工单 G-ORCH-AUDIT-03：ADR + 功能范围 + 开放项台账
**范围冻结**：只新建 `docs/decisions/g-orch-adr.md`、`docs/decisions/g-orch-open-items.md`，并在 `tech-decisions.md`、`capability-list.md` 各增一节指向。不改实现。
**任务表**：T1 5 条 ADR（wt 并发底座 / 600s 预算 / merge target 语义 / 18766→11434 / bridge 只搬不解析），每条含 决策/理由/后果/备选 → T2 能力分层 L0–L4 + 不做清单 → T3 OPEN 台账登记 6 个未决项（各带状态/影响/更新时间/归属）
**验收**：每条 ADR 三段齐；能力分层与本报告 §一 能力表一一对应；OPEN 项每项有状态枚举
**禁止**：不替 Owner 拍板未决项（状态写"待 Owner"）

### 工单 G-ORCH-AUDIT-04：补建 S1–S7 三段式工单
**范围冻结**：只在 `docs/work-orders/` 新建 7 张回溯工单，不重跑、不改代码。
**任务表**：T1–T7 每阶段一张（范围冻结 / 任务表 / T 明细三段式 / 总验收 / 禁止清单），口径标「回溯补记，依据 = 阶段报告 + 提交链」
**验收**：7 张四段齐；T 序列不撞号；每张引对应 tag 与报告路径
**禁止**：不把补记工单冒充当时冻结件；不在工单里新增未做过的任务

---

## 审计声明

- 检查范围：`docs/`（14 子目录、22 个 G-ORCH 文件）、`tasks/`、`scripts/gorch/`（5 文件）、`src/brain/slot_adapter.py`、`config/gorch/`（2 文件）、`data/gorch/runs/`（16 批次 16 份 `codex-channel.json`）
- 证据方式：清单核对（两份索引逐条比对）/ 编号一致性（`^## L` 正则 + 行号顺序）/ 交叉引用（`git grep` + `Test-Path` 逐落点）/ 参数并排（代码常量 vs 三处文档）/ 工单四段（`tasks/` 递归）/ 能力实跑（跳 1 独立复跑一次、L1-04 四类畸形行实测、16 批次结果汇总、ollama 在线性与模型清单核对）
- 未覆盖：`libs/memory/mem0` 的 4 处 model 硬编码、ccpm 其余 15 脚本、`Kanban` 前端渲染、真实合并未二次复跑（`gorch/S7-smoke-report` 分支已被 wt 删除，重建成本高于收益，引用 227.4s 单次实测记录）
- 结论不超过上述检查范围
