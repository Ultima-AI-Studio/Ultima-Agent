# Codex 工单 · 0043 主脑 provider 抽象层与硬编码收敛

> 版本：v2.0 ｜ 状态：可开工 ｜ 适用工具：Codex
> 修订说明：v2.0 于 2026-11-12 首轮执行受阻后修订。扩 T2 范围（补 `memory/backend.py`、`orchestration/engine.py`），细化扫描判据为 AST 级，并把 `ultima-config.toml` 显式登记为已知未收口项。T0 / T1 的完成状态与证据不受本次修订影响。
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
- `src/brain/memory/backend.py`：L57 `memory_llm_model="qwen3-8b-uncensored"` / L58 `ollama_base_url="http://localhost:11434"` —— 记忆提取用本地 LLM 的**运行期默认值**
- `src/brain/orchestration/engine.py`：L121 `self._model_keys = ("qwen3-8b-uncensored",)` —— 路由判定"哪些 key 算本地模型"的**运行期常量**
- `src/brain/ultima-config.toml`：L9 `default_model = "qwen3-8b-uncensored"` —— 底座 openjarvis 的 bootstrap 注入配置（经 `OPENJARVIS_CONFIG` 生效），**与主脑 provider 不是同一条路径**；本单不改，只登记为未收口
- 上述后三项为首轮执行实测补充，原 §0 仅列 4 个文件，属建卡漏项，已并入 T2 范围（`ultima-config.toml` 除外）
- `config/gorch/slots.json` **当前不存在**，`S-MAIN` 走内置默认且 `enabled=false`
- `agent_server.py` 走 **Ollama 原生 `/api/chat`**，依赖 `think` / `format`(JSON Schema) / `options.num_predict` 三个原生能力
- `slot_adapter.call_main()` 走 **OpenAI 兼容**，没有上述三个原生能力

**因此本单的正确形态不是"新建一套 provider 取代 slot_adapter"，而是**：`slot_adapter` 保留为**唯一配置权威源**，新增的 `src/brain/providers/` 只做**协议适配**（同配置、两种协议），`agent_server` 等消费方不再持有任何 model/url 字面量。

---

## 1. 范围冻结

**本阶段只做**

1. 新建 `src/brain/providers/`：协议适配层（`base.py` / `ollama_native.py` / `openai_compat.py` / `resolve.py`），**配置一律取自 `slot_adapter`，不自己读 json、不自己读环境变量**。
2. `agent_server.py` 的 4 个模型调用点改走 provider，**保留 `think` / `format` JSON Schema / `options.num_predict` 在 Ollama 路径下的原有语义**。
3. `mainbrain_proposal.py`、`agent_tools_ultima.py`、`memory/backend.py`、`orchestration/engine.py` 收敛到 `slot_adapter`，**删掉各自的 model/url 副本常量与运行期默认字面量**；`memory/backend.py` 的两个形参保留、调用契约不变，只换默认值来源。
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
8. 不联网、不装依赖、不 `git add -A`、**不主动改** `queue-status.json`（派发器自身写入的本单状态流转副作用除外，见 Gate T5 判据）。

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

### T2 · 其余副本收敛（含记忆层与路由层）

> 修订 v2（2026-11-12，首轮执行受阻后）：实测锁定 revision `6df6b1a3` 上另有
> `memory/backend.py`（L57 默认模型 / L58 默认地址）、`orchestration/engine.py`（L121 路由 key 元组）
> 两处**运行时生效的**同类硬编码，原卡漏列；`interaction.py` L220、`memory/backend.py` L43/L110、
> `orchestration/engine.py` L94 为注释与 docstring 命中；`ultima-config.toml` L9 为底座 openjarvis
> 注入配置。据此扩范围并细化判据，判据**不放宽**。

**文件**：`src/brain/mainbrain_proposal.py`、`src/brain/agent_tools_ultima.py`、`src/brain/memory/backend.py`、`src/brain/orchestration/engine.py`、`src/brain/tests/test_provider_layer.py`

**写什么**：

1. `mainbrain_proposal.py` 删除 `OLLAMA_CHAT_URL` / `MODEL` 两个常量，改为调用时取 `slot_adapter.main_settings()`；请求体结构与超时/温度/num_predict 三个常量**保持原值不动**。
2. `agent_tools_ultima.py` L107 的 `Jarvis(engine_key="ollama", model="qwen3-8b-uncensored")` 改为取生效设置；子代理工厂行为不变。
3. `memory/backend.py`：`memory_llm_model` 与 `ollama_base_url` 两个形参**保留且调用契约不变**（显式传入仍以入参为准），只把**默认值**改为取 `slot_adapter.main_settings()` 的生效值。
4. `orchestration/engine.py`：`_model_keys` 不再写字面量元组，改为由生效设置推导；语义仍是"哪些模型 key 视为本地模型"，匹配行为不变。**该文件访问 `slot_adapter` 必须用绝对导入 `from src.brain.slot_adapter import main_settings`**，与 `agent_server.py` / `agent_tools_ultima.py` / `mainbrain_proposal.py` 三处既有写法一致；**禁止**使用 `from ..slot_adapter import ...` 这类双点相对导入——`orchestration` 存在顶层包与 `src.brain.orchestration` 两种加载形态，双点会越过顶层包导致 `ImportError: attempted relative import beyond top-level package`（该回归已在 2026-11-12 实测复现并由主脑修正）。
5. `interaction.py` L220、`memory/backend.py` L43/L110、`orchestration/engine.py` L94 的**注释与 docstring** 中的模型名/端口一并改写为中性表述（防止后人误读为活配置），不触及运行时逻辑。
6. 以上模块均保留"配置不可用时报错"的既有路径，不新增静默兜底。

**验收（Gate T2）**：

- **全量 AST 扫描**：遍历 `src/brain/**/*.py`（排除 `tests/`），抽取全部字符串常量，扫描目标为 `qwen3-8b-uncensored`（模型名）与 `11434`（Ollama 端口）两个字面量；**必须贴出全量输出**，不允许只贴过滤后的结果，以此证明扫描穷尽。
- 命中只允许落在这三处，逐处标明归属，并在**输出**里写清被命中的 `(file, lineno)`：（1）`src/brain/slot_adapter.py` 的 `_DEFAULTS` —— 唯一权威默认值，扫描**输出**须**含**该处；（2）`src/brain/routing/config.py` L11 的 `ollama_embed_url` —— embedding 相似度路由、非主脑 chat 路径，**记录**为未收口；（3）`src/brain/slot_adapter.py` L189 的 docstring —— 说明文字、非运行值，扫描**输出**中须**出现**该处的归属标注。
- 出现第四处即 Gate 失败；**不得**在执行过程中临时追加豁免，遇到新命中须停下来报回执。
- **`ollama-8b` 不在扫描目标内**：它是 impl 协议标识（枚举值），不是模型名也不是地址，因此出现在 `resolve.py` / `agent_server.py` / `agent_tools_ultima.py` 中属正常，扫描**输出**中不列为违规。
- 上述注释/docstring 行不再含模型名，贴 `rg` 空结果**输出**。
- `pytest src/brain/tests` 全绿，贴输出；`pytest src/brain/orchestration/tests` 全绿，贴输出。
- 用例断言 `mainbrain_proposal` 请求体的 `model` 字段与 `slot_adapter.main_settings()['model']` **相同**，贴断言输出。
- 双向断言 `memory/backend.py`：不显式传参时默认模型与生效 model **相同**；显式传参时仍以入参为准。两条都贴**输出**。
- **已知未收口清单**：回执中必须逐条**记录**，每条都要有能被 `grep` **定位**的**输出**：（1）`src/brain/routing/config.py` L11 `ollama_embed_url` —— 语义相似度路由的 embedding 直连地址，与主脑 chat 不是同一条路径，本单不改，回执须**记录**该条；（2）`src/brain/ultima-config.toml` L9 `default_model` —— 底座 openjarvis 的 bootstrap 注入配置（经 `OPENJARVIS_CONFIG` 生效），与主脑 provider 权威不是同一条路径，本单不改，回执须**记录**该条，**禁止**把上述任一条当作已收口，**记录**缺失即 Gate 失败。

