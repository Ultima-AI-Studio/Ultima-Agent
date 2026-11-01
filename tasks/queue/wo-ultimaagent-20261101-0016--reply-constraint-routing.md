# 工单 wo-ultimaagent-20261101-0016 ｜ UltimaAgent ｜ 工程 ｜ 意图路由门 + 回答校验器 + 主脑规则接入（工单 C）

> 原单 ID：`wo-ultimaagent-20261101-0016` ｜ 显示标题：UltimaAgent｜工程｜意图路由门+回答校验器+主脑规则接入
> 依据：G-DISPATCH-001 自主推进版 + G-TASKFLOW-001 ｜ 方案：`docs/plans/reply-constraint-implementation-plan-20261031.md`（工单 C 正式实施方案，2026-11-01 更新：模型引用 8B + 规则接入写域）
> 北极星：贾维斯（防"瞎回答"：域外/不可信输入入口拦截 + 出口校验兜底）
> 创建：2026-11-01 ｜ 状态：待派发

---

## 一、目标与范围

### 1.1 目标（Result）

**回答约束栈第 ①③ 层 + 主脑规则接入**：
1. **意图路由门**：ASR final 文本进 Agent 前三态判定 ALLOW / DENY / ABSTAIN——ALLOW（域内）进 Agent；DENY（域外/不可信/恶意）直接兜底话术不进 Agent；ABSTAIN（模糊/低置信）澄清式话术或重问，不进 Agent 自由发挥。
2. **回答校验器升级**：Agent 回答统一出口再过一道——banned_phrases 语义化（规则词 + nomic-embed 相似度双检）、≤2 句硬校验、grounded 字段真实性校验接口（工单 D 后启用，先留 schema）；FAIL → 有界 1 次重试 → 兜底话术。
3. **主脑规则接入**：`agent_server.py` system prompt 组装处接入 `docs/specs/mainbrain-rules-baseline.md` v1.0 规则块（恒加载；规则=第一道软约束，校验器=硬兜底）。

### 1.2 范围冻结（边界，禁止越界）

- **只做**：`src/brain/routing/`（新建模块）、interaction.py 接入、agent_server.py 规则组装、对应测试与证据。
- **禁止修改**：ollama / qwen3-8b-uncensored 模型与推理参数（0010 已切换，14B 蓝绿回滚保留）；jarvis.md 人设正文（如需只追加不改既有五条）；daemon 采集/ASR/KWS/TTS 主链；W6 UI；voice_profile.py（0003 冻结）；不杀/不重启守护进程；不引入云端意图 API（隐私红线）；不换推理栈。
- 主脑规则块以基线文档 v1.0 为唯一权威源，只读引用（不把规则正文复制进代码常量）。

### 1.3 写域

| 文件 | 动作 | 说明 |
|---|---|---|
| `src/brain/routing/intent_gate.py` | 新建 | 三态判定：规则层 + nomic-embed 相似度层（复用 memory/backend.py 嵌入通道），输出 ALLOW/DENY/ABSTAIN + 置信度 |
| `src/brain/routing/config.py`（或 JSON） | 新建 | 域内意图清单、DENY 关键词/句式、ABSTAIN 触发（低置信/ASR 标记）、兜底话术表 |
| `src/brain/interaction.py`（_try_agent_fallback 及统一出口） | 修改 | 接入路由门（进 Agent 前）+ 校验器升级（出口后） |
| `src/brain/agent_server.py`（system prompt 组装处） | 修改 | 接入 mainbrain-rules-baseline.md v1.0 规则块（恒加载） |
| `docs/specs/mainbrain-rules-baseline.md` | 只读 | 规则权威源（v1.0 已冻结 tag） |
| `src/brain/routing/tests/test_intent_gate.py` + `test_reply_verifier.py` | 新建 | 单测 |
| `docs/reports/stage-reply-constraint-c-20261101.md` + `docs/reports/evidence/reply-constraint-c/` | 新建 | 阶段报告与证据 |

---

## 二、DoR 就绪门

| # | 就绪项 | 判定 | 证据 |
|---|---|---|---|
| 1 | 验收 Gate 可判定 | ✅ 封闭清单（§四） | 路由拦截/正常回答/规则恒载/回归 |
| 2 | 无未决依赖 | ✅ nomic-embed-text 在位（ollama list 核验）；规则基线 v1.0 已冻结 | tag ultimaagent-mainbrain-rules-20261101 |
| 3 | 写入域已声明 | ✅ §1.3 | — |
| 4 | 推理强度已声明 | ✅ T0 medium / T1 medium / T2 medium / T3 high / T4 low | — |
| 5 | 禁止项已写 | ✅ §1.2 | — |

---

## 三、执行步骤（T0→T4，逐 T Gate PASS 再进下一条）

