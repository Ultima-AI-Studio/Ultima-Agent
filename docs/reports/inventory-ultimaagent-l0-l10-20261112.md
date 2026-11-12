# UltimaAgent 全仓梳理（v2 · 经 Codex 独立复审修正）

> 生成：2026-11-12 ｜ v1 已由 Codex 独立复审（`docs/reports/review-inventory-20261112.md`，`REVIEW_DONE 12/12`）
> 依据：`docs/plans/product-plan.md`（v2.3 冻结）+ `docs/specs/registry.md`（L0-L10 实施状态）+ `docs/specs/plugin-bus-spec.md` + AST 实测 + Git 只读历史
> 复审判定：12 条中 **5 成立 / 6 不成立 / 1 证据不足**。**本文已按复审结论逐条修正，修正处在文中标 ⚠️ 更正。**
> 基线：分支 `codex/voice-fsmn-new-path`，`HEAD=9737961744ce5c35dc71519d546e1cb9f7b85c45`

---

## 零、先说三条最重要的更正（v1 判错了）

### 更正一：插件总线**存在**，在 `execution/server/ultima_bus/`，不在 `src/`

⚠️ v1 我搜 `src/` 找 `plugin_bus` 零命中，就断言"只有规格文档、无实现"。**错。**

实际当前工作区有 12 个文件：

```
execution/server/ultima_bus/
├── __main__.py  __init__.py
├── kernel.py    ← class BusKernel (L61)，load(L200) / unload(L242) / switch(L258) / rollback(L317)
├── cli.py       ← argparse，注册 list/load/unload/switch/rollback/status；L55 调 kernel.unload()
├── registry.py  ← 它自己的 Registry
├── manifest.py  storage.py  events.py  errors.py
└── static_registry.json
ultima_bus/      ← 根包门面（__main__.py / __init__.py）
```

**关键边界**：这 12 个文件**全部未跟踪**（`git status` 显示 `?? execution/server/ultima_bus/`、`?? ultima_bus/`），`git ls-tree HEAD` 无对应条目 —— **存在于工作区，尚未进入版本历史**。

`docs/specs/registry.md:55` 已登记：`ultima-plugin-bus` = **「s3-bus-kernel 已实现，待独立评审」**。

#### ⚠️ 更正（v2.1）：这套总线**真的跑过，且拒绝过 189 次**

`logs/plugin-bus.jsonl` 实测 **12737 行 / 2225746 B**，时间跨度 **2026-10-27 08:46:12 → 2026-11-10 12:12:53**，`session_id = "plugin-bus"`：

| 事件类型 | 次数 |
|---|---:|
| `manifest.registered` | 5766 |
| `boot.ready` | 5736 |
| `bus.call` | 724 |
| `audit.permission.denied` | 189 |
| **`audit.resident.unload.denied`** | **189** |
| `audit.plugin.direct-import.denied` | 82 |
| `manifest.rejected` | 23 |
| `lifecycle.transition` | 18 |
| `boot.fail-closed` | 10 |

**189 次拒绝的对象是 `ultima.guard.policy` 与 `ultima.credential.center`（都是 L8）——没有一次落在 L9。**

所以准确的说法不是"门把手没装"，是：**门把手装了、也被拉了 189 次，但这扇门只装了 L8 和 L10 两把锁，没见过 L9。**

**同时必须分清**：这 189 次是**总线自己的运行实例**记录，**不是** `src/brain/*/registry.py` 的 `unload()` 被调用 —— 两者仍是两条独立链路。

### 更正二：生产代码**有** `unload()` 调用，不是零

⚠️ v1 说"生产零 unload、8 处全在测试"。**错。**

第一方范围实测 **14 个真实 `unload()` 调用**：生产 1 + 测试 13。

- **生产反例**：`execution/server/ultima_bus/cli.py:55` → `kernel.unload(args.module_id)`
- 四个自建 Registry 的 `unload()` 确实恰好 8 处、全在测试（这部分对），但**不能写成"全仓生产零 unload"**

而且 8 处里也不是"都验证拒绝卸载"：**5 个驻留拒绝断言 + 2 个正常卸载 + 1 个缺失键返回 False**。

### 更正三：真正的结构问题不是"三个空转"，是**两套驻留机制互不相通**

