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

## 4. 替换方式：配置点 vs 需改代码

| 插槽 | 配置点 | 现状 | 换实现要不要改代码 |
|---|---|---|---|
| `S-MAIN` | `MAINBRAIN_BASE_URL` / `MAINBRAIN_MODEL`（**尚未建立**） | 8B 未起（18766 无监听、ollama 无模型） | 要：现在没有读取这两个变量的入口 |
| `S-REVIEW` | `DEEPSEEK_API_BASE`（`config/.env`，已读）· `DEFAULT_MODEL`（4 处各自硬编码） | 可换 base_url；**model 硬编码在 4 个位置**（`orchestrator.py:19`、`audit-work-order.py:58`、`loop/external_executor.py:28`、`interaction.py:395` 写的是 `deepseek-flash`） | 换 model 要改代码（4 处）；换 base_url 不改代码 |
| `S-EXEC` | `ULTIMA_CODEX_EXE`（可覆盖 exe 路径） | 只能换 codex 的二进制位置 | **换 CLI 类型必须改代码**：`run_codex` 的 cmd 是 codex 专属参数（`-a never` / `exec` / `-m` / `--sandbox` / `--output-last-message`） |

> 结论：**契约上三插槽都可替换；代码上只有 `S-REVIEW` 的 base_url 和 `S-EXEC` 的 exe 路径能纯配置替换。其余要改代码。**

---

## 5. 当前实际链路（两条，尚未接通）

| 路径 | 入口 | 覆盖环节 | 状态 |
|---|---|---|---|
| A：审议链 | `run-gorch.py` → `orchestrate-order.py` → `orchestrator.run_stage` → DeepSeek | 需求 → 理解/拆解 → 工单 → 排程 | 有实现、有调用方；只到 ④ |
| B：执行链 | `batch_orchestrator.py` → `gate` / `provision` / `execute` → `codex_channel.py` | 开工判定 → 隔离位 → 并发执行 | **S5 已真实跑通** |
| 合并链 | `batch_orchestrator.py merge/remove` | 串行合并 → 清理 | **S6 未写**，目前手调 `wt merge` |

**两条路没有接起来**：A 说完话就停，B 自己从 ccpm 读任务开始，中间没有东西把 A 的产出交给 B。这是 **S7（全链路串起来）** 的核心工作，也是"正式八跳一单都没跑过"的直接原因。

八跳实际的空档：

| 跳 | 环节 | 载体 | 现状 |
|---|---|---|---|
| 1 | 主脑理解 | `S-MAIN` | 空（8B 未起） |
| 2 | 审议·理解/方案 | `orchestrator` decompose | 有 |
| 3 | Owner 确认 | 人工 | 人工 |
| 4 | 主脑回传授权条件 | `S-MAIN` | 空 |
| 5 | 审议·拆解/工单 | `orchestrator` work_order | 有 |
| 6 | 审议·工单自检 | 同 stage 内自检 | 有 |
| 7 | 执行·写码/自检/提交 | `S-EXEC` | 有（S5 真实跑通） |
| 8 | 审议·复检 → 主脑汇报 → Owner 抽检 | `audit-work-order.py` / `S-MAIN` | 部分 |

---

## 6. 已知缺口（不粉饰）

| 缺口 | 影响 | 下一步 |
|---|---|---|
| 执行位硬编码 codex 命令行 | 换 Claude/Gemini/Qwen CLI 必须改代码 | 加 `S-EXEC` 适配器层；参考 golutra `default_members/*.rs` 的多 CLI 适配**思路**（不复制文件，因 BSL 1.1） |
| 回执两套结构 | 下游无法用同一套判定处理不同插槽产物 | §3 统一结构落地 |
| `model` 硬编码 4 处 | 换 model 要改 4 个文件，易漏改 | 收到 `DEEPSEEK_MODEL` 环境变量一处 |
| 主脑未接线 | 第 1、4 跳靠人工代做 | S7 前 |
| 两条路未接 | 无法一单跑完八跳 | S7 |
| S6 合并编排未写 | 合并靠手调 | S6 |
| 未接线插槽无 fail-closed | 若静默 fallback 到别的实现，会出现"以为换了其实没换" | 调用未配置插槽必须报错 |

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
