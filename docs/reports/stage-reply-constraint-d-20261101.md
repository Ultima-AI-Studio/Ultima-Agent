# UltimaAgent 回答约束工单 D 阶段报告（2026-11-01）

工单：`wo-ultimaagent-20261101-0017`
范围：Ollama 原生约束解码、结构化回答 schema、解析降级、grounded/confidence 校验
状态：完成（T0–T4 PASS）

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
- 并行提交后的最终主线复测 PASS：再次执行全量 `pytest src -q`，结果仍为 `852 passed, 36 warnings, 120 subtests passed in 170.80s`。
- C4 PASS：仅精确暂存本工单 13 个文件/片段；`agent_server.py` 中并行 HUD 事件改动未进入提交；`git diff --cached --check` 与暂存版本编译均通过。
- C5 PASS：实现 commit `5ef3ec30a8635b3232d78a1edcabdc7362d9ae07`（`feat: 工单 0017 约束解码结构化输出`）；tag `ultimaagent-reply-constraint-structured-20261101` 精确指向该提交。
- C6 PASS：branch/tag 均以代理配置显式置空方式推送，并由 `ls-remote` 独立读回。初始 DNS 边缘地址 443 不可达，经有界诊断后在保持 `github.com` 主机名和 TLS 校验的前提下，为本次命令临时指定可达 GitHub 边缘地址。
- 并发保护：另一授权工单在 push 前于本提交之上生成 `b4fb88a37660d081fce43fd8da4ab50e876b6708`；未覆盖、回退或拆除该提交。远端 `main` 读回为 `b4fb88a...`，0017 的不可变 tag 读回为 `5ef3ec3...`。

证据：`docs/reports/evidence/reply-constraint-d/t3-regression.txt`、`docs/reports/evidence/reply-constraint-d/t3-git.txt`

## T4 八字段回执

- 链路号：`wo-ultimaagent-20261101-0017`
- 执行端：Ultima coding executor；`H:\\UltimaAI\\UltimaAgent`
- 完成状态：PASS；T0–T4 全部完成，实现提交与 tag 已推送且独立读回
- 根因结论：自由文本出口缺少生成期形状边界；实测对象支持 Ollama 原生 JSON Schema，但 `grounded` 自报仍须校验器强制执行
- 产出路径：`src/brain/reply/schema.py`、`src/brain/agent_server.py`、`src/brain/routing/reply_verifier.py`、probe、阶段报告与 evidence 目录
- 验收证据：T0 20/20；全量 `852 passed + 120 subtests`；0016+D `43 passed`；注入/正常 `18 passed`；显式双保险 `6 passed`；commit/tag/远端读回见 T3
- 越界声明：未改模型权重/全局推理参数、`jarvis.md` 人设正文、daemon 主链、W6 UI、`voice_profile.py`；未引云端结构化 API、Outlines、vLLM 或更换推理栈；并行脏改动均保留且未混入
- 环境声明：Windows PowerShell；专用 Python 3.13.16；本地 Ollama 0.32.15 / qwen3-8b-uncensored；未使用默认 Python312；push 代理项显式置空

机器可读回执：`docs/reports/evidence/reply-constraint-d/t4-receipt.txt`
