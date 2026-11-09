# G-ORCH 职能归位与多通道并发 · 实施方案 v0.1

> 日期：2026-11-09 ｜ 状态：待 Owner 拍板 ｜ 依据：G-ORCH-001（INDEX 行 17）、工程铁律 §9、`dispatch-rules-v0.2-20261108.md`
>
> **定位**：这是 `dispatch-rules-v0.2` 的**施工图**，不替代 v0.2。v0.2 定"谁做什么"，本文定"用什么做、按什么顺序做、怎么验"。

---

## 0. 一句话

把已经定死的「三模型 / 八环节」范式，**用开源现成件拼出来**：先归位（角色各回各位）、再并发（一任务一 worktree）；每一步都有机检验收，不靠人读代码判断。

---

## 1. 诊断：11 轮为什么过不了

| # | 结论 | 依据 |
|---|---|---|
| 1 | **目标本身不可达** | 「让门自证可信」没有任何开源项目在做。edict 做的是审计轨迹，Omnigent 是 *enforce policies and sandboxing*，Hive 是 human-in-the-loop。我们追的是"防篡改证明"，业界追的是"留痕 + 人审 + 沙箱" |
| 2 | **权力错配** | 让无裁决权的 Codex 做裁决（违铁律 §9-3）。没有裁决权的角色拿到裁决权，又没有被冻结的判据，它必然每轮再加三条——不是它苛刻，是这个权力不该给 |
| 3 | **三个角色同时越界** | 主脑判/审/派/改主表；外脑八环节一环没走；Codex 被赋裁决权。等于三角色一人兼，再让第四方（无裁决权）来判 |

**推论**：11 份 `VERDICT: FAIL` 在制度上不构成验收结论，只能算**顾问意见**。其中技术成立的部分（解释器精确相等、逐目标计数、表 schema 完整匹配）不丢弃，但要转成 ③ 工单判据，而不是由评审方在 ⑥ 现场发明。

---

## 2. 现状实测（代码级）

| 能力 | 状态 | 证据 |
|---|---|---|
| 单卡执行 | **只支持单卡** | `run-gorch.py:44`、`audit-work-order.py:250` 的 `--card` 均 `required=True` |
| 单流水线 | **只支持一条** | `run-gorch.py` 全链共用一个 `args.run_dir` |
| 审计名额 | **默认 2** | `dispatch-work-order.py:169` `AUDIT_SLOT_LIMIT` |
| 写隔离 | **无** | `dispatch-work-order.py:86/138` 只读 `worktree_dirty` 状态 |
| 并发实现 | **零** | 全仓 `concurrent|parallel` 无命中 |
| worktree 能力 | **已有，但只读** | `verify-order.py` 的 `_run_in_clean_worktree` 用 `git worktree add --detach` 做验证（实测 24.8s / 35,824 文件） |
| ②③ 两轮自审 | **无载体** | v0.2 §11 已登记 |
| DeepSeek 八环节 | **只有一次 API 调用** | `audit-work-order.py`，不是有产出物的角色 |
| 8B 主脑 | **未接线** | `ollama ps` 空、18766 无监听 |

---

## 3. 目标形态

### 3.1 角色边界

直接沿用 `dispatch-rules-v0.2` §1 与铁律 §9，**本文不复述、不修改**。一句话记牢：

- **主脑 = 8B 本地**：只传达（原样转）· 汇报（必带 tag + commit）· 记忆 · 按习惯交互。**不判、不审、不派、不改主表**。
- **外脑 = DeepSeek**：八环节全包，**每环节独立会话**。
- **Codex**：只写码 + 自检 + 提交。**无裁决权、无 tag 权**。

### 3.2 通道五件套（并发的最小单元）

一个"通道"必须同时具备五项，缺一即不合法：