这是本次梳理最有价值的结论，v1 完全没看到：

| 系统 | 位置 | 驻留判定方式 | 谁在用 |
|---|---|---|---|
| **A. 自建 Registry** | `src/brain/{guardrails,memory,orchestration,skills}/registry.py` | 各 Registry 内的 `_resident` set；`unload()` 抛 `ResidencyViolationError` | 生产：`scanner.py` / `backend.py` / `engine.py` / `bootstrap.py` |
| **B. 插件总线** | `execution/server/ultima_bus/kernel.py` | `RESIDENT_DOMAINS = {"L8", "L10"}`（**硬编码、无 L9**）；`PermissionDenied` | 生产：只有自己的 CLI；`src/` 内**仅测试**引用 |

**两套机制都声称"拒绝卸载驻留组件"，但：**

1. `BusKernel.unload()` **不调用** `src/brain/*/registry.py` 的 `unload()`
2. `src/brain/*/registry.py` 的驻留标记，`BusKernel` **完全不知道**
3. `BusKernel` 的 `RESIDENT_DOMAINS` **漏了 L9**（而 `memory/registry.py` 头部写"与 L8 同规"）

**这才是"拼接"留下的真正代价 —— 不是名字杂乱，是两个并行系统各自实现了同一件事，且彼此 unaware。**

---

## 一、那三个 registry 到底是什么（复审 A1 成立，A2 已修正）

### 1.1 它们是"防误删的锁"

| 文件 | 头部原话 | 能力层 |
|---|---|---|
| `brain/guardrails/registry.py` | 「L8 驻留标记注册表（fail-closed，热插拔拒绝卸载）」 | **L8 行为约束** |
| `brain/memory/registry.py` | 「L9 记忆注册表（驻留标记，与 L8 同规）」 | **L9 记忆** |
| `brain/orchestration/registry.py` | 「L10 范式注册表（驻留标记，与 L8/L9 同规）」 | **L10 范式引擎** |

用大白话：将来要有一个热插拔 CLI 能在线装卸能力模块，但 L8 安全护栏、L9 记忆、L10 范式引擎**不能被卸掉**。所以给它们加**驻留标记**：谁想卸载，注册表直接拒绝，抛 `ResidencyViolationError`。

**这是一个门锁，不是一个仓库。**

### 1.2 它们功能完整且在跑（不是空转）

`unload()` 内有真实的 fail-closed 保护（`guardrails/registry.py` L104–111）：

```python
def unload(cls, key: str) -> bool:
    if key not in cls._registry:
        return False
    if key in cls._resident:
        raise ResidencyViolationError(
            f"L8 护栏 '{key}' 为驻留组件（fail-closed），禁止热卸载"
        )
    del cls._registry[key]
    return True
```

**生产调用方**（复审 A1 判定成立）：

| 注册表 | 生产调用点 |
|---|---|
| `GuardrailsRegistry` | `guardrails/scanner.py:113 is_registered` + `:114 register`（`NeMoScanner.__init__` 内） |
| `MemoryRegistry` | `memory/backend.py:88 is_registered` + `:89 register`（`Mem0Backend.__init__`）；`:273 is_resident`（`snapshot()`） |
| `OrchestrationRegistry` | `orchestration/engine.py:127 is_registered` + `:128 register`；`:321 is_resident` |
| `SkillRegistry` | `bootstrap.py:247` 导入（**实际调用在 `:249` `install_task_domain`**）；`skills/dispatch.py:44/60/69`；`skills/whitelist.py:74/93/150` |

**AST 精确统计（`src/` 范围）**：

```
is_registered    4 处
register         8 处（生产 3 + 测试 5）
is_resident     14 处
unload           8 处（全部在测试 —— 仅指这四个 Registry）
```

**v1 把行号写错一处**：`bootstrap.py:247` 是 import，真调用在 `:249`。

### 1.3 准确的表述

| 项 | 状态 |
|---|---|
| 注册链（register + 驻留标记） | ✅ 生产在跑 |
| 驻留查询（`is_resident`） | ✅ 生产在读 |
| `unload()` 拒绝逻辑 | ✅ 实现完整 |
| 四个 Registry 的 `unload()` **生产**调用 | ❌ 零（8 处全在测试） |
| 有热插拔 CLI 调 `unload()` | ⚠️ **有**，但调的是 `BusKernel.unload()`，不是这四个 Registry 的 |

