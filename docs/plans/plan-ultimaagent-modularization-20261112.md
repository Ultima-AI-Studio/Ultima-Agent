# 散代码模块化改造可行性方案 v3（经 Codex 独立复审修正）

> 生成：2026-11-12 ｜ 状态：待 Owner 评审
> **v2 → v3 变更**：v2 的核心前提「三个 registry 空转」经 Codex 独立复审（`docs/reports/review-inventory-20261112.md`，`REVIEW_DONE 12/12`）**判为不成立**。四个自建 Registry 均有生产调用方（`scanner.py`/`backend.py`/`engine.py`/`bootstrap.py`）。**原「第 2.5 批」已撤回**，替换为「文档/职责对齐批」。另有 C1/C2/C6 三处数据修正。
> 复审总判：12 条结论中 **5 成立 / 6 不成立 / 1 证据不足**。
> 数据来源：AST 精确依赖解析 + 源码结构探测 + git 只读历史 + `openjarvis` 包实测 + Codex 独立复审
> 前置：`wo-ultimaagent-20261112-0052` 队列状态 `executing`（21:42 派发），但该单 note 记录过 401 派发失败、需重登后重派；**第 0 批必须先确认它的真实状态**

---

## 零、检查结论汇总（v3 · 已按复审修正）

| # | v1 状态 | v3 实测结论 |
|---|---|---|
| 1 | 5 个 registry 是否真模块化 | ⚠️ **修正**：4 个自建 Registry **全部有生产调用方**（不是空转）。真问题是**三套注册体系并行**（底座/自建/插件总线）且**两套驻留机制互不相通**（见第一节） |
| 2 | 是否有绕过 registry 的直接 import | **存在，但要区分三套体系**，不是"绕过"而是"分工不同且缺权威定义" |
| 3 | `interaction.py` 20 个引用方符号清单 | **已拿到**：生产 5 个符号 / 3 个文件；测试 15 个符号 / 6 个文件（⚠️"20 个引用方"术语不准，实为 9 个来源文件） |
| 4 | 测试是否直接断言 `TOOLS` 字面量 | 用 **`issubset` 子集断言**，不是等值。⚠️ 但这**不等于注册表化就安全**——子集断言发现不了额外泄漏、顺序、重复、`ANSWER_TOOLS` 名单错 |
| 5 | `agent_server.py` 各职责行数分布 | ⚠️ **修正**：可搬 **5 组共 130 行（7.68%）**（v2 误写"4 组"）；`_health_payload` 函数本体 **34 行**、`get_jarvis` **22 行**（v2 的 56/48 是"节点组"不是词法闭包）；**且"不可搬"结论过强——薄包装/参数注入可保住 patch 契约** |
| 6 | 工具新增频率 | `TOOLS` 白名单被改过 **≥2 次**（收窄史）；`agent_server.py` **近 30 天被改 28 次**（Git 可复现） |
| 7 | `TOOLS` 与注册表的关系 | **`@ToolRegistry.register` 已覆盖 9/11**，`TOOLS` 是白名单筛选结果，不是注册表缺失 |

---

## 一、最重要的一处修正：不是"三个空转"，是三套体系并行 + 两套驻留机制互不相通

`bootstrap.py` L4–L9 的注释是权威说明：

```
双登记进底座运行时注册表（openjarvis.core.registry），使
- 底座注册表 = 运行时取件通道（RegistryBase.create/get）
- 自建注册表 = 驻留/审计/白名单管控通道（src.brain.*.Registry）
```

### 1.1 底座取件通道（在用）

`openjarvis` 是**外部包**（`tools/venv-openjarvis/Lib/site-packages/openjarvis`），其 `core/registry.py` 有 **17 个 ClassDef** = `RegistryBase` 基类 + **16 个具体注册表**：

`AgentRegistry` / `BenchmarkRegistry` / `ChannelRegistry` / `CompressionRegistry` / `ConnectorRegistry` / `EngineRegistry` / `FactStoreRegistry` / `LearningRegistry` / `MemoryRegistry` / `MinerRegistry` / `ModelRegistry` / `RouterPolicyRegistry` / `SkillRegistry` / `SpeechRegistry` / `TTSRegistry` / `ToolRegistry`

实际使用点：