| 要素 | 作用 | 缺失后果 |
|---|---|---|
| 独立 `git worktree` | 物理隔离写 | 两个 Codex 改同一 checkout，必冲突 |
| 独立分支 | 失败可整条丢弃 | 污染主树 |
| 独立 `run-dir` | done/verify/audit 不混 | 回执串单，审计无法定位 |
| **独占写域** | 同一文件不许两通道同时改 | 静默覆盖 |
| 独立审计单 | 一卡一判 | 打包验收，单卡责任消失 |

### 3.3 批次表（并发编排的唯一输入）

DeepSeek 拆解产出的不是"任务列表"，而是**批次表**。同批的卡必须满足：写域两两不相交 + 无依赖边。

```json
{
  "batch": 1,
  "channels": [
    {"card": "s1-host-shell-envcheck", "channel": 1,
     "worktree": "wt/s1-envcheck", "branch": "ch/s1-envcheck",
     "write_scope": ["scripts/envcheck.py", "tests/test_envcheck.py"],
     "depends_on": [], "gates_frozen": ["ACC-1", "ACC-2"]}
  ],
  "serial_merge": true
}
```

**规则**：写域有交集 → 拆到不同批；有依赖边 → 后者进下一批；`serial_merge` 恒为 true（合并永不并发）。

---

## 4. 开源复用清单（本文核心）

原则：**别人的成熟经验直接借，自研只留非做不可的三件。**

| 能力 | 复用对象 | 借哪部分 | 不借哪部分 | 自研量 |
|---|---|---|---|---|
| **worktree 管理** | `max-sixty/worktrunk` ~12,149★ | 「一任务一 worktree 一分支」的 CLI 化；topics 明确支持 `codex` | 它的 TUI/交互 | **0**（Windows 支持待验证） |
| 备选 | 我们自己的 `_run_in_clean_worktree` | 已实测可用的 `git worktree add --detach` + `finally` 清理 | 只读验证用法（扩成可写） | 小 |
| **工单驱动并行** | `automazeio/ccpm` ~8,437★ | 「GitHub Issues 即工单 + worktree 即执行位」的对应关系 | 它的 skill 包体系 | 0（只借形态） |
| **多厂商统一编排** | `golutra/golutra` ~3,865★ | Codex + Claude Code + 多 CLI 统一适配层的抽象 | 桌面 UI、长任务工作流引擎 | 小（适配层） |
| **状态机** | `cft0808/edict` ~17,049★ | `_VALID_TRANSITIONS` 非法跳转拒绝 + 审计日志；「每一个旨意都必须经过门下省，没有例外」 | 12 Agent 规模、三省六部角色名 | 0（照做法） |
| **合并语义** | GitHub merge queue（官方文档） | **并行验证 + 串行合并**；必需检查由 ruleset **事先定死** | Actions 那套 YAML | 小（串行合并队列） |
| **判据冻结** | Frozen Rubric（agentpatternscatalog） | 固定 schema + **清单外发现类别直接拒收** + temperature 0 | — | 0 |
| **隔离上下文** | Claude Code 官方 worktree 文档 / Blind Grader | 每会话独立 worktree；**混厂商必须自己管 worktree** | — | 0 |
| **端口隔离** | aq.dev 指南 | 每 worktree 独立 env + 独立端口（*Port collisions, almost always*） | — | 0 |
| **状态交接** | `parcadei/Continuous-Claude-v3` ~3,949★ | ledger + handoff 传状态、隔离上下文窗口 | — | 0 |

**三条硬结论（均有出处）**：

1. **一任务、一 worktree、一分支** —— 唯一隔离规则。
2. **混厂商必须自己管 worktree** —— 我们混 DeepSeek + Codex，Codex 自带的 worktree 自动化只管它自己。
3. **文件隔离靠 worktree 就够，不用容器** —— 容器只在有"仓库之外的副作用"时才需要。

**需要自研的只剩三件**：批次表生成 · 写域冲突检测 · 串行合并队列。其余全部借。

---

## 5. 三阶段施工

### Phase 0 · 止血（0.5 天，不写功能代码）