**结论**：**驻留机制建成、注册在跑、拒绝逻辑测试过；但存在两套（见第零节更正三），且各管各的。**

---

## 二、拼接来源（⚠️ 原始数字已被复审判为"证据不足"，改用 AST 口径）

v1 给了一张"名字出现次数"表，Codex 判 **证据不足** —— 因为没定义大小写、子串/完整词、行数/出现次数、是否含注释。

**复审实测（`src/` 277 个 `.py`）**：

| 口径 | openjarvis | mem0 | LangGraph | NeMo | A2UI | Pipecat |
|---|---:|---:|---:|---:|---:|---:|
| v1 声称 | 139 | 103 | 80 | 46 | 22 | 11 |
| 原样大小写子串 | 125 | 63 | 45 | 46 | 22 | 8 |
| 忽略大小写子串 | 142 | 103 | 80 | 67 | 135 | 11 |
| **AST 外部导入语句数** | **69** | **6** | **3** | **3** | **0** | **0** |

**结论**：`139` 在统一口径下**复现不出来**；v1 的表混用了两种口径。**应改用 AST 口径**：真正被 import 的只有 4 个外部件 —— `openjarvis`（69 处）、`mem0`（6）、`LangGraph`（3）、`NeMo`（3）。**A2UI 与 Pipecat 在 Python 侧零 import**（A2UI 是协议/前端概念，Pipecat 已被替换）。

按能力层对应关系仍然成立（来自 `product-plan.md` §4 的 Build 决策表，不是靠计数推出来的）：

| 外部件 | 能力层 | 说明 |
|---|---|---|
| `openjarvis` | 运行时骨架 | 16 个具体 Registry + RegistryBase |
| `mem0` | L9 记忆后端 | `Mem0Backend` |
| `LangGraph` | L10 范式引擎 | `LangGraphStateMachine` |
| `NeMo` | L8 安全护栏 | `NeMoScanner` |
| A2UI | L4 组件树协议 | 概念层，Python 侧无 import |
| Pipecat | L0 语音管线 | 已被 sherpa-onnx + CV3 替代 |

---

## 三、命名混乱（⚠️ 重名实际 3 处，v1 漏了 1 处）

### 根源一：自建类与底座注册表同名（复审 B1 不成立 → 已修正）

| 自建类 | 文件 | 与底座同名? |
|---|---|---|
| `ChannelRegistry` | `brain/channel/channel_breadth.py:55` | ⚠️ **重名（v1 漏了）** |
| `MemoryRegistry` | `brain/memory/registry.py:18` | ⚠️ 重名 |
| `SkillRegistry` | `brain/skills/registry.py:39` | ⚠️ 重名 |
| `GuardrailsRegistry` | `brain/guardrails/registry.py` | 唯一 |
| `OrchestrationRegistry` | `brain/orchestration/registry.py` | 唯一 |
| `FrozenToolRegistry` | `middleware/registry.py` | 唯一 |

**交集是 3 个，不是 2 个。** `ChannelRegistry` 不是测试桩 —— `ChannelDispatcher` 会实例化它。

底座文件 `openjarvis/core/registry.py` 实际是 **17 个 ClassDef**（`RegistryBase` 基类 + 16 个具体注册表）。表述要分清："16 个具体 Registry" 或 "17 个 Registry 类定义（含基类）"。

### 根源二：三套注册体系并存，分工规则没有权威落点

现在实际有**三套**：

1. `openjarvis.core.registry.*`（底座取件通道，16 个）
2. `src/brain.*.registry.*`（自建驻留管控，4 个）
3. `execution/server/ultima_bus/registry.py`（插件总线自己的）

分工规则只写在 `bootstrap.py` L4–L9 的 docstring 里，**没有进 `docs/specs/registry.md`**，也没有命名约束，所以无法执行。

### 根源三：能力层与目录不是一一对应（⚠️ v1 这里也错了）

v1 断言"L1/L3/L5/L7 各只对应一个散文件，所以没目录不是漏归位"。

**复审 B4 判不成立。** 权威表 `docs/specs/registry.md` 原文：