| 注册表 | 使用处 |
|---|---|
| `ToolRegistry` | `agent_server.py:88`、`agent_tools_ultima.py:31`、`middleware/registry.py:44` |
| `MemoryRegistry` | `bootstrap.py:102` 注册 `"mem0_ultima"` → `Mem0Backend` |
| `RouterPolicyRegistry` | `bootstrap.py:135` 注册 `"ultima_langgraph"` |

### 1.2 自建驻留管控通道（⚠️ 四个全在用，v2 判"空转"是错的）

| 文件 | 生产调用方 | 状态 |
|---|---|---|
| `brain/skills/registry.py` | `bootstrap.py:247` import（**真调用在 `:249`** `install_task_domain`）；`skills/dispatch.py:44/60/69`；`skills/whitelist.py:74/93/150` | **在用** |
| `brain/guardrails/registry.py` | `guardrails/scanner.py:113 is_registered` + `:114 register` | **在用** |
| `brain/memory/registry.py` | `memory/backend.py:88 is_registered` + `:89 register`；`:273 is_resident` | **在用** |
| `brain/orchestration/registry.py` | `orchestration/engine.py:127 is_registered` + `:128 register`；`:321 is_resident` | **在用** |
| `middleware/registry.py` | 用底座 `ToolRegistry` | 在用（底座） |

**AST 精确统计（`src/`）**：`is_registered` 4 处、`register` 8 处（生产 3 + 测试 5）、`is_resident` 14 处、`unload` 8 处（**全部在测试，仅指这四个 Registry**）。

### 1.3 第三套：插件总线（v2 完全漏了）

`execution/server/ultima_bus/`（**12 个文件，全部未跟踪、不在 HEAD**）：

```
kernel.py  ← class BusKernel (L61)；load(L200) / unload(L242) / switch(L258) / rollback(L317)
cli.py     ← argparse；L55 调 kernel.unload(args.module_id)
registry.py / manifest.py / storage.py / events.py / errors.py / static_registry.json
```

`docs/specs/registry.md:55` 已登记：`ultima-plugin-bus` = **「s3-bus-kernel 已实现，待独立评审」**。

### 1.4 真正的结构问题：两套驻留机制互不相通

| | 自建 Registry | 插件总线 BusKernel |
|---|---|---|
| 驻留判定 | 各 Registry 内 `_resident` set | `RESIDENT_DOMAINS = {"L8", "L10"}`（**硬编码、漏 L9**） |
| 拒绝卸载 | 抛 `ResidencyViolationError` | 抛 `PermissionDenied` |
| 谁在用 | 生产：`scanner`/`backend`/`engine`/`bootstrap` | 生产：自己的 CLI；`src/` 内**仅测试** |

**两点必须记录**：
1. `BusKernel.unload()` **不调用** `src/brain/*/registry.py` 的 `unload()`
2. `BusKernel.RESIDENT_DOMAINS` **漏了 L9**（记忆），而 `memory/registry.py` 头部写"与 L8 同规"

**这才是"拼接"留下的真正代价：两个并行系统各自实现了同一件事，且彼此 unaware。**

---

## 二、第二处重要发现：`TOOLS` 不是"注册表缺失"，是"白名单焊死"

`agent_server.py` L12 注释：
```
- 工具注册：import agent_tools_ultima 触发 ToolRegistry 装饰器注册；
```

实测 9 个装饰器注册点（`agent_tools_ultima.py`）：

| 行 | 工具名 |
|---|---|
| L96 | `ultima_subagent` |
| L206 | `ultima_skill_manage` |
| L239 | `ultima_memory` |
| L264 | `ultima_web_search` |
| L305 | `ultima_task_query` |
| L377 | `ultima_task_adjust` |
| L486 | `ultima_env_snapshot` |
| L796 | `ultima_dispatch` |
| L873 | `ultima_dispatch_status` |

加底座自带的 2 个（`calculator` / `think`）= **11 个 = `TOOLS` 列表**。

**所以 `TOOLS` 和 `ANSWER_TOOLS` 是「暴露给 LLM 的白名单」，不是注册表缺失。** 注册表已经覆盖了 9/11。

**这改变了第二批的做法**：

| v1 说法（错） | v2 正确做法 |
|---|---|
| "把 TOOLS 改成注册表登记，参照 skills/registry.py" | 注册表已有。要做的是**把白名单从字面量改成声明式常量，并从 `ToolRegistry` 校验取件** |

