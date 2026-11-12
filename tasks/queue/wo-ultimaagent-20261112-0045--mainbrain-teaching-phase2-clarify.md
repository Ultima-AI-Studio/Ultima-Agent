# Codex 工单 · 0045 主脑教学 Phase 2：多轮澄清（听不懂时怎么问、问几次）

> 版本：v1.0 ｜ 状态：可开工 ｜ 适用工具：Codex
> 链路：`wo-ultimaagent-20261112-0045`
> 执行端：Codex（主脑不参与判据定夺）
> 前置：前置单 `wo-ultimaagent-20261112-0044` 已验收冻结（`938d451b` → 终版 `de12aa26`，tag `ultimaagent-mainbrain-teaching-phase1-20261112`），Phase 1 的四类病已收口，可作回归对照
> 方案依据：`docs/plans/plan-ultimaagent-mainbrain-teaching-phase2-20261112.md`（本单方案，含 7 条 F 探针实测基线）
> 锁定 revision：`de12aa26`
> 工作目录锁定：`H:\UltimaAI\UltimaAgent`
> 用法：按 T0→T3 顺序执行，每 T 的 Gate 全绿再进下一条，禁止跳序。

---

## 0. 本单定位

本单只做一件事：**让主脑在"听不懂"时不再装懂派单，而是问一次、问得出方向、且能接上用户的补充；问不动就放弃**。

方案已落盘 `docs/plans/plan-ultimaagent-mainbrain-teaching-phase2-20261112.md`，其中第 1 节是 7 条 F 探针的**原始实测输出**，是本单的事实基线。本单的四项改动逐条对应方案第 4 节。

**核心原则（已在方案声明，本单不得偏离）**：四项改动**全部落代码层**，不做提示词调优。依据是 L138 / L157 两次实测证明「行为层约束对 8B 无效」，Phase 1 的四项改动全部落代码层后 11 条探针 100% 生效。

**三类病灶（实测原文，见方案第 1 节）**：

- **装懂派单（最严重）**：「帮我把那个弄一下」判 task、10.71s、直接派单；「把文件发给他」判 task、1.82s、直接派单。派出去的单子没有宾语，执行端必然空转。
- **无澄清状态**：「打开」回了「你是指打开设备还是应用？」，但用户答「应用」时主脑完全接不上——全仓无会话上下文。
- **推回式话术**：「呃那个嗯」「嗯」都回「你再说一遍？」；「那个东西还是不行」回了「不清楚你指的是哪个部分」却不给任何可选方向。

**已正常工作、本单不得改动**：A 类危险诉求（`_risk_gate`）、B 类实时数据（`_no_tool_gate`）、Phase 1 的四项出口清洗（`_claim_clean` / `_SERVILE_TAIL_PATTERN` / `_DIAGNOSE_DIRECTIONS` / 求代劳短路）。

---

## 1. 范围冻结

**本阶段只做**

1. 新增 `_slot_gate(query) -> str | None`：确定性正则判据，返回缺失槽位类型（`object` / `referent` / `noise`）或 `None`，**不调模型**。
2. 新增 `_CLARIFY_TEMPLATES` 与 `_clarify_reply(slot) -> str`：三类槽位各一条固定澄清话术，**含具体索要方向**，不含「需要我…吗」句式。
3. 新增 `_PUSHBACK_PATTERN`（`你再说一遍|您再说一遍|再说一遍|没听清`），在 `_clean_content` 内一并剥除，命中则替换为对应澄清模板，不留把球踢回去的出口。
4. 新增模块级 `_PENDING_CLARIFY` 单轮挂起状态（dict，含 `query` / `slot` / `asked` / `at`）与 `_CLARIFY_TTL = 30.0`、`_CLARIFY_MAX_ASK = 2`。
5. `ask_once` 入口在 `_classify_intent` **之前**接入 pending 填槽逻辑：命中未过期 pending 则合并为 `f"{原请求}（补充：{新输入}）"` 并清状态；过期或问满则清状态并返回放弃话术。
6. `ask_once` 在判 `task` 后、进 `_ask_task_branch` **之前**接入 `_slot_gate`：有缺失则不派单，记 pending 并返回澄清话术，`intent` 取新值 `clarify`。
7. 新建 `src/brain/tests/test_mainbrain_phase2_clarify.py`：方案第 6 节的 7 条正向 + 3 条接续 + 4 条反向全部落成用例。

