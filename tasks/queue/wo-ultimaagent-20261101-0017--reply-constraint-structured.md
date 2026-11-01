# 工单 wo-ultimaagent-20261101-0017 ｜ UltimaAgent ｜ 工程 ｜ 约束解码结构化输出（工单 D）

> 原单 ID：`wo-ultimaagent-20261101-0017` ｜ 显示标题：UltimaAgent｜工程｜约束解码结构化输出
> 依据：G-DISPATCH-001 自主推进版 + G-TASKFLOW-001 ｜ 方案：`docs/plans/reply-constraint-implementation-plan-20261031.md`（工单 D 正式实施方案，2026-11-01 更新：实测对象 8B）
> 北极星：贾维斯（生成期硬约束：回答恒为 {reply_text,confidence,grounded} 结构，schema 之外形态不可产出）
> 创建：2026-11-01 ｜ 状态：待派发（**依赖 0016 出口稳定后启动**）

---

## 一、目标与范围

### 1.1 目标（Result）

Agent 生成期**硬约束**：回答不再是自由文本，而是固定 JSON 结构 `{"reply_text": str, "confidence": float, "grounded": bool}`：
- `reply_text`：≤2 句短句，无 markdown/表情；
- `confidence`：模型自评置信度（0~1）；
- `grounded`：是否有真实依据（输入原文/工具返回/检索结果）。
**模型在解码阶段被约束**，schema 之外的"瞎话形态"（营销话术、编造、跨轮旧文本）在生成期即不可能产出。

### 1.2 范围冻结（边界，禁止越界）

- **只做**：ollama format/grammar 约束解码实测与接入、schema 定义、调用层改造、降级路径、测试与证据。
- **禁止修改**：模型权重/推理温度等全局参数（如确需调参须先走基线文档评估）；jarvis.md 人设正文（可只追加结构输出指令）；daemon 主链；W6 UI；voice_profile.py（0003 冻结）。
- 不引入云端结构化输出 API；不换推理栈（vLLM 等暂不做，实测 ollama 能力不足时评估 Outlines 包装，仍本地）。

### 1.3 写域

| 文件 | 动作 | 说明 |
|---|---|---|
| `scripts/probe_ollama_format.py` | 新建 | 实测 ollama format/grammar 对 qwen3-8b-uncensored 的 JSON schema 遵守率（样本集） |
| `src/brain/reply/schema.py`（或 JSON） | 新建 | 输出 JSON schema（Pydantic 或 dict 定义） |
| `src/brain/agent_server.py`（或底座 agent 调用层） | 修改 | 接入约束解码；解析 schema → 取 reply_text/confidence/grounded |
| `src/brain/routing/reply_verifier.py` | 修改 | 启用 grounded 校验（0016 留的接口）：grounded=false 或 confidence 低于阈值 → 重试/兜底 |
| `src/brain/reply/tests/test_structured_reply.py` | 新建 | 单测 |
| `docs/reports/stage-reply-constraint-d-20261101.md` + `docs/reports/evidence/reply-constraint-d/` | 新建 | 阶段报告与证据 |

---

## 二、DoR 就绪门

| # | 就绪项 | 判定 | 证据 |
|---|---|---|---|
| 1 | 验收 Gate 可判定 | ✅ 封闭清单（§四） | 遵守率/降级/校验器启用/回归 |
| 2 | 无未决依赖 | ✅ **依赖 0016 completed**（出口稳定后本单才可派发） | 全局登记 0016 状态 |
| 3 | 写入域已声明 | ✅ §1.3 | — |
| 4 | 推理强度已声明 | ✅ T0 high / T1 medium / T2 medium / T3 high / T4 low | — |
| 5 | 禁止项已写 | ✅ §1.2 | — |

---

## 三、执行步骤（T0→T4，逐 T Gate PASS 再进下一条）