| 动作 | 产出 | 机检验收 |
|---|---|---|
| 11 份 Codex 意见转判据条目 | `docs/reports/gorch-judgement-baseline-20261109.md` | 每条带「来源文件名 + 原文摘句」；条数 = 意见中技术上成立的条目数 |
| 明确宣布 Codex 无裁决权 | 入 `dispatch-rules-v0.2` §11 | 文本可检索 |

**不做**：不改任何 `scripts/` 代码。

### Phase 1 · 归位（2–3 天）

| 动作 | 产出 | 机检验收 |
|---|---|---|
| DeepSeek 八环节接线（每环节独立会话） | `scripts/gorch_stage.py`（或扩 `orchestrate-order.py`） | 一条真实小单跑完 ①–⑧，每环节留独立 `session_id` + 产物文件 |
| ②③ 自审载体（另一会话） | 同上 | ②、③ 各有一条自审记录，含「审→修≤2→复验」三次痕迹 |
| 判据冻结进工单 | 工单 manifest 扩 `gates` 字段（JSON，不是 Markdown 表格） | ⑥ 审计只对 `gates` 里的 id 出结论；清单外类别被 schema 拒收 |
| 主脑接线 | 8B → 18766 | 主脑能原样转需求 + 带 tag/commit 汇报 |

### Phase 2 · 并发（3–5 天）

| 动作 | 产出 | 机检验收 |
|---|---|---|
| 通道五件套 | worktree/branch/run-dir/写域/审计单 | 3 张写域不相交的卡同批并发，各自独立 run-dir |
| 批次表 | 拆解阶段产出 JSON | 批次表 schema 校验通过；同批写域两两不相交 |
| 写域冲突检测 | 拆解阶段静态检查 | **故意造一次冲突，必须在拆解阶段被拦下**（不能等到运行期） |
| 串行合并队列 | 验收通过后逐单合并打 tag | 3 单全部验收后，tag 逐个生成；中间失败一单不影响另两单 |

---

## 6. 待 Owner 拍板（5 项）

| 参数 | 建议值 | 影响 |
|---|---|---|
| 并发上限 | **3** | 一个 worktree 24.8s / 35,824 文件；5 并发磁盘 IO 吃紧。3 对齐执行端调度 fan-out ≤3 |
| 通道载体 | **plain git**（先用） | worktrunk 的 Windows 支持**未验证**；我们已有可用的 worktree 代码，先扩不引依赖 |
| 审计名额 | **4**（并发 3 + 1 缓冲） | 现为 2，并发 3 必然排队；不改就"执行快、审计堵" |
| 返工上限 | **2** | 超 2 次升级到 Owner，不占 REVISE 额度 |
| 是否引入 worktrunk | **暂不引入** | 待验证 Windows 后再评估；当前自研量很小 |

---

## 7. 明确不做

| 不做 | 理由 |
|---|---|
| 让门自证可信（防篡改证明） | 无任何开源先例；追它必然无限后退 |
| 扩到 12 个 Agent | 3 角色质价比 0.77，6 角色掉到 0.35；同模型多角色只换座位不换眼睛 |
| 上容器 | worktree 已保证文件隔离；容器只在有仓库外副作用时才有价值 |
| 上 A2A 协议 | MCP 已够用；多轮有状态编排在应用层自己写更轻 |
| 让同一模型扮演审核者 | 实证：同模型多轨迹「继承同一套盲点」，拿不到独立判断 |

---

## 8. 风险

| 风险 | 处置 |
|---|---|
| worktrunk Windows 支持未验证 | 已定：先用 plain git，不引依赖 |
| 3 个 worktree ≈ 10 万文件的磁盘占用 | 合并后立即 `worktree remove` + `prune`；设残留清理 |
| 执行快于审计导致主表堆积 | 名额提到 4；仍堆积则记录为已知常态，不掩盖 |
| 8B 主脑未接线 | Phase 1 前置项，未接通则 Phase 1 只做外脑与判据两部分 |
| Phase 1 判据 JSON 化需回填存量工单 | 先只对新单生效；`wo-orb-w9.md`、`wo-s1-host-shell.md` 标注"旧格式，待回填" |