正确的实现形态：

```python
# src/brain/tools/catalog.py
MAIN_WHITELIST = ("calculator", "think", "ultima_subagent", ...)   # 11
ANSWER_WHITELIST = ("calculator", "think", "ultima_memory",
                    "ultima_dispatch", "ultima_dispatch_status")   # 5

def resolve(whitelist):
    missing = [n for n in whitelist if not ToolRegistry.contains(n)]
    if missing:
        raise RuntimeError(f"白名单工具未在 ToolRegistry 注册: {missing}")
    return list(whitelist)

TOOLS = resolve(MAIN_WHITELIST)
ANSWER_TOOLS = resolve(ANSWER_WHITELIST)
```

**收益不是"能加工具了"（本来就能加），而是「名字拼错会立刻报错」**。当前若在 `TOOLS` 里写错一个名字，没有任何校验，静默失效。

**⚠️ 切不可让 `ANSWER_TOOLS = TOOLS`**：L172–187 的实测注释是行为约束（8B 拿 `task_adjust` 会乱改队列，拿只读查询会把「修 CV3」理解成「查队列」）。

---

## 三、第三处发现：`interaction.py` 第 3 批其实可行

v1 判「当前不可行，材料不足」。材料补齐后：

**生产引用仅 5 处 / 3 个文件**：

| 引用方 | 符号 | 跨域 |
|---|---|---|
| `brain/cli.py:13` | `InteractionLoop` | 同域 |
| `brain/interaction_orb.py:26` | `InteractionLoop`、`InteractionResponse` | 同域 |
| `voice-next/turn_worker.py:228` | `_extract_wakeword_change`、`_is_ambiguous_wakeword_change` | **跨域（voice-next → brain）** |

**测试引用 15 处**，涉及符号：`InteractionLoop`、`_ADJUST_INTENT`、`_CONFIRM_INTENT`、`_CONSULT_INTENT`、`_INSERT_COMMAND`、`_PRIORITY_COMMAND`、`_normalize_utterance`、`_load_asr_near_homophones`、`_DEFAULT_ASR_NEAR_HOMOPHONE`。

**关键洞察**：`voice-next/turn_worker.py` 从 `brain/interaction.py` 取语音唤醒词相关函数 → **说明 `interaction.py` 里混了本该属于语音域的逻辑**。这是第一个拆分切口，而且切口清楚：**把语音相关函数搬到 `brain/voice/`，`voice-next` 改为从 voice 域取**。

**所以第 3 批从「不可行」改为「可行但有顺序」**，前置是先拆语音部分。

---

## 四、可插拔的机械判据（⚠️ 六条经复审全部需要修正）

| # | 判据 | 检查方式 | 自动 | 复审判定 |
|---|---|---|---|---|
| 1 | ~~单一入口~~ | ~~AST 扫 `ImportFrom`，包内 `level>0` 且导入的不是包名本身 → 违规~~ | ~~是~~ | ❌ **不可采用**：包内相对导入是合法的（`scanner.py` 的 `.registry` 正是）。应先定义每包公开入口与允许边，再查绕过，且须覆盖绝对导入 |
| 2 | 无反向依赖 | import 图检测环（手写 DFS，不引入 `networkx`） | 是 | ⚠️ **必要但不充分**：违反层级方向的边可能不成环。需补允许依赖矩阵 + 强连通分量 + 动态导入清单 |
| 3 | ~~注册表驱动而非字面量~~ | ~~模块内存在被外部读取的 `^\s*[A-Z_]+\s*=\s*\[` 列表字面量 → 违规~~ | ~~是~~ | ❌ **不可采用**：安全白名单可合理为常量；改成元组就绕过正则。应查"注册完成后的解析路径 + 精确允许集合 + fail-fast" |
| 4 | 入口与逻辑分离 | 含 `__main__`/`def main()` 的文件，非测试文件入度须为 0 | 是 | ⚠️ **仅本项目约定**：CLI 模块可同时提供稳定可测 API；要区分 `main()`、业务 API、进程启动关系 |
| 5 | **注册表有生产调用方**（v3 修正） | AST 区分注册/查询/卸载三类调用，区分生产/测试，正确处理相对导入、别名、try/条件导入、动态入口；**一个 import 不算调用** | 是 | ⚠️ **目标合理、判据不足** |
| 6 | 单文件职责 ≤1 领域 | 提取 `^def _(\w+?)_` 前缀，去重 ≥3 | 人工复核后固化 | ⚠️ **只能作人工审阅提示，不能当阻断门**：漏类方法和公开函数，"降到 ≤2"无依据 |

