# Codex 工单 · 0043 主脑 provider 抽象层与硬编码收敛

> 版本：v1.0 ｜ 状态：可开工 ｜ 适用工具：Codex
> 链路：`wo-ultimaagent-20261112-0043`
> 执行端：Codex（主脑不参与判据定夺）
> 前置：无硬前置（不依赖 0037–0042 任一单的产物）；现状基线为 HEAD `6df6b1a3` 的工作区，主脑在线可作回归对照
> 方案依据：`docs/plans/plan-ultimaagent-monolith-installer-lifecycle-provider-20261112.md` §4（provider 层）、§9（Owner 已决 8 条）
> 锁定 revision：`6df6b1a3`
> 工作目录锁定：`H:\UltimaAI\UltimaAgent`
> 用法：按 T0→T5 顺序执行，每 T 的 Gate 全绿再进下一条，禁止跳序。

---

## 0. 本单定位

本单只做一件事：把主脑接谁、怎么接，从**代码里写死**改成**配置决定**，并让"没配主脑"这件事**显式报出来**而不是静默失败。

背景事实（已实测，非推断）：

- 主脑接入当前写死在 **4 个文件、16 处**：
  - `src/brain/agent_server.py`：`ENGINE_KEY`(L138) / `MODEL`(L139) / `OLLAMA_CHAT_URL`(L176)，及 L388 / L445 / L455 / L683 / L697 / L773 / L788 / L996 / L1113 / L13 引用
  - `src/brain/mainbrain_proposal.py`：**第二份副本** `OLLAMA_CHAT_URL`(L22) / `MODEL`(L23)
  - `src/brain/agent_tools_ultima.py`：L107 `Jarvis(engine_key="ollama", model="qwen3-8b-uncensored")`
  - `src/brain/slot_adapter.py`：已有 `S-MAIN` 插槽配置（`impl`/`endpoint`/`model`/`enabled`），**这是本工程已有的 provider 雏形**
- `config/gorch/slots.json` **当前不存在**，`S-MAIN` 走内置默认且 `enabled=false`
- `agent_server.py` 走 **Ollama 原生 `/api/chat`**，依赖 `think` / `format`(JSON Schema) / `options.num_predict` 三个原生能力
- `slot_adapter.call_main()` 走 **OpenAI 兼容**，没有上述三个原生能力

**因此本单的正确形态不是"新建一套 provider 取代 slot_adapter"，而是**：`slot_adapter` 保留为**唯一配置权威源**，新增的 `src/brain/providers/` 只做**协议适配**（同配置、两种协议），`agent_server` 等消费方不再持有任何 model/url 字面量。

---

## 1. 范围冻结

**本阶段只做**

1. 新建 `src/brain/providers/`：协议适配层（`base.py` / `ollama_native.py` / `openai_compat.py` / `resolve.py`），**配置一律取自 `slot_adapter`，不自己读 json、不自己读环境变量**。
2. `agent_server.py` 的 4 个模型调用点改走 provider，**保留 `think` / `format` JSON Schema / `options.num_predict` 在 Ollama 路径下的原有语义**。
3. `mainbrain_proposal.py`、`agent_tools_ultima.py` 收敛到 `slot_adapter`，**删掉各自的 model/url 副本常量**。
4. `/health` 暴露 provider 身份（impl / model / enabled），**并在主脑未配置或不可达时给出显式状态**，不允许继续返回"看起来正常"。
5. 新增 `probe()` 连通性自检，供 `/health` 与安装向导复用。
6. 新增 `src/brain/tests/test_provider_layer.py`：协议选择、能力降级、空状态、单源断言四类用例。

**本阶段不做（Non-goals）**

1. **不改** `_risk_gate` / `_no_tool_gate` / `_clean_content` 三个门与 `MAINBRAIN_SYSTEM_PROMPT` / `_QUERY_SYSTEM` / `_ASK_CLASSIFY_SYSTEM` 任何提示词文本。
2. **不改** `slot_adapter.py` 的 `S-REVIEW` / `S-EXEC` 两个插槽的任何行为与默认值。
3. **不改** `orchestrator.call_deepseek` 的签名与行为。
4. **不动**语音链路：不碰 `src/voice-next/**`、`src/brain/voice/**`、`daemon.py`。
5. **不做** GUI：不碰 `src/host-shell/**`、`UltimaAgent.Hud/**`。
6. **不做**安装器：不建 `installer/`、不写 `.iss`。
7. **不引入** litellm / langchain / openai SDK 等新依赖，只用标准库 `urllib.request`（与现状一致）。
8. 不联网、不装依赖、不 `git add -A`、不改 `queue-status.json`。

---

