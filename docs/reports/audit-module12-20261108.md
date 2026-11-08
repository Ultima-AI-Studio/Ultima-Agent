# 模块1 / 模块2 独立审计报告

- **日期**：2026-11-08
- **审计对象**：北极星看板「模块1｜底座基础设施」「模块2｜G-TASKFLOW-001 工单契约规范」，两者均标注 100% ✅ 已冻结
- **审计人**：主脑（独立复核，不采信执行端自述与看板标注）
- **审计方法**：不看文档声称，逐条取运行时与文件实证；标注与实证不符即降级
- **对照基准**：北极星方向（贾维斯：自动优化 / 自动选方向 / 交付结果 / 人只验收）+ G-TASKFLOW-001 + 工程铁律清单 G-OSS-001/G-OWF-001

---

## 一、总体判定

| 模块 | 看板标注 | 审计结论 | 真实完成度 |
|---|---|---|---|
| 模块1 底座基础设施 | 100% ✅ 6/6 | **5 真 + 1 假**，不足 100% | **约 83%（5/6）** |
| 模块2 工单契约规范 | 100% ✅ 2/2 | 2 项均成立，但有 1 个隐性缺口 | **成立，但缺机器校验** |

**核心结论一句话**：模块1/2 的 100% 是「**人工流程完备**」，不是「**系统自动能力完备**」。人可以靠它把活干完，但系统还不能自己跑完——这与贾维斯方向存在结构性差距，且模块1 有一条标注是虚的。

---

## 二、模块1 逐条取证

### 1. 专用 venv-openjarvis Python3.13.16 环境 — ✅ 真

- 实证：`tools/venv-openjarvis/Scripts/python.exe --version` → `Python 3.13.16`
- 依赖：129 个包（aiohttp 3.14.5 / aiohttp-retry 2.9.1 / annotated-types 等）
- 结论：环境真实可用，非空壳。

### 2. Git 自动打 Tag、冻结门机制 — ⚠️ 半真（措辞夸大）

- 实证：`git tag --list` → **248 个 tag**，命名规范统一（`wo-ultimaagent-20261029-0001-closed-20261029` / `wo-ultimaagent-20261030-0003-frozen-20261030`）
- 冻结门：`scripts/freeze-approved-v01.py` / `freeze-approved-v03.py` 真实存在，v03 脚本逻辑为打 `v0.3-frozen` tag 并调用 `tasks/queue_engine/card_contract.py` 的 `check_version_gates`
- **缺口**：
  - 「**自动**」无实证——没有任何脚本会在任务完成后自动打 tag，实际是主脑/执行端**手工**打（本次 `tracker-v1.0-auto-flow` 就是我手工打的）
  - 「冻结门」是**版本级专用脚本**（针对 v0.1 / v0.3 特定基线），不是可复用的通用门；新任务想在收尾时走门，没有现成入口
- 判定：机制真实存在，但「自动」与「通用门」两点名不副实。建议改述为「Git tag 规范 + 版本级冻结脚本」。

### 3. lessons-log 复盘日志规范 — ✅ 真，且是活的

- 实证：`docs/references/lessons-log.md` → **80,897 字节 / 478 行 / 64 条标题（L01–L58+）**
- 最后修改：**2026-11-08 17:39**（今天，正在使用中）
- 末三条：L56 Codex 进程被终止不写回执 / L57 最小改动边界须证据核验 / L58 元工具看板与产品看板是两种写权
- 结论：不是摆设，是持续增长的活文档。

### 4. UltimaManager 全局工单登记接口 — ❌ 名不副实（本次审计最重要发现）

- 实证：
  - `Test-NetConnection 127.0.0.1:18766` → **False（无监听）**
  - 进程中无任何 UltimaManager 服务
  - 登记实际走 `GlobalQueueRegistrar`（`src/brain/orchestration/queue.py`），**直接读写 `H:\UltimaAI\_shared\queue\global-queue-index.md` 纯文本文件**
  - `18766` 在 UltimaAgent 代码里只被 `src/brain/agent_server.py` 引用（可选对接，非登记主路径）
  - UltimaManager 项目自身完整（src/scripts/docs/state/tests + `docs/api-v1.md`），是**代码在、服务未部署**
- 判定：看板写「 UltimaManager 全局工单登记接口 100% ✅」不成立。准确表述应为「**全局工单登记：文件级已通（写 global-queue-index.md）；UltimaManager HTTP 接口未部署**」。
- 影响：G-DISPATCH-001 规定的「派发前必须走 18766 登记接口」当前**无法执行**，0026/0027 实际全部退化为手工改文件。这条规范与运行时脱节。

### 5. 文档目录规范（docs/specs/references/reports）— ✅ 真

- 实证：specs 37 项 / references 6 项 / reports 201 项 / tracker 6 项 / plans 112 项
- 结论：目录体系真实且使用度高（201 份报告是硬证据）。

### 6. KWS 唤醒参数基线文档 — ✅ 真

- 实证：`docs/specs/kws-wakeup-params-baseline.md` → 28,617 字节 / 110 行
- 首行自称「权威单一来源」，符合用户既定要求
- 结论：真实存在且分量足够。

---

## 三、模块2 逐条取证

### 1. 根工单、子工单 Schema、验收/冻结规则定稿 — ✅ 成立，但有隐性缺口

证据链（四层都在）：

