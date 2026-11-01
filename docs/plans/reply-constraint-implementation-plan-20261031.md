# UltimaAgent 回答约束实施计划（工单 C + 工单 D）

> 方案：2026-10-31 豆包主脑 ｜ 依据调研：`docs/research/agent-reply-constraint-research-20261031.md`
> 上游规则：G-TASKFLOW-001（登记→计划评审→执行→审计→修复→验收→冻结）+ G-PLAN-001（先方案后工单，方案随单落盘）
> 北极星：贾维斯 ｜ 现状基线：0003 voice-profile 已落地（jarvis.md 五条软约束 + banned 词过滤 + 超句截断）
> 本文件为工单 C、工单 D 的**正式实施方案**，派发工单时随单引用；两单独立编号、独立验收、独立冻结。

---

## 〇、总览（三层约束栈）

```
用户语音 → ASR final 文本
   │
   ▼
① 意图路由门（工单 C 交付）        ← 域外/模糊/不可信 → 兜底话术（不进 Agent）
   │  ALLOW
   ▼
② Agent 生成（工单 D 交付）        ← 约束解码：输出固定 JSON {reply_text, confidence, grounded}
   │
   ▼
③ 回答校验器（工单 C 交付）        ← banned 语义化 + grounded 真实性 + ≤2 句硬校验；FAIL → 有界 1 次重试 → 兜底
   │
   ▼
④ 语音播报（现状不变）
```

**依赖关系**：工单 C 先行（入口+出口闭环，立即止血）；工单 D 依赖 C 的出口稳定后再做（生成期硬约束，根治）。

---

# 工单 C（先做）｜意图路由门 + 回答校验器升级

**拟命名**：`wo-ultimaagent-<日期>-<NNNN>--reply-constraint-routing.md`（编号随派发时核发）

## C.1 目标

1. **意图路由门**：ASR final 文本进入 Agent 前先三态判定 ALLOW / DENY / ABSTAIN：
   - ALLOW（域内：查天气/时间/日程/任务/闲聊等）→ 进 Agent；
   - DENY（域外/不可信/恶意）→ 直接走兜底话术，**不进 Agent**；
   - ABSTAIN（模糊/歧义/ASR 低置信）→ 澄清式话术或重问，**不进 Agent 自由发挥**。
2. **回答校验器升级**：Agent 兜底回答在统一出口再过一道：
   - banned_phrases 升级为语义化（规则词 + nomic-embed 相似度双检）；
   - 校验 ≤2 句硬约束；
   - 校验 grounded 字段真实性（工单 D 后启用，先留接口）；
   - FAIL → 有界 1 次重试 → 仍 FAIL 走兜底话术。

## C.2 范围冻结

- 只做：路由模块（新增）、校验器升级（interaction 层）、兜底话术表（新增配置）、对应测试与证据。
- **禁止修改**：ollama / qwen3-8b-uncensored 模型与推理参数（0010 已切换主脑，14B 蓝绿回滚保留）；jarvis.md 人设正文（如需可只追加不改既有五条）；daemon 采集/ASR/KWS/TTS 主链；W6 UI；voice_profile.py（0003 冻结）；不杀/不重启守护进程。
- 不引入云端意图 API（隐私红线）；不换推理栈。

## C.3 写域

| 文件 | 动作 | 说明 |
|---|---|---|
| `src/brain/routing/intent_gate.py` | 新建 | 三态判定：规则层 + nomic-embed 相似度层（复用 `memory/backend.py` 嵌入通道），输出 ALLOW/DENY/ABSTAIN + 置信度 |
| `src/brain/routing/config.py` 或 JSON | 新建 | 域内意图清单、DENY 关键词/句式、ABSTAIN 触发（低置信/ASR 标记）、兜底话术表 |
| `src/brain/interaction.py`（`_try_agent_fallback` 及统一出口） | 修改 | 接入路由门（进 Agent 前）+ 校验器升级（出口后） |
| `src/brain/agent_server.py`（system prompt 组装处） | 修改 | 接入主脑底层规则块（`docs/specs/mainbrain-rules-baseline.md` v1.0 全文，恒定加载；规则=第一道软约束，校验器兜底） |
| `src/brain/routing/tests/test_intent_gate.py` + `test_reply_verifier.py` | 新建 | 单测 |
| `docs/reports/stage-reply-constraint-c-<日期>.md` + `docs/reports/evidence/reply-constraint-c/` | 新建 | 阶段报告与证据 |

