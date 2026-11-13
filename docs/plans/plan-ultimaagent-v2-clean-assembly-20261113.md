# UltimaAgent v2 干净拼装方案（Clean Assembly Plan）

> 版本：v0.1 草案 ｜ 起草：2026-11-13（0054 执行期间并行起草，只读未动在途 run）
> 性质：A 级变更方案，待 Owner 拍板后拆工单
> 前置输入：0052/0053 已冻结；0054（watchdog 内化+零计划任务+应用内面板）验收冻结后本方案生效
> 决策依据：docs/decisions/pd-20261113-0054-watchdog内化与零计划任务裁决.md、docs/research/naming-audit-20261113.md（含 orb 六套重复盘点）

---

## 一、北极星重述（唯一方向判据）

**产品北极星 = UltimaAgent 本体。** 一切模块、能力、界面以"让 UltimaAgent 自身成为理想智能代理"为唯一方向；产品对外统一只称 UltimaAgent，不再冠以贾维斯之名。开源项目（白龙马/大飞鱼/LobeHub 等）只作接线方式参考，不改北极星。

UltimaAgent 的五条行为学原则（源自原贾维斯调研结论，2026-11-13 起命名收敛为 UltimaAgent）：

| 原则 | 含义 | v2 落点 |
|---|---|---|
| 感官分工（通道分工） | 语音通道与显示通道各司其职，不混通道 | Senses.Voice（语音进出）、Surface（输出呈现）分模块 |
| 理解先于行动 | 先理解意图再执行，不条件反射 | Core 的意图→路由→编排固定顺序 |
| 复述确认 | 关键动作执行前向用户复述确认 | Core 的 confirm 协议（语音+面板双通道） |
| 记忆分层 | 工作记忆/长期记忆/温度分层 | Memory 模块三层结构 |
| 不打扰与反馈闭环 | 平时隐身，有事说话，说完即静 | Shell 常驻（托盘）+ 四角壳锚位按需显隐（常驻仅顶/左上/右上） |

语音状态机（冻结基线，v2 原样继承）：`warming→ready→capturing→processing→speaking/acknowledging/stopped/error`；唤醒词「幂幂」、threshold 0.25、warm_progress 0/25/50/75/100。参数唯一权威源 `docs/specs/kws-wakeup-params-baseline.md`，v2 搬运不改。

## 二、v2 模块架构（职责命名，一步到位）

> **架构组织逻辑声明（Owner 纠偏 2026-11-13）**：本产品架构按**能力分层**组织与拓展——基础能力（L0-L10 能力清单，权威源 `docs/plans/capability-list.md` + `docs/specs/registry.md` 注册表）→ 外脑（DeepSeek/Codex/本地 8B 主脑，执行端可替换）→ 顾问（豆包 V1 后转型验收/咨询/方向建议）→ Skill（技能注册表，给智能体消费）→ 插件（开源拼装接线），**不是**按"脑/耳/身/脸"身体器官构建。下方八模块只是**基础能力的本体承载**（v2 冻结裁决），模块名一律用职责命名；"感官分工"等词仅作行为原则表述，不构成架构轴。外脑/顾问/Skill/插件均为本体之上的能力扩展层，随 v2 后演进逐层建设，不在本拼装工单内搬运。

新仓目录（拟定名，全部去迭代代号/上游名）：

```
H:\UltimaAI\UltimaAgentNext\
├── src\
│   ├── Core\            编排与裁决：意图理解、编排、记忆写入边界、复述确认协议
│   ├── Senses\Voice\    语音进出：KWS 唤醒、VAD、TTS(CV3)、语音会话循环
│   ├── Shell\           常驻托管：HostShell(WinUI3)、ProcessHost/GuardianService、Job 托管、自启
│   ├── Surface\         输出呈现：四角壳 HUD（8 锚点，唯一显示形态）、任务管理器面板
│   ├── Memory\          记忆：工作/长期/温度分层
│   ├── Middleware\      调度：路由、委派、沙箱、任务窗口、票据
│   ├── Update\          更新：发布通道、manifest 签名
│   └── Lifecycle\       安装包：Setup、shipped-tasks、升级链
├── tools\               venv（规范名）、验收脚本、测试夹具
├── devtools\            开发兜底：watchdog 手动脚本、旧 orb 测试样式（降级归档）
├── config\               host-tasks.json 等
├── installer\
├── 最小文档面：仅安装包/运行必需（LICENSE、README 一页级）——零开发文档
└── tasks\queue\         队列引擎（从冻结仓原样搬运）
```

## 三、模块 × 能力/工具/技能三层表

每模块三层定义（能力=用户可感知功能；工具=模块内可调用进程/脚本/API；技能=可组合任务能力）：

