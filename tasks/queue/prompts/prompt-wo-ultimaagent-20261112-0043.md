# 执行载荷 · wo-ultimaagent-20261112-0043

你在一台 Windows 本机上执行一个已冻结范围的工程工单。

## 工作目录

`H:\UltimaAI\UltimaAgent`（仓库根，分支 `codex/voice-fsmn-new-path`）

## 必读（按顺序，读全）

1. `docs/INDEX.md`（即 `H:\UltimaAI\UltimaAgent\docs\INDEX.md`）—— 本项目权威文档入口
2. `wo-ultimaagent-20261112-0043--mainbrain-provider-layer.md`（即 `H:\UltimaAI\UltimaAgent\tasks\queue\wo-ultimaagent-20261112-0043--mainbrain-provider-layer.md`）—— **本单唯一工单卡，一切以它为准**
3. `H:\UltimaAI\UltimaAgent\docs\plans\plan-ultimaagent-monolith-installer-lifecycle-provider-20261112.md` §4 —— 方案依据

## 唯一任务

按工单卡的 T0 → T1 → T2 → T3 → T4 → T5 顺序执行。**每完成一个 T，先跑该 T 的 Gate，全绿才进下一个 T。任何 Gate 未过，停下来在回执里写明卡在哪，不要跳序、不要"先做完再补测"。**

## 硬约束（违反即作废，不接受事后补救）

1. **不改** `_risk_gate` / `_no_tool_gate` / `_clean_content` 三个函数，不改任何 system prompt 文本（`MAINBRAIN_SYSTEM_PROMPT` / `_QUERY_SYSTEM` / `_ASK_CLASSIFY_SYSTEM`）。
2. **不改** `slot_adapter.py` 的 `S-REVIEW` / `S-EXEC` 插槽，**不改** `_DEFAULTS` 里 `S-MAIN` 的默认值（零配置行为必须与今天完全一致）。
3. **不引入** litellm / langchain / openai SDK 等任何新依赖，只用标准库（现有代码用 `urllib.request`）。
4. **不碰** `src/voice-next/**`、`src/brain/voice/**`、`src/host-shell/**`、`UltimaAgent.Hud/**`、`installer/`。
5. **不改** `tasks/queue/queue-status.json`。
6. **禁止** `git add -A`（仓库常态有数百未跟踪文件）。提交必须按路径精确 add。
7. **不联网、不装依赖。**

## 关键技术点（工单里已写，这里再强调，因为最容易做错）

`agent_server.py` 现在走的是 **Ollama 原生 `/api/chat`**，依赖三个原生能力：

- `think=False`（关思考，用于结构化应答）
- `format=REPLY_JSON_SCHEMA`（JSON Schema 强约束输出）
- `options.num_predict`（token 预算）

而 `slot_adapter.call_main()` 走的是 **OpenAI 兼容**，这三项都没有。所以：

- **不要把 Ollama 路径改成"提示模型自己输出 JSON"**——那是能力降级，会让结构化应答不再可靠。
- 正确做法是 provider 层支持两种协议，由 `impl` 决定走哪条，Ollama 路径逐字段保留原有 payload。
- `_classify_intent` 的思考**不能关**：关了以后 qwen3 在极短判定上会返回空串，导致意图分类静默失败（这是本工程已踩过的坑，见 `docs/references/lessons-log.md`）。

## 唯一权威源

配置只能来自 `src/brain/slot_adapter.py` 的 `S-MAIN`（`main_settings()` / `main_chat_url()` / `require_main()`）。

`src/brain/providers/` 只做协议适配，**不得**自己读 `os.environ`、**不得**自己 `json.load` 读配置文件。工单 T0 有一条单源断言专门扫这个。

## 验收命令（用这个解释器，不要用别的 Python）

```powershell
H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest src/brain/tests src/brain/orchestration/tests -o addopts= -p no:cacheprovider -q
```

基线：**422 passed / 1 failed**。唯一失败是 `test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains`，属环境噪声（该用例依赖 `ollama` 命令在 PATH，本机 ollama 装在 `%LOCALAPPDATA%\Programs\Ollama` 不在 PATH），**允许它继续失败，但不允许新增任何失败**。

## 回执要求

在工单卡末尾「回执（执行端填写）」段，逐项填写：

- run 目录
- 改动文件清单
- **T0-T5 每个 Gate 的原始命令 + 原始输出**（不要只写"通过"，要贴真实终端输出）
- 全仓字面量扫描结果（`rg -n 'qwen3-8b-uncensored|127.0.0.1:11434' src/ --glob '!**/tests/**'`）
- `/health` 与 `/ask` 实跑原始输出
- 已知限制（如实写，不要把没做的说成做了）

最后在 stdout 输出最后一行结构化 JSON：`{"business_success": true|false, "summary": "...", "gates": {...}}`，供派发器解析。

## 如果卡住

不要为了"让测试变绿"去删断言、跳过用例、放宽判据。卡住就如实写 BLOCKED + 原因 + 你判断需要什么才能继续。削判据的交付一律作废。