**本阶段不做（Non-goals）**

1. **不改** `_risk_gate` / `_no_tool_gate` 的任何正则与话术——这两类已 100% 生效，动它只有风险。
2. **不改** `_classify_intent` 的模型调用方式（必须保留 `disable_thinking=False`，L140 已证明关思考会让 qwen3 在极短判定上返回空串）；**不改**分类器的判据本身，只在其后加槽位门。
3. **不改** `MAINBRAIN_SYSTEM_PROMPT` 的规则条文与 `docs/specs/mainbrain-rules-baseline.md`。
4. **不回退** Phase 1 的任何改动：`_claim_clean`、`_SERVILE_TAIL_PATTERN` 两分支、`_is_too_short`（阈值为 2）、`_DIAGNOSE_DIRECTIONS` 规则表、`_ask_query_branch` 入口的求代劳短路，全部保持原样；Phase 1 的既有测试断言一律不得修改。
5. **不动** provider 层、`slot_adapter`、语音链路（`src/voice-next/**`、`src/brain/voice/**`、`daemon.py`）、GUI（`src/host-shell/**`、`UltimaAgent.Hud/**`）、`installer/`。
6. **不引入**新依赖，只用标准库 `re` / `time` / `datetime`（与现状一致）；**不落盘**会话状态（只在进程内存，不写文件、不入库）。
7. **不做**多任务拆分（「帮我查一下天气然后整理桌面」只处理被拦那半边的问题留 Phase 3）、**不做**主动回报节奏（Phase 3）、**不做** `/health` 的 `provider_note` 文案校准（Phase 4）。
8. 不联网、不装依赖、不 `git add -A`、**不主动改** `queue-status.json`（派发器自身写入的本单状态流转副作用除外，见 Gate T3 判据）。

---

## 2. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `src/brain/tests/test_mainbrain_phase2_clarify.py` + `src/brain/agent_server.py`（仅加 `_slot_gate` 与三类槽位正则常量） | 新增单测先 RED 后 GREEN；`_slot_gate` 对 7 条 F 探针判定正确，且对 4 条反向样本全部返回 `None` |
| T1 | `src/brain/agent_server.py`（`_CLARIFY_TEMPLATES` / `_clarify_reply` / `_PUSHBACK_PATTERN` 接入 `_clean_content`） | 三类话术可被单测定位；推回话术被替换；话术不含服务性反问句式 |
| T2 | `src/brain/agent_server.py`（`_PENDING_CLARIFY` / `_CLARIFY_TTL` / `_CLARIFY_MAX_ASK` + `ask_once` 入口填槽） | 接续三条用例全绿；超时与问满两条放弃路径可复现；`ask_once` 签名未变 |
| T3 | `src/brain/agent_server.py`（`ask_once` 判 task 后的槽位门）+ 回执 | F1/F5 不再派单、intent 取值为 `clarify` 且与方案一致；Phase 1 的 11 条探针无回退；全量无新增失败 |

---

## 3. 任务明细

### T0 · 槽位门与正则常量（先 RED）

**文件**：`src/brain/tests/test_mainbrain_phase2_clarify.py`、`src/brain/agent_server.py`

**写什么**：