| 层 | 权威落点 |
|---|---|
| L1 | `intent.py` |
| **L3** | **`queue_source.py` + `environment.py`**（两个） |
| L5 | `reporter.py` |
| **L7** | **`interaction.py` + `cli.py --loop`**，另在 `registry.md:50/51/54` 还登记了 L7 的 `interaction_orb.py`、`voice_loop.py` 与宿主侧落点 |

**所以"单文件层"这个说法本身站不住。** 而且：

> `registry.md` 只登记"实际落点"，**没有记录"之所以没目录是因为单文件"这个因果解释**。工程上"一个文件放不进目录"也不成立 —— 是否建包应由公开边界、依赖方向、扩展计划、迁移成本决定，不是由文件数机械决定。

**正确的说法是**：L 层与目录并存两套坐标、缺映射；**但"为什么没有目录"这个原因是未知的，不能断言是"单文件所致"。**

---

## 四、L0-L10 → 实际落点（权威映射，经复核）

| 层 | 能力 | 官方状态 | 权威落点 | 形态 |
|---|---|---|---|---|
| L0 | 终端四 IO | 已实现 | `brain/voice/`（17 文件）+ `brain/cli.py` + `host-shell/` | 子域 + 散文件 + C# 壳 |
| L1 | 意图理解 | 已实现（16/16） | `brain/intent.py`（155 行） | 散文件 |
| L2 | 领域知识/技能注册 | 已实现 | `brain/skills/`（4 文件，11 任务域） | 子域 |
| L3 | 执行与外部接入 | 已实现 | `brain/queue_source.py`（182 行）+ `brain/environment.py`（358 行）+ `environment_upgrade.py` | 散文件 ×3 |
| L4 | 编排与组合窗口 | 已实现 | `src/window/`（14 文件）+ `host-shell/OrbLiveRenderer.cs` + `brain/display/host_pusher.py` | 顶层目录 + 子域 |
| L5 | 表达与总结 | 已实现 | `brain/reporter.py`（111 行） | 散文件 |
| L6 | 输出呈现 | 已实现 | `brain/display/`（4 文件）+ `host-shell/` | 子域 |
| L7 | 交互循环 | 已实现（15/15） | `brain/interaction.py`（929 行）+ `cli.py --loop` + `interaction_orb.py` + `voice_loop.py` | 散文件 ×4 |
| L8 | 行为约束 | 已实现（24/24） | `brain/guardrails/`（16 文件，含 registry） | 子域 |
| L9 | 记忆 | 已实现 | `brain/memory/`（8 文件，含 registry） | 子域 |
| L10 | 范式引擎 | 已实现 | `brain/orchestration/`（6 文件，含 registry）+ `LangGraphStateMachine` | 子域 |

**只有 L2/L6/L8/L9/L10 是真正的"子域"（≥4 文件）；L1/L5 是单散文件；L3/L7 是多散文件。** 这是事实，不是"该不该建目录"的依据。

---

## 五、命名收敛方案（不变，且与 registry 去留解耦）

### 5.1 消除同名（3 处）

| 现状 | 建议 |
|---|---|
| `openjarvis.core.registry.*` | 不动（外部包） |
| `brain/memory/registry.py` 的 `MemoryRegistry` | → `MemoryResidencyRegistry` |
| `brain/skills/registry.py` 的 `SkillRegistry` | → `SkillResidencyRegistry`（或保持在 import 处强制全路径 + 注释） |
| `brain/channel/channel_breadth.py` 的 `ChannelRegistry` | → `ChannelBreadthRegistry` |
| `brain/guardrails/registry.py` 的 `GuardrailsRegistry` | → `GuardrailsResidencyRegistry` |
| `brain/orchestration/registry.py` 的 `OrchestrationRegistry` | → `OrchestrationResidencyRegistry` |

统一后缀 `*ResidencyRegistry` 后，一眼能分辨"驻留锁"而非"取件通道"。

### 5.2 把三套注册体系的分工写进权威文档

```
规则 R-REG-01：三套注册体系职责分离
  ① openjarvis.core.registry.*   = 运行时取件通道
  ② src.brain.*.ResidencyRegistry = 驻留/审计/白名单
  ③ ultima_bus.Registry           = 插件装载状态（生命周期/版本/回滚）
  三者不得同名；跨体系调用必须显式登记。
规则 R-REG-02：驻留真源唯一
  「某能力是否驻留」这个事实只能有一个权威判定点。
  当前两套并行（brain Registry 的 _resident / BusKernel 的 RESIDENT_DOMAINS），
  必须收敛为一套，否则卸载权限判定会出现矛盾结论。
规则 R-REG-03：注册表非悬空
  任何 registry.py 必须有 ≥1 个生产调用方；仅测试调用需在 registry.md 标「待接入」。
```

