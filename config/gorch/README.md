# G-ORCH 三插槽配置

G-ORCH 通过 `S-MAIN`、`S-REVIEW` 和 `S-EXEC` 三个插槽分别配置主脑、审议接口和执行 CLI。配置文件中的字段可以只写需要覆盖的部分，缺少的字段会使用内置默认值。

## 1. 配置优先级

配置按以下顺序生效：**环境变量 > `config/gorch/slots.json` > 内置默认值**。完全不配置时，系统使用内置默认值，行为与当前已经跑通的版本一致。

示例文件给出的三插槽默认配置如下：

- `S-MAIN`：`impl` 为 `ollama-8b`，`endpoint` 为 `http://127.0.0.1:18766`，`model` 为 `qwen3:8b`，`enabled` 为 `false`。
- `S-REVIEW`：`impl` 为 `deepseek`，`base_url` 为 `https://api.deepseek.com/chat/completions`，`model` 为 `deepseek-chat`，`api_key_env` 为 `DEEPSEEK_API_KEY`，`max_tokens` 为 `4096`，`timeout` 为 `60.0` 秒。
- `S-EXEC`：`impl` 为 `codex`，`exe` 为空字符串，`model` 为 `gpt-5.6-sol`，`args_template` 为空数组，`env` 为空对象。

常用字段可以通过环境变量覆盖：`S-MAIN` 使用 `GORCH_MAIN_ENDPOINT`、`GORCH_MAIN_MODEL`；`S-REVIEW` 使用 `GORCH_REVIEW_BASE_URL`、`GORCH_REVIEW_MODEL`、`GORCH_REVIEW_KEY_ENV`；`S-EXEC` 使用 `GORCH_EXEC_EXE`、`GORCH_EXEC_MODEL`。也可以用 `GORCH_SLOT_CONFIG` 指定其他配置文件路径。

## 2. 使用方式

先复制样例文件，再按需修改副本：

```powershell
Copy-Item config/gorch/slots.example.json config/gorch/slots.json
```

运行时读取的是 `config/gorch/slots.json`；请保留三个插槽的 JSON 对象结构，只修改需要覆盖的字段。样例中的 `_readme`、`_其他供应商示例_S-REVIEW` 和 `_其他CLI示例_S-EXEC` 是说明及备选示例，不是插槽配置。

## 3. S-REVIEW：审议接口

`S-REVIEW` 调用 OpenAI-compatible 的 `/chat/completions` 接口。切换供应商时，只需把 `base_url`、`model` 和 `api_key_env` 改成目标供应商对应的值，并在 `api_key_env` 所指向的环境变量中提供 API Key。

`slots.example.json` 中可直接参考以下填写方式：

| 供应商 | `base_url` | `model` | `api_key_env` |
| --- | --- | --- | --- |
| DeepSeek | `https://api.deepseek.com/chat/completions` | `deepseek-chat` | `DEEPSEEK_API_KEY` |
| OpenAI | `https://api.openai.com/v1/chat/completions` | `gpt-4.1-mini` | `OPENAI_API_KEY` |
| Moonshot | `https://api.moonshot.cn/v1/chat/completions` | `kimi-k2` | `MOONSHOT_API_KEY` |
| Qwen（DashScope compatible-mode） | `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions` | `qwen-plus` | `DASHSCOPE_API_KEY` |
| 本地 vLLM | `http://127.0.0.1:8000/v1/chat/completions` | `Qwen2.5-Coder-14B-Instruct` | `VLLM_API_KEY` |

例如选择 Moonshot 时，将 `S-REVIEW` 中这三个字段替换为 Moonshot 所在行的值，然后设置 `MOONSHOT_API_KEY`。`max_tokens` 和 `timeout` 不需要随供应商一起修改，除非目标服务有不同要求。

## 4. S-EXEC：执行 CLI

`args_template` 一旦填写，就会**整体替换 argv**，不是在内置参数后追加，也不会与内置参数合并。模板中的参数语法必须与目标 CLI 的真实参数一致，适配层不会猜测或翻译。`args_template` 留空时，调用方继续使用内置的 Codex 命令行。

模板支持五个占位符：

- `{exe}`：调用方传入的 CLI 可执行文件路径或名称。
- `{model}`：当前生效的 `S-EXEC.model` 模型名。
- `{workdir}`：本次执行任务的工作目录。
- `{last_msg}`：传给执行 CLI 的最新一条消息或任务内容。
- `{effort}`：本次执行使用的推理强度设置。

样例中的 Claude Code 模板为：

```json
["{exe}", "-p", "{last_msg}", "--permission-mode", "acceptEdits"]
```

## 5. S-MAIN：主脑插槽

`S-MAIN` 默认使用本地 `qwen3:8b`，但 `enabled` 默认为 `false`。未启用时调用 `require_main()` 会抛出 `SlotConfigError`，明确报告主脑位尚未接线。

这是刻意的 **fail-closed** 行为：在主脑不可用时立即报错，避免上游误以为主脑已经运行，也不会由适配层悄悄代做依赖主脑的流程。只有在对应服务真实可用并完成接线后，才应将 `enabled` 设为 `true`。