**判据 5 的实际教训**：v2 用它推出"三个空转"，但 AST 只扫了跨目录 import、漏了同包相对导入 `from .registry import X`，结论是错的。**这条判据本身没错，错在实现方法。**

---

## 五、分批方案

### 第 0 批（前置，不改代码）

- **等 0052 落地**（当前 state=executing，2026-11-12 21:42 派发）
- 跑全量 pytest 固化基线
- **产出**：基线记录（passed/failed 数与 failed 测试名）

### 第 1 批（低风险）：按依赖闭包搬 5 组共 130 行

| 目标模块 | 行数 | 依赖闭包 |
|---|---|---|
| `gates/risk.py` | 17 | `_RISK_PATTERNS`, `_RISK_REFUSAL`, `_risk_gate` |
| `gates/no_tool.py` | 12 | `_NO_TOOL_PATTERNS`, `_NO_TOOL_REPLY`, `_no_tool_gate` |
| `gates/content.py` | 66 | `_CLARIFY_TEMPLATES`, 5 个 Pattern, `_clean_content` |
| `tools/catalog.py` | 20 | `TOOLS`, `ANSWER_TOOLS` |
| `prompts/mainbrain.py` | 15 | `_QUERY_SYSTEM`, `STRUCTURED_REPLY_*` |

**必须留原地**（依赖被 monkeypatch 的模块级状态）：

| 组 | 本体行数 | 原因 |
|---|---|---|
| `_health_payload` | **34**（L1407–1440） | 读 `_MAIN`（测试 patch **7 次**）；v2 写的 56 是"节点组"不是函数本体 |
| `get_jarvis` | **22**（L401–422） | 读 `_jars`/`_MAIN`，`_ensure_tools_registered` 单独被 patch；v2 写的 48 同理 |

**为什么这批排第一**：全是常量/纯函数，无状态无 IO；`agent_server.py` 生产侧入度 0，只有测试受影响。
**为什么不更早**：与 0052 冲突，且第 0 批必须先确认 0052 状态。
**为什么不更晚**：是第 2 批的硬前置。

**⚠️ 必做（数据已按复审修正）**：`agent_server.py` 保留 re-export，且**只搬无状态符号**。

测试里有 **16 个 `monkeypatch.setattr(agent_server, ...)` 调用、8 种符号**（v2 误写"7 处"）：

```
EVENT_BUS 3 ｜ _MAIN 7 ｜ SSE_PING_SECONDS 1 ｜ ask_once 1
_jars 1 ｜ _ensure_tools_registered 1 ｜ Jarvis 1 ｜ get_jarvis 1
```

位置：`test_agent_server_sse.py:20/115/131`、`test_prompt_boundary_p0.py:120`、`test_provider_layer.py:211/253/273/274/275/276/430/452/476/499`、`test_mainbrain_rules_prompt.py:36/37`。

⚠️ **"一个都不能搬"这个结论过强**（v2 的原话）。复审已用两个 `ModuleType` 最小实验确认风险真实存在（直搬函数后 `__globals__` 指向新模块，patch 打不中），**但可用薄包装 / 显式参数注入 / 共享状态对象保住 patch 契约。** 所以准确表述是：**这 8 个符号不能"直接搬定义"，但可以经由包装保留契约。**

### 第 2 批（低风险，核心收益）：白名单声明式化 + 注册表校验

- **前提**：第 1 批已把 `TOOLS`/`ANSWER_TOOLS` 搬进 `tools/catalog.py`
- **改什么**：白名单改成元组常量 + `resolve()` 从 `ToolRegistry` 校验取件；名字未注册则 **fail-fast 抛错**
- **加工具的新路径**：① `agent_tools_ultima.py` 加 `@ToolRegistry.register("xxx")` ② 白名单加一行。**不动 `agent_server.py`**
- **收益的实测支撑**：`agent_server.py` **近 30 天被改 28 次**；`TOOLS` 白名单被改过 ≥2 次（`6be0c75b` 收窄、`0b281baa` 按副作用收口）
- **风险**：白名单与 `ToolRegistry` 不一致时启动即失败 → 这是**想要的**（fail-fast 优于静默失效），但需在启动前跑一次校验测试

