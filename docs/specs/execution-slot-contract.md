# 执行插槽契约（Execution Slot Contract）

版本：v1.0 · 2026-11-09 · 状态：权威源（运行时边界）
上游：`INDEX.md` G-ORCH-001 · `dispatch-rules-v0.2-20261108.md` §1
关联：`execution-param-contract.md`（参数与四段协议）· `independent-review-contract.md`（复核结论 schema）· `mainbrain-rules-baseline.md`（主脑回答规则）

---

## 0. 一句话

流水线的三个智能位——**主脑位 / 审议位 / 执行位**——都是**可替换插槽**。插槽只认接口（吃什么、吐什么、守什么、不许做什么），**不认具体模型**。换模型是换配置，不是改编排代码。

---

## 1. 三个插槽与接口

| 插槽 | 代号 | 当前实现 | 接口形态 | 可替换族 |
|---|---|---|---|---|
| 主脑位 | `S-MAIN` | 本地 8B（ollama，OpenAI 兼容 HTTP） | `POST /chat/completions` | 任意 OpenAI 兼容服务；换 `base_url` + `model` |
| 审议位 | `S-REVIEW` | DeepSeek（`src/brain/orchestrator.py`，requests） | `POST /chat/completions` | 任意 OpenAI 兼容服务；换 `base_url` + `model` + `api_key` |
| 执行位 | `S-EXEC` | Codex CLI（`codex_channel.py`） | **本机进程**（stdin 喂 prompt，指定 workdir 干活） | 任意 CLI：Claude Code / Gemini CLI / Qwen Code / 自建脚本；HTTP 型 API 需一层适配器 |

**插槽不绑定厂商**：`S-REVIEW` 换成 OpenAI、Claude、本地 14B，只要按 §2.3 的约束产出，编排层不做任何改动。

---

## 2. 每个插槽的硬边界

### 2.1 三位共同约束

1. **只产出结构化回执**（JSON），不产出"我觉得做完了"这种散文结论；
2. **失败必须显式**：非 0 退出码 / `result=blocked`，禁止静默成功；
3. **不写主表、不改状态机、不打 tag**——这三项权力只属主脑与 Owner；
4. **不越自己的写域**：执行位只写自己被授权的 worktree，不碰主线与其他通道。

### 2.2 主脑位专项（`S-MAIN`）

- 只做四件事：转需求（原样）· 报结果（**必须带 tag + commit**）· 存本地记忆 · 按 Owner 习惯交互；
- **不做语义判断**——只做路由、搬运、汇报（AgentGate 前提：8B 做主脑成立的条件）；
- 流程内不判、不审、不派、不改主表；
- 回答规则见 `mainbrain-rules-baseline.md`。

### 2.3 审议位专项（`S-REVIEW`）

- 两轮介入：**工单自检**（拆解后、派发前）+ **执行复检**（执行后）；
- 判据必须**冻结**：判据写成固定文件/schema，清单外类别直接拒收（Frozen Rubric）；
- **不拿执行位的推理痕迹**（Blind Grader 隔离）——只读产物与证据，不读执行端自述的思考过程；
- **不重新规划**：只判 PASS/FAIL，不改成"我觉得应该这样做"；
- 复核结论 schema 与放行顺序见 `independent-review-contract.md`。

### 2.4 执行位专项（`S-EXEC`）

- 只做三件事：**写码 + 自检 + 提交**；
- **不做裁决**、无 tag 权限、自检结果不算验收；
- 必须能吃：`prompt 文件路径` / `workdir` / `timeout` / `effort`；
- 必须能吐：`exit code` / `stdout` / `stderr` / `末段消息文件`；
- 角色卡见 `agents/execution/SOUL.md`。

---

## 3. 回执统一（插槽无关）

任何插槽的返回都必须落成同一结构，下游只认这个结构、不认谁产的：

```json
{
  "slot": "main|review|exec",
  "impl": "实际实现标识（模型名或 CLI 名，如 deepseek-chat / codex）",
  "endpoint": "base_url 或可执行文件绝对路径",
  "ok": true,
  "result": "done|blocked|timeout",
  "exit_code": 0,
  "elapsed_sec": 70.4,
  "artifact_dir": "本次产物目录绝对路径",
  "evidence": ["证据文件路径，可复跑"],
  "error": "失败时的错误摘要，成功为空"
}
```

**现状差距（如实记录）**：`codex-channel.json` 与 `independent-review.json` 目前是两套结构，字段名不同（前者 `task/channel/run_dir/exit_code`，后者 `work_order/ok/role/blocker`）。统一到上表需要一次适配层改造，**尚未做**。

---

## 4. 替换方式：全部走适配层配置（2026-11-09 落地）

适配层唯一入口：`src/brain/slot_adapter.py`。三个插槽共用一套配置，优先级 **环境变量 > `config/gorch/slots.json` > 内置默认值**；内置默认值就是已跑通的那一套，**不配时行为完全不变**。

