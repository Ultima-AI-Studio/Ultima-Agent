# 语音回复的「内容提炼 + 字数/时长限制」成熟经验调研

- 日期：2026-11-11
- 范围：语音助手回复长度控制（业界规范 + 机器上已下载的 Agent 源码）
- 触发原因：用户反馈「回答的内容范围太小」，需确认业界上限与下限，避免把「砍短」当成唯一解法

## 一、结论先行

1. **语音单轮的业界主流是 1–2 句**，但**不是无条件下限**。Smallest AI 的原文口径：`Default to one sentence. If the user asks for detail, take two. Three is too many.` —— 即「默认 1 句，用户要细节给 2 句，3 句已过多」。
2. **真正的主约束是「朗读时长」，不是句数**。Bluejay 给出的经验值：**单条回复 < 15 秒**；依据是**人脑一次只能持有约 8–10 秒的口语信息**，超过就注意力掉线。按中文 4–5 字/秒估，**15 秒 ≈ 60–75 字**。
3. **语音回复应比同内容的文本回复短 60–70%**（Bluejay）。这条解释了为什么「把聊天回答直接进 TTS」体验一定差。
4. **字符硬上限有明确先例**：Google Assistant 的 Simple Response 在 **640 字符**处截断，且**建议少于 300 字符**。
5. **电话场景最严**：开源实现 talker 的 `prompts/outgoing.md` 对 `channel=CALL` 直接规定 **Maximum 2 sentences**，同时要求数字转口语、URL 说成「在我们网站上」。
6. **形式比长度更影响听感**：Alexa「Be Brief」明确要求「能被人在一到两次呼吸内读完」；口播禁止 bullet/numbered list（模型会真的读出「bullet」）；一次最多 3 个选项；电话号/邮箱这类易忘信息应推送到屏/App 而不是朗读。

## 二、业界做法对照

| 来源 | 核心口径 | 可复用的点 |
|---|---|---|
| Amazon Alexa「Be Brief」设计原则 | 一到两次呼吸内读完；最少步骤；主动语态；一次 1–3 个选项；长信息推卡片 | **「呼吸数」作为长度单位**；长信息转屏 |
| Google Assistant Simple Response | 640 字符截断，**建议 < 300 字符** | 硬上限兜底 + 软建议双档 |
| Smallest AI（Hydra 语音 Agent 提示词指南） | 默认 1 句 / 要细节 2 句 / 3 句过多；不要 numbered list、不要 bullet、不要「尽可能详细」 | **按「要不要细节」分级**，不是一刀切 |
| Bluejay 语音 Prompt 工程 | 比文本短 60–70%；< 15 秒；系统提示 < 500 token；最多 3 选项；停顿 300–500ms；**每多 1 秒延迟满意度 -16%** | 用「秒」而不是「字」做验收口径 |
| talker `outgoing.md`（开源后处理器） | CALL ≤ 2 句；SMS 160 字符；WhatsApp 500 字符；按 channel 分别做 markdown/URL/数字清洗 | **按「输出通道」而不是全局定规则** |

## 三、机器上已下载的 Agent 源码对照