### 5.3 目录归位（等 Owner 定，不在本轮执行）

| 方案 | 做法 | 判断 |
|---|---|---|
| A. 按 L 层命名目录 | `l1_intent/`、`l5_report/`… | 与产品目标完全对齐，但跨层文件（`slot_adapter.py` 被 7 处用）无处放 |
| B. 保持功能域，加 L 层映射表 | 目录不变，`registry.md` 维护「层→目录」表 | 改动小、不破坏 import；两套坐标并存 |
| **C. 混合** | 多文件层保持子域；单文件层进 `brain/capabilities/` 平铺 | 避免"一个文件一个目录"，但仍边界模糊 |

**注意**：**没有证据显示 `gates/`、`tools/catalog.py` 的位置依赖 registry 去留**（复审第五节第 5 点）。所以目录方案不必阻塞在 registry 决策上。

---

## 六、registry 处置（⚠️ v1 的"接上/删除"二选一已被复审否决）

复审明确：**"接上或删除"这个强制二选一是错的前提，不能执行。**

正确的选项：

| 选项 | 做法 | 前提 |
|---|---|---|
| **① 先做职责对齐（纯文档）** | 写 `R-REG-01/02/03` 规则，明确三套体系的边界与驻留真源；不改代码 | 立刻可做 |
| **② 统一驻留真源** | 选定一套为权威（推荐 `BusKernel` 的 `RESIDENT_DOMAINS`，因为它有 CLI 和审计日志），让 `src/brain/*/registry.py` 向它登记或退化为查询视图 | 需独立工单 + 适配/回滚测试 |
| ③ 删除自建 Registry | ❌ **不建议**：它们有生产调用（`scanner`/`backend`/`engine`），删了会拆掉 `bootstrap.py` 双登记的一半 | — |

**特别提醒**：`BusKernel.RESIDENT_DOMAINS = {"L8", "L10"}` **漏了 L9**。若选 ② 统一真源，必须补 L9（记忆），否则记忆层可被热卸载，与 `memory/registry.py` "与 L8 同规"的声明矛盾。

---

## 七、下一步顺序（采纳复审建议，已调整）

复审否决了 v1 的 `2.5 → 0 → 1 → 2 → 3 → 4`，给出替代顺序：

```
① 文档/职责对齐（不改代码）
   └ 写 R-REG-01/02/03；对齐两份文档（inventory 与 plan v2 的前提冲突）
② 第 0 批：确认 0052 状态（完成/终止/重派）+ 记录 HEAD、目标文件哈希、测试基线
③ 第 1 批：搬 130 行（有条件可行）
④ 第 2 批：白名单声明式化（注册完成后显式校验，断言精确集合而非子集）
⑤ 独立的 Registry/Bus 统一工单（若 Owner 选择选项 ②）
⑥ 第 3 批：拆 interaction.py（先移 wakeword 函数消跨域边，再拆主链）
⑦ 第 4 批：可选
```

**关键变化**：
- **原"第 2.5 批"撤回**（建立错误前提上）
- **Registry/Bus 统一从"前置阻塞"降为"独立工单、可插在第 2 批之后"**
- **第 0 批成为所有代码改动的第一门**

---

## 八、方案数据修正（复审 C 组）