## 2. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `src/brain/providers/*.py` + `src/brain/tests/test_provider_layer.py` | 两种协议各自构造出正确请求体；配置只来自 slot_adapter（单源断言） |
| T1 | `src/brain/agent_server.py` + 测试 | 4 个调用点零字面量；Ollama 路径 `think`/`format`/`num_predict` 语义不变 |
| T2 | `src/brain/mainbrain_proposal.py`、`src/brain/agent_tools_ultima.py` + 测试 | 副本常量删除；全仓 model/url 字面量只剩 slot_adapter 默认值一处 |
| T3 | `src/brain/agent_server.py`（`/health`）+ 测试 | provider 身份可见；未配置/不可达时显式状态，不伪装 ok |
| T4 | `src/brain/providers/probe.py` 或等价 + 测试 | `probe()` 三态（ok / unreachable / not-configured）各自可复现 |
| T5 | 回归 + 回执（`tasks/queue/wo-ultimaagent-20261112-0043--mainbrain-provider-layer.md`） | brain+orchestration 基线只增不减；实测 `/health` 与 `/ask` 仍工作 |

---

## 3. 任务明细

### T0 · 协议适配层

**文件**：`src/brain/providers/__init__.py`、`base.py`、`ollama_native.py`、`openai_compat.py`、`resolve.py`、`src/brain/tests/test_provider_layer.py`

**写什么**：

1. `base.py` 定义最小协议契约：一个 `ChatProvider` 抽象，方法 `chat(*, system_prompt, messages, temperature, max_tokens, json_schema=None, disable_thinking=False, timeout) -> ChatResult`；`ChatResult` 含 `content: str`、`raw: dict`、`usage: dict`。
2. `ollama_native.py`：`POST {endpoint}/api/chat`，body 保留 `stream=False`、`think`、`format`(schema)、`options{temperature,num_predict}`；响应解析 `message.content` 与 `usage`。**必须与 `agent_server.py` 现有 payload 逐字段等价**（本单不是重构请求体，只是把它搬进 provider）。
3. `openai_compat.py`：`POST {base}/chat/completions`，body 用 `messages` / `temperature` / `max_tokens`；`json_schema` 映射为 `response_format={"type":"json_schema", ...}`；`disable_thinking` 映射为**无动作**（OpenAI 兼容协议无 `think`，不得伪造字段）；响应解析 `choices[0].message.content` 与 `usage`。
4. `resolve.py`：`provider_for(settings) -> ChatProvider`，依据 `settings['impl']` 分派；**只认白名单取值**（`ollama` / `openai` / `openai-compatible` / `lmstudio` / `vllm` 视为 openai 兼容），未知 impl 抛 `ProviderConfigError`，**不回落默认值**。
5. `resolve.py` 的 `chat_url()` 复刻 `slot_adapter.main_chat_url()` 的三种写法归一逻辑（`/`、`/v1`、`/v1/chat/completions`），或直接复用该函数——**复用优先，不复制第二份实现**。
6. **单源硬约束**：本目录任何文件**不得**出现 `os.environ.get(` 读宿主配置、**不得**自己 `json.load` 读 `config/*.json`；一切配置来自调用方传入的 settings（由 `slot_adapter` 产出）。

**验收（Gate T0）**：

- `& H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest src/brain/tests/test_provider_layer.py -o addopts= -p no:cacheprovider -q` 全绿，贴完整输出。
- 用例断言：给同一组 settings，`ollama` 分支的请求体键集合包含 `think` / `format` / `options`，`openai` 分支的请求体**不含** `think` 且含 `max_tokens`，贴两条断言与 payload 差异输出。
- 用例断言：构造 `impl="weird"` 时抛 `ProviderConfigError`，**pytest 输出**中可见该异常用例判定为 PASS，贴该用例名与输出行。
- 单源断言：用例用 `pathlib` 扫 `src/brain/providers/` 全部 `.py` 源文本，断言不含 `os.environ`、不含 `json.load`、不含 `11434`、不含 `qwen3-8b`，贴扫描结果计数。

**禁止**：不得在 providers 内读环境变量或配置文件；不得为未知 impl 回落任一种协议；不得改变现有 Ollama payload 的任何字段名或取值。

---

### T1 · `agent_server.py` 四个调用点接入

**文件**：`src/brain/agent_server.py`、`src/brain/tests/test_provider_layer.py`

**写什么**：