目录：`H:\UltimaAI\_vendor\`（`lobehub-canary`、`edict`、`golutra`、`worktrunk`），另 `H:\FriendAgentTest`（OpenCode 相关）。

| 源码 | 是否有回复长度机制 | 结论 |
|---|---|---|
| **LobeChat（`lobehub-canary`）** | `packages/model-runtime/src/utils/resolveSafeMaxTokens.ts`：`DEFAULT_MAX_TOKENS_BUFFER = 1024`、`DEFAULT_MIN_OUTPUT_TOKENS = 1024`，按上下文窗口**动态推导 max_tokens**，余量不足时抛 `ContextExceededPreFlightError` 并给 `fork_topic` / `switch_to_larger_ctx_model` 两条显式建议 | **有「回复预算」概念，但管的是上下文容量，不针对语音短回复**。可借鉴的是 **fail-fast + 给可执行建议** 这一模式 |
| **edict** | `edict_agent_architecture.md` 只定义 thoughts/todo 的结构化与事件流，**回复侧无长度约束** | 多 Agent 编排参考，不提供回复精简机制 |
| **golutra** | 桌面 Agent 壳（Tauri + React），未见回复长度策略 | 无 |
| **worktrunk** | Rust 的 git worktree 工具，含 skills/.agents 目录 | 无 |

**结论**：本地已下载源码里**没有现成的「语音回复长度控制器」可直接搬**；LobeChat 只提供「按 token 预算 + 预检失败」的思路。真正的语音侧规则必须自建，依据应是上表的业界口径。

## 四、UltimaAgent 现状与差距

| 位置 | 现状 | 差距 |
|---|---|---|
| `config/voice-profile.json` `style.max_sentences` | 本轮 2 → **4** | 业界主流 1–2 句；4 句按中文估约 20–30 秒，**已超 Bluejay 的 15 秒线** |
| `src/brain/interaction.py:420` `content.split("\n")[0].strip()[:60]` | 云端回复只取第一行 + 硬截 60 字 | 与「整段回复」自相矛盾；且只作用于云端路径 |
| `src/brain/routing/reply_verifier.py:102-105` | 仅按句截断到 `max_sentences` | **只切句，不压字数、不去列表/编号、不处理 URL** |
| `_try_agent_fallback` 重试提示词 | 仍写「不得超过两句」 | 与 `max_sentences=4` 不一致，会让模型与验证器互相打架 |
| `voice_profile.py` `DEFAULT_PROFILE` | `max_sentences: 2` | 与配置 4 不一致（配置为 4 时以配置为准，但默认值已漂移） |
| 全链路 | 无「朗读秒数」口径；无列表/编号过滤；无数字拼读 | 关键缺口 |
| 延迟 | 本地 8B 实测开放问答 **18–28 秒**（含工具循环） | 远超「<1 秒」的语音体验线，属于模型/链路层面的结构性问题，不是回复长度能解决的 |

## 五、建议（按风险分三档）

**立即可做（低风险、与现有验证器同层）**
1. 统一 `max_sentences`：配置、`DEFAULT_PROFILE`、`_try_agent_fallback` 重试提示词三者取同一来源，消除「配置 4 / 提示词 2」冲突。
2. 把「去列表、去编号、去 markdown、URL→『在网站上』」加入 `filter_reply`，这类清洗对听感的改善大于再砍一句。
3. 给 `filter_reply` 补一条**字符硬上限兜底**（参考 Google 的 640 / 建议 300；中文建议 **120 字 / 硬截 200 字**）。

**中期（需要改契约）**
4. 双口径：`max_sentences`（结构）+ `max_chars`/`max_seconds`（时长）。用中文 4–5 字/秒把秒换算成字，**验收看秒不看句**。
5. **按意图分级**而不是全局砍短：闲聊/事实类 1–2 句；解释/方案类允许 3–4 句，但**结尾主动问一句「要不要展开」**。这是同时满足「范围别太小」和「别念 30 秒」的唯一解法。
6. 长内容（清单、地址、号码）不朗读，回复里明说「我发到屏幕/控制台了」。

**不建议**
7. 直接把 `max_sentences` 砍回 1–2。用户已明确反馈「内容范围太小」，砍句数会立刻复现该问题；应先做「分级 + 清洗 + 秒数验收」。

## 六、证据出处

- Alexa Be Brief：https://www.developer.amazon.com/en-US/alexa/alexa-haus/design-principles/be-brief
- Google Assistant Simple Response（640/300 字符）：https://developers.google.cn/assistant/conversational/prompts-simple
- Smallest AI Prompting voice agents（1–2 句口径）：https://docs.smallest.ai/models/speech-to-speech/prompting-voice-agents
- Bluejay Voice AI Prompt Engineering（短 60–70%、<15 秒、8–10 秒窗口）：https://getbluejay.ai/resources/voice-ai-prompt-engineering
- talker `outgoing.md`（CALL ≤2 句）：https://raw.githubusercontent.com/diegoaltoworks/talker/HEAD/prompts/outgoing.md
- LobeChat `resolveSafeMaxTokens.ts`：`H:\UltimaAI\_vendor\lobehub-canary\packages\model-runtime\src\utils\resolveSafeMaxTokens.ts`
