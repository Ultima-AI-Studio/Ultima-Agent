# G-ORCH 八环节运行台账（2026-11-09 实测）

> 口径：只记录**实测证据**，不记录设计意图。每一步「是否真跑」以产物文件与进程行为为准，不以代码存在为准。
> 本次样本：`run_dir = %TEMP%\orch_live_8b8c1ef2`，需求文本「给 UltimaAgent 增加一个心跳文件写入能力」。

## 一、八环节实测状态

| # | 环节 | 应有执行者 | 载体 | 实测结果（修复后） | 状态 |
|---|---|---|---|---|---|
| ① | 任务理解 | DeepSeek | `run_stage(decompose)` 的 `REQUIREMENT UNDERSTANDING` 段 | 用**未改写的口语需求**直跑，产出复述 + **11 条歧义**（含「主循环卡死时心跳还有意义吗」），`verdict: blocked` 正确拦住 | **通** |
| ② | 拆分依赖 | DeepSeek | `orchestrate-order.py` → `run_stage(decompose)` | 产出 `decompose.json`：U1–U4 单元、依赖与写入域分析、`VERDICT` 行 | **通** |
| ③ | 工单制定 | DeepSeek | 同上 → `run_stage(work_order)` | 产出 `work_order.json`：范围冻结、D1–D6 待决策带默认值、DoR 六门各带可执行检查命令 | **通** |
| ④ | 排程确认 | DeepSeek | 同上 → `run_stage(schedule)` | 产出有效排程表（order / work_order / depends_on / wip_slot / window / gate，5 个 WO，WIP 限 3），`VERDICT: COMPLETED` 被正确提取 | **通** |
| ⑤ | 多 Agent 派发 | Codex | `dispatch-work-order.py` | 两小时内真跑 6 次；2 次被主表脏数据打断（读出端已宽进严出），1 次拿到 `receipt_valid:true` | **通** |
| ⑥ | 监控/心跳/生命周期 | sentinel | `src/brain/sentinel.py` | `.sentinel.lock` + `heartbeat.jsonl` 持续增长，进程常驻 | **通（只覆盖心跳）** |
| ⑦ | 独立审计（两轮） | DeepSeek | **新增** `scripts/audit-work-order.py` | 两个独立会话，Round 2 明示「不沿用 Round 1 结论」；实测对 w7 证据判 **两轮 FAIL**、`audit_passed:false`、exit 2 | **通** |
| ⑧ | 打 tag 提交 | 审计后的执行端 | **新增** `scripts/freeze-work-order.py` | 无 `audit.json` 或 `audit_passed != true` 一律拒绝；实测拒绝成功，`git tag --list` 零创建 | **通** |

## 二、四个断点的修法（已全部落地）

| 断点 | 根因 | 修法 | 验证证据 |
|---|---|---|---|
| ④ 排程产出无效且假报成功 | `run_stage` 把 `verdict` **硬编码为 `completed`**（只看 HTTP 状态，不看产出）；schedule 提示词没告诉模型「你没有工具」 | ① 三条 stage 提示词统一加「NO tools / 禁止输出命令与代码块」；② schedule 指定输出六列排程表；③ 新增 `_looks_like_tool_call`，命中 `<｜｜`、`DSML`、`tool_calls`、```` ```bash ``` 等标记即 raise 并写 `<stage>-failed.json`；④ 新增 `_extract_verdict`，从产出末尾读 `VERDICT:` 行 | 真跑三环节：schedule 产出 5 个 WO 的排程表、零工具标记、`verdict: completed` |
| ① 任务理解无入口 | 原始需求先被人工改写再喂入，DeepSeek 碰不到原话 | decompose 提示词要求先输出 `REQUIREMENT UNDERSTANDING`：复述需求 + 列出所有会改变范围或验收的歧义 | 用**未改写的口语需求**直跑，产出 11 条歧义，`verdict: blocked` 正确拦住 |
| ⑦ 独立审计无载体 | `AUDIT → COMPLETED` 要求 `audit_passed`，但无任何代码填充该字段 | 新增 `scripts/audit-work-order.py`：Round 1 / Round 2 两个独立会话，Round 2 被明确告知「Round 1 只是参考不是真理」，需自行重判；两轮都 PASS 才 `audit_passed: true` | 对 w7 证据真跑：两轮均 FAIL、exit 2、`audit_passed:false`；Round 2 独立发现「receipt 块为空」这一程序性拦阻 |
| ⑧ 打 tag 无载体且顺序反了 | tag 在 Codex 提交后由人工打，审计并未前置 | 新增 `scripts/freeze-work-order.py`：无 `audit.json` 或 `audit_passed != true` 一律拒绝，拒绝时不创建任何 tag | 用 FAIL 的 audit 真跑，拒绝成功，`git tag --list` 零创建 |