**禁止**：不得把 `slot_adapter._DEFAULTS` 的默认值改掉（零配置行为必须与今天完全一致）；不得给 `mainbrain_proposal` 增加重试或备用地址；不得修改 `ultima-config.toml` 与 `routing/config.py`；不得删除 `memory/backend.py` 两个形参（只能改默认值来源）。

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
- `tasks/queue/queue-status.json` 的改动**只允许是派发器对本工单的状态流转副作用**：`git diff --numstat -- tasks/queue/queue-status.json` 的新增与删除行数**各自 ≤ 8**，且 `git diff -- tasks/queue/queue-status.json` 输出中**只出现 `wo-ultimaagent-20261112-0043` 这一个工单号**、不含任何其它工单记录变更。满足即视为未主动改。**不允许**用 `git restore` / `git stash` / 操作 index 的方式制造「porcelain 为空」的假象来通过本门。

**禁止**：不得为了让测试变绿而跳过或改写既有断言；不得在真实队列上跑派发；不得重启语音链路。

---

## 4. 总验收

1. **代码文件**（`src/brain/**/*.py`，排除 `tests/`）中的 model / endpoint 字面量，除 `slot_adapter._DEFAULTS` 外只允许 `routing/config.py` 的 `ollama_embed_url` 与 `slot_adapter` 自身 docstring 两处；前者与 `ultima-config.toml` 一并**显式登记为已知未收口项**，不算收口。`_DEFAULTS` 该处的零配置行为与今天完全一致。
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
7. **不得主动改** `queue-status.json`（派发器写入的本单状态流转副作用除外）；不得 `git add -A`；不得联网装依赖。

---

## 回执（执行端填写）

- 执行状态：**BLOCKED at revised v2 T2 AST Gate（按序停止，未进入 T3）**
- run 目录：`H:\UltimaAI\UltimaAgent\.superpowers\sdd\wo-ultimaagent-20261112-0043--mainbrain-provider-layer`
- 改动文件：
  - `src/brain/providers/__init__.py`
  - `src/brain/providers/base.py`
  - `src/brain/providers/ollama_native.py`
  - `src/brain/providers/openai_compat.py`
  - `src/brain/providers/resolve.py`
  - `src/brain/agent_server.py`
  - `src/brain/mainbrain_proposal.py`
  - `src/brain/agent_tools_ultima.py`
  - `src/brain/memory/backend.py`
  - `src/brain/orchestration/engine.py`
  - `src/brain/interaction.py`（仅把冻结字面量注释改为中性表述）
  - `src/brain/tests/test_provider_layer.py`
  - `src/brain/reply/tests/test_structured_reply.py`（仅把 monkeypatch 目标改到 provider，既有断言未改）
  - `src/brain/tests/test_prompt_boundary_p0.py`（仅把 monkeypatch 目标改到 provider，既有断言未改）
  - `tasks/queue/wo-ultimaagent-20261112-0043--mainbrain-provider-layer.md`（本回执）
  - `.superpowers/sdd/wo-ultimaagent-20261112-0043--mainbrain-provider-layer/progress.md`（执行 ledger）
  - `.superpowers/sdd/wo-ultimaagent-20261112-0043--mainbrain-provider-layer/t2_ast_scan.py`（T2 Gate 脚本）
- 未改文件：`tasks/queue/queue-status.json`。开工前该文件已是 `M`，本轮未还原、未覆盖、未暂存。
- 未改越界命中：`src/brain/routing/config.py`。该文件不在 v2 T2 写域，本轮只读取证。

### 基线（开工前）

原始命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/tests src/brain/orchestration/tests -o addopts= -p no:cacheprovider -q
```

原始输出（终端摘要）：

```text
FAILED src/brain/tests/test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains
1 failed, 434 passed, 25 warnings, 46 subtests passed in 87.90s (0:01:27)
```

失败原因为 `subprocess.run(["ollama", "list"])` 抛 `FileNotFoundError: [WinError 2]`，与工单预先声明的环境噪声一致。

### Gate T0

原始命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/tests/test_provider_layer.py -o addopts= -p no:cacheprovider -q
```

原始输出：

```text
..........                                                               [100%]
10 passed in 1.74s
T0_EXIT=0
```

payload / 未知 impl / 单源扫描证据命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/tests/test_provider_layer.py::test_ollama_native_payload_preserves_native_fields src/brain/tests/test_provider_layer.py::test_openai_compat_payload_maps_schema_without_think src/brain/tests/test_provider_layer.py::test_unknown_impl_raises_provider_config_error src/brain/tests/test_provider_layer.py::test_provider_sources_have_no_config_reads_or_hardcoded_defaults -o addopts= -p no:cacheprovider -vv -s
```

原始输出：

```text
============================= test session starts =============================
platform win32 -- Python 3.13.16, pytest-9.2.0, pluggy-1.7.0 -- H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe
rootdir: H:\UltimaAI\UltimaAgent
configfile: pytest.ini
plugins: anyio-4.15.1, langsmith-0.14.12
collecting ... collected 4 items

src/brain/tests/test_provider_layer.py::test_ollama_native_payload_preserves_native_fields ollama_payload={"format": {"required": ["reply_text"], "type": "object"}, "messages": [{"content": "system", "role": "system"}, {"content": "hello", "role": "user"}], "model": "test-model", "options": {"num_predict": 321, "temperature": 0.25}, "stream": false, "think": false}
PASSED
src/brain/tests/test_provider_layer.py::test_openai_compat_payload_maps_schema_without_think openai_payload={"max_tokens": 222, "messages": [{"content": "system", "role": "system"}, {"content": "hello", "role": "user"}], "model": "test-model", "response_format": {"json_schema": {"properties": {"answer": {"type": "string"}}, "type": "object"}, "type": "json_schema"}, "temperature": 0.1}
PASSED
src/brain/tests/test_provider_layer.py::test_unknown_impl_raises_provider_config_error PASSED
src/brain/tests/test_provider_layer.py::test_provider_sources_have_no_config_reads_or_hardcoded_defaults provider_scan files=5 banned_matches=0
PASSED

============================== 4 passed in 0.04s ==============================
T0_EVIDENCE_EXIT=0
```

### Gate T1

原始命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/tests -o addopts= -p no:cacheprovider -q
```

原始输出（唯一失败与获准基线相同）：

```text
........................................................................ [ 17%]
.F...................................................................... [ 35%]
.................................................................................................................. [ 62%]
................................................................................................................ [ 93%]
...........................                                              [100%]
================================== FAILURES ===================================
__________________ TestC1Environment.test_ollama_has_brains ___________________
E                                    FileNotFoundError: [WinError 2] 系统找不到指定的文件。
=========================== short test summary info ===========================
FAILED src/brain/tests/test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains
1 failed, 412 passed, 25 warnings, 46 subtests passed in 66.18s (0:01:06)
```

本次续行第一次复跑曾新增一个失败：`test_subagent_factory_uses_effective_main_settings` 在全套顺序中以第二个模块名导入 `agent_tools_ultima`，撞上 OpenJarvis 全局工具注册。先用以下最小命令稳定复现：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/tests/test_agent_tools_extend.py src/brain/tests/test_provider_layer.py::test_subagent_factory_uses_effective_main_settings -o addopts= -p no:cacheprovider -q
```

RED 原始输出：

```text
........F                                                                [100%]
FAILED src/brain/tests/test_provider_layer.py::test_subagent_factory_uses_effective_main_settings
1 failed, 8 passed in 4.83s
```

测试改为优先复用已加载的真实模块后，同命令 GREEN 原始输出：

```text
.........                                                                [100%]
9 passed in 1.92s
```

字面量清零原始命令：

```powershell
rg -n '"qwen3-8b-uncensored"|"http://127.0.0.1:11434/api/chat"' src/brain/agent_server.py
```

原始输出：

```text
```

命令退出码为 1，表示无匹配。

等价 payload / 分类思考 / Jarvis 映射证据命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/tests/test_provider_layer.py::test_agent_server_structured_reply_preserves_locked_ollama_payload src/brain/tests/test_provider_layer.py::test_agent_server_intent_classification_keeps_thinking_enabled src/brain/tests/test_provider_layer.py::test_agent_server_get_jarvis_maps_ollama_alias_and_model -o addopts= -p no:cacheprovider -vv -s
```