| 插槽 | 配置键 | 环境变量 | 换实现要不要改代码 |
|---|---|---|---|
| `S-MAIN` | `endpoint` / `model` / `enabled` | `GORCH_MAIN_ENDPOINT` · `GORCH_MAIN_MODEL` | **不要**（`enabled=false` 时 `require_main()` fail-closed 报错，取代当前"静默当没有") |
| `S-REVIEW` | `base_url` / `model` / `api_key_env` / `max_tokens` / `timeout` | `GORCH_REVIEW_BASE_URL` · `GORCH_REVIEW_MODEL` · `GORCH_REVIEW_KEY_ENV` | **不要**。走 OpenAI-compatible `/chat/completions`，DeepSeek / OpenAI / Moonshot / Qwen compatible-mode / vLLM / Ollama 同一形态 |
| `S-EXEC` | `exe` / `model` / `args_template` / `env` | `GORCH_EXEC_EXE` · `GORCH_EXEC_MODEL` | **不要**。`args_template` 一旦配置就整体替换 argv（占位 `{exe}` `{model}` `{workdir}` `{last_msg}` `{effort}`），换 Claude / Gemini / Qwen / OpenCode 只换模板 |

配置样例见 `config/gorch/slots.example.json`（含 OpenAI / Moonshot / Qwen / vLLM 与 claude-code 模板示例）。

**接线落点（改了哪几处）**：
- `orchestrator.py`：`call_deepseek` / `run_stage` / `_request_once` 新增 `base_url`、`api_key` 参数；`api_key` 显式传入优先，未传才回退 `DEEPSEEK_API_KEY`（修复了"model 换了但 key 还是 DeepSeek"的假替换）
- `scripts/orchestrate-order.py`：从 `review_settings()` 取 model / base_url / api_key / max_tokens / timeout 传进每一次 `run_stage`
- `scripts/gorch/codex_channel.py`：`resolve_codex_exe()` 先读适配层 `exe`；`run_codex()` 的 `-m` 取适配层 model，配了 `args_template` 则整体换 argv，配了 `env` 则合并进子进程环境

> 结论（更新）：**三插槽换 API / 换 CLI / 换模型，全部不需要改编排代码**，只改配置。已用"本地假端点 + python 冒充 CLI"两条真实链路验证：base_url、model、api key、argv 全部按配置生效。

**尚未覆盖的 4 处 model 硬编码**（不在本适配层路径内，属后续清理）：`scripts/audit-work-order.py:58`、`src/brain/loop/external_executor.py:28`、`src/brain/interaction.py:395`（写的是 `deepseek-flash`，与其余三处不一致）、`libs/memory/mem0/mem0/llms/deepseek.py:37,40`。

---

## 5. 当前实际链路（A 与 B 已接通）

| 路径 | 入口 | 覆盖环节 | 状态 |
|---|---|---|---|
| A：审议链 | `run-gorch.py` → `orchestrate-order.py` → `orchestrator.run_stage` → DeepSeek | 需求 → 理解/拆解 → 工单 → 排程 | 有实现、真跑通过 |
| 交接点 | `batch_orchestrator.py bridge --run-dir --batch-dir` | A 的 stages → B 的批次目录 | **S7 已落地并真跑** |
| B：执行链 | `batch_orchestrator.py` → `gate` / `provision` / `execute` → `codex_channel.py` | 开工判定 → 隔离位 → 并发执行 | **S5 已真实跑通** |
| 合并链 | `batch_orchestrator.py` → `merge` / `cleanup` → `wt merge` / `wt remove` | 串行合并 → 清理兜底 | **S6 已完成**（真冲突硬验收：rc=1 显式 CONFLICT、主线不污染） |

**交接边界（重要）**：`bridge` **只搬不解析**。它可以做三件确定性的事——校验每段 `verdict` 为 `completed`、把 `stages/*.json` 原样复制到 `<批次>/_handoff/` 作审计证据、写 `manifest.json`（run_dir / 各段结论 / task_files / ready_to_gate / UTC 时间戳）。它**不做**的事是把自然语言工单反解成 `depends_on` / `conflicts_with`——那等于拿 Markdown 当类型系统，误解析会派错写域，而并发写域切错是这条链路里代价最高的事故。**带 frontmatter 的 `<id>.md` 由第 3 跳 Owner 确认后放进批次目录。**

八跳实测状态（2026-11-09 真跑 GORCH 一单）：

| 跳 | 环节 | 载体 | 现状 |
|---|---|---|---|
| 1 | 主脑理解 | `S-MAIN` | ✅ 真调本地 8B（`qwen3-8b-uncensored:latest` @ `127.0.0.1:11434`，12.4s / in 170 / out 242）：把带执行细节的原始需求转写成只描述产物的版本 |
| 2 | 审议·理解/方案 | `orchestrator` decompose | ✅ 真调 DeepSeek，verdict=completed |
| 3 | Owner 确认 | 人工 | 人工（本轮代做并改判：7 道串行同文件 → 合 1 张工单） |
| 4 | 主脑回传授权条件 | `S-MAIN` | 能力已落地（`call_main()` + 8 条单测），**尚未与真实需求串跑**；本轮授权条件写进工单验收 A1-A3 |
| 5 | 审议·拆解/工单 | `orchestrator` work_order | ✅ 真调，verdict=completed |
| 6 | 审议·工单自检 | 同 stage 内自检 | ✅ 产出自检清单 G1-G6 |
| 7 | 执行·写码/自检/提交 | `S-EXEC` | ✅ Codex rc=0 result=done，产出 4209B 并提交 |
| 8 | 审议·复检 → 主脑汇报 → Owner 抽检 | `S-REVIEW` 独立复核 | ✅ 复检 A1/A2/A3 全 PASS（主脑汇报由本轮代做） |