### 第 0.5 批（**替换原第 2.5 批**，纯文档、不改代码）：三套注册体系职责对齐

⚠️ **原第 2.5 批「三个空转 registry 接上或删除」已被复审撤回**——它建立在错误前提上（四个 Registry 都有生产调用方），且"接上或删除"是强制二选一，不成立。

**本批只做三件事（不改一行代码）**：

1. **定义三套体系的职责边界与唯一真源**（写入 `docs/specs/registry.md`）：

   | 体系 | 职责 | 权威性 |
   |---|---|---|
   | `openjarvis.core.registry.*`（16 个） | 运行时取件通道 | 外部包，不改 |
   | `src/brain.*/*ResidencyRegistry`（4 个） | 驻留/审计/白名单管控 | 自建，待命名收敛 |
   | `execution/server/ultima_bus/registry.py` | 插件装载状态（生命周期/版本/回滚） | 自建，**未跟踪、待评审** |

2. **回答一个 Owner 决策问题**：**驻留真源是谁？**
   - 当前两套并行（`brain Registry` 的 `_resident` / `BusKernel` 的 `RESIDENT_DOMAINS`），彼此 unaware
   - 若选 `BusKernel` 为真源，必须补 L9（当前 `RESIDENT_DOMAINS = {"L8","L10"}` 漏了记忆层）
   - 若选自建 Registry 为真源，则 `BusKernel` 要改为向它查询
   - **这是架构决策，不是技术细节，但也不需要 Owner 现在拍——先由本批把选项和代价写清**

3. **把三套体系的命名冲突整理成清单**（`inventory` 附表已列 16 项）

**为什么不做成代码批次**：复审明确——"任何代码迁移必须放到新鲜基线之后"，且"Registry/Bus 批次不必阻塞第 1、2 批的目录布局"。

### 第 2 批（低风险，核心收益）：白名单声明式化 + 注册表校验

### 第 3 批（中风险，改判为可行）：`interaction.py` 929 行

**拆分顺序（不可乱）**：

1. **先切语音部分**：`_extract_wakeword_change` / `_is_ambiguous_wakeword_change` → 搬到 `brain/voice/`，`voice-next/turn_worker.py` 改从 voice 域取。**这一步消掉唯一的跨域引用**。
2. **再拆对话主链**：`InteractionLoop` 内部按职责分组（意图识别 / 模板渲染 / 槽位填充 / 应答组装）
3. **`interaction_orb.py` 与 `cli.py`** 只取 `InteractionLoop`/`InteractionResponse`，re-export 即可

**风险控制**：15 个测试引了 8 个私有常量（`_ADJUST_INTENT` 等），这些**必须 re-export**，否则测试失败。

### 第 4 批（低价值，可选）：15 个入度 2–3 的散文件归域

纯可读性收益，不单开工单，可随第 3 批顺手做。

---

## 六、明确否决清单

1. **否决把 `weather.py` / `interface_route.py` 归入子域** —— `interaction.py:501` 与 `:474` 是刻意的确定性快路径（几十毫秒，绕过 LLM）。归域会诱导后人改成走 LLM。若要整理，应建 `brain/bypass/` 并明确注释「不得改走 LLM」。
2. **否决把 `sentinel.py` / `cli.py` 当散代码整理** —— 入度 0 + 独立 CLI 是正确形态。
3. **否决把 `ANSWER_TOOLS` 与 `TOOLS` 统一** —— 11 vs 5 是实测行为约束，统一即回归。
4. **否决让 `TOOLS` 直接等于 `ToolRegistry` 全量** —— 会把 11 个全暴露给应答侧。
5. **否决"接上或删除"式处理自建 registry** —— 四个都有生产调用方，删除会拆掉 `bootstrap.py` 双登记的一半；且"必须二选一"这个前提本身不成立。**三套体系的职责边界应先文档化，代码迁移放到新鲜基线之后。**
6. **否决把「provider 配置层落地」混入本次改造** —— `provider_configured: false` 是功能缺口，不是模块化问题。
7. **否决引入任何新依赖**（含 `networkx`）。
8. **否决在基线前删除任何有生产调用的代码** —— 复审明确要求先定义驻留真源，再谈接通。