原始输出：

```text
============================= test session starts =============================
platform win32 -- Python 3.13.16, pytest-9.2.0, pluggy-1.7.0 -- H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe
rootdir: H:\UltimaAI\UltimaAgent
configfile: pytest.ini
plugins: anyio-4.15.1, langsmith-0.14.12
collecting ... collected 3 items

src/brain/tests/test_provider_layer.py::test_agent_server_structured_reply_preserves_locked_ollama_payload structured_payload={"format": {"additionalProperties": false, "properties": {"confidence": {"maximum": 1, "minimum": 0, "type": "number"}, "grounded": {"type": "boolean"}, "reply_text": {"minLength": 1, "type": "string"}}, "required": ["reply_text", "confidence", "grounded"], "type": "object"}, "messages": [{"content": "你是本地 Agent 的最终回答边界。输出必须严格匹配给定 JSON Schema，禁止 markdown 和额外文本。\nreply_text 最多两句，不含营销、关注、点赞或订阅话术。\nconfidence 是 0 到 1 的自评置信度。\ngrounded 仅当 reply_text 能被用户原文或工具证据直接支持时为 true；草稿本身不是证据。\n无法确认时将 grounded 设为 false，并在 reply_text 中简短说明无法可靠回答。\n", "role": "system"}, {"content": "{\"user_query\": \"状态？\", \"agent_draft\": \"完成。\", \"tool_evidence\": [], \"retry_note\": null}", "role": "user"}], "model": "configured-model", "stream": false, "think": false}
PASSED
src/brain/tests/test_provider_layer.py::test_agent_server_intent_classification_keeps_thinking_enabled PASSED
src/brain/tests/test_provider_layer.py::test_agent_server_get_jarvis_maps_ollama_alias_and_model PASSED

============================== 3 passed in 1.85s ==============================
```

orchestration 原始命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/orchestration/tests -o addopts= -p no:cacheprovider -q
```

原始输出：

```text
................................                                         [100%]
32 passed in 2.50s
```

### Gate T2（BLOCKED at first revised v2 Gate）

本次续行先为 v2 新增的 memory 默认/显式覆盖与 orchestration 动态 model key 写用例。RED 原始命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/tests/test_provider_layer.py::test_memory_backend_defaults_use_effective_main_settings src/brain/tests/test_provider_layer.py::test_memory_backend_explicit_settings_override_main_settings src/brain/tests/test_provider_layer.py::test_orchestration_model_key_is_derived_from_effective_main_settings -o addopts= -p no:cacheprovider -q -s
```

RED 原始输出：

```text
Fmemory_explicit={"endpoint": "http://explicit-memory.invalid", "model": "explicit-memory-model"}
.F
FAILED src/brain/tests/test_provider_layer.py::test_memory_backend_defaults_use_effective_main_settings
FAILED src/brain/tests/test_provider_layer.py::test_orchestration_model_key_is_derived_from_effective_main_settings
2 failed, 1 passed in 2.77s
```

实现后同命令 GREEN 原始输出：

```text
memory_defaults={"endpoint": "http://configured-memory.invalid", "model": "configured-memory-model"}
.memory_explicit={"endpoint": "http://explicit-memory.invalid", "model": "explicit-memory-model"}
.orchestration_model_key=configured-route-model
.
3 passed in 2.28s
```

随后执行 v2 T2 第一条正式 Gate。原始命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' '.superpowers\sdd\wo-ultimaagent-20261112-0043--mainbrain-provider-layer\t2_ast_scan.py'
```

AST 级字面量扫描脚本原文：

```python
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BRAIN = ROOT / "src" / "brain"
TOKENS = ("qwen3-8b-uncensored", "11434", "ollama-8b")


def _docstring_constants(tree: ast.AST) -> set[int]:
    ignored: set[int] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not body or not isinstance(body, list):
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            ignored.add(id(first.value))
    return ignored


def _defaults_span(tree: ast.AST) -> tuple[int, int]:
    for node in ast.walk(tree):
        target = None
        if isinstance(node, ast.Assign):
            target = node.targets[0] if len(node.targets) == 1 else None
        elif isinstance(node, ast.AnnAssign):
            target = node.target
        if isinstance(target, ast.Name) and target.id == "_DEFAULTS":
            return node.lineno, node.end_lineno or node.lineno
    raise AssertionError("slot_adapter._DEFAULTS assignment not found")


slot_tree = ast.parse((BRAIN / "slot_adapter.py").read_text(encoding="utf-8"))
defaults_start, defaults_end = _defaults_span(slot_tree)
matches: list[tuple[str, int, str]] = []

for path in sorted(BRAIN.rglob("*.py")):
    relative_parts = path.relative_to(BRAIN).parts
    if "tests" in relative_parts:
        continue
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    ignored = _docstring_constants(tree)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in ignored
        ):
            for token in TOKENS:
                if token in node.value:
                    matches.append(
                        (path.relative_to(ROOT).as_posix(), node.lineno, token)
                    )

outside_defaults = [
    item
    for item in matches
    if not (
        item[0] == "src/brain/slot_adapter.py"
        and defaults_start <= item[1] <= defaults_end
    )
]
covered = {token for _, _, token in matches}

print("AST_STRING_MATCHES")
for item in matches:
    print(item)
print(f"MATCH_COUNT={len(matches)}")
print(f"OFF_AUTHORITY_MATCHES={len(outside_defaults)}")
print("TOKENS_COVERED=" + ",".join(sorted(covered)))

assert not outside_defaults, outside_defaults
assert covered == set(TOKENS), (covered, set(TOKENS))
print("PASS: literals are confined to slot_adapter._DEFAULTS")
```

原始输出与命中的 `(file, lineno)` 清单：

```text
AST_STRING_MATCHES
('src/brain/agent_server.py', 408, 'ollama-8b')
('src/brain/agent_tools_ultima.py', 112, 'ollama-8b')
('src/brain/providers/resolve.py', 11, 'ollama-8b')
('src/brain/routing/config.py', 11, '11434')
('src/brain/slot_adapter.py', 35, 'ollama-8b')
('src/brain/slot_adapter.py', 39, '11434')
('src/brain/slot_adapter.py', 40, 'qwen3-8b-uncensored')
MATCH_COUNT=7
OFF_AUTHORITY_MATCHES=4
TOKENS_COVERED=11434,ollama-8b,qwen3-8b-uncensored
Traceback (most recent call last):
  File "H:\UltimaAI\UltimaAgent\.superpowers\sdd\wo-ultimaagent-20261112-0043--mainbrain-provider-layer\t2_ast_scan.py", line 79, in <module>
    assert not outside_defaults, outside_defaults
AssertionError: [('src/brain/agent_server.py', 408, 'ollama-8b'), ('src/brain/agent_tools_ultima.py', 112, 'ollama-8b'), ('src/brain/providers/resolve.py', 11, 'ollama-8b'), ('src/brain/routing/config.py', 11, '11434')]
ast_scan_exit=1
```

判定：Gate 要求三个字面量只命中 `slot_adapter._DEFAULTS`，实际有 4 个越权命中，因此 T2 Gate 未过，按工单停止。

- `agent_server.py:408`、`agent_tools_ultima.py:112`、`providers/resolve.py:11` 是上一轮 T0/T1 为冻结默认 `impl='ollama-8b'` 增加的兼容别名；v2 声明 T0/T1 完成状态不受修订影响，但新版 AST 判据同时禁止这些运行时字面量，两项要求冲突。
- `routing/config.py:11` 是 reply-constraint routing 的 embedding endpoint，工单 v2 未把该文件纳入 T2 写域。

为确认 `routing/config.py` 不是本轮引入，执行只读取证：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' cat-file -e '6df6b1a3:src/brain/routing/config.py'
& 'C:\Program Files\Git\cmd\git.exe' show '6df6b1a3:src/brain/routing/config.py'
```