| 项 | v1 | 复审结论 |
|---|---|---|
| C1 可搬行数 | "4 组共 130 行 / 7.7%" | **算术✅（17+12+66+20+15=130，130/1692=7.68%）但"4 组"错——实际列了 5 组**；"只有这些可搬"是排他判断，证据不足；130 是 AST 节点跨度，不是净减行数 |
| C2 monkeypatch | "7 处 / `_MAIN` 9 次" | ⚠️ **实际 16 个 `setattr`、8 种符号、`_MAIN` 7 次**，漏了 `ask_once` |
| C2 不可搬结论 | "一律不能离开" | ⚠️ **过强**。风险真实（直搬函数后 `__globals__` 指向新模块，patch 打不中），但可用**薄包装 / 显式参数注入 / 共享状态对象**保住 patch 契约 |
| C2 行数 | `_health_payload` 56 行 / `get_jarvis` 48 行 | ⚠️ **函数本体是 34 行（1407–1440）/ 22 行（401–422）**；56/48 是"选择性相加的节点组"，不是词法闭包 |
| C3 | 近 30 天改 28 次 | ✅ 成立（Git 可复现） |
| C4 | TOOLS 11 = 9 自建 + 2 底座 | ✅ 成立 |
| C5 | `issubset` 非等值 | ✅ 成立，但**不等于"注册表化就安全"**——子集断言发现不了额外泄漏、顺序、重复、`ANSWER_TOOLS` 名单错 |
| C6 | "入度" | ⚠️ **术语错**：这是"被导入符号/alias 出现数"，不是图论入度。`interaction.py` 实为 9 个来源文件/20 个符号；`agent_server.py` 12 个来源文件/18 个符号（全测试） |

**22 个散文件完整对照（复审验证，方案值可复现）**：

| 文件 | 方案值（导入符号数） | 导入语句处数 | 独立来源文件数 |
|---|---:|---:|---:|
| interaction.py | 20 | 9 | 9 |
| agent_server.py | 18 | 18 | 12 |
| prompt_boundary.py | 15 | 3 | 3 |
| environment.py | 12 | 7 | 6 |
| agent_tools_ultima.py | 11 | 6 | 3 |
| environment_upgrade.py | 9 | 3 | 3 |
| capability.py | 8 | 2 | 2 |
| intent.py | 8 | 4 | 3 |
| bootstrap.py | 7 | 7 | 2 |
| slot_adapter.py | 7 | 7 | 7 |
| queue_source.py | 6 | 3 | 3 |
| reporter.py | 5 | 5 | 5 |
| voice_loop.py | 4 | 4 | 3 |
| weather.py | 3 | 2 | 2 |
| mainbrain_proposal.py | 3 | 3 | 2 |
| agent_client.py | 3 | 2 | 2 |
| memory_write_boundary.py | 3 | 3 | 2 |
| orchestrator.py | 2 | 2 | 1 |
| interaction_orb.py | 2 | 2 | 2 |
| interface_route.py | 1 | 1 | 1 |
| sentinel.py | 0 | 0 | 0 |
| cli.py | 0 | 0 | 0 |

---

## 九、六条机械判据（复审全部提出修正）

| # | v1 判据 | 复审结论 | 修正 |
|---|---|---|---|
| 1 | 单一入口：相对导入 `level>0` 即违规 | ❌ **不可采用** | 包内相对导入是合法的（`scanner.py` 的 `.registry` 正是）。应先定义每包公开入口与允许边，再查绕过，且要覆盖绝对导入 |
| 2 | 无反向依赖：图无环 | ⚠️ **必要但不充分** | 违反层级方向的边可能不成环。需补允许依赖矩阵 + 强连通分量 + 动态导入清单 |
| 3 | 外部读取的大写列表字面量即违规 | ❌ **不可采用** | 安全白名单可以合理地是常量；改元组就绕过正则。应查"注册完成后的解析路径 + 精确允许集合 + fail-fast" |
| 4 | 含 main 的文件生产入度必须为 0 | ⚠️ **仅本项目约定** | CLI 模块可同时提供稳定可测 API。要区分 `main()`、业务 API、进程启动关系 |
| 5 | registry 有 ≥1 外部调用方 | ⚠️ **目标合理、判据不足** | import ≠ 调用 ≠ 生产使用；装饰器/动态加载可能无直接调用。机检要区分注册/查询/卸载、生产/测试，并处理相对导入、别名、try/条件导入、动态入口 |
| 6 | 私有函数前缀族 ≥3 即多职责 | ⚠️ **只能当人工提示，不能当阻断门** | 漏类方法和公开函数；同一职责不同动词会误判；"降到 ≤2"无依据 |

---

## 十、本次自校与复审的完整记录

### 10.1 我自己跑的自校（5 FAIL / 10）

脚本：`C:\Users\Administrator\AppData\Local\Temp\selfcheck_inventory.py`、`selfcheck_inventory_v2.py`