### 1. Core（编排与裁决）
- **能力**：意图理解、任务编排、复述确认、记忆写入裁决
- **工具**：orchestrator、intent、interface_route、queue_source、capability registry
- **技能**：任务规划、主动追问、结果汇报
- **搬运源**：`src/brain/*`（剔除 weather.py 等杂物归 devtools；`openjarvis.*` import 全部吸收为 `UltimaAgentNext.Core.*` 或适配层）

### 2. Senses.Voice（语音进出）
- **能力**：唤醒、听写、对话、TTS 播报
- **工具**：kws_backend、turn_worker、live_core、apm_dsp、CV3 推理
- **技能**：语音会话、尾音处理、音色切换
- **搬运源**：`src/voice-next/*`（KWS/CV3 参数冻结基线，搬运后逐项复测，禁顺手优化）

### 3. Shell（常驻托管）
- **能力**：常驻托管、守护自愈（agent-server）、开机自启、子进程零弹窗
- **工具**：GuardianService（20s/3次/300s）、HostTaskRegistry、JobObjectManager、ChildProcessSupervisor、ReadinessProbe、AutostartEntry（启动文件夹 .lnk）
- **技能**：任务托管、崩溃回收（Job 归属）
- **搬运源**：0054 冻结产物（这是本方案的直接输入）+ 0052 ProcessHost 三件套

### 4. Surface（输出呈现）
- **能力**：四角壳 HUD 展示（8 锚点）、应用内任务管理器面板
- **工具**：UltimaAgent.Hud 原生壳（2026-10-29 验收通过）、hud-live-four-corner 设计基线（--hd-* token、锚位宽度锁定 clamp(280px,24vw,352px)、无边框气泡形态、置顶才显边框）、TaskManagerRenderer、taskmanager.html、WebView2 双向消息
- **技能**：状态反馈、任务可视
- **形态裁决（Owner 拍板 2026-11-13）**：**四角壳为唯一显示形态，悬浮球方案退场**。全部 orb 渲染器（OrbLiveRenderer/OrbBallRenderer/ComboWindowRenderer 及 ULTIMA_HOST_ORB_TEST/LIVE/COMBO 测试链）**均不进入新仓产品形态**，只降级 devtools 测试夹具归档；OrbHost/OrbNative 死工程不搬（留冻结仓归档）；python 侧 `src/window/*.py` 不搬（活链路未用）。0054 在途 T6 的 orb 视觉增量属 v1 收口证据链，照常完成工单验收，但不改变 v2 Surface 裁决。

### 5. Memory（记忆与自学习）
- **能力**：工作记忆、长期记忆、温度分层
- **工具**：writer、poison_guard、backend 适配
- **技能**：上下文注入、记忆检索

### 6. Middleware（多端调度）
- **能力**：多执行端路由、任务窗口、沙箱隔离
- **工具**：router、delegation、sandbox、task_window、ticket
- **搬运源**：`src/middleware/*`

### 7. Update / Lifecycle（更新与交付）
- **能力**：远程更新、签名校验、安装/升级/卸载
- **工具**：manifest、publisher、Setup 链、check-shipped-tasks
- **搬运源**：`src/update/*`、`installer/*`、`dist/release-assets.json` 模板

### 8. Tools / Devtools（工程底座）
- venv 规范重命名（如 `tools/venv-ultimaagent`，指向解释器不变）；验收脚本（test-jobkill、check-shipped-tasks、test-phase3-*）；队列引擎 `tasks/queue_engine/*` + 渲染器

## 四、搬运白名单总则

1. **只搬冻结产物**：每项搬运必须能指出冻结来源（tag 或冻结 commit），逐项登记映射表（源→目的），搬运后新仓第一件事是全量复验。
2. **明确不带走的**：jarvis-work 90 份过程文档（冻结仓留档）；**全部 orb 渲染线（悬浮球退场裁决）**；OrbHost/OrbNative 死工程；`src/window/*.py` python 渲染线；gorch 系脚本；`_readme_local_backup.md`；config/_backup 全部。
3. **改名一步到位**：`UltimaAgentNext.*` 命名空间、无 voice-next、无 openjarvis import、无迭代代号分支（新仓从 `main` 起步）。
4. **零开发文档（Owner 拍板 2026-11-13）**：新仓是未来干净的**交付工程**，最终形态=打包封装成安装包，**不融入任何开发内容**——00-19 工程文档体系、方案文档、过程文档、标准文档一律不进新仓（全部留老仓冻结归档，引用靠 git tag 锚定）；新仓文档面仅保留安装包/运行必需的最小集（LICENSE、README 一页级）。冻结文档（v2 方案、能力清单、KWS 基线、四角壳设计基线）作为**搬运工单的输入依据**在老仓被引用，不作为产物复制进新仓。
5. **非目标**：四角壳 8 锚点框架不在 v2 拼装工单内新建实现（Hud 原生壳与布局定稿为既有冻结基线，随 P2V-03 搬运对接，新锚位功能走后续独立工单）；不动 KWS/CV3 冻结参数；不改 8756 端口与 20/3/300 守护语义；不建 UltimaManager 依赖。