锁定 revision 原始相关输出：

```text
cat_file_exit=0
class RoutingConfig:
    embedding_model: str = "nomic-embed-text"
    ollama_embed_url: str = "http://localhost:11434/api/embed"
```

T2 后续注释/docstring `rg`、`pytest src/brain/tests`、`pytest src/brain/orchestration/tests`、proposal/memory 定向证据：**NOT RUN（第一条正式 Gate 已失败，禁止越过失败继续补门）**。

### Gate T3

**NOT RUN（T2 Gate 阻塞，未进入 T3）**。

### Gate T4

**NOT RUN（T2 Gate 阻塞，未进入 T4）**。

### Gate T5

**NOT RUN（T2 Gate 阻塞，未进入 T5）**。

### 全仓字面量扫描结果

见 Gate T2 AST 原始输出。结论为不满足“只剩 `slot_adapter._DEFAULTS` 一处”：3 个命中来自上一轮 T0/T1 的兼容别名，1 个命中来自锁定 revision 已存在但未纳入 v2 写域的 `routing/config.py`。

### `ultima-config.toml` 已知未收口项

`src/brain/ultima-config.toml` 是底座 openjarvis 经 `OPENJARVIS_CONFIG` 使用的 bootstrap 注入配置；其 `[intelligence] default_model` 与本单主脑 provider 的 `slot_adapter.S-MAIN` 权威不是同一条路径。本单按 v2 明令不修改该文件，交由后续 Phase 1 配置体系归并，禁止把它描述成已收口。

### `/health` 与 `/ask` 实跑输出

**NOT RUN**。工单要求 T2 全绿后才能进入 T3/T5；本轮没有跨 Gate 启动、重启或实跑服务。只读取证确认旧实例仍为 PID `24596`、创建时间 `2026-11-11 23:51:00`，未重启该实例，也未重启语音链路。

### 已知限制 / 继续所需条件

1. 继续所需条件：由工单权威方修订写域，明确授权如何收敛 `src/brain/routing/config.py`；该文件属于 embedding routing endpoint，不在当前 v2 T2 文件清单内。不能由执行端擅自扩单。
2. 继续所需条件：消解“v2 声明 T0/T1 完成状态不受影响”与“AST 禁止 T0/T1 三处 `ollama-8b` 兼容别名”的冲突，并给出不改变 `_DEFAULTS`、不破坏零配置 Ollama-native 行为的获准实现落点。不能用隐藏拼串或放宽 AST 判据规避。
3. `src/brain/ultima-config.toml` 是明确的**已知未收口项**，本单不得修改，也不得在最终口径中冒充已收口。
4. `tasks/queue/queue-status.json` 在本轮开工前已是 `M`。本轮遵守禁改要求未触碰；若未来 T5 仍要求该路径 status 为空，需要由既有改动所有者先处理，不能由本工单擅自还原。
5. T2 的 memory/orchestration 定向行为已做到 RED→GREEN，但正式 AST Gate 失败，因此不声明 T2 完成；T3/T4/T5 均未实现或验证，`/health` 与 `/ask` 未实跑。
6. 未联网、未安装依赖、未使用 `git add -A`、未提交、未暂存任何文件；未修改任何 system prompt、三个 gate 函数、`slot_adapter._DEFAULTS`、`ultima-config.toml`、语音/GUI/installer 路径。

---

## 回执（执行端填写，第二续行，2026-11-12）

- 工单号：`wo-ultimaagent-20261112-0043`
- 执行状态：**BLOCKED at T1 recheck（按序停止，未进入 T2）**
- run 目录：`H:\UltimaAI\UltimaAgent\.superpowers\sdd\wo-ultimaagent-20261112-0043--mainbrain-provider-layer`
- 本续行实际改动文件：
  - `.superpowers/sdd/wo-ultimaagent-20261112-0043--mainbrain-provider-layer/progress.md`（追加本次阻塞记录）
  - `tasks/queue/wo-ultimaagent-20261112-0043--mainbrain-provider-layer.md`（追加本回执）
- 前两轮实现文件仍存在：`src/brain/providers/` 五个文件、`src/brain/agent_server.py`、`src/brain/mainbrain_proposal.py`、`src/brain/agent_tools_ultima.py`、`src/brain/memory/backend.py`、`src/brain/orchestration/engine.py`、`src/brain/interaction.py` 及相关测试。
- `tasks/queue/queue-status.json` 开工前已经是 `M`；本续行未还原、未覆盖、未暂存该文件。
- 未启动或重启任何服务，未触碰语音链路。

### Gate T0（复核）

原始命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/tests/test_provider_layer.py -o addopts= -p no:cacheprovider -q
```

原始输出：

```text
.............                                                            [100%]
13 passed in 2.40s
T0_RECHECK_EXIT=0
```

结论：T0 Gate 复核通过，五个 provider 文件及其单源/协议用例仍在。

### Gate T1（复核失败，顺序停止点）

原始命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/tests -o addopts= -p no:cacheprovider -q
```

原始输出：

```text
=================================== ERRORS ====================================
______________ ERROR collecting src/brain/tests/test_adapters.py ______________
ImportError while importing test module 'H:\UltimaAI\UltimaAgent\src\brain\tests\test_adapters.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Users\Administrator\AppData\Local\Doubao\User Data\sandbox_runtime\bases\772984f6fd3a8ae0ae7d2422cd7c2bfa\python\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\brain\tests\test_adapters.py:15: in <module>
    from orchestration.adapters import error_payload, map_exception_to_error_code, map_structured_to_contract
src\brain\orchestration\__init__.py:12: in <module>
    from .engine import (
src\brain\orchestration\engine.py:30: in <module>
    from ..slot_adapter import main_settings
E   ImportError: attempted relative import beyond top-level package
=========================== short test summary info ===========================
ERROR src/brain/tests/test_adapters.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 3.35s
T1_BRAIN_RECHECK_EXIT=2
```

最小复现命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/tests/test_adapters.py -o addopts= -p no:cacheprovider -q
```

最小复现原始输出：

```text
=================================== ERRORS ====================================
______________ ERROR collecting src/brain/tests/test_adapters.py ______________
ImportError while importing test module 'H:\UltimaAI\UltimaAgent\src\brain\tests\test_adapters.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Users\Administrator\AppData\Local\Doubao\User Data\sandbox_runtime\bases\772984f6fd3a8ae0ae7d2422cd7c2bfa\python\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\brain\tests\test_adapters.py:15: in <module>
    from orchestration.adapters import error_payload, map_exception_to_error_code, map_structured_to_contract