---

## 七、风险清单

| 批次 | 风险 | 影响面 | 缓解 |
|---|---|---|---|
| 0 | 0052 未完成就动手 | `agent_server.py` 相关 12 个测试 | 等 commit 落地 |
| 0 | 基线未固化 | 无法区分改造失败与既有 1 failed（ollama 缺失） | 第 0 批产出基线 |
| 1 | 搬走被 monkeypatch 的状态符号 | `_MAIN`(**7次**)/`_jars`/`EVENT_BUS`/`Jarvis`/`get_jarvis`/`_ensure_tools_registered`/`SSE_PING_SECONDS`/`ask_once` → 测试静默失效 | **不直搬定义**；如必须搬，用薄包装/参数注入保住 patch 契约 |
| 1 | `_QUERY_SYSTEM` 搬运改动任何字符 | `test_mainbrain_rules_prompt`、`test_prompt_boundary_p0` | 逐字节搬迁 + diff 校验 |
| 1 | 漏搬闭包内常量 | `gates/content.py` 内 ImportError（`_CLARIFY_TEMPLATES` 等） | 按第 1 批闭包表整组搬 |
| 2 | 白名单与 ToolRegistry 不一致 | 启动即抛错（预期行为），但若无测试会阻塞启动 | 加启动前校验测试，**断言精确集合而非子集** |
| 2 | 误把 11 个给应答侧 | 8B 行为回归 | 断言 `ANSWER_TOOLS` **精确等于 5 项名单** |
| **0.5** | 三套注册体系职责未定就动代码 | 驻留判定出现矛盾结论 | 先出文档、定真源，代码迁移放新鲜基线之后 |
| 3 | 15 个测试引 8 个私有常量 | 未 re-export → 测试失败 | 逐符号 re-export（私有常量长期 re-export 只能作过渡层） |

**对 580 passed 的影响面**（12 个测试文件）：`test_agent_server_sse`、`test_mainbrain_gates`、`test_mainbrain_teaching`、`test_mainbrain_phase2_clarify`、`test_mainbrain_phase3_preclassify`、`test_mainbrain_phase3_5_deliverable`、`test_prompt_boundary_p0`、`test_provider_layer`、`test_agent_tools_extend`、`test_closed_loop_audit`、`test_structured_reply`、`test_mainbrain_rules_prompt`

---

## 八、每批可执行验收判据

**第 0.5 批（纯文档）**
- `docs/specs/registry.md` 新增「三套注册体系职责边界」章节，含唯一真源声明
- `inventory` 与 `plan` 两份文档的前提不再互相冲突（都写"四个 Registry 有生产调用方"）
- 三套体系的命名冲突清单落盘（16 项）

**第 0 批**
- ⚠️ **先确认 0052 的真实状态**：完成 / 终止 / 需重派（队列 note 记录过 401 派发失败，不能仅凭 `state=executing` 判断）
- 记录 HEAD、`agent_server.py` 的 sha256、目标测试基线
- **验收应比对"失败身份与行为"，而不是写死 `580 passed / 1 failed`**——新增必要测试会导致 passed 数变化，不应因此阻断

**第 1 批**
- 基线失败项身份与行为不变（不强制 passed 数相同）
- `python -c "from src.brain import agent_server as m; [getattr(m,s) for s in ['TOOLS','ANSWER_TOOLS','_clean_content','_no_tool_gate','_risk_gate','_QUERY_SYSTEM']]"` 退出 0
- `agent_server.py` 行数从 1692 降到约 1562（±5）（**这是节点跨度参考，不是承诺的净减行数**）
- 新模块可独立导入且**不加载 agent_server**：`python -c "from src.brain.gates.risk import _risk_gate"` 退出 0
- 对实际依赖闭包加测试（不只测搬走的符号）

**第 2 批**
- 基线失败项身份与行为不变
- 判据 3（修正版）：注册完成后的解析路径、精确允许集合、fail-fast 行为均有测试覆盖
- **校验生效测试**：故意在 `MAIN_WHITELIST` 里放一个不存在的名字 → `resolve()` 抛 `RuntimeError`
- **断言精确集合**：`set(TOOLS) == 11 项名单`、`set(ANSWER_TOOLS) == 5 项名单`，并断言禁止集合（哪些绝不能进应答侧）
- `catalog` 不在导入时过早解析注册表；校验时序在 `_ensure_tools_registered()` 之后

