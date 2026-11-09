# G-ORCH S7 真跑报告（2026-11-09）

> 目的：S7 不是"代码写完就算通"，而是**一单八跳真的跑过一次**。本文记录那一单的
> 实际结果、证据位置和当场暴露的缺陷。凡未真跑的一律标"空"，不写成完成。

## 一、八跳实测

| 跳 | 环节 | 载体 | 结果 | 证据 |
|---|---|---|---|---|
| 1 | 主脑理解（需求转写） | `S-MAIN` / `qwen3-8b-uncensored` | 已真跑 12.4s | 把"记得 git add 和 git commit"收成"提交至 git"，执行细节剥离、结果要求保留 |
| 2 | 审议·理解/方案 | `S-REVIEW` / `deepseek-chat` | completed | `stages/decompose.json`（in 421 / out 1708 tokens） |
| 3 | Owner 确认 | 人工 | 人工代做 | 7 道串行工序全写同一个文件 → 合 1 张工单 `WO-README` |
| 4 | 主脑回传授权条件 | `S-MAIN` | 已接线，本轮未实跑 | `call_main()` 已落地并有单测；本轮授权条件由人写入工单 A1–A3 |
| 5 | 审议·拆解/工单 | `S-REVIEW` | completed | `stages/work_order.json`（out 926） |
| 6 | 审议·工单自检 | 同 stage 内自检 | completed | 产出自检清单 G1–G6 |
| 7 | 执行·写码/自检/提交 | `S-EXEC` / Codex | `result=done` | `config/gorch/README.md` 4209B，提交 `def92006` |
| 8 | 审议·复检 | `S-REVIEW` | `pass: true` | `review-deepseek.json`，A1/A2/A3 全 ok 且各带证据 |

第 3 跳按定义必须由 Owner 做，不算空档。第 1 跳原本判为"空（8B 未起）"，本次发现
ollama 实际一直在跑（11434 监听、已有 8B 模型），已接上。

## 二、产物

`config/gorch/README.md`（4209 字节）六标题五节：配置优先级三级链、使用方式（含
`slots.example.json` 复制命令）、S-REVIEW 五家供应商填写要点、S-EXEC 五个占位符与
"整体替换 argv"语义、S-MAIN 未启用即 `require_main()` 报错的 fail-closed 说明。
五家供应商字段与 `slots.example.json` 第 33–53 行逐字一致，无编造。

## 三、独立复检（第 8 跳）

复检只喂三样：工单（含 A1–A3）、产物全文、变更集（仅新增 1 文件 65 行）。不给主脑
判断、不给执行端自述。结果 `pass: true`，`blockers: []`，A2 证据里逐项列出五节标题、
三级链原文、五家供应商、五占位符、整体替换、fail-closed。

## 四、当场暴露的两个缺陷

**L72 · `wt merge` 超时被当成"没动手"**：180s 超时后核查发现 worktree 与分支都已
被 wt 删掉、主线却没进账，执行端提交成了孤儿（`def92006` 不在任何分支上）。靠
`git cherry-pick` 恢复。修复：`MERGE_TIMEOUT=600` 独立预算 + 超时先 `_branch_exists()`
探现场，两种结论分别表述。

**L73 · 工单里合法的命令示例被判成"模型调用工具"**：`work_order` 阶段两次被拒，命中的
只是工单正文里的 `cp slots.example.json slots.json`。修复：判定改走协议字段
（原生 `tool_calls`），文本标记只留控制 token；失败落盘补原文摘录。

## 五、主脑位（S-MAIN）现状

本机 ollama 装在 `%LOCALAPPDATA%\Programs\Ollama`（**不在 PATH**，此前据此误判为
"未安装"），监听 `127.0.0.1:11434`，已有 `qwen3-8b-uncensored:latest`。适配层默认
endpoint/model 已改为指向它（原默认 `18766` 是没落地的自定端口，指向不存在的地址等于
主脑位永远"未接线"）。`call_main()` 复用 orchestrator 的 OpenAI-compatible 客户端，
不自研 HTTP；`GORCH_MAIN_ENABLED` 用 `_as_bool` 解析，避免 `bool("false") == True` 的坑。

## 六、仍未收口

1. **bridge 边界**：`bridge` 只搬不解析，带 frontmatter 的工单由第 3 跳确认后放进
   批次目录。这与"全自动跑八跳"有张力，需 Owner 定夺。
2. **`MERGE_TIMEOUT=600` 的真实耗时**：本文这一单只有在真实合并上跑过一次才算验证。
3. 跳 4 尚未与真实需求串跑，只有能力与单测到位。