1. 删除模块级 `MODEL` / `OLLAMA_CHAT_URL` / `ENGINE_KEY` 三个字面量常量，改为启动时经 `slot_adapter.main_settings()` 取一次生效设置（模块级 `_MAIN = ...`），失败要**在日志里明确写出原因**再降级为 `enabled=false` 的空设置，不得静默。
2. 四个调用点逐个改走 `providers.resolve.provider_for(_MAIN)`：
   - `_structured_reply`（原 L444-466）：`format=REPLY_JSON_SCHEMA` → `json_schema=REPLY_JSON_SCHEMA`，`think=False` → `disable_thinking=True`
   - `_classify_intent`（原 L682-706）：保留 `num_predict=256` 等价预算、`temperature=0`、思考开启
   - `_ask_query_branch` 直连（原 L772-797）：保留 `temperature=0.2`、`num_predict=max_tokens`
   - `get_jarvis()`（原 L388）：`Jarvis(engine_key=..., model=...)` 的参数改取 `_MAIN['impl']` 与 `_MAIN['model']`；**engine_key 的取值映射写进注释**（如 `ollama`→`"ollama"`），映射不到时明确报错
3. 保持异常路径原文措辞的可检索性：`StructuredReplyError`、`[ask] 查询直连失败` 等日志前缀不变。

**验收（Gate T1）**：

- `pytest src/brain/tests` 全绿（含新增用例），贴输出。
- 字面量清零断言：`rg -n '"qwen3-8b-uncensored"|"http://127.0.0.1:11434/api/chat"' src/brain/agent_server.py` 输出为空（注释行也须改掉），贴命令与空输出。
- 等价性断言：新增用例用 monkeypatch 替换 `urllib.request.urlopen` 捕获请求体，断言 `_structured_reply` 发出的 body 与改造前逐字段一致（`model` 取 `_MAIN['model']`，`format` 仍在顶层），贴断言与捕获到的 payload。
- `pytest src/brain/orchestration/tests` 全绿，贴输出。

**禁止**：不得把 `_structured_reply` 的 JSON Schema 约束换成"提示模型自己输出 JSON"；不得关闭 `_classify_intent` 的思考（关掉会使短判定返回空串，见 lessons-log 既有记录）；不得改任何 gate 函数。

---

### T2 · 另两处副本收敛

**文件**：`src/brain/mainbrain_proposal.py`、`src/brain/agent_tools_ultima.py`、`src/brain/tests/test_provider_layer.py`

**写什么**：

1. `mainbrain_proposal.py` 删除 `OLLAMA_CHAT_URL` / `MODEL` 两个常量，改为调用时取 `slot_adapter.main_settings()`；请求体结构与超时/温度/num_predict 三个常量**保持原值不动**。
2. `agent_tools_ultima.py` L107 的 `Jarvis(engine_key="ollama", model="qwen3-8b-uncensored")` 改为取生效设置；子代理工厂行为不变。
3. 两个模块均保留"配置不可用时报错"的既有路径，不新增静默兜底。

**验收（Gate T2）**：

- 全仓字面量扫描：`rg -n 'qwen3-8b-uncensored|127.0.0.1:11434' src/ --glob '!**/tests/**'` 只允许命中 `src/brain/slot_adapter.py` 的 `_DEFAULTS` 一处，贴完整输出并标注该行为唯一权威默认值。
- `pytest src/brain/tests` 全绿，贴输出。
- 用例断言 `mainbrain_proposal` 生成的请求体 `model` 字段与 `slot_adapter.main_settings()['model']` **相同**，贴断言输出。

**禁止**：不得把 `slot_adapter._DEFAULTS` 的默认值改掉（零配置行为必须与今天完全一致）；不得给 `mainbrain_proposal` 增加重试或备用地址。

---

### T3 · `/health` 暴露 provider 与未配置状态

**文件**：`src/brain/agent_server.py`、`src/brain/tests/test_provider_layer.py`

**写什么**：

1. `/health` 返回增加字段：`provider`（impl 字符串）、`provider_model`（生效 model）、`provider_configured`（bool）。
2. **保留向后兼容**：现有键 `ok` / `model` / `agent` / `tools` 一律保留且语义不变（`model` 值改为生效 model 的实际值，不再写字面量）。
3. 主脑未配置（`enabled=false` 或 endpoint 为空）时：`ok` **仍为 true**（服务本身活着），但 `provider_configured=false`，并在响应里加 `provider_note` 明确写"主脑未配置，/ask 将无法作答"，**禁止**把这种情况报告成一切正常。
4. 不改 `/ask` 的既有路由与响应结构（provider 信息只加在不影响既有消费者的位置）。

**验收（Gate T3）**：

- 实跑：`Invoke-RestMethod http://127.0.0.1:<当前端口>/health | ConvertTo-Json`，贴原始输出，可见新增三字段。
- 未配置态复现：用 `GORCH_MAIN_ENABLED=false` 起一个临时实例（独立端口），贴其 `/health` 输出，断言 `provider_configured=false` 且 `provider_note` 非空。
- 用例断言既有键仍存在（`ok`/`model`/`agent`/`tools` 四键齐备），贴断言。