## C.4 执行步骤（T0→T4，逐 Gate）

- **T0 环境盘点（medium）**：读 `interaction.py` 现有路由/兜底/过滤调用链；确认 nomic-embed 可用（`ollama list` 有 nomic-embed-text）；确认 0003 banned 词实现位置与测试基线；输出 `t0-env-probe.txt`。
- **T1 意图路由门实现（medium）**：规则层（域内意图清单 + DENY 词/句式）→ 相似度层（embedding 余弦阈值，起步阈值可配）→ 三态输出；ABSTAIN 语义=低置信/歧义/含 ASR 修正标记；证据 `t1-intent-gate.txt`（各态样例 + 判定日志）。
- **T2 回答校验器升级（medium）**：banned 语义化（词 → 词 + embedding 相似度）；≤2 句硬校验；grounded 校验接口（工单 D 启用，先留 schema 字段）；FAIL → 有界 1 次重试 → 兜底；证据 `t2-verifier.txt`。
- **T3 回归与收口（high）**：`tools/venv-openjarvis/Scripts/python.exe -m pytest src -q` 全绿 + 0003 voice-profile 专项绿；注入用例（"水量天听"类不可信输入 → DENY/ABSTAIN 不进 Agent；"查天气" → 正常）；git commit + tag `ultimaagent-reply-constraint-routing-<日期>`；阶段报告。
- **T4 回执（low）**：八字段。

## C.5 验收口径（封闭清单）

| Gate | 判定 |
|---|---|
| 机制 | 路由门命中 DENY/ABSTAIN → 未进 Agent（日志可见 routing 标记 + 兜底话术播报） |
| 功能 | "查天气/时间/日程"正常回答不受影响；"水量天听"类不可信输入被拦；banned 语义化（如"请关注我"句式）拦截 |
| 回归 | pytest 全绿（venv-openjarvis）+ 0003 专项全绿 |
| 冻结 | tag `ultimaagent-reply-constraint-routing-<日期>` 存在可解析 |

## C.6 推理强度

T0 medium ｜ T1 medium ｜ T2 medium ｜ T3 high ｜ T4 low

---

# 工单 D（后续，依赖 C）｜约束解码结构化输出

**拟命名**：`wo-ultimaagent-<日期>-<NNNN>--reply-constraint-structured-output.md`（编号随派发时核发）

## D.1 目标

Agent 生成期**硬约束**：回答不再是自由文本，而是固定 JSON 结构 `{"reply_text": str, "confidence": float, "grounded": bool}`：
- `reply_text`：≤2 句短句，无 markdown/表情；
- `confidence`：模型自评置信度（0~1）；
- `grounded`：是否有真实依据（输入原文/工具返回/检索结果）。
**模型在解码阶段被约束**，schema 之外的"瞎话形态"（营销话术、编造、跨轮旧文本）在生成期即不可能产出。

## D.2 范围冻结

- 只做：ollama format/grammar 约束解码实测与接入、schema 定义、调用层改造、降级路径、测试与证据。
- **禁止修改**：模型权重/推理温度等全局参数（如确需调参须先走基线文档评估）；jarvis.md 人设正文（可只追加结构输出指令）；daemon 主链；W6 UI；voice_profile.py（0003 冻结）。
- 不引入云端结构化输出 API；不换推理栈（vLLM 等暂不做，实测 ollama 能力不足时评估 Outlines 包装，仍本地）。