### T0 环境盘点（medium）
- [ ] C1 读 `src/brain/interaction.py` 现有路由/兜底/过滤调用链（_normalize_utterance / _try_agent_fallback / 统一出口），确认接入点。
- [ ] C2 确认 nomic-embed 可用：`ollama list` 有 nomic-embed-text；读 `memory/backend.py` 嵌入通道调用方式（复用，不改）。
- [ ] C3 确认 0003 banned 词实现位置（config/voice-profile.json style.banned_phrases）与测试基线。
- [ ] C4 读 `src/brain/agent_server.py` system prompt 组装处现状（jarvis.md 如何加载/拼装），确认规则块接入点。
- [ ] C5 证据落盘 `docs/reports/evidence/reply-constraint-c/t0-env-probe.txt`。
- Gate：C1-C5 全绿 → T1。

### T1 意图路由门实现（medium）
- [ ] C1 规则层：域内意图清单 + DENY 关键词/句式 + ABSTAIN 触发（低置信/ASR 修正标记）。
- [ ] C2 相似度层：embedding 余弦阈值（起步阈值可配，nomic-embed 复用 memory/backend.py 通道）。
- [ ] C3 三态输出 + 置信度；ABSTAIN 语义=低置信/歧义/含 ASR 修正标记。
- [ ] C4 证据 `t1-intent-gate.txt`：各态样例 + 判定日志（ALLOW/DENY/ABSTAIN 各 ≥3 例）。
- Gate：注入用例三态判定正确（含"水量天听"类不可信输入 → DENY/ABSTAIN）。

### T2 回答校验器升级（medium）
- [ ] C1 banned 语义化：规则词（现有 4 条）→ 词 + embedding 相似度双检（"请关注我"类句式拦截）。
- [ ] C2 ≤2 句硬校验 + 有界 1 次重试 → 兜底话术。
- [ ] C3 grounded 校验接口：schema 字段预留（工单 D 启用，先不生效）。
- [ ] C4 证据 `t2-verifier.txt`：banned 拦截样例 + 超句截断样例 + 重试路径样例。
- Gate：注入样例全过。

### T2.5 主脑规则接入（medium）
- [ ] C1 agent_server.py system prompt 组装处加载 mainbrain-rules-baseline.md v1.0 规则块（与 jarvis.md 角色五条拼接；规则正文不复制进代码常量，运行时读基线文件）。
- [ ] C2 验证恒加载：启动加载一次，每轮对话 prompt 含规则块（日志或测试断言）。
- [ ] C3 证据 `t25-rules.txt`：组装后 prompt 摘要 + 规则块在。
- Gate：规则块恒加载验证通过。

### T3 回归与收口（high）
- [ ] C1 全量回归：`tools/venv-openjarvis/Scripts/python.exe -m pytest src -q` 全绿（工程验收必须用 venv-openjarvis 解释器）+ 0003 voice-profile 专项绿。
- [ ] C2 注入用例：不可信输入（"水量天听"类/诱导编造）→ DENY/ABSTAIN 未进 Agent（日志 routing 标记 + 兜底话术）；"查天气/时间"正常回答不受影响。
- [ ] C3 冻结 tag：`git tag ultimaagent-reply-constraint-routing-20261101`（先 commit，`git rev-parse` 可解析）；**推送用免代理：`git -c http.proxy= -c https.proxy= -c http.https://github.com.proxy= push`**。
- [ ] C4 阶段报告 `docs/reports/stage-reply-constraint-c-20261101.md`。
- Gate：C1-C4 全绿 → T4。

### T4 回执（low）
八字段（见 §五）。

---

## 四、验收口径（封闭清单，全绿才过）

| Gate | 判定 | 证据位置 |
|---|---|---|
| 机制 | 路由门命中 DENY/ABSTAIN → 未进 Agent（日志 routing 标记 + 兜底话术播报）；规则块恒加载 | t1/t2/t25 + stage 报告 |
| 功能 | "查天气/时间/日程"正常回答不受影响；"水量天听"类不可信输入被拦；banned 语义化（"请关注我"类）拦截 | t2-verifier.txt + t3 注入 |
| 回归 | pytest 全量绿（venv-openjarvis）+ 0003 专项绿 | t3/ |
| 冻结 | tag `ultimaagent-reply-constraint-routing-20261101` 存在且可解析 | git tag -l |

---

## 五、执行端回执（八字段，必填）

| 字段 | 值 |
|---|---|
| 链路号/工单号 | wo-ultimaagent-20261101-0016 |
| 执行端 | Codex（gpt-5.6-sol，codex exec） |
| 完成状态 | 已完成 / 阻塞 / 已终止（三选一） |
| 根因结论 | （一句话） |
| 产出路径 | src/brain/routing/、interaction.py、agent_server.py、测试、stage 报告、evidence/ |
| 验收证据 | T0-C1~C5 / T1 / T2 / T2.5 / T3-C1~C4 逐条 PASS + pytest 摘要 + 路由判定日志 |
| 越界声明 | 无=明确写"无"；含未动范围（模型/推理参数/jarvis.md 正文/daemon/voice_profile/UI） |
| 环境声明 | 真机：路由门真实链路实测；如仅单测须写"仅单测预期，真机待验收" |

## 附：推理强度
T0 medium ｜ T1 medium ｜ T2 medium ｜ T2.5 medium ｜ T3 high ｜ T4 low