**第 0.5 批（代码部分，若 Owner 选择统一驻留真源）**
- 驻留真源唯一：卸载权限判定只有一个权威点
- 若选 `BusKernel` 为真源 → `RESIDENT_DOMAINS` 必须补 L9
- 适配/回滚测试通过

**第 3 批**
- 语音函数已搬至 `brain/voice/`，`voice-next/turn_worker.py` 不再 import `brain.interaction`
- 基线失败项身份与行为不变
- 允许依赖矩阵检查通过（不只看"图无环"）
- 天气/取数快路径端到端测试通过

---

## 九、结论

**整体可行。但真正的病灶与我们最初的判断不同——不是"缺注册表"，也不是"三个空转"，而是「三套注册体系并行、两套驻留机制互不相通、白名单焊死、装配入口被绕过」。**

| 判断 | v1 | v2 | **v3（经复审）** |
|---|---|---|---|
| 模块化缺口 | 缺注册表 | 注册表有，但 3 个空转 | **注册表有且四个都在用；真问题是三套体系并行 + 驻留真源不唯一**；`ToolRegistry` 已覆盖 9/11 |
| 插件总线 | — | 只有规格文档 | **已实现（12 文件），但在 `execution/server/ultima_bus/`、未跟踪、待评审** |
| 核心收益 | 减 1692 行 | 白名单 fail-fast 校验 + 高频改动文件可拆 | **不变**：白名单 fail-fast + 可独立测试；130 行是节点跨度不是净减 |
| 第 3 批 | 不可行 | 可行，但先切语音部分 | **可行（中风险 API 迁移）** |
| 收益量级 | 大幅瘦身 | 130 行 / 7.7% | **5 组 130 行 / 7.68%**（"4 组"是笔误） |

**推荐执行顺序（采纳复审意见，已重排）**：

```
0.5（纯文档：三套体系职责对齐 + 驻留真源选项）
  ↓
0（确认 0052 状态 + 记录基线，所有代码改动的第一门）
  ↓
1（搬 5 组 130 行，有条件可行）
  ↓
2（白名单声明式化 + 注册后显式校验，断言精确集合）
  ↓
[独立工单] Registry/Bus 统一（若 Owner 选择）
  ↓
3（拆 interaction.py：先移 wakeword 消跨域边，再拆主链）
  ↓
4（可选，重新逐文件评估）
```

**关键改变**：
1. **原"2.5 批"撤回**——建立在错误前提上，不能把"接上或删除"作为强制二选一
2. **Registry/Bus 统一从"前置阻塞"降为"独立工单"**——现文没有证明 `gates/`、`tools/catalog.py` 的位置依赖驻留 Registry 的去留
3. **第 0 批成为所有代码改动的第一门**——且验收应比对失败身份，不写死 passed 数
4. **第 4 批保持可选**——标题称"15 个入度 2–3"但自己的 E 表含 11/12/15 等值，分类前提错误

**需要 Owner 决策的一件事（但不必现在拍）**：**驻留真源选谁。**
选项 A：`BusKernel.RESIDENT_DOMAINS`（有 CLI + 审计日志，但当前漏 L9）
选项 B：`src/brain/*/registry.py`（生产在跑，但无 CLI 入口）
**第 0.5 批的任务就是把这两个选项的代价写清，供 Owner 选。**

---

## 十、22 个散文件处置表（逐个定去向）

**分类原则**：不是"入度高的就归域"。入度高意味着被广泛依赖，塞进子域会让子域内其他文件 import 它，产生**新的内部耦合**。所以按处置动作分四类，而不是按"该归哪"分。

### A 类 · 搬（第 1 批，共 130 行，5 组）

只搬 `agent_server.py` 内的无状态符号，不涉及散文件本身。

### B 类 · 拆（第 3 批）

| 文件 | 行数 | 导入符号数 / 来源文件数 | 拆法 |
|---|---|---|---|
| `interaction.py` | 929 | **20 / 9**（生产 5 符号 3 文件 + 测试 15 符号 6 文件） | 先切语音函数（`_extract_wakeword_change`/`_is_ambiguous_wakeword_change`）→ `brain/voice/`；再拆对话主链 |

### C 类 · 留原地，不动（4 个）