| 载体 | 内容 | 体积 |
|---|---|---|
| `docs/specs/codex-task-queue-spec.md` v1.3 | 任务卡 10 字段表（task_id/goal/acceptance/dependsOn/fileDomain/priority/reasoningEffort/category+skill/receipt/retryCount） | 14,379 B |
| `docs/specs/engineering-laws.md` v1.0 | G-OWF-001 三段式 + DoR 六项 + G-OSS-001 开源优先 | 5,256 B |
| `_shared/paradigms/Ultima-工程铁律清单.md` | 唯一权威源（项目内为镜像） | 5,256 B |
| `_shared/templates/工单模板.md` | 任务卡模板 | 4,337 B |
| `src/brain/orchestration/queue.py` `TaskRecord` | 代码化子工单结构 12 字段（task_id/title/phase/priority/permissions/parent_task/created_at/updated_at/replan_count/history/receipt/project_key） | — |
| `docs/specs/registry.md` v2.9 | 11 个技能的六字段（职责边界/适用任务/产出标准/验收口径等） | 22,971 B |

- **缺口（P2）**：**没有独立 JSON Schema 文件**，也没有 `*.schema.json`。工单卡本体是 markdown，字段完整性靠人对照表格检查；`TaskRecord` 只在代码内部流转，**不校验外部工单卡**。所谓「Schema 定稿」= 文档定稿 + 代码内结构定稿，**不是可机校验的契约**。
- 判定：定稿成立（有权威源、有模板、有字段表、有代码结构），但「防呆」只到文档级，没到机器级。

### 2. 需求→拆解→执行→审计→归档 标准流程 — ✅ 真

- 实证：`queue.py` 第 31 行 `PHASES = ("立项", "排队", "派发", "执行", "自检", "审计", "回执")` —— **七环状态机硬编码**
- `SevenRingCheck` 复用 `ParadigmGate`（L10），`pre_dispatch` 前置检查未完成即拒绝派发
- `TaskQueue.advance` 强制按阶段推进；`check_wip` 有 WIP 上限控制
- 配套规范：`docs/specs/codex-task-queue-spec.md`（目录/事件/归档纪律）+ `docs/specs/sequencing.md`（运行时时序）
- 结论：流程不是纸面流程，是代码里跑的状态机。

---

## 四、对照北极星方向的结构性差距

北极星 = 贾维斯：**自动优化、自动选方向、交付结果，用户只验收**。

模块1/2 现在支撑的是「**人推着系统走**」，具体表现：

| 环节 | 现状 | 贾维斯要求 | 差距 |
|---|---|---|---|
| 打 tag | 手工 `git tag` | 收尾自动冻结 | ⚠️ |
| 全局登记 | 手工改 md 文件 | 系统自动登记 | ⚠️ |
| 看板回写 | 主脑手工改 HTML | 系统自动更新 | ⚠️（本轮已暴露：我自己改错过） |
| 工单派发 | 手工写载荷 + 起 codex | 队列自动派发 | ⚠️（0026/0027 都是人工搬） |
| 审计 | 人工复跑 + 手写结论 | 机制化独立复核 | ⚠️（0027 正在补） |

**这不是说模块1/2 做得差**——底座该有的规范和目录都真做出来了，是可用的。问题是它们的 **100% 属于"人工可用"，不是"自动可用"**。按贾维斯标准，模块1 最多算 83%，且缺的正是"自动化"这一环。

---

## 五、审计建议（按优先级）

### P0｜修正虚标（必须做）
模块1 第 4 条从 `100% ✅` 降级为「**文件登记已通 / UltimaManager HTTP 接口未部署**」，模块1 回落 **5/6 = 83%**。同时把 G-DISPATCH-001 的「必须走 18766」改为「**18766 可用时走接口，不可用时落文件并登记口径**」，否则规范永久无法执行。

### P1｜补机器校验
新增 `docs/specs/work-order.schema.json` + 一个 `validate_work_order.py`，把工单卡 10 个必填字段做成可执行校验，接进派发前 DoR 检查。这样「Schema 定稿」才从文档级升到机器级。

### P2｜冻结门通用化
把 `freeze-approved-v01/v03.py` 抽成通用 `freeze_work_order.py`（读工单 → 校验验收全绿 → 打 tag → 推远端），让"打 tag + 冻结"变成一条命令，而不是每次手写。

### P3｜方向对齐
上述三条做完，模块1/2 才真正对齐「自动」方向；在此之前，不要把模块2 的"工单契约"当作已完成自动化能力对外表述。

---

## 六、取证命令附录（可复现）

```powershell
# 环境
& "H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe" --version
& "H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe" -m pip list --format=columns

# 18766 登记接口
(Test-NetConnection -ComputerName 127.0.0.1 -Port 18766).TcpTestSucceeded

# tag 与冻结脚本
git -C "H:\UltimaAI\UltimaAgent" tag --list | Measure-Object -Line
Get-ChildItem "H:\UltimaAI\UltimaAgent\scripts" | Where-Object Name -match "freeze"

# 七环状态机
Select-String -Path "H:\UltimaAI\UltimaAgent\src\brain\orchestration\queue.py" -Pattern "PHASES ="

# 工单契约四件套
Get-Item "H:\UltimaAI\UltimaAgent\docs\specs\codex-task-queue-spec.md",
        "H:\UltimaAI\UltimaAgent\docs\specs\engineering-laws.md",
        "H:\UltimaAI\_shared\paradigms\Ultima-工程铁律清单.md",
        "H:\UltimaAI\_shared\templates\工单模板.md"
```