## D.3 写域

| 文件 | 动作 | 说明 |
|---|---|---|
| `src/brain/agent_server.py`（或底座 agent 调用层） | 修改 | 接入约束解码；解析 schema → 取 reply_text/confidence/grounded |
| `src/brain/reply/schema.py` 或 JSON | 新建 | 输出 JSON schema（Pydantic 或 dict 定义） |
| `src/brain/routing/reply_verifier.py` | 修改 | 启用 grounded 校验（工单 C 留的接口）：grounded=false 或 confidence 低于阈值 → 重试/兜底 |
| `scripts/probe_ollama_format.py` | 新建 | 实测 ollama format/grammar 对 qwen3-8b-uncensored 的 JSON schema 遵守率（样本集） |
| `src/brain/reply/tests/test_structured_reply.py` | 新建 | 单测 |
| `docs/reports/stage-reply-constraint-d-<日期>.md` + `docs/reports/evidence/reply-constraint-d/` | 新建 | 阶段报告与证据 |

## D.4 执行步骤（T0→T4，逐 Gate）

- **T0 能力实测（high）**：`scripts/probe_ollama_format.py` 实测 qwen3-8b-uncensored 在 `format: json`/grammar 下输出合法 JSON 的比率（≥10 样本：天气/时间/任务/闲聊/注入）；记录 schema 字段遵守率、非法输出形态；**实测结论决定主路径**（ollama 原生 vs Outlines 包装）；证据 `t0-probe.txt`。
- **T1 schema 定义与接入（medium）**：定义 `{reply_text, confidence, grounded}` schema；接入 agent 调用层；解析失败/非法 JSON 走降级（自由文本 + 校验器兜底）；证据 `t1-schema.txt`。
- **T2 校验器启用（medium）**：`reply_verifier` 启用 grounded/confidence 校验：grounded=false → 有界 1 次重试 → 兜底；confidence<阈值 → 兜底；证据 `t2-verifier.txt`。
- **T3 回归与收口（high）**：pytest 全绿（venv-openjarvis）+ C 单专项绿；注入用例全过（"水量天听"类在 C 门拦截 + D 结构层双保险）；git commit + tag `ultimaagent-reply-constraint-structured-<日期>`；阶段报告。
- **T4 回执（low）**：八字段。

## D.5 验收口径（封闭清单）

| Gate | 判定 |
|---|---|
| 机制 | agent 输出恒为合法 JSON 结构（实测遵守率记录在案）；非法输出走降级不裸播 |
| 功能 | 注入不可信输入：C 门拦截或 D 结构层 grounded=false → 不播编造内容；正常问答 reply_text ≤2 句无营销 |
| 回归 | pytest 全绿 + C 单专项全绿 |
| 冻结 | tag `ultimaagent-reply-constraint-structured-<日期>` 存在可解析 |

## D.6 推理强度

T0 high ｜ T1 medium ｜ T2 medium ｜ T3 high ｜ T4 low

---

## 附：与在途工单的关系

- 工单 A（0009，KWS 改词）：**已 completed（2026-11-01 核验，tag ultimaagent-kws-wakeword-reconfig-20261031）**，与本计划无写域重叠（scripts + KWS 词链 vs 本计划 interaction/routing/agent_server）。
- 0008（GPT-SoVITS 训练）：写域在训练包，与本计划无重叠。
- **2026-11-01 更新**：工单 C 本次派发 = `wo-ultimaagent-20261101-0016`（意图路由门+校验器+主脑规则接入，规则基线 `docs/specs/mainbrain-rules-baseline.md` v1.0）；工单 D 本次派发 = `wo-ultimaagent-20261101-0017`（约束解码，依赖 0016 出口稳定后启动）。0016 写域新增 agent_server.py 规则组装（见 C.3）。