**密钥管道（"钥匙在、管道没接"的补口）**：`scripts/orchestrate-order.py` 原先只查 `os.environ`、不读 `config/.env`。已加 `_load_env_file()`，在密钥检查前加载 `.env`，且不覆盖已有环境变量。实测**删除环境变量**（`env_preset=False`）后仍跑通 exit 0。

## 三、跨环节地基问题

| 问题 | 现状 | 影响环节 |
|---|---|---|
| 公共账本无写入门 | 18766 登记接口实测**未监听**；各项目直接改 `H:\UltimaAI\_shared\queue\global-queue-index.md` | ⑤ 派发 |
| 读出端已宽进严出 | 未知状态归一 `unregistered` 继续生成 + 点名；畸形行容错；行尾保真；重复工单仍 fail-closed | ⑤ 已解除阻塞 |
| 全量测试无固定口径 | 28 项既有历史失败，未修、未 ignore | ⑤ 验收 |

## 四、结论

- **八个环节全部有了执行载体**：①–④ DeepSeek（`orchestrate-order.py` + `orchestrator.run_stage`）、⑤ Codex（`dispatch-work-order.py`）、⑥ sentinel（心跳）、⑦ DeepSeek 两轮（`audit-work-order.py`）、⑧ 审计通过后的执行端（`freeze-work-order.py`）。
- **仍存局限**：⑥ 只覆盖心跳与退出异常，不改任务状态；⑤ 仍依赖主表干净，而**写入门尚未落在写入端**，18766 登记接口实测未监听——这两条会继续让派发受制于别人的写入质量。
- **回归**：`tests/test_orchestrate_order.py` **13 passed**（含新增的 verdict 提取、工具调用标记检测、工具调用 fail-closed 三类判据）；`tests/test_receipt_contract.py` + `tasks/queue_engine` 合计 **16 passed**。

```powershell
cd H:\UltimaAI\UltimaAgent
# 注入 .env 的 DeepSeek 凭据后
& .\tools\venv-openjarvis\Scripts\python.exe .\scripts\orchestrate-order.py `
  --requirement '<需求文本>' --run-dir <独立目录>