### 10.2 Codex 复审（12 条：5 成立 / 6 不成立 / 1 证据不足）

| 编号 | 结论 | 判定 |
|---|---|---|
| A1 | 四个自建注册表都有生产调用方 | ✅ 成立（有行号小误差） |
| A2 | 生产零 unload / 8 处全在测试 | ❌ 不成立（漏了 `ultima_bus/cli.py:55`） |
| B1 | 重名只有 2 处 | ❌ 不成立（实际 3 处，漏 `ChannelRegistry`） |
| B2 | plugin-bus 零实现 | ❌ 不成立（`execution/server/ultima_bus/` 存在，但未跟踪） |
| B3 | 六个来源引用次数 | ⚠️ 证据不足（口径未定义，139 不可复现） |
| B4 | L1/L3/L5/L7 各单文件 | ❌ 不成立（L3/L7 权威表就是多文件） |
| C1 | 4 组 130 行 / 7.7% | ❌ 不成立（算术对，"4 组"错，且"只有"是排他判断） |
| C2 | 7 处 setattr / `_MAIN` 9 次 / 不可搬 | ❌ 不成立（16 处、8 符号、`_MAIN` 7 次；薄包装可保住契约） |
| C3 | 近 30 天 28 次 | ✅ 成立 |
| C4 | TOOLS 11 = 9+2 | ✅ 成立 |
| C5 | `issubset` 非等值 | ✅ 成立 |
| C6 | 22 个入度 / agent_server 全测试 | ✅ 成立（但"入度"术语错，应为导入符号数） |

### 10.3 我犯错误的三个模式（供以后自查）

1. **搜索范围窄化**：只搜 `src/`，漏了 `execution/`。**这解释了 "plugin-bus 零实现" 和 "生产零 unload" 两个错误。**
2. **局部统计冒充全局**：四个 Registry 的 `unload()` 8 处 → 写成"全仓生产零 unload"。
3. **未定义口径就给数字**：引用次数 139/103/80 混用了大小写两种口径，无法复现。

---

## 附：命名混乱完整清单（供后续收敛）

| 名字 | 出现位置 | 实际含义 | 易混淆点 |
|---|---|---|---|
| `ChannelRegistry` | `openjarvis.core.registry` | 底座通道取件 | **与自建同名** |
| `ChannelRegistry` | `brain/channel/channel_breadth.py:55` | 通道广度登记 | **与底座同名（v1 漏）** |
| `MemoryRegistry` | `openjarvis.core.registry` | 底座记忆取件 | **与自建同名** |
| `MemoryRegistry` | `brain/memory/registry.py:18` | 记忆驻留锁 | **与底座同名** |
| `SkillRegistry` | `openjarvis.core.registry` | 底座技能取件 | **与自建同名** |
| `SkillRegistry` | `brain/skills/registry.py:39` | 技能登记 + 驻留锁 | **与底座同名** |
| `Registry` | `execution/server/ultima_bus/registry.py` | 插件装载状态 | **第三套注册体系** |
| `RegistryBase` | `openjarvis.core.registry` | 底座注册基类 | 常被误算进"16 个具体 Registry" |
| `ToolRegistry` | `openjarvis.core.registry` | 底座工具取件 | 与 `FrozenToolRegistry` 易混 |
| `FrozenToolRegistry` | `middleware/registry.py` | 冻结工具白名单 | — |
| `TOOLS` / `ANSWER_TOOLS` | `agent_server.py` | LLM 白名单（11/5） | 与 `ToolRegistry` 是两个概念 |
| `ResidencyViolationError` | 4 个 registry 各定义一个 | 驻留拒绝卸载 | **4 个同名异常类，互不继承** |
| `PermissionDenied` | `ultima_bus/errors.py` | 总线侧拒绝卸载 | **与 `ResidencyViolationError` 语义重叠、不同类** |
| `_MAIN` | `agent_server.py` | 主脑配置 | 与 `main_settings()`（slot_adapter）是同一件事的两种叫法 |
| `slot_adapter.py` | 散文件，7 个来源文件引用 | 配置读取适配 | 名字看不出它读的是主脑配置 |
| `RESIDENT_DOMAINS` | `ultima_bus/kernel.py:53` | 驻留域 `{"L8","L10"}` | **漏 L9** |