## 五、执行阶段（拆单草案）

| 工单 | 内容 | Gate |
|---|---|---|
| P2V-00 立项 | 新仓初始化、队列引擎搬运、venv 规范名（零开发文档：工程只留安装/运行必需最小文档面） | 队列渲染器自检过 |
| P2V-01 搬 Core+Memory+Middleware | import 吸收（openjarvis→Core） | AST 3/3 + 单测绿 + Windows-only 依赖扫描 0 处 |
| P2V-02 搬 Senses.Voice | KWS/CV3 冻结基线复测 | 唤醒/对话链路实测一致 + Windows-only 依赖扫描 0 处 |
| P2V-03 搬 Shell+Surface | 0054 产物 + 四角壳对接（orb 渲染线不搬）+ 宿主契约接口落文档 | build 0/0 + Guardian 事件 + 零计划任务 + 零弹窗 + 四角壳锚位渲染自检 |
| P2V-04 搬 Update+Lifecycle | 安装包链重建 | Setup 全流程验收（复用 0052/0054 判据） |
| P2V-05 总验收 | 全链路贯通 + 北极星清单更新 + 冻结 tag | 端到端冒烟 + 独立审计 |

老仓处置：P2V-05 验收后打 `ultimaagent-v1-final-frozen-*` tag，老仓转只读归档区（M7），此后现行区唯一 = 新仓（M6）。

## 六、配置内化与安装包设置（v2 最新思路固化）

### 6.1 配置内化原则：config/ 是唯一配置面，环境变量降为测试注入

v2 的配置治理四条铁律：

1. **单一配置面**：`config/` 是运行时唯一权威配置目录，全部 schema 版本化（`ultimaagent-*/v1` 风格），应用启动时集中加载，禁止散落硬编码。现行六件配置原样继承并归位：
   - `host-tasks.json`（应用内任务注册表：agent-server guardian 20/3/300 + voice-launcher manual）→ Shell 模块权威
   - `interface-routing.json`（L0>L1>L2>L3 分级路由，schema v2）→ Core 权威
   - `voice-profile.json`、`asr-normalize.json` → Senses.Voice 权威
   - `interface-seeds.json`、`.env` → 迁移时逐项裁定归属，`.env` 只留开发机本地项
2. **环境变量降级为测试注入**：现行 `ULTIMA_*` 12 个变量（`ULTIMA_HOST_LIVE/ORB_TEST/COMBO/WARM_RING/COMBO_COMMAND_FILE/AUTOSTART_KIND/HOST_EXE/HOST_TASK_STATE_FILE/HOST_STATUS_FILE/USE_PROCESS_HOST/PROJECT_ROOT/HOST_AUTO_EXIT_MS/HOST_CRASH_SELF`）在 v2 里**只作验收脚本与测试夹具的注入通道，不是产品配置**——产品行为一律走 config/；测试开关集中登记在 devtools/README 一张表，杜绝"环境变量驱动产品形态"造成的混版（0054 期间 orb 旧样式被频繁唤起的根因）。
3. **运行态与配置分离**：`data/host/host-tasks-state.json`、`data/logs/guardian-events.jsonl` 等运行态只落在 data/（gitignored），配置永远可重放、运行态永远可丢弃。
4. **config/_backup 历史堆不迁移**：现行目录下 15+ 个 `_backup` 快照属过程产物，v2 用 git 历史承担回溯，不再生成文件级备份堆积（M6 违例源头之一）。

### 6.2 安装包设置（继承 0054 裁决，全部冻结进 v2）

| 项 | v2 设置 | 依据 |
|---|---|---|
| 计划任务 | **零**：`installer/shipped-tasks.json`（shipped_tasks=[]）是唯一权威声明，Phase 4 的 .iss 只读不写 | pd-20261113-0054 裁决 |
| 开机自启 | 启动文件夹 `.lnk`（进程内晚绑定 COM 创建，零外部进程、零弹窗），`ULTIMA_AUTOSTART_KIND` 仅测试旁路 | 0054 T8 |
| 守护自愈 | GuardianService 内化（20s/3 次/300s，agent-server 自动重启；应用崩溃不自愈已由 Owner 接受） | 0054 T2 |
| 子进程零窗 | pythonw + UseShellExecute=false + CreateNoWindow + 标准流重定向排空（0054 实证修复） | 0054 深层修复 |
| 升级/卸载 | Update 模块 manifest 签名链；卸载清理 = 零计划任务残留（天然满足，因从未创建） | 0052 生命周期线 |
| 开发机兜底 | devtools/watchdog.py 手动脚本 + devtools/README | 0054 |
| 安装包命名 | `UltimaAgent-Setup-*` 沿用，release-assets.json 模板继承（签名 scope 注明 temporary-test-only 直至真签名密钥启用） | dist 现行 |