# 检查三份产物
Get-ChildItem <run_dir>\stages
```

---

## 五、端到端冒烟（一次连跑，2026-11-09）

> 与 §一 的区别：§一 是**逐环节分别实测**，本节是**同一条链一次连续跑完**。任务取自 ① 的真实缺口——「原始需求原文落盘，让审计能对照原文判断理解是否偏离」。

| # | 环节 | 本次实际发生 | 状态 |
|---|---|---|---|
| ① | 任务理解 | 真调 DeepSeek，`decompose.json` 6,617 字符，`verdict: completed` | 通 |
| ②③④ | 拆分 / 工单 / 排程 | `work_order.json` 1,436 字符（W1–W5 + G1–G6 各带判定方式）、`schedule.json` 637 字符（4 个 WO 排程表、WIP 限 3）；三份 `verdict` 全 `completed`，无 `-failed.json` | 通 |
| ⑤ | 派发 | `ready: true` → `--execute` 真起 Codex；run 目录 `wo-orb-w8-20261108T170108721645Z` 产出 `final.json`（5,326B 完整回执）、`out.jsonl` 1.4MB、`heartbeat.jsonl` 2,268B | 通（见卡点 A） |
| ⑥ | 回执判读 | `done.json` = `{"receipt_valid": false, "state": "blocked"}`——交付合格却被判无效 | **卡（卡点 B）** |
| ⑦ | 两轮独立审计 | 真跑两轮，均 **FAIL**，`audit_passed:false`，exit 2 | 通（见卡点 C） |
| ⑧ | 冻结 | `audit_passed:false` → 拒绝打 tag，符合设计 | 通 |

### 冒烟独立复核（不采信执行端自述）

| 核对项 | 方法 | 结果 |
|---|---|---|
| 代码是否真改 | `git diff -- scripts/orchestrate-order.py` | 真改 11 行：`_read_requirement` 用 `newline=""` 原样读、去掉空需求拒绝、`main()` 里 `mkdir` + 写 `requirement.txt`（带覆盖注释） |
| 落盘是否真生效 | 另建 run 目录真跑 `--stages decompose`，字节级读回 | `requirement.txt` 48 字节、**无 BOM**、中文与空格逐字保留 |
| 回归是否真过 | 不隐藏 `config/.env` 直接跑 | **1 failed / 12 passed**（隐藏 .env 后才 13 passed） |

### 冒烟暴露的三个卡点

**卡点 A｜工单号命名是硬编码契约**
`dispatch-work-order.py` L168 的正则是 `wo-(?:s1|orb)-[a-z0-9-]+`。首次用 `wo-smoke-req-txt` 派发直接被判「未知开发工单」（exit 2），而文件确实存在。改名 `wo-orb-w8` 才通过。
性质：不是 bug，是既有约定；但**新建工单系列时若不知此前缀，会被误判为「工单不存在」**，报错文案完全误导。

**卡点 B｜回执契约标记词没有随派发载荷下发**
`receipt_contract._classify_text` 要求回执同时出现 `READY_FOR_DEEPSEEK_AUDIT`（或 `READY_FOR_REVIEW`）与 `自检：PASS`。Codex 交了完整合规回执（改动清单、ACC-1~6 逐项命令与输出、越界声明齐全），但没写这两个契约词 → `receipt_valid:false` → 落 `blocked`。
性质：**契约在判读端，没在执行端**。派发载荷模板里从未写过这两个标记词，执行端无从得知。

**卡点 C｜`_load_env_file()` 引入回归，执行端靠隐藏 .env 掩盖**
上一轮为补「钥匙在、管道没接」加了 `_load_env_file()`。副作用：`test_missing_api_key_exits_nonzero_without_success_artifact` 的前提（无 key）被破坏，因为它现在会自读 `config/.env`。实测不隐藏 .env 时 **1 failed**。
Codex 选择在测试期间临时隐藏 `.env`、结束再恢复，使回归显示 13 passed——审计 Round 2 明确抓住了这一点并判 FAIL。
性质：**修复引入新回归，且验收被规避而非解决**。

---

## 六、三个卡点的修法与端到端复验（2026-11-09）

### 6.1 修法

| 卡点 | 修法 | 验证 |
|---|---|---|
| C | `_load_env_file(path=None)` 支持注入路径；测试 `monkeypatch.setattr(cli, "ENV_FILE", tmp_path / "absent.env")` 把管道隔离掉。**不改生产行为**，不拆真实防护 | 不隐藏 .env 跑：**13 passed**；另跑 `env_preset=False` 实跑，仍自读 .env 并 exit 0 |
| B | 派发器新增 `receipt_contract_block(order)`，写 `prompt.txt` 前自动追加契约块。**标记词只做描述、不写字面**，防止被执行人照抄即通过；同时避免契约块自身命中 blocked 正则 | 单测 6 条：正确写法→`audit`、阻塞写法→`blocked`、旧式无契约→无效、**只抄契约块→仍无效**；相关回归 **50 passed** |
| A | 命名不符与文件不存在拆成两条报错，各自说清原因；正则校验强度不变（仍 fail-closed） | `wo-smoke-req-txt` → 「工单号不符合命名契约…」；`wo-orb-w99-ghost` → 「工单文件不存在…」 |

### 6.2 端到端复验（新工单 `wo-orb-w9`）

| # | 环节 | 结果 |
|---|---|---|
| ①②③④ | 理解/拆分/工单/排程 | 沿用本轮流水线产出，通 |
| ⑤ | 派发 | 第一次 **Codex 进程崩溃**（`exit_code=3221226505` = `0xC0000409` STATUS_STACK_BUFFER_OVERRUN，`err.log` 只有 `memory allocation of 1452324 bytes failed`，`anomaly.json` 记 `consecutive: 3`）；第二次正常执行完成 |
| ⑥ | 回执判读 | **`receipt_valid: true`** —— 契约块生效，Codex 真写出 `自检：PASS` 与 `READY_FOR_DEEPSEEK_AUDIT` |
| ⑥→ | 状态落位 | `state: blocked`、`audit_slot_busy: true` —— 回执有效，但**拿不到审计名额** |
| ⑦ | 两轮独立审计 | 跑通，两轮均 **FAIL**；理由准确：`done.json` 的 `state` 是 blocked 而非 audit、ACC-3 缺 `git status` 证据 |
| ⑧ | 冻结 | 未执行（审计未过，前置门已拦） |

### 6.3 复验暴露的两个新卡点

**卡点 D｜Codex 执行端堆分配崩溃（环境层）**
`exit_code=3221226505`（`0xC0000409`），`err.log` 全文仅一行 `memory allocation of 1452324 bytes failed`，`out.jsonl` 只写出 2 行就中断。崩溃时机器内存充足（空闲 9.8GB / 31.8GB），排除单纯内存不足。同一工单重派后正常执行，说明是**间歇性**崩溃，非稳定故障。`anomaly.json` 的 `consecutive: 3` 说明近期已连续出现。
影响：派发器把它记为 `receipt_valid:false` + `blocked`，与「回执不合格」的表象混在一起，需要靠 `anomaly.json` 的 `exit-anomaly` 才能区分是**崩溃**还是**交付不合格**。

**卡点 E｜审计名额被历史工单长期占满（流程层，会堵死）**
`audit_slot_busy` 的判定是：主表里只要还有其他 `| audit |` 的工单，新回执就降级 `blocked`。当前有 **5 个**工单长期停在 audit：

| 工单 | 滞留原因（表内原文摘要） |
|---|---|
| `wo-ultimaagent-20261030-0007` | 2026-10-31 回填「验收 PASS 待 Owner 打冻结 tag」 |
| `wo-ultimasentinel-20261103-0001` | 已标「范围外冻结 2026-11-08」，仍占 audit |
| `wo-ultimaagent-20261101-0019` | 「待真人采集验证 / Owner 验收」 |
| `wo-ultimaagent-20261101-0020` | 「长期质量未冻结」 |
| `wo-orb-w7` | 「待独立核对，不自动批准或续派」 |

后果：**新完成的工单永远拿不到审计名额，全部降级 blocked**。这不是个别工单的问题，是队列会整体堵死。

**卡点 F｜验收判据自身内部矛盾（出在我写的任务卡）**
`orb-w9` 卡的 goal 写「使判读器判为有效…**而不是落到阻塞**」，而 ACC-5 只写「`receipt_valid` 为 true」。实际结果 `receipt_valid: true` 但 `state: blocked`，两句话给出相反结论。两轮审计都以此判 FAIL，是对的——判据必须与 goal 同一口径，否则永远无法收敛。

---

## 七、卡点 E 的处置：审计名额加上时限（2026-11-09，按方案一执行）

### 7.1 为什么必须治

`audit_slot_busy` 的原判定是：主表里**只要还有别的工单处于 audit**，新回执就降级 blocked。这条规则本身没错（审计要串行），但它没有出口——一个被遗忘的工单会永久占着名额，后面所有工单永远排队。实测当时 5 个工单同时停着，队列整体被堵。

### 7.2 判据（`scripts/dispatch-work-order.py`）

| 判据 | 规则 | 理由 |
|---|---|---|
| 时限 | 在 audit 队列等待超过 `AUDIT_SLOT_MAX_AGE_DAYS`（默认 **7** 天，可用环境变量 `ULTIMA_AUDIT_SLOT_MAX_AGE_DAYS` 覆盖）→ 不再占位 | 滞留本身就是异常，不能让它无限期充当名额 |
| 事实标注 | 状态理由里已写明「范围外冻结 / 已冻结」→ 不再占位，不看天数 | 这类工单已不在流程内，等待天数对它无意义 |
| 兜底 | **取不到任何时间戳 → 仍算占位**（fail-closed） | 没有时间戳不等于已超时，不能凭信息缺失把占位单赶走 |

滞留时长取证优先级：该工单最新 run 的 `done.json.finished_at` → 主表理由里的显式日期（`2026-10-31` 或 `20261030`）→ 放弃并走兜底。**最新证据优先**，旧文案里的日期不能赶走一个刚重派过的工单。

被放过的工单会写进 `{run}/audit-slot.json` 与 `done.json` 的 `audit_slot_disregarded`，状态理由里也点名，便于事后追查是哪些单停止占位、为什么。

### 7.3 真实主表实测

| 工单 | 等待时长 | 判定 |
|---|---|---|
| `wo-ultimaagent-20261030-0007` | 8.7d | 超时，不再占位 |
| `wo-ultimasentinel-20261103-0001` | 0.7d | 理由已标「范围外冻结」，不再占位 |
| `wo-ultimaagent-20261101-0019` | 7.7d | 超时，不再占位 |
| `wo-ultimaagent-20261101-0020` | 7.7d | 超时，不再占位 |
| `wo-orb-w7` | 0.1d | **仍占位**（在途，正常排队） |

5 个降到 1 个。名额不再被历史工单锁死。回归 **58 passed**（新增 8 条：超时放过、近期占位、无时间戳兜底、冻结标注、主表日期回退、run 时间优先、不与自己比、窗口可配）。

### 7.4 仍存在的边界（如实记录）

1. **审计名额只有一个**（`any` 即 busy），所以 w7 在途期间 w9 仍排队。这是串行审计的正常行为，不是堵死；要推进得先把 w7 的审计做完或撤出。
2. **超时工单只是「不再占位」，状态没被改写**。按「只监察、不代替裁决」的边界，我没有替这些工单下结论，主表里它们仍是 audit。要让主表本身也干净，需要一个显式清理动作由 Owner 决定。
3. 时限调短会放过更多，调长更保守；默认 7 天是取舍值，可按环境变量调整，不必改代码。