**禁止**：不得在 `/health` 里做真实模型推理（会拖慢健康检查）；不得为未配置态返回非 200（监控会误判服务挂了）；不得删掉既有任何键。

---

### T4 · 连通性自检 `probe()`

**文件**：`src/brain/providers/probe.py`（或并入 `resolve.py`，二选一，不建两份）、`src/brain/tests/test_provider_layer.py`

**写什么**：

1. `probe(settings, timeout=5.0) -> ProbeResult`，`ProbeResult` 含 `state`（`"ok"` / `"unreachable"` / `"not-configured"` / `"unauthorized"`）、`detail`（人可读原因）、`latency_ms`。
2. 判定顺序：先判 `enabled` 与 endpoint 是否为空 → `not-configured`；再发一次最小请求（如 `GET {endpoint}/api/tags` 或 `GET {base}/models`）→ 通则 `ok`，401/403 则 `unauthorized`，其余连接类错误 `unreachable`。
3. 全路径**有超时上限**，不得无限等；异常一律转成 `state` 而不是抛出。

**验收（Gate T4）**：

- 三态用例各一：`not-configured`（`enabled=false`）、`unreachable`（指向 `http://127.0.0.1:1` 这种关闭端口）、`ok`（指向本机 11434 真实 ollama，若本机可用；不可用时该用例 skip 并注明），贴三条输出。
- 用例断言 `probe` 对关闭端口**在 timeout 内返回**而非挂起，贴**输出**中的实测耗时数值（该数值须 ≤ timeout）。

**禁止**：不得在 `probe` 里下发推理请求（只要模型清单级别的最小请求）；不得让 `probe` 抛异常给调用方。

---

### T5 · 回归与实跑

**文件**：`tasks/queue/wo-ultimaagent-20261112-0043--mainbrain-provider-layer.md`（回执段）

**写什么**：

1. 全量回归两组。
2. **实跑证据**：现网主脑重启后，`/health` 与一次真实 `/ask` 都要贴原始输出。重启必须走既有的 pid 锁与 Popen 方式（`python.exe -X utf8 src/brain/agent_server.py`，cwd=仓库根，日志接 `data/agent.stdout.log` / `data/agent.stderr.log`），**不得**用其它方式另起。
3. 回填本卡回执。

**验收（Gate T5）**：

- `pytest src/brain/tests src/brain/orchestration/tests` 通过数 **≥ 422 passed**（基线 422 passed / 1 failed，唯一失败 `test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains` 为环境噪声，允许继续存在但**不得新增失败**），贴完整输出。
- `/health` 实测输出贴出，含 `provider` / `provider_model` / `provider_configured`。
- `/ask` 实测一问一答的**原始输出**贴出（问题用「你是谁」这类不与工具/实时数据耦合的），证明改造后主脑仍能作答。
- `git status --porcelain -- tasks/queue/queue-status.json` 输出为空。

**禁止**：不得为了让测试变绿而跳过或改写既有断言；不得在真实队列上跑派发；不得重启语音链路。

---

## 4. 总验收

1. 全仓 model / endpoint 字面量只剩 `slot_adapter._DEFAULTS` 一处，且该处零配置行为与今天完全一致。
2. 两种协议各自可用；Ollama 路径保留 `think` / `format` / `num_predict` 三个原生能力，未降级为提示词约束。
3. 未配置主脑时 `/health` 显式报告，不伪装正常；`probe()` 四态可复现且不阻塞。
4. 三个 gate（`_risk_gate` / `_no_tool_gate` / `_clean_content`）与全部提示词文本零改动。
5. 语音链路与 GUI 零改动。
6. 回归只增不减；`/health` 与 `/ask` 实跑通过。

---

## 5. 禁止清单

1. 不得改 `_risk_gate` / `_no_tool_gate` / `_clean_content` / 任何 system prompt 文本。
2. 不得改 `slot_adapter` 的 `S-REVIEW` / `S-EXEC` 任何行为与默认值。
3. 不得引入 litellm / langchain / openai SDK 等新依赖。
4. 不得在 providers 内读环境变量或直接读配置文件（配置只经 slot_adapter）。
5. 不得为未知 impl 回落默认协议；不得静默兜底主脑不可用。
6. 不得碰 `src/voice-next/**`、`src/brain/voice/**`、`src/host-shell/**`、`installer/`。
7. 不得改 `queue-status.json`；不得 `git add -A`；不得联网装依赖。

---

## 回执（执行端填写）

- run 目录：
- 改动文件：
- T0-T5 逐 Gate 原始命令与输出：
- 全仓字面量扫描结果：
- `/health` 与 `/ask` 实跑输出：
- 已知限制：