| 文件 | 行数 | 导入符号数 / 来源文件数 | 理由 |
|---|---|---|---|
| `agent_server.py` | 1692→1562 | 18 / **12**（全测试） | **进程入口**。剩下的 HTTP handler + 业务逻辑依赖 `_MAIN`（测试 patch **7 次**）/`_jars`，**直接搬定义会失效**（可用薄包装绕过，但收益不抵成本） |
| `bootstrap.py` | 392 | 7 / 2 | **装配入口**。第 0.5 批只定位它的职责边界，不搬位置 |
| `sentinel.py` | 181 | 0 / 0 | 独立 CLI，`__main__` 是正确形态 |
| `cli.py` | 72 | 0 / 0 | 独立 CLI，同上 |

### D 类 · 刻意旁路，留原地 + 加注释（2 个）

| 文件 | 行数 | 入度 | 处置 |
|---|---|---|---|
| `weather.py` | 379 | 3 | **不归域**。在文件头显式标注「确定性快路径，被 `interaction.py:501` 直达调用，**不得改为走 LLM 工具选择**」 |
| `interface_route.py` | 469 | 1 | **不归域**。同样标注（`interaction.py:474` `from . import interface_route`） |

**若一定要有目录归属**，建 `brain/bypass/` 单独装这两个，目录名本身即约束。

### E 类 · 暂不动，等 A/B 做完再评估（15 个）

> ⚠️ **术语更正**：下表"导入符号数"不是图论入度。一个 `from module import A,B,C` 算 3 个符号，但依赖图只有 1 条来源边——用它夸大会造成误判。
> ⚠️ **E 类标题原称"15 个入度 2–3"已被复审判为分类前提错误**：下表实际含 11、12、15 等值。**本类应保持可选并逐文件重新评估。**

| 文件 | 行数 | 导入符号数 / 来源文件数 | 当前判断 |
|---|---|---|---|
| `agent_tools_ultima.py` | 965 | 11 | 工具实现，将来可归 `tools/`，但它已用 `@ToolRegistry.register` 自注册，**归域的收益低** |
| `environment.py` | 358 | 12 | 与 `environment_upgrade.py` 成对，可合建 `environment/` 域，但两者入度合计 21，合并后内部耦合高 |
| `environment_upgrade.py` | 230 | 9 | 同上 |
| `orchestrator.py` | 290 | 2 | `orchestration/` 域已存在，塞进去会与 `engine.py`/`queue.py` 耦合 |
| `voice_loop.py` | 276 | 4 | `voice/` 域已存在（17 文件），但该域已很大，再塞会更难拆 |
| `slot_adapter.py` | 242 | 7 / **7** | **小而被 7 个来源文件引用**，是最稳定的接口之一，搬它风险高于收益 |
| `interaction_orb.py` | 209 | 2 | 悬浮球 UI，与 `display/` 域职责有重叠 |
| `queue_source.py` | 182 | 6 | 队列数据源，与 `orchestration/queue.py` 有重叠 |
| `capability.py` | 177 | 8 | 能力策略，与 `guardrails/policy.py` 职责重叠 |
| `prompt_boundary.py` | 160 | 15 | **入度 15 但只有 160 行**，是全仓最稳定的接口之一，**强烈建议不动** |
| `intent.py` | 155 | 8 | 与 `routing/` 域职责重叠 |
| `reporter.py` | 111 | 5 | 汇报，无对应域 |
| `mainbrain_proposal.py` | 76 | 3 | 主脑提议，无对应域 |
| `agent_client.py` | 50 | 3 | 客户端，无对应域 |
| `memory_write_boundary.py` | 24 | 3 | 可归 `memory/`，但仅 24 行，搬它收益极低 |

**E 类的共同判断**：这些文件当前的"没归域"**没有造成实际问题**。真正造成问题的是 `agent_server.py` 一人 7 职责和 `interaction.py` 929 行。**先把 B 类做完，再回来评估 E 类**，否则是在没有病因的地方动刀。

### 汇总

| 类 | 数量 | 动作 | 批次 |
|---|---|---|---|
| A | 5 组（agent_server 内） | 搬 130 行 | 第 1 批 |
| B | 1 | 拆 | 第 3 批 |
| C | 4 | 不动 | — |
| D | 2 | 加注释约束 | 随时 |
| E | 15 | 暂不动 | 待评估 |
