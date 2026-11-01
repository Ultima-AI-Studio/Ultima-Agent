# UltimaAgent 回答约束工单 C 阶段报告（2026-11-01）

工单：`wo-ultimaagent-20261101-0016`
范围：意图路由门、回答校验器、主脑规则运行时接入
状态：技术实现与本单自验通过；待独立审计 / Owner 冻结门

## T0 环境盘点

- C1 PASS：已定位 raw ASR → `handle()` → 确定性路由 → `_try_agent_fallback()` → `_respond()`；路由门须在归一化前检查原文。
- C2 PASS：`nomic-embed-text:latest` 在位；复用 `memory/backend.py` 相同的本地 Ollama/nomic 通道，不修改记忆后端。
- C3 PASS：0003 基线为 4 条 banned phrase + `max_sentences=2`；专项基线 `13 passed`。
- C4 PASS：已定位 `agent_server.py:ask_once()` 每轮 `Jarvis.ask_full()` 调用；规则源 tag `38551c2` 可解析。
- C5 PASS：证据已落盘，并建立目标文件预工作快照以隔离既有未提交改动。

证据：`docs/reports/evidence/reply-constraint-c/t0-env-probe.txt`

## T1 意图路由门

- C1 PASS：规则层覆盖域内天气/时间/日程/任务/设置/设备/搜索/闲聊，以及提示词注入、诱导编造、营销和明确伤害请求。
- C2 PASS：相似度层复用本地 Ollama `nomic-embed-text`；阈值可配（ALLOW/DENY `0.82`，margin `0.04`），嵌入异常时保守 ABSTAIN。
- C3 PASS：输出 `ALLOW / DENY / ABSTAIN + confidence + reason`；低 ASR 置信度、修正标记和已知不可信片段进入 ABSTAIN。
- C4 PASS：三态各 3 个样例及判定日志已落盘；专项 `13 passed`。

证据：`docs/reports/evidence/reply-constraint-c/t1-intent-gate.txt`

## T2 回答校验器

- C1 PASS：读取现有 4 条 banned phrase，先做句式规则检查，再用本地 nomic 对完整营销意图做语义双检；“欢迎持续留意我的频道”以 `0.9912` 命中。
- C2 PASS：超过 2 句硬截断到前 2 句；规则/语义拒绝后只重试 1 次，第二次仍失败固定兜底“收到。”。
- C3 PASS：`ReplySchema(reply_text, confidence, grounded)` 已预留；工单 C 默认 `grounded_checked=False`，测试覆盖未来启用开关。
- C4 PASS：规则 banned、语义 banned、超句截断、重试成功和重试耗尽兜底样例已落盘；专项 `19 passed`。

证据：`docs/reports/evidence/reply-constraint-c/t2-verifier.txt`

## T2.5 主脑规则接入

- C1 PASS：`agent_server.py` 启动时读取 `jarvis.md` 与 `mainbrain-rules-baseline.md` v1.0 的可嵌入代码块；规则正文未复制进代码常量。
- C2 PASS：两轮 `NativeReActAgent.run()` 的捕获消息均存在 `role=SYSTEM` 且含同一规则块；测试在两轮期间禁止 `Path.read_text`，证明启动加载一次、每轮恒带、每轮文件读取为 0。
- C3 PASS：组装摘要、源文件 SHA-256、规则标记与两轮断言已落盘；最终相关专项 `34 passed`。

说明：当前 `Jarvis.ask_full()` 无独立 `system_prompt` 参数，`agent_server.py` 通过 `native_react` 既有 system-prompt loader 注入启动时缓存的组合模板；用户消息保持独立。未改底座源码、agent、模型或推理参数。

证据：`docs/reports/evidence/reply-constraint-c/t25-rules.txt`

## T3 回归与收口

- C1 PASS：指定 Python 3.13.16 全量 `pytest src -q` 最终退出 0，`816 passed + 120 subtests passed`；0003 专项 `13 passed`。
- C2 PASS：注入链路 `4 passed`；“水量天听”→ ABSTAIN、诱导编造→ DENY，均断言 Agent 未调用；天气走原确定性路径，时间正常进入 Agent。
- C3 PASS：精确暂存 18 个本单文件；实现 commit `a3fca7c3751e8a2f3227c29b6eb3c09455ae0490`；tag `ultimaagent-reply-constraint-routing-20261101` 与远端 `main` 独立读回均解析到该 commit。
- C4 PASS：阶段报告与 T0/T1/T2/T2.5/T3 证据齐备。

证据：

- `docs/reports/evidence/reply-constraint-c/t3-regression.txt`
- `docs/reports/evidence/reply-constraint-c/t3-injection.txt`
- `docs/reports/evidence/reply-constraint-c/t3-git.txt`

### 已知但未越界修复

全量早期尝试暴露了预先存在且未跟踪的 memory 毫秒时间戳 flaky；相同最终命令已有真实退出 0。该模块不属 0016 写域，未修改、未暂存。详见 `t3-regression.txt`。

## 边界核验

- 未修改/暂存模型、推理参数、`jarvis.md` 正文、daemon 采集/ASR/KWS/TTS 主链、W6 UI、`voice_profile.py`、`memory/backend.py`。
- 未杀、未重启任何守护进程；未播放、未录音、未调用麦克风；未引入云端意图 API。
- 规则正文只从 `docs/specs/mainbrain-rules-baseline.md` v1.0 运行时读取，不复制进代码常量。