src\brain\orchestration\__init__.py:12: in <module>
    from .engine import (
src\brain\orchestration\engine.py:30: in <module>
    from ..slot_adapter import main_settings
E   ImportError: attempted relative import beyond top-level package
=========================== short test summary info ===========================
ERROR src/brain/tests/test_adapters.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 2.80s
MIN_REPRO_EXIT=2
```

只读取证命令与输出：

```powershell
rg -n "from \.\.slot_adapter|from src\.brain\.slot_adapter|from orchestration" src/brain/orchestration src/brain/tests/test_adapters.py
```

```text
src/brain/tests/test_adapters.py:15:from orchestration.adapters import error_payload, map_exception_to_error_code, map_structured_to_contract
src/brain/orchestration/engine.py:30:from ..slot_adapter import main_settings
```

根因：上轮 T2 半成品在 `src/brain/orchestration/engine.py` 新增了 `from ..slot_adapter import main_settings`。该导入仅在模块名为 `src.brain.orchestration.engine` 时成立；既有测试按顶层包 `orchestration.adapters` 导入，进而加载 `orchestration.engine`，双点相对导入越过顶层包并在收集期失败。锁定 revision `6df6b1a3` 没有这条导入，因此不是获准的 Ollama PATH 环境噪声。

T1 的字面量清零、payload 等价性与 orchestration 子 Gate：**NOT RUN**。第一条 T1 复核命令已失败，按工单禁止越过失败继续补门。

### Gate T2

**NOT RUN**。T1 复核失败，未进入 T2。

T2 v3 AST 脚本原文、原始输出与 `(file, lineno)` 清单：**本续行没有生成或执行**。前一轮遗留的 `t2_ast_scan.py` 使用旧判据（包含 `ollama-8b`），不满足本轮明确的 v3 两字面量判据，因此本续行没有把它冒充当前 Gate 证据。

`src/brain/routing/config.py` 与 `src/brain/ultima-config.toml` 定位输出：**NOT RUN**，原因同上。

### Gate T3

**NOT RUN**。T1 复核失败，未进入 T2/T3；没有启动临时未配置实例。

### Gate T4

**NOT RUN**。T1 复核失败，未进入 T2/T3/T4；没有执行 `probe()` 三态。

### Gate T5

**NOT RUN**。T1 复核失败，未进入 T2/T3/T4/T5；没有重启现网主脑，没有执行 `/health` 或 `/ask` 实跑，也没有执行最终全量回归。

### `ultima-config.toml` 已知未收口项

`src/brain/ultima-config.toml` 是底座 openjarvis 经 `OPENJARVIS_CONFIG` 生效的 bootstrap 注入配置，与本单主脑 provider 的 `slot_adapter.S-MAIN` 不是同一条路径。本单不改；这是**已知未收口项**，不得描述为已收口。

### `/health` 与 `/ask` 实跑原始输出

**NOT RUN**。顺序停止于 T1 复核 Gate；本续行没有启动、重启或调用服务。

### 已知限制 / 继续所需条件

1. 必须先修复 `src/brain/orchestration/engine.py` 在项目既有双导入形态（`orchestration.*` 与 `src.brain.orchestration.*`）下的兼容性，并以当前失败命令完成 RED→GREEN；此修复属于上轮 T2 半成品的回归，不得通过改测试导入、跳过用例或放宽 Gate 规避。
2. 修复后须从 T1 第一条 Gate 重新开始复核；只有 T1 全绿才可进入 T2，不能直接从 T2 AST 扫描续跑。
3. `tasks/queue/queue-status.json` 当前已有别处改动；本续行未触碰。若未来 T5 仍要求该路径 porcelain 为空，需要由既有改动所有者处理，不能由本工单擅自还原。
4. 本续行未联网、未安装依赖、未使用 `git add -A`、未提交、未暂存；未修改任何 system prompt、三个 gate 函数、`slot_adapter._DEFAULTS`、`routing/config.py`、`ultima-config.toml`、语音/GUI/installer 路径。

---

## 回执（执行端填写，第三续行 repair，2026-11-12）

- 工单号：`wo-ultimaagent-20261112-0043`
- 执行状态：**BLOCKED at T5 queue-status porcelain check**。T1 复核、T2、T3、T4 及 T5 的回归、`/health`、`/ask` 均已取得本轮新鲜证据；最后一项要求输出为空，但原始输出为 ` M tasks/queue/queue-status.json`。该文件开工前已经是他人修改态，且本单硬约束禁止修改，因此没有还原、暂存或用 index 标志隐藏。
- run 目录：`H:\UltimaAI\UltimaAgent\.superpowers\sdd\wo-ultimaagent-20261112-0043--mainbrain-provider-layer`
- 本单实现/修复文件清单：
  - `src/brain/providers/__init__.py`
  - `src/brain/providers/base.py`
  - `src/brain/providers/ollama_native.py`
  - `src/brain/providers/openai_compat.py`
  - `src/brain/providers/resolve.py`
  - `src/brain/providers/probe.py`
  - `src/brain/agent_server.py`
  - `src/brain/mainbrain_proposal.py`
  - `src/brain/agent_tools_ultima.py`
  - `src/brain/memory/backend.py`
  - `src/brain/orchestration/engine.py`
  - `src/brain/interaction.py`
  - `src/brain/tests/test_provider_layer.py`
  - `src/brain/reply/tests/test_structured_reply.py`
  - `src/brain/tests/test_prompt_boundary_p0.py`
  - `.superpowers/sdd/wo-ultimaagent-20261112-0043--mainbrain-provider-layer/t2_ast_scan.py`
  - `.superpowers/sdd/wo-ultimaagent-20261112-0043--mainbrain-provider-layer/progress.md`
  - `tasks/queue/wo-ultimaagent-20261112-0043--mainbrain-provider-layer.md`
- 未改：`tasks/queue/queue-status.json`、`src/brain/routing/config.py`、`src/brain/ultima-config.toml`、三个 gate 函数、全部 system prompt、`slot_adapter._DEFAULTS`、语音/GUI/installer 路径。

### Gate T0（沿用本卡第二续行的新鲜复核证据）

原始命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/tests/test_provider_layer.py -o addopts= -p no:cacheprovider -q
```

原始输出：

```text
.............                                                            [100%]
13 passed in 2.40s
T0_RECHECK_EXIT=0
```

本续行另只读核对 `src/brain/providers/` 的五个 T0 文件全部仍在；新增的第六个 `probe.py` 属 T4。

### Gate T1（本轮复核）

brain 原始命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/tests -o addopts= -p no:cacheprovider -q
```

原始终端输出（失败项与工单获准环境噪声完全相同）：

```text
........................................................................ [ 17%]
.F...................................................................... [ 34%]
.................................................................................................................. [ 62%]
................................................................................................................................ [ 92%]
..............................                                           [100%]
FAILED src/brain/tests/test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains
1 failed, 415 passed, 25 warnings, 46 subtests passed in 52.39s
T1_BRAIN_RECHECK_EXIT=1
```

失败原因为 `subprocess.run(["ollama", "list"])` 抛 `FileNotFoundError: [WinError 2]`，无新增失败。

字面量清零原始命令：

```powershell
rg -n '"qwen3-8b-uncensored"|"http://127.0.0.1:11434/api/chat"' src/brain/agent_server.py
```

原始输出为空，退出码为 1：

```text
T1_LITERAL_RG_EXIT=1
```

payload / 分类思考 / Jarvis 映射原始命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/tests/test_provider_layer.py::test_agent_server_structured_reply_preserves_locked_ollama_payload src/brain/tests/test_provider_layer.py::test_agent_server_intent_classification_keeps_thinking_enabled src/brain/tests/test_provider_layer.py::test_agent_server_get_jarvis_maps_ollama_alias_and_model -o addopts= -p no:cacheprovider -vv -s
```

原始输出：

```text
collected 3 items
src/brain/tests/test_provider_layer.py::test_agent_server_structured_reply_preserves_locked_ollama_payload structured_payload={"format": {"additionalProperties": false, "properties": {"confidence": {"maximum": 1, "minimum": 0, "type": "number"}, "grounded": {"type": "boolean"}, "reply_text": {"minLength": 1, "type": "string"}}, "required": ["reply_text", "confidence", "grounded"], "type": "object"}, "messages": [{"content": "你是本地 Agent 的最终回答边界。输出必须严格匹配给定 JSON Schema，禁止 markdown 和额外文本。\nreply_text 最多两句，不含营销、关注、点赞或订阅话术。\nconfidence 是 0 到 1 的自评置信度。\ngrounded 仅当 reply_text 能被用户原文或工具证据直接支持时为 true；草稿本身不是证据。\n无法确认时将 grounded 设为 false，并在 reply_text 中简短说明无法可靠回答。\n", "role": "system"}, {"content": "{\"user_query\": \"状态？\", \"agent_draft\": \"完成。\", \"tool_evidence\": [], \"retry_note\": null}", "role": "user"}], "model": "configured-model", "stream": false, "think": false}
PASSED
src/brain/tests/test_provider_layer.py::test_agent_server_intent_classification_keeps_thinking_enabled PASSED
src/brain/tests/test_provider_layer.py::test_agent_server_get_jarvis_maps_ollama_alias_and_model PASSED
============================== 3 passed in 1.76s ==============================
T1_PAYLOAD_EXIT=0
```

orchestration 原始命令与输出：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/orchestration/tests -o addopts= -p no:cacheprovider -q
```

```text
................................                                         [100%]
32 passed in 2.40s
T1_ORCHESTRATION_RECHECK_EXIT=0
```

只读取证确认 `src/brain/orchestration/engine.py:30` 为绝对导入：

```text
src/brain/orchestration/engine.py:30:from src.brain.slot_adapter import main_settings
```

### Gate T2

AST Gate 原始命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' '.superpowers\sdd\wo-ultimaagent-20261112-0043--mainbrain-provider-layer\t2_ast_scan.py'
```

AST 级字面量扫描脚本原文：

```python
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BRAIN = ROOT / "src" / "brain"
TOKENS = ("qwen3-8b-uncensored", "11434")


def _docstring_constants(tree: ast.AST) -> set[int]:
    docstrings: set[int] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not body or not isinstance(body, list):
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            docstrings.add(id(first.value))
    return docstrings


def _defaults_span(tree: ast.AST) -> tuple[int, int]:
    for node in ast.walk(tree):
        target = None
        if isinstance(node, ast.Assign):
            target = node.targets[0] if len(node.targets) == 1 else None
        elif isinstance(node, ast.AnnAssign):
            target = node.target
        if isinstance(target, ast.Name) and target.id == "_DEFAULTS":
            return node.lineno, node.end_lineno or node.lineno
    raise AssertionError("slot_adapter._DEFAULTS assignment not found")


slot_tree = ast.parse((BRAIN / "slot_adapter.py").read_text(encoding="utf-8"))
defaults_start, defaults_end = _defaults_span(slot_tree)
matches: list[tuple[str, int, str]] = []
docstring_matches: list[tuple[str, int, str]] = []
scanned: list[tuple[str, int]] = []

for path in sorted(BRAIN.rglob("*.py")):
    relative_parts = path.relative_to(BRAIN).parts
    if "tests" in relative_parts:
        continue
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    docstrings = _docstring_constants(tree)
    relative_path = path.relative_to(ROOT).as_posix()
    string_constants = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        string_constants += 1
        for token in TOKENS:
            if token not in node.value:
                continue
            item = (relative_path, node.lineno, token)
            if id(node) in docstrings:
                docstring_matches.append(item)
            else:
                matches.append(item)
    scanned.append((relative_path, string_constants))


def _owner(item: tuple[str, int, str]) -> str | None:
    path, lineno, _ = item
    if path == "src/brain/slot_adapter.py" and defaults_start <= lineno <= defaults_end:
        return "slot_adapter._DEFAULTS"
    if path == "src/brain/routing/config.py" and lineno == 11:
        return "routing.config.ollama_embed_url (known unclosed embedding route)"
    return None


print("AST_SCAN_FILES")
for path, constant_count in scanned:
    print(f"SCAN {path} string_constants={constant_count}")

print("AST_RUNTIME_STRING_MATCHES")
for item in matches:
    print(f"{item} owner={_owner(item) or 'UNAUTHORIZED'}")

print("AST_DOCSTRING_MATCHES_NOT_COUNTED_AS_RUNTIME")
for item in docstring_matches:
    owner = (
        "slot_adapter.main_chat_url docstring"
        if item[0] == "src/brain/slot_adapter.py" and item[1] == 189
        else "UNAUTHORIZED"
    )
    print(f"{item} owner={owner}")

unauthorized = [item for item in matches if _owner(item) is None]
unexpected_docstrings = [
    item
    for item in docstring_matches
    if not (item[0] == "src/brain/slot_adapter.py" and item[1] == 189)
]
covered = {token for _, _, token in matches}

print(f"SCANNED_FILE_COUNT={len(scanned)}")
print(f"RUNTIME_MATCH_COUNT={len(matches)}")
print(f"DOCSTRING_MATCH_COUNT={len(docstring_matches)}")
print(f"UNAUTHORIZED_MATCH_COUNT={len(unauthorized)}")
print("TOKENS_COVERED=" + ",".join(sorted(covered)))

assert not unauthorized, unauthorized
assert not unexpected_docstrings, unexpected_docstrings
assert covered == set(TOKENS), (covered, set(TOKENS))
assert any(_owner(item) == "slot_adapter._DEFAULTS" for item in matches)
assert any(
    _owner(item) == "routing.config.ollama_embed_url (known unclosed embedding route)"
    for item in matches
)
assert docstring_matches == [("src/brain/slot_adapter.py", 189, "11434")]
print("PASS: v3 literal ownership is exact; comments and docstrings are not runtime matches")
```

原始完整扫描输出：

```text
AST_SCAN_FILES
SCAN src/brain/__init__.py string_constants=1
SCAN src/brain/agent_client.py string_constants=23
SCAN src/brain/agent_server.py string_constants=486
SCAN src/brain/agent_tools_ultima.py string_constants=487
SCAN src/brain/bootstrap.py string_constants=64
SCAN src/brain/browser/__init__.py string_constants=0
SCAN src/brain/browser/channel.py string_constants=64
SCAN src/brain/capability.py string_constants=123
SCAN src/brain/channel/__init__.py string_constants=0
SCAN src/brain/channel/channel_breadth.py string_constants=124
SCAN src/brain/channel/ime_bridge.py string_constants=137
SCAN src/brain/cli.py string_constants=20
SCAN src/brain/display/__init__.py string_constants=4
SCAN src/brain/display/behavior.py string_constants=139
SCAN src/brain/display/host_pusher.py string_constants=21
SCAN src/brain/display/orb.py string_constants=179
SCAN src/brain/environment.py string_constants=97
SCAN src/brain/environment_upgrade.py string_constants=130
SCAN src/brain/events/__init__.py string_constants=4
SCAN src/brain/events/bus.py string_constants=10
SCAN src/brain/events/journal.py string_constants=53
SCAN src/brain/exec/__init__.py string_constants=1
SCAN src/brain/exec/channel.py string_constants=84
SCAN src/brain/exec/codex_provider.py string_constants=369
SCAN src/brain/guardrails/__init__.py string_constants=43
SCAN src/brain/guardrails/adjudicate.py string_constants=67
SCAN src/brain/guardrails/audit_log.py string_constants=78
SCAN src/brain/guardrails/audit_prompt.py string_constants=88
SCAN src/brain/guardrails/audit_report.py string_constants=124
SCAN src/brain/guardrails/credentials.py string_constants=186
SCAN src/brain/guardrails/hazard.py string_constants=97
SCAN src/brain/guardrails/paradigm.py string_constants=70
SCAN src/brain/guardrails/policy.py string_constants=43
SCAN src/brain/guardrails/receipt.py string_constants=70
SCAN src/brain/guardrails/registry.py string_constants=24
SCAN src/brain/guardrails/reviewer.py string_constants=47
SCAN src/brain/guardrails/scanner.py string_constants=67
SCAN src/brain/guardrails/scope.py string_constants=59
SCAN src/brain/guardrails/stage_gate.py string_constants=58
SCAN src/brain/guardrails/supply_chain.py string_constants=89
SCAN src/brain/health/__init__.py string_constants=7
SCAN src/brain/health/repair.py string_constants=160
SCAN src/brain/heartbeat/__init__.py string_constants=0
SCAN src/brain/heartbeat/proactive_scenes.py string_constants=69
SCAN src/brain/heartbeat/ticker.py string_constants=47
SCAN src/brain/intent.py string_constants=52
SCAN src/brain/interaction.py string_constants=327
SCAN src/brain/interaction_orb.py string_constants=45
SCAN src/brain/interface_route.py string_constants=311
SCAN src/brain/iot/__init__.py string_constants=0
SCAN src/brain/iot/device_profile.py string_constants=87
SCAN src/brain/iot/mcp_runtime.py string_constants=170
SCAN src/brain/learn/__init__.py string_constants=7
SCAN src/brain/learn/evaluator.py string_constants=69
SCAN src/brain/learn/improver.py string_constants=74
SCAN src/brain/learn/trace_collector.py string_constants=147
SCAN src/brain/loop/__init__.py string_constants=1
SCAN src/brain/loop/brain_loop.py string_constants=287
SCAN src/brain/loop/external_executor.py string_constants=139
SCAN src/brain/loop/params.py string_constants=58
SCAN src/brain/mainbrain_proposal.py string_constants=33
SCAN src/brain/memory/__init__.py string_constants=21
SCAN src/brain/memory/backend.py string_constants=79
SCAN src/brain/memory/gate.py string_constants=43
SCAN src/brain/memory/layers.py string_constants=163
SCAN src/brain/memory/preference.py string_constants=80
SCAN src/brain/memory/reflection.py string_constants=39
SCAN src/brain/memory/registry.py string_constants=16
SCAN src/brain/memory/vectors.py string_constants=34
SCAN src/brain/memory_write_boundary.py string_constants=3
SCAN src/brain/orchestration/__init__.py string_constants=9
SCAN src/brain/orchestration/adapters.py string_constants=32
SCAN src/brain/orchestration/audit.py string_constants=19
SCAN src/brain/orchestration/engine.py string_constants=104
SCAN src/brain/orchestration/queue.py string_constants=228
SCAN src/brain/orchestration/registry.py string_constants=16
SCAN src/brain/orchestrator.py string_constants=98
SCAN src/brain/persona/__init__.py string_constants=0
SCAN src/brain/persona/bond.py string_constants=98
SCAN src/brain/prompt_boundary.py string_constants=58
SCAN src/brain/providers/__init__.py string_constants=5
SCAN src/brain/providers/base.py string_constants=7
SCAN src/brain/providers/ollama_native.py string_constants=33
SCAN src/brain/providers/openai_compat.py string_constants=27
SCAN src/brain/providers/resolve.py string_constants=12
SCAN src/brain/queue_source.py string_constants=70
SCAN src/brain/reply/__init__.py string_constants=5
SCAN src/brain/reply/schema.py string_constants=37
SCAN src/brain/reporter.py string_constants=56
SCAN src/brain/routing/__init__.py string_constants=5
SCAN src/brain/routing/config.py string_constants=42
SCAN src/brain/routing/intent_gate.py string_constants=36
SCAN src/brain/routing/reply_verifier.py string_constants=31
SCAN src/brain/search/__init__.py string_constants=0
SCAN src/brain/search/upgrade.py string_constants=60
SCAN src/brain/sentinel.py string_constants=59
SCAN src/brain/skills/__init__.py string_constants=8
SCAN src/brain/skills/dispatch.py string_constants=20
SCAN src/brain/skills/registry.py string_constants=150
SCAN src/brain/skills/whitelist.py string_constants=36
SCAN src/brain/slot_adapter.py string_constants=148
SCAN src/brain/state/__init__.py string_constants=1
SCAN src/brain/state/axis.py string_constants=61
SCAN src/brain/voice/__init__.py string_constants=1
SCAN src/brain/voice/_resample.py string_constants=10
SCAN src/brain/voice/_vendor/pkg_resources.py string_constants=14
SCAN src/brain/voice/_vendor/wetext/__init__.py string_constants=1
SCAN src/brain/voice/_vendor/wetext/cli.py string_constants=15
SCAN src/brain/voice/_vendor/wetext/token_parser.py string_constants=78
SCAN src/brain/voice/_vendor/wetext/wetext.py string_constants=41
SCAN src/brain/voice/asr.py string_constants=138
SCAN src/brain/voice/daemon.py string_constants=102
SCAN src/brain/voice/fullchain.py string_constants=65
SCAN src/brain/voice/input_probe.py string_constants=121
SCAN src/brain/voice/resources.py string_constants=27
SCAN src/brain/voice/session_restart.py string_constants=4
SCAN src/brain/voice/transcription_backends.py string_constants=15
SCAN src/brain/voice/tts.py string_constants=279
SCAN src/brain/voice/voice_profile.py string_constants=204
SCAN src/brain/voice/wake_matching.py string_constants=12
SCAN src/brain/voice_loop.py string_constants=93
SCAN src/brain/weather.py string_constants=342
AST_RUNTIME_STRING_MATCHES
('src/brain/routing/config.py', 11, '11434') owner=routing.config.ollama_embed_url (known unclosed embedding route)
('src/brain/slot_adapter.py', 39, '11434') owner=slot_adapter._DEFAULTS
('src/brain/slot_adapter.py', 40, 'qwen3-8b-uncensored') owner=slot_adapter._DEFAULTS
AST_DOCSTRING_MATCHES_NOT_COUNTED_AS_RUNTIME
('src/brain/slot_adapter.py', 189, '11434') owner=slot_adapter.main_chat_url docstring
SCANNED_FILE_COUNT=122
RUNTIME_MATCH_COUNT=3
DOCSTRING_MATCH_COUNT=1
UNAUTHORIZED_MATCH_COUNT=0
TOKENS_COVERED=11434,qwen3-8b-uncensored
PASS: v3 literal ownership is exact; comments and docstrings are not runtime matches
T2_AST_SCAN_EXIT=0
```

命中的 `(file, lineno)` 清单：

```text
('src/brain/routing/config.py', 11, '11434')
('src/brain/slot_adapter.py', 39, '11434')
('src/brain/slot_adapter.py', 40, 'qwen3-8b-uncensored')
('src/brain/slot_adapter.py', 189, '11434')  # docstring，不计运行期命中
```

注释/docstring 收敛范围原始命令与空输出：

```powershell
rg -n "qwen3-8b-uncensored|11434" src/brain/interaction.py src/brain/memory/backend.py src/brain/orchestration/engine.py
```

```text
T2_COMMENT_RG_EXIT=1
```

brain / orchestration 原始终端输出：

```text
FAILED src/brain/tests/test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains
1 failed, 415 passed, 25 warnings, 46 subtests passed in 52.10s
T2_BRAIN_EXIT=1
................................                                         [100%]
32 passed in 2.52s
T2_ORCHESTRATION_EXIT=0
```

proposal / memory / orchestration 定向原始命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/tests/test_provider_layer.py::test_mainbrain_proposal_uses_call_time_main_settings src/brain/tests/test_provider_layer.py::test_memory_backend_defaults_use_effective_main_settings src/brain/tests/test_provider_layer.py::test_memory_backend_explicit_settings_override_main_settings src/brain/tests/test_provider_layer.py::test_orchestration_model_key_is_derived_from_effective_main_settings -o addopts= -p no:cacheprovider -vv -s
```

原始输出：

```text
proposal_payload={... "model": "configured-model", "options": {"num_predict": 500, "temperature": 0.2}, "stream": false}
PASSED
memory_defaults={"endpoint": "http://configured-memory.invalid", "model": "configured-memory-model"}
PASSED
memory_explicit={"endpoint": "http://explicit-memory.invalid", "model": "explicit-memory-model"}
PASSED
orchestration_model_key=configured-route-model
PASSED
============================== 4 passed in 2.23s ==============================
T2_TARGETED_EXIT=0
```

已知未收口项定位原始命令与输出：

```powershell
rg -n "ollama_embed_url|default_model" src/brain/routing/config.py src/brain/ultima-config.toml
```

```text
src/brain/ultima-config.toml:9:default_model = "qwen3-8b-uncensored"
src/brain/routing/config.py:11:    ollama_embed_url: str = "http://localhost:11434/api/embed"
```

- `src/brain/routing/config.py:11` 是语义相似度路由的 embedding 直连地址，与主脑 chat 不同路径，本单不改。
- `src/brain/ultima-config.toml:9` 是底座 openjarvis 经 `OPENJARVIS_CONFIG` 生效的 bootstrap 注入配置，与主脑 provider 不同路径；这是**已知未收口项**，本单不改且不描述为已收口。

### Gate T3

TDD RED 原始输出：

```text
FF
E AttributeError: module 'src.brain.agent_server' has no attribute '_health_payload'
FAILED test_agent_server_health_payload_preserves_keys_and_exposes_provider
FAILED test_agent_server_health_payload_marks_unconfigured_provider
2 failed in 2.45s
T3_RED_EXIT=1
```

GREEN 原始输出：

```text
health_configured={"agent": "native_react", "model": "configured-model", "ok": true, "provider": "ollama-8b", "provider_configured": true, "provider_model": "configured-model", "tools": ["calculator", "think", "ultima_memory", "ultima_dispatch", "ultima_dispatch_status"]}
.health_unconfigured={"agent": "native_react", "model": "configured-model", "ok": true, "provider": "ollama-8b", "provider_configured": false, "provider_model": "configured-model", "provider_note": "主脑未配置，/ask 将无法作答", "tools": ["calculator", "think", "ultima_memory", "ultima_dispatch", "ultima_dispatch_status"]}
.
2 passed in 1.77s
T3_GREEN_EXIT=0
```

主脑按既有 Popen 方式从 PID `24596` 重启为 `19764`；命令参数为 `python.exe -X utf8 src/brain/agent_server.py`，cwd 为仓库根，stdout/stderr 追加到 `data/agent.stdout.log` / `data/agent.stderr.log`。重启前后语音相关 PID 集合相同：

```text
VOICE_PIDS_BEFORE=6704,23392,23976,28344,28816,28928
VOICE_PIDS_AFTER=6704,23392,23976,28344,28816,28928
```

当前 8756 `/health` 原始输出：

```json
{
  "ok": true,
  "model": "qwen3-8b-uncensored:latest",
  "agent": "native_react",
  "tools": ["calculator", "think", "ultima_memory", "ultima_dispatch", "ultima_dispatch_status"],
  "provider": "ollama-8b",
  "provider_model": "qwen3-8b-uncensored:latest",
  "provider_configured": false,
  "provider_note": "主脑未配置，/ask 将无法作答"
}
```

独立端口未配置态原始命令与输出：

```powershell
$env:GORCH_MAIN_ENABLED=false; Invoke-RestMethod http://127.0.0.1:18756/health | ConvertTo-Json -Depth 6
```

```json
{
  "ok": true,
  "model": "qwen3-8b-uncensored:latest",
  "agent": "native_react",
  "tools": ["calculator", "think", "ultima_memory", "ultima_dispatch", "ultima_dispatch_status"],
  "provider": "ollama-8b",
  "provider_model": "qwen3-8b-uncensored:latest",
  "provider_configured": false,
  "provider_note": "主脑未配置，/ask 将无法作答"
}
```

```text
TEMP_SERVER_EXIT=0
ASSERT_PROVIDER_CONFIGURED_FALSE=True
ASSERT_PROVIDER_NOTE_NONEMPTY=True
```

### Gate T4

TDD RED 原始输出：

```text
FFFFF
Failed: provider probe is not implemented: No module named 'src.brain.providers.probe'
5 failed in 0.34s
T4_RED_EXIT=1
```

最终四态与超时 Gate 原始命令：

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -m pytest src/brain/tests/test_provider_layer.py::test_probe_not_configured_skips_network src/brain/tests/test_provider_layer.py::test_probe_closed_port_returns_within_timeout src/brain/tests/test_provider_layer.py::test_probe_ok_uses_model_listing_endpoint src/brain/tests/test_provider_layer.py::test_probe_unauthorized_is_a_state src/brain/tests/test_provider_layer.py::test_probe_local_ollama_when_available -o addopts= -p no:cacheprovider -q -s
```

原始输出：

```text
probe_not_configured state=not-configured latency_ms=0
.probe_unreachable state=unreachable latency_ms=463.772 elapsed_ms=463.803 timeout_ms=500.0
.probe_ok state=ok latency_ms=0.103 url=http://provider.invalid/api/tags
.probe_unauthorized state=unauthorized latency_ms=0.082
.probe_local_ollama state=ok latency_ms=10.821
.
5 passed in 0.53s
T4_GREEN_FINAL_EXIT=0
```

### Gate T5（最后一项失败，顺序停止点）

全量回归原始命令：

```powershell
H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest src/brain/tests src/brain/orchestration/tests -o addopts= -p no:cacheprovider -q
```

原始终端输出：

```text
........................................................................ [ 15%]
.F...................................................................... [ 31%]
.................................................................................................................. [ 56%]
.................................................................. [ 71%]
.............................................................. [ 84%]
.....................................................................    [100%]
FAILED src/brain/tests/test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains
1 failed, 454 passed, 25 warnings, 46 subtests passed in 66.36s (0:01:06)
T5_REGRESSION_EXIT=1
```

唯一失败仍为 `ollama` 命令不在 PATH 的获准环境项；通过数 `454` ≥ `422`，无新增失败。

`/health` 原始命令：

```powershell
Invoke-RestMethod http://127.0.0.1:8756/health | ConvertTo-Json -Depth 8
```

原始输出：

```json
{
  "ok": true,
  "model": "qwen3-8b-uncensored:latest",
  "agent": "native_react",
  "tools": ["calculator", "think", "ultima_memory", "ultima_dispatch", "ultima_dispatch_status"],
  "provider": "ollama-8b",
  "provider_model": "qwen3-8b-uncensored:latest",
  "provider_configured": false,
  "provider_note": "主脑未配置，/ask 将无法作答"
}
```

`/ask` 原始命令：

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8756/ask -ContentType application/json -Body '{"query":"你是谁"}' | ConvertTo-Json -Depth 12
```

原始输出：

```json
{
  "content": "我是贾维斯，您的语音助手。随时为您效劳。",
  "reply_text": "我是贾维斯，您的语音助手。随时为您效劳。",
  "confidence": 1.0,
  "grounded": true,
  "intent": "query",
  "tool_results": [],
  "usage": {"prompt_tokens": 1290, "completion_tokens": 229, "total_tokens": 1519},
  "ok": true
}
```

最后一项原始命令与输出：

```powershell
git status --porcelain -- tasks/queue/queue-status.json
```

```text
 M tasks/queue/queue-status.json
T5_QUEUE_STATUS_EXIT=0
```

判定：要求为空，实际非空，T5 Gate 未全绿；按工单停止，不写通过/交审标记。

### 已知限制 / 继续所需条件

1. 阻塞解除条件：由该文件既有改动的所有者处置 `tasks/queue/queue-status.json`，使 porcelain 为空；本单不能自行还原或覆盖，也不能用暂存/index 标志伪造空结果。之后只需从 T5 最后一项重新核验，并按工单决定是否需要重跑整组 T5。
2. `src/brain/routing/config.py:11` 与 `src/brain/ultima-config.toml:9` 均为**已知未收口项**；前者是 embedding 路由，后者是底座 openjarvis 注入配置，与主脑 provider 不同路径。
3. 当前零配置默认的 `S-MAIN enabled=false`，所以 `/health` 按卡报告 `provider_configured=false`；与此同时本机默认 endpoint/model 可访问，真实 `/ask` 本轮仍成功。这是现有零配置兼容路径与配置状态语义并存的事实，本单未擅自改变 `_DEFAULTS` 或扩大到调用门控。
4. T3 独立端口第一次启动器使用一次性 `ThreadingHTTPServer`，因 daemon worker 尚未写回时主进程退出而连接关闭；该次没有改产品代码。改为同步 `HTTPServer` 后同 Gate 原始响应和断言通过。
5. T4 在 Windows 上对 `127.0.0.1:1` 表现为丢包式超时；probe 对 loopback 绕过系统代理并为调用开销预留 10% 网络预算后，总耗时 463.803ms ≤ 500ms。
6. 本轮未联网、未安装依赖、未使用 `git add -A`、未提交或暂存；没有重启语音链路，且主脑重启前后语音 PID 集合一致。