### T0 能力实测（high）
- [ ] C1 `scripts/probe_ollama_format.py`：实测 qwen3-8b-uncensored 在 `format: json`/grammar 下输出合法 JSON 的比率（≥10 样本：天气/时间/任务/闲聊/注入）；记录 schema 字段遵守率、非法输出形态。
- [ ] C2 **实测结论决定主路径**（ollama 原生 vs Outlines 包装），结论落盘。
- [ ] C3 证据 `docs/reports/evidence/reply-constraint-d/t0-probe.txt`。
- Gate：C1-C3 全绿（结论明确，不要求遵守率达标，要求路径定案）→ T1。

### T1 schema 定义与接入（medium）
- [ ] C1 定义 `{reply_text, confidence, grounded}` schema（`src/brain/reply/schema.py`）。
- [ ] C2 接入 agent 调用层（agent_server.py 底座）；解析失败/非法 JSON 走降级（自由文本 + 校验器兜底，不裸播）。
- [ ] C3 证据 `t1-schema.txt`：schema 定义 + 接入点 + 降级路径样例。
- Gate：正常样本产出合法 JSON；非法样本走降级不崩溃。

### T2 校验器启用（medium）
- [ ] C1 `reply_verifier` 启用 grounded/confidence 校验：grounded=false → 有界 1 次重试 → 兜底；confidence<阈值 → 兜底。
- [ ] C2 证据 `t2-verifier.txt`：grounded=false 样例、低置信样例、重试路径样例。
- Gate：注入样例全过。

### T3 回归与收口（high）
- [ ] C1 全量回归：`tools/venv-openjarvis/Scripts/python.exe -m pytest src -q` 全绿（工程验收必须用 venv-openjarvis 解释器）+ 0016 专项绿。
- [ ] C2 注入用例全过：不可信输入（"水量天听"类在 0016 门拦截 + D 结构层双保险）；正常问答 reply_text ≤2 句无营销。
- [ ] C3 冻结 tag：`git tag ultimaagent-reply-constraint-structured-20261101`（先 commit，`git rev-parse` 可解析）；**推送用免代理：`git -c http.proxy= -c https.proxy= -c http.https://github.com.proxy= push`**。
- [ ] C4 阶段报告 `docs/reports/stage-reply-constraint-d-20261101.md`。
- Gate：C1-C4 全绿 → T4。

### T4 回执（low）
八字段（见 §五）。

---

## 四、验收口径（封闭清单，全绿才过）

| Gate | 判定 | 证据位置 |
|---|---|---|
| 机制 | agent 输出恒为合法 JSON 结构（实测遵守率记录在案）；非法输出走降级不裸播 | t0-probe.txt + t1-schema.txt |
| 功能 | 注入不可信输入：0016 门拦截或 D 结构层 grounded=false → 不播编造内容；正常问答 reply_text ≤2 句无营销 | t2-verifier.txt + t3 |
| 回归 | pytest 全量绿 + 0016 专项绿 | t3/ |
| 冻结 | tag `ultimaagent-reply-constraint-structured-20261101` 存在且可解析 | git tag -l |

---

## 五、执行端回执（八字段，必填）

| 字段 | 值 |
|---|---|
| 链路号/工单号 | wo-ultimaagent-20261101-0017 |
| 执行端 | Codex（gpt-5.6-sol，codex exec） |
| 完成状态 | 已完成 / 阻塞 / 已终止（三选一） |
| 根因结论 | （一句话） |
| 产出路径 | scripts/probe_ollama_format.py、src/brain/reply/、agent_server.py、reply_verifier.py、测试、stage 报告、evidence/ |
| 验收证据 | T0-C1~C3 / T1 / T2 / T3-C1~C4 逐条 PASS + pytest 摘要 + 遵守率实测 |
| 越界声明 | 无=明确写"无"；含未动范围（模型权重/全局推理参数/jarvis.md 正文/daemon/UI/voice_profile） |
| 环境声明 | 真机：agent 真实输出链路实测；如仅离线实测须写"仅离线预期，真机待验收" |

## 附：推理强度
T0 high ｜ T1 medium ｜ T2 medium ｜ T3 high ｜ T4 low