---

## 6. 已知缺口（不粉饰）

| 缺口 | 影响 | 下一步 |
|---|---|---|
| 回执两套结构 | 下游无法用同一套判定处理不同插槽产物 | §3 统一结构落地 |
| 4 处 model 硬编码不在适配层路径内 | 换 model 时要单独改这 4 个文件 | 收口到 `slot_adapter` 一处（`audit-work-order.py` / `external_executor.py` / `interaction.py` / mem0） |
| `wt merge` 的目标分支 | `TARGET` 缺省是 default branch（main），而施工在 `codex/voice-fsmn-new-path` 上；已加 `_current_branch()` + `merge(target=)` + CLI `--target`，默认取当前检出分支 | 发布期合 main 须显式 `--target main`，流程上需明确"编码期合工作分支、发布期合 main" |

> 已关闭：S6 合并编排（2026-11-09）、A/B 两路未接（S7 `bridge`）、执行位 CLI 硬编码、model 硬编码（编排主路径）、未接线插槽无 fail-closed（`require_main()` 现在报错）、工单命令块被误判成工具调用（L73）、**主脑未接线**（`S-MAIN` 默认指向 `127.0.0.1:11434` 的 `qwen3-8b-uncensored:latest`，`call_main()` 落地，跳 1 真跑 12.4s / in 170 / out 242）、**`MERGE_TIMEOUT=600` 未验证**（2026-11-09 真实合并 **227.4s rc=0**，主线 `50af6549→3d0fc8dd`，报告 4020B 落地；227.4s 正好落在"旧 180s 必超时、新 600s 有余量"之间）。

---

## 7. 可机检（怎么证明"可替换"是真的）

1. **插槽自报**：任何一次调用，回执必须含 `slot` / `impl` / `endpoint`，缺一即判不合格；
2. **换实现不改编排**：同一批任务用两套配置（如 DeepSeek vs 本地 14B）各跑一次，编排代码 `git diff` 为空；
3. **fail-closed**：给未配置的插槽发任务，必须报错退出，不许 fallback；
4. **写域核对**：执行位产物只能出现在自己 worktree 内，越界即拒收。

---

## 8. 与既有契约的关系（不重复造）

| 内容 | 归谁 |
|---|---|
| 三层职责边界（主脑四件/外脑八环节/Codex 三件） | `dispatch-rules-v0.2-20261108.md` §1 |
| 执行参数基线 + 四段协议 THOUGHT/ACTION/OBSERVE/FINAL + 8B→外部模型调用链 | `execution-param-contract.md` |
| 复核结论 schema + `stage_gate` 放行顺序 | `independent-review-contract.md` |
| 主脑回答/行为规则 | `mainbrain-rules-baseline.md` |
| **插槽接口 + 可替换性 + 回执统一** | **本文件（唯一新增部分）** |

---

## 变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-11-09 | 初版：三插槽接口、共同与专项硬边界、回执统一结构、替换方式（配置 vs 改码）、两条路径现状与八跳空档、已知缺口、可机检判定 |
| v1.1 | 2026-11-09 | 适配层落地：新增 `src/brain/slot_adapter.py`（`config/gorch/slots.json` + 环境变量 + 内置默认值三级），三插槽换 API/CLI/模型全部不需要改码；§4 重写、§5 合并链标 S6 完成、§6 缺口表关闭三项；`call_deepseek`/`run_stage` 增加 `base_url`/`api_key` 显式入参（修复"model 换了 key 没换"的假替换） |
| v1.2 | 2026-11-09 | S7 接通：新增 `bridge` 交接点（只搬不解析，带 frontmatter 的工单由 Owner 放进批次目录）；§5 改为「A 与 B 已接通」并补八跳实测状态（2/5/6/7/8 已真跑，1/4 仍空）；§6 关闭「两条路未接」、新增「wt merge 超 180s 需 600s 且 600s 未经真实合并验证」 |
| v1.3 | 2026-11-09 | 收口：① `S-MAIN` 接到真在跑的本地 ollama（`127.0.0.1:11434` / `qwen3-8b-uncensored:latest`，原 18766 是无落地的自定端口），新增 `_as_bool`/`main_chat_url`/`call_main`，跳 1 真跑 12.4s 通过；② `MERGE_TIMEOUT=600` 经真实合并验证（**227.4s rc=0**，主线 `50af6549→3d0fc8dd`）；③ 发现并修复 `wt merge` 的 TARGET 缺省为 default branch（main）导致施工全铺到 main——`merge()` 增加 `target` 参数、默认取当前检出分支、CLI 加 `--target`；④ 补正 L72：上一单并非"没合入"，而是合进了 main（`d1e51eb3`），新增 L74 |
