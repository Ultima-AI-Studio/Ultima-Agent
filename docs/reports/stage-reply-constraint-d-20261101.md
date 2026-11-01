# UltimaAgent 回答约束工单 D 阶段报告（2026-11-01）

工单：`wo-ultimaagent-20261101-0017`
范围：Ollama 原生约束解码、结构化回答 schema、解析降级、grounded/confidence 校验
状态：T3 回归 PASS，Git 收口待执行

## 前置门

- PASS：工单 0016 已完成并推送；实现 tag `ultimaagent-reply-constraint-routing-20261101` → `a3fca7c3751e8a2f3227c29b6eb3c09455ae0490`。
- PASS：0016 报告回填 commit `c448a5dc21d1a21bfb817416e745fb7383a8826a` 已由远端 `origin/main` 独立读回。
- PASS：0016 终态回执为已完成；本单开始前未覆盖其执行中写域。

## T0 能力实测

- C1 PASS：`scripts/probe_ollama_format.py` 使用 qwen3-8b-uncensored 实测两种模式各 10 样本，覆盖天气/时间/任务/闲聊/注入。
- C2 PASS：`format="json"` 合法 JSON 10/10、schema 遵守 10/10；原生 JSON Schema grammar 合法 JSON 10/10、schema 遵守 10/10。
- C3 PASS：证据已落盘；结构非法输出 0，但记录了注入样本可能错误自报 grounded=true 的语义边界。
- 路径结论：选择 `ollama_native_schema`；不引入 Outlines，不更换推理栈。

证据：`docs/reports/evidence/reply-constraint-d/t0-probe.txt`

## T1 schema 定义与接入

- C1 PASS：`src/brain/reply/schema.py` 定义精确三字段 JSON Schema 与严格 parser，拒绝 schema 外形态和隐式类型转换。
- C2 PASS：`agent_server.py` 在现有工具 Agent 内部循环后，通过本地 Ollama `format=<schema>` 生成最终可见回答；`content` 只是 `reply_text` 兼容镜像。
- C3 PASS：解析失败走“原草稿 → 0016 ReplyVerifier → 安全结构/固定兜底”；非法营销草稿未裸播。
- Gate PASS：真实正常样本为合法三字段结构；非法 JSON 模拟安全降级；相关测试 `19 passed`。

证据：`docs/reports/evidence/reply-constraint-d/t1-schema.txt`

## T2 校验器启用

- C1 PASS：最终出口显式启用 grounded/confidence 校验；阈值为 `0.60`（回答验收阈值，不是推理参数）。
- C2 PASS：grounded=false 最多重试 1 次；重试成功放行，仍失败走固定兜底；低 confidence 直接兜底。
- C3 PASS：三条受控路径样例已落盘；D 专项 + 0016 verifier/intent/integration 组合 `34 passed`。
- Gate PASS：注入与失败路径均不裸播未验证内容。

证据：`docs/reports/evidence/reply-constraint-d/t2-verifier.txt`

## T3 回归与收口

- C1 PASS：专用解释器确认为 Python 3.13.16；执行 `tools\\venv-openjarvis\\Scripts\\python.exe -m pytest src -q`，结果 `852 passed, 36 warnings, 120 subtests passed in 242.85s`。
- C2 PASS：0016 专项 + D 专项组合 `43 passed`；注入/正常回答组合 `18 passed`；双保险显式用例 `6 passed`。
- C3 PASS：不可信输入由 0016 门拒绝/弃权，D 层另行阻断即使自报 `grounded=true` 的营销形态；正常问答最多两句。
- 回归修复：发现并消除每轮读取 voice profile 的副作用，改为模块启动时读取现有风格约束；未修改 `voice_profile.py`，未改产品默认值；焦点复测 `1 passed`。
- Git 精确写域收口、tag、免代理推送与远端读回：待执行。

证据：`docs/reports/evidence/reply-constraint-d/t3-regression.txt`

## T4 八字段回执

待执行。