### 6.3 搬运时的路径重写

host-tasks.json 中 `tools/venv-openjarvis/...`、`src/voice-next/launch.py` 等路径在 v2 搬运时随白名单一次性重写为新仓规范路径（venv 规范名 + `src/Senses/Voice/launch.py`），并跑 Guardian 探活复验——配置文件不改就搬运等于把旧命名走私进新仓。

## 七、终端演进策略（Owner 方向拍板 2026-11-13：Windows → Linux → 自研 AR 眼镜系统）

**产品最终形态 = AR 眼镜上使用的智能代理**。v2 干净拼装不只是清理旧仓，更是为多终端演进铺路：当前 Windows 是第一站，下一版适配 Linux，未来做自研 AR 眼镜系统。据此立三条架构铁律：

1. **模块分层按"终端无关/终端相关"切分**（本方案八模块架构天然满足，搬运时以依赖检查守住）：
   - **终端无关层（跨终端常量）**：Core、Senses.Voice、Memory、Middleware、Update——五模块搬运与后续演进**禁止引入 Windows-only 依赖**（无 win32api/pywin32/WMI 依赖进这些层；开发验收工具例外，归 devtools）。KWS/CV3 语音链路本身终端无关，是 AR 眼镜语音通道的直接复用层。
   - **终端相关层（每终端一套适配）**：Shell（常驻托管/自愈/自启）与 Surface（显示形态）——Windows 版 = HostShell(WinUI3)+四角壳锚位；Linux 版另立 Shell 适配（systemd/dbus 方向，后续专项方案）；AR 眼镜版 = 自研系统内嵌。Shell 与 Surface 之间约定**宿主契约接口**（托管生命周期/事件/渲染挂点），跨终端只换实现不换契约。
2. **显示形态跨终端唯一常量 = 四角壳 8 锚点范式**：hud-layout-zone-plan v0.2 的 AR HUD 显示哲学（边缘常驻×按需显隐×中央零遮挡、锚位职责锁定、宽度锁定、无边框气泡、置顶才显边框）本就为 AR 前瞻设计——Windows 上是屏幕四角，AR 上贴视野边缘，范式不变只换投射载体。AR 安全基线（透明度三档 0.14/0.55/0.85、中央永远透传）沿用既有定稿。
3. **演进次序与不可逆纪律**：Windows v2（P2V-00~05）→ Linux 适配版（独立方案+工单，不与拼装混做）→ AR 眼镜系统（远期，自研内核前先在 Windows/Linux 上把四角壳+语音链路打磨成熟）。每一步迁移都走「冻结仓+白名单搬运」范式，不复用被冻结的旧实现直接混写。

**对 v2 拼装的直接影响**：P2V-01/02 搬运时增加一项 Gate——终端无关五模块 import 依赖扫描（win32/pywin32/WMI/Windows 路径硬编码 = 0 处）；Shell 与 Surface 间宿主契约接口在 P2V-03 落文档。AR 适配本身不在本方案范围（非目标），本节只锁方向与分层纪律。

## 八、风险与代价（如实）

- 安装包生命周期线要在新壳重走一遍验收（判据全冻结可复用，主要是执行时间）
- venv 改名涉及用户侧路径偏好与多份冻结文档引用，需同步公告一次
- 老仓在途的其他工单（若有）需先收口或明确弃单，冻结时点要对齐
- 环境变量降级为测试注入后，依赖 ULTIMA_* 的历史验收脚本需同步改写为 config/ 或 devtools 夹具通道（P2V-03/04 Gate 内含此项）

---

> Owner 拍板记录（2026-11-13，本节为最终裁决）：① 新仓目录 = `H:\UltimaAI\UltimaAgentNext`（无版本后缀，新旧靠 final-frozen tag 区分）；② venv 规范名 = `tools/venv-ultimaagent`（搬运时全量引用清扫 + 渲染器自检作 Gate）；③ 老仓冻结时点 = P2V-05 总验收后打 `ultimaagent-v1-final-frozen-*` tag 转只读；④ 模块架构 = 八模块原方案（Shell/Surface 分离、Update/Lifecycle 分开）；⑤ Surface 显示形态 = 四角壳 HUD 为唯一形态，悬浮球方案退场（全部 orb 渲染线不进新仓产品形态，0054 在途 T6 照常完成 v1 收口）；⑥ 新仓定位 = 干净交付工程，零开发文档（00-19 文档体系/方案/过程/标准文档一律留老仓冻结归档，新仓仅留安装/运行必需最小文档面，最终形态=打包封装成安装包）。六项已定，方案视为冻结，可拆 P2V-00 工单。