1. 在 `agent_server.py` 新增四个模块级编译常量，与 `_RISK_PATTERNS` / `_NO_TOOL_PATTERNS` 同风格：
   - `_NOISE_PATTERN`：整句只由语气词构成（`嗯|呃|啊|那个|喂|在吗` 的组合），或实质字符少于 3。
   - `_REFERENT_PATTERN`：宾语为纯指代（`那个|这个|那些|这些|它|东西|那个东西`）且其后**没有**具体名词/路径/文件名跟随。
   - `_GENERIC_OBJECT_PATTERN`：动作命中但宾语是泛指（如「文件」「那个文件」），**不是**路径、扩展名或带限定的具体名词。
   - `_SPECIFIC_OBJECT_PATTERN`：**排除用**——命中路径（含 `\` 或 `/`）、文件扩展名（`.log` `.txt` `.py` 等）、或「桌面的日志」这类「限定词+具体名词」结构。
2. 新增 `_slot_gate(query: str) -> str | None`：按 `noise` → `referent` → `object` 顺序判定，返回槽位类型或 `None`。**纯正则，不调模型，零延迟**。
3. **判据必须窄**：`_slot_gate` 对「帮我把桌面的日志整理一下」「帮我把 D:\logs\a.log 重命名成 b.log」必须返回 `None`——有具体宾语就不拦。
4. 先写测试到 RED，再实现到 GREEN。单测必须覆盖方案 6.3 的四条反向（R1-R4）与方案 6.1 的七条正向（F1-F7）中的槽位判定部分。

**验收（Gate T0）**：

- `pytest src/brain/tests/test_mainbrain_phase2_clarify.py` 输出含 `passed`，且用例数与 T0 覆盖条数一致。
- `_slot_gate` 对「帮我把那个弄一下」返回 `referent`，对「打开」返回 `object`，对「呃那个嗯」返回 `noise`，三者的返回值分别与上述字面串**一致**。
- `_slot_gate` 对「帮我把桌面的日志整理一下」返回 `None`，对「帮我把 D:\logs\a.log 重命名成 b.log」返回 `None`，二者与 `None` **一致**。
- `_slot_gate` 对「1+1等于几」「什么是市盈率」返回 `None`，与 `None` **一致**。
- `grep -n "_slot_gate" src/brain/agent_server.py` 输出至少 2 行（定义处 + 使用处）。

**禁止**：

- 不许把 `_slot_gate` 改成调模型的判断——本门必须是确定性正则，零延迟。
- 不许把「文件」「桌面」这类词无差别当成缺宾语——只拦纯指代与无宾语两种情形。
- 不许删改 Phase 1 的既有测试断言。

---

### T1 · 澄清话术与推回话术剥离

**文件**：`src/brain/agent_server.py`

**写什么**：

1. 新增 `_CLARIFY_TEMPLATES` 字典，三个槽位各一条固定话术（依方案 4.2 表格逐字落盘）：
   - `object`：`你要我处理哪个？给我个具体名字，比如文件名或路径。`
   - `referent`：`你说的「那个」是指哪一个？说一下名字我就能动。`
   - `noise`：`没听清，再说一遍要做什么。`
2. 新增 `_clarify_reply(slot: str) -> str`：查表返回；未知槽位退回 `noise` 那条。
3. 新增 `_PUSHBACK_PATTERN`（`你再说一遍|您再说一遍|再说一遍|没听清`）与 `_PUSHBACK_REPLY`（取值与 `noise` 模板相同）。
4. `_clean_content` 内新增一步：`_PUSHBACK_PATTERN` 命中则把该句替换为 `_PUSHBACK_REPLY`；与既有 `_SERVILE_TAIL_PATTERN` 剥离并存，先后顺序不得改变既有行为。
5. 单测覆盖：三条模板逐字可查；`_clean_content("你再说一遍？")` 输出与 `_PUSHBACK_REPLY` **一致**；`_clean_content("1+1等于2。")` 输出与入参**相同**。

**验收（Gate T1）**：

- `pytest src/brain/tests/test_mainbrain_phase2_clarify.py` 输出含 `passed`，T1 新增用例全部包含在内。
- `_clarify_reply("object")`、`_clarify_reply("referent")`、`_clarify_reply("noise")` 三者返回值与方案 4.2 表格字面**一致**。
- `_clean_content("你再说一遍？")` 返回值与 `_PUSHBACK_REPLY` **一致**。
- `_clean_content("1+1等于2。")` 返回值与入参**相同**（用 `==` 断言，证明未误伤）。
- `_clean_content` 对 Phase 1 的三条既有断言仍**相同**：`您有什么可以帮您？` 保留原文、`您问的是贾维斯，Ultima Agent主脑。有什么可以帮您？` 剥成主体句、`grounded:false 不确定。` 剥成 `不确定。`。

**禁止**：

- 不许把澄清话术写成「需要我帮您…吗」这类服务性反问——那是 Phase 1 的 P4，已被出口剥掉。
- 不许把 `_PUSHBACK_PATTERN` 做成全局替换导致正常文本（如「我没听清你说什么，请重复」作为用户输入被误改）被误伤——只作用于模型输出侧 `_clean_content`。
- 不许删改 Phase 1 的任何既有断言。

---

### T2 · 单轮挂起状态与填槽

**文件**：`src/brain/agent_server.py`

**写什么**：

1. 新增模块级常量与状态：`_CLARIFY_TTL = 30.0`、`_CLARIFY_MAX_ASK = 2`、`_PENDING_CLARIFY: dict[str, Any] | None = None`。
2. 新增 `_pending_fill(query: str) -> str | None`：存在 pending 且 `time.time() - pending["at"] <= _CLARIFY_TTL` 且 `pending["asked"] < _CLARIFY_MAX_ASK` 时，清 pending 并返回合并后的请求 `f"{pending['query']}（补充：{query}）"`；否则返回 `None`。
3. 新增 `_pending_expire_reply() -> str | None`：存在 pending 但已超时或已问满时，清 pending 并返回放弃话术 `先不弄了，需要的时候再叫我。`；否则返回 `None`。
4. 新增 `_pending_set(query: str, slot: str) -> None`：写入 pending，`asked` 在已有同 `query` 时自增，否则置 1。
5. `ask_once` 入口在 `_no_tool_gate` 之后、`_classify_intent` 之前接入：先试 `_pending_fill`，命中则用合并后的 query 继续走后续流程；再试 `_pending_expire_reply`，命中则直接返回该话术（`intent` 取 `clarify`）。
6. 单测覆盖方案 6.2 的三条接续（G1 / G2 / G3），其中 G3 必须用可注入的时间手段（如 `monkeypatch` 改 `_CLARIFY_TTL` 或用历史时间戳）复现超时路径。

**验收（Gate T2）**：

- `pytest src/brain/tests/test_mainbrain_phase2_clarify.py` 输出含 `passed`，三条接续用例全部包含在内。
- G1：先 `ask_once("帮我把那个弄一下")` 再 `ask_once("就是桌面那个日志文件")`，第二次的 `intent` 与 `task` **一致**（说明已被填槽、不再判 clarify）。
- G3：将 pending 的 `at` 置为 `time.time() - 60` 后再调用，返回话术与 `先不弄了，需要的时候再叫我。` **一致**。
- `grep -n "_PENDING_CLARIFY" src/brain/agent_server.py` 输出至少 3 行（定义处 + 读写处）。
- `inspect.signature(agent_server.ask_once)` 的参数列表与改动前**相同**（用 `assert str(sig) == ...` 或参数名集合断言证明签名未变）。

**禁止**：

- 不许把 pending 状态落到磁盘、写进 `EVENT_BUS` 或塞进 `queue-status.json`。
- 不许让 pending 影响并发：状态读写必须在既有的 `_ask_lock` 保护范围之外也不得引入新的全局锁竞争——只用模块级字典与 `time.time()`，不得加线程锁以外的同步原语。
- 不许删改 Phase 1 的任何既有断言。

---

### T3 · 槽位门接入 task 分支 + 总验收

**文件**：`src/brain/agent_server.py`、`src/brain/tests/test_mainbrain_phase2_clarify.py`

**写什么**：

1. `ask_once` 在 `_classify_intent(query) == "task"` 之后、进 `_ask_task_branch` **之前**接入 `_slot_gate`：有缺失槽位则不派单，`_pending_set(query, slot)` 后返回 `_clarify_reply(slot)`，`intent` 取值 `clarify`。
2. 返回结构与 `_ask_query_branch` 一致（含 `content` / `reply_text` / `confidence` / `grounded` / `intent` / `tool_results` / `usage`），并照常 `EVENT_BUS.emit_event("message", ...)`，使 HUD 可见。
3. 单测覆盖方案 6.1 的七个正向全部（F1-F7），其中 F4 作为**防回退**基线，断言其 `intent` 与 `no_tool` **一致**。
4. 全量回归必须与 T3 开工前快照**一致**（基线口径：唯一失败是 `test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains` 的 ollama-not-in-PATH 环境噪声，该条失败在本单前后应同样存在，不得新增其他失败）。

**验收（Gate T3）**：

- `pytest src/brain/tests/test_mainbrain_phase2_clarify.py` 全绿，方案 6.1 的七条正向全部包含在内。
- F1「帮我把那个弄一下」的 `intent` 与 `clarify` **一致**，且 `content` 不含「已派给」字样（证明未派单）。
- F5「把文件发给他」的 `intent` 与 `clarify` **一致**，且 `content` 不含「已派给」字样。
- F2「打开」的 `intent` 与 `clarify` **一致**，`content` 不含「你再说一遍」字样。
- F7「那个东西还是不行」的 `content` 含「哪一个」或「名字」字样（证明给出方向而非推回）。
- F4「帮我查一下天气然后整理桌面」的 `intent` 与 `no_tool` **一致**（防回退基线）。
- Phase 1 的 11 条探针语义**未回退**：A1/A2 仍 `refused` 且输出两句拼接；B1/B2 仍 `no_tool`；C1/C2 仍 `query` 且 0 秒给方向；D1 仍 `query` 且不派单；D2 仍 `task`；E2/E3 答案不变。
- 全量回归命令 `pytest "src/brain/tests" "src/brain/orchestration/tests"` 结果中，passed 数不少于 T3 开工时快照的 passed 数，且失败集合与快照**一致**。
- `git status --porcelain` 中新增改动只涉及 `src/brain/agent_server.py`、`src/brain/tests/test_mainbrain_phase2_clarify.py`、本单方案与工单文件，其余路径**未新增**改动。

**禁止**：

- 不许为了让 F1/F5 通过而把 `_classify_intent` 改成直接返回 `clarify`——分类职责与槽位职责必须分开。
- 不许改 Phase 1 的探针期望值来"适配"新行为。
- 不许把 `queue-status.json` 整体重排或改写（该文件是纯 LF、2 空格缩进，任何整体重写都会造成大范围假 diff）。
- 不许 `git add -A`（仓库常驻数百未跟踪文件）。

---

## 4. 给编码代理的任务粘贴模板

```
T# <标题>：已完成，Gate 全绿（附证据）
- 验收项逐条结果：✅/❌ + 命令输出
- 改动文件清单：<与"写什么"一一对应>
- 越界声明：无
- 单测：pytest 输出摘要
- 回归：passed 数 + 失败集合
```

---

## 5. 验收要点

- [ ] 范围冻结内逐项完成（无越界）
- [ ] 每 T 验收清单全绿 + 自证完整
- [ ] Phase 1 的所有既有断言与探针期望**零回退**
- [ ] `ask_once` 签名未变、无新依赖、状态不落盘
- [ ] 阶段报告产出 → 冻结 tag
