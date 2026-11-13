# UltimaAgent Next 从零重做总纲方案（N 系列）

> 版本：v1.0 ｜ 状态：方案定稿（待 0054 收口冻结后开 N-00）｜ Owner 拍板日期：2026-11-13
> 权威源：本文件（Next 重做唯一事实源）｜ **先行规则**：`docs/specs/next-双域分离与开工设置规范.md`（工程域/客户端域分离 + 每步设置表，开工前必读，优先级高于本文件细节）｜ 关联：`docs/plans/plan-ultimaagent-v2-clean-assembly-20261113.md`（被本方案取代的旧拼装路线，留档）、`docs/tracker/北极星架构树.html`（架构呈现）、`docs/decisions/pd-20261113-0054-watchdog内化与零计划任务裁决.md`
> 适用方法论：`ultima-工程方法论`（工单三段式 / DoD 分层 / 冻结门 / M1-M8 / 审批矩阵）+ G-PLAN-001（方案随工单落盘）+ G-TASKFLOW-001（登记→计划评审→执行→独立审计→有界修复→验收→冻结）

---

## 一、裁决与背景

**Owner 判定（2026-11-13）**：v1、v2 两版的结果都是「乱七八糟、七零八落」，不再在旧仓上做增量修补；开启 **Next 版**——把每一个模块重新整理、逐块填内容、所有工单按顺序排队，一路推进到能打出最终形态（安装包）。

**量化依据（旧仓实测，2026-11-13 12:20）**：

| 维度 | 实测 | 问题 |
|---|---|---|
| 工作区未提交改动 | 478 条（未跟踪 docs 264 / tasks 101 / scripts 20 / src 15 / data 13） | 代码与文档从未一次性收敛 |
| `src` 目录 | 9 个：`brain` / `host` / `host-shell` / `memory` / `middleware` / `ui` / `update` / `voice-next` / `window` | 命名口径不一，`host` 与 `host-shell` 重叠、`ui` 与 `window` 并存、`voice-next` 带迭代代号 |
| `docs` 文件数 | 23 792 | 文档沉积，权威源被稀释 |
| tracked 文件数 | 36 461 | 交付面被历史面淹没 |
| 队列卡 | 大量历史卡命名含过程词（kws/cv3/audit/hud…） | 无法一眼看出「产品还剩什么」 |

**两条并行裁决**：

1. **Next 取径 = 全部从零重写**。旧仓代码零搬运、零复制、零 import；旧仓此后只作为「规格与实测结论的来源文档」存在。
2. **0054 先跑完收口**（run `wo-ultimaagent-20261113-0054-20261113T023840201172Z`，现处 T9 最后收口），出总验收后打 v1 冻结 tag，老仓转只读；Next 在其后启动。**0054 不在本方案内改范围**。

---

## 二、「从零重写」的边界（唯一允许带入的是规格，不是代码）

从零重写 ≠ 从零发明。以下内容是**已验证的规格值与结论**，允许写入 Next 的规格文档并据以实现；它们不是代码资产。

| 允许带入（规格/结论） | 来源 | 用途 |
|---|---|---|
| 唤醒词「幂幂」、threshold 0.25、七态状态机（warming→ready→capturing→processing→speaking/acknowledging/stopped/error）、warm_progress 0/25/50/75/100 | `docs/specs/kws-wakeup-params-baseline.md`（KWS 唯一权威基线） | Voice 实现时的参数表 |
| CV3 音色冻结参数 | 同上 + voice-profile 规格 | TTS 播报 |
| Guardian 20s 探活 / 3 次失败 / 300s 冷却 | 0054 ADR | Shell 守护自愈 |
| 子进程零窗四要素：pythonw + UseShellExecute=false + CreateNoWindow + 标准流重定向排空 | 0054 ADR（T2 实证） | Shell 子进程托管 |
| 时序基线：window 541ms / first frame 1530ms / voice-ready 15 651ms / 残留 0 | 0054 T5 基线 | 验收判据阈值 |
| 四角壳 8 锚点职责与宽度 lock `clamp(280px,24vw,352px)` | `docs/specs/hud-layout-zone-plan-20261031.md` v0.2 | Surface 唯一显示形态 |
| 零计划任务：`shipped_tasks=[]` 唯一权威声明、`.iss` 只读不写 | 0054 ADR | Lifecycle |
| Job 归属判据：宿主强杀子进程树 3 秒内同步消失 | 0052/0054 | Shell 验收 |

**硬禁止（越界即打回）**：

- 禁止把旧仓任何 `.py/.cs/.xaml/.ps1` 文件复制进 Next；
- 禁止 `import openjarvis.*` / 旧包名 / 旧模块名沿用；
- 禁止「参考旧实现顺手粘贴」——每个文件必须是按规格重写的新实现；
- 禁止旧仓 `data/`、`models/` 产物原样搬入（模型文件按规格重新获取）。

---

## 三、架构定稿

**组织逻辑**：能力分类模块化。第一层五大模块，其中两个包含原子模块，合计八原子模块（工程口径不变）。

```
UltimaAgent 本体
├─ 基础能力（本体承载）──────── Core · Senses.Voice · Shell · Surface · Memory · Middleware
├─ 外部能力（外脑与顾问）────── 外脑执行端体系 · 顾问（裁决与咨询）
├─ Skill（技能体系）────────── 技能注册表 · 防重复开发（M1）
├─ 插件（开源拼装）────────── 调度组件 · 组件树基底 · 语音管线
└─ 交付（更新与安装）────────── Update（远程更新）· Lifecycle（安装与交付）
```

**分层铁律（终端演进）**：

- 终端无关层 = Core / Senses.Voice / Memory / Middleware / Update → 禁 Windows-only 依赖（每轮 Gate 含依赖扫描 0 处）；
- 终端相关层 = Shell / Surface → 宿主契约接口「只换实现不换契约」，Linux 版（systemd/dbus）与 AR 版各自实现；
- 显示常量 = 四角壳 8 锚点范式（跨终端唯一）；悬浮球形态已退场，不进 Next。

---

## 四、模块内容填充表（逐模块定「填什么」）

> 每个模块四件套：**职责**（一句话边界）/ **对外契约**（别的模块只能通过这些接口用它）/ **内部组成**（Tools，新代码一律模块化封装为 Tools，不平铺）/ **验收判据**（Gate 可机检）。

### 4.1 Core（编排与裁决）
- **职责**：把自然语言变成结构化意图，编排多步任务，关键动作复述确认，裁决记忆是否写入。
- **对外契约**：`Intent`（结构化意图对象）、`Plan`（多步任务计划）、`confirm(prompt)→bool`、`memory_write_request→裁决结果`；对内不暴露 LLM 供应商细节。
- **内部组成**：`intent_router`（L0>L1>L2>L3 分级路由）、`planner`、`confirm_gate`、`memory_boundary`、`capability_registry`
- **规格约束**：意图→路由→编排顺序固定，不条件反射；复述确认双通道（语音 + 面板）；写入边界由 Core 裁决，Memory 只执行
- **验收判据**：意图分类黄金集 ≥50 例准确率达标；计划可重入（同输入同计划）；越界写入被拒并留痕；单测绿

### 4.2 Senses.Voice（语音进出）
- **职责**：唤醒、听写、对话、TTS 播报四件事，且只有这四件。
- **对外契约**：`WakeEvent`、`Transcript(text, confidence)`、`Speak(text, voice_id)`、`VoiceState`（七态）；上层只订阅事件，不直接碰音频设备
- **内部组成**：`kws_backend`、`vad_tail`、`asr_pipeline`、`tts_cv3`、`session_loop`、`apm_dsp`
- **规格约束**：KWS 参数严格按 `docs/specs/kws-wakeup-params-baseline.md`；参数冻结，不得顺手优化；尾音处理按 VAD 规格
- **验收判据**：唤醒率/误唤醒在基线区间；warm_progress 五档可视化；TTS 音色一致性抽检；语音链路零 Windows-only 依赖

### 4.3 Shell（常驻托管）
- **职责**：进程活着的责任人——常驻、守护、自启、子进程托管、零弹窗。
- **对外契约**：`HostTask`（可托管任务声明）、`Restart(task_id)`、`Status`（含重启次数/冷却剩余）；Surface 通过此契约读状态
- **内部组成**：`host_shell`（WinUI3 原生壳）、`guardian`（20s/3次/300s）、`job_manager`、`child_supervisor`（零窗四要素）、`readiness_probe`、`autostart_entry`
- **规格约束**：**零计划任务**（不自建任何 schtasks）；自启只走启动文件夹 `.lnk`；全部子进程无窗
- **验收判据**：强杀子进程树 3s 内消失；Guardian 故障恢复 ≤ 冷却窗口；计划任务查询 0 条；启动截图无控制台窗

### 4.4 Surface（输出呈现）
- **职责**：把状态与结果呈现给人，且只在四角壳里呈现。
- **对外契约**：`AnchorUpdate(anchor_id, payload)`、`TranscriptStream`、`TaskPanel(state)`；只读 Core/Shell 状态，不反向驱动
- **内部组成**：`hud_shell`（四角壳原生壳）、`anchor_renderer`（8 锚点）、`task_manager_panel`、`webview_bridge`
- **规格约束**：8 锚点职责锁定（顶=时钟 / 左上=系统状态 / 右上=单功能 / 左下=任务队列 / 右下=即时消息 / 左中=Agent 反馈 / 右中=主动唤出 / 底=交流转写）；常驻仅顶/左上/右上；宽度 lock 同四角壳基线；中央零遮挡
- **验收判据**：8 锚点渲染自检逐项过；窄屏堆叠规则生效；150% DPI 无字段被挤出；任务管理器面板状态/重启/停用三键可用

### 4.5 Memory（记忆与自学习）
- **职责**：只负责存与取，写不写由 Core 裁决。
- **对外契约**：`Recall(query, scope)`、`Write(entry)`（仅接受 Core 已裁决的请求）、`Forget(entry_id)`
- **内部组成**：`writer`、`poison_guard`、`store_backend`（适配层，换存储不改调用方）、`temperature_tier`（工作/长期/温度三层）
- **规格约束**：三层记忆职责不混；检索结果带来源与置信度
- **验收判据**：越权写入一律拒绝；检索命中率基线；存储后端可替换（同一套契约两套后端跑通）

### 4.6 Middleware（多端调度）
- **职责**：任务往哪跑、跑在哪个窗口、出问题怎么隔离。
- **对外契约**：`Route(task)→executor`、`TaskWindow`、`Sandbox`、`Ticket`
- **内部组成**：`router`、`delegation`、`sandbox`、`task_window`、`ticket`
- **规格约束**：执行端可替换（换实现不改调用方）；一次一主；票据可追溯
- **验收判据**：断掉某执行端后降级路径生效；票据全链路可追；沙箱越界拦截

### 4.7 Update（远程更新）
- **职责**：新版本怎么安全到用户机器上。
- **对外契约**：`CheckUpdate()`、`ApplyUpdate(manifest)`、签名校验结果
- **内部组成**：`manifest`、`publisher`、`signature_verify`
- **规格约束**：签名密钥启用前 scope 标 `temporary-test-only`；回滚路径必须存在
- **验收判据**：篡改包被拒；回滚成功；更新后自检过

### 4.8 Lifecycle（安装与交付）
- **职责**：装得上、升得动、卸得干净。
- **对外契约**：安装/升级/卸载三链 + `shipped_tasks=[]` 声明
- **内部组成**：`setup_chain`、`check_shipped_tasks`、`release_assets`
- **规格约束**：零计划任务；`.iss` 只读不写；卸载零残留
- **验收判据**：Setup 全流程绿；计划任务 0 条；卸载后无遗留目录/注册项

### 4.9 外部能力 / Skill / 插件（v1.1 批次，v1.0 只留接口）
- **外部能力**：外脑执行端（Codex / DeepSeek / 本地 8B）+ 顾问；v1.0 只落 `executor_provider` 契约与一个可用的本地执行端适配，其余 v1.1 接入
- **Skill**：技能注册表 + M1 查重；v1.0 只有注册表与两条内置技能
- **插件**：开源接线（LobeHub/SuperAgent 调度、A2UI 组件树、Pipecat/LiveKit 语音管线）；v1.0 不接，v1.1 按「能用开源绝不自研 + 附替代排查结论」逐项接

---

## 五、工单序列（N-00 → N-12，按依赖顺序推进，不跳单）

> 节奏纪律：**先贯通后深修**。N-00～N-07 先把一条最小闭环跑通（语音唤醒 → Core 编排 → 执行 → 四角壳呈现），再在 N-08 起加深。

| # | 工单 | 依赖 | 交付物 | Gate（全绿才过） |
|---|---|---|---|---|
| N-00 | 建仓与骨架（工程域 + 客户端域双根，双域严格分离） | — | `H:\UltimaAI\UltimaAgentNext` 工程域目录树、客户端域目录契约（`dist/client` 预览树 + `installer/release-assets.json`）、构建脚本、precheck（构建+单测+依赖扫描+双域边界扫描+资产登记校验）、config 面、日志、LICENSE+README 一页级 | 空壳构建 0/0；precheck 一条命令全绿；双域边界扫描 0 违规；资产登记校验通过；零开发文档自检（无 00-19 体系） |
| N-01 | Core 最小闭环 | N-00 | intent_router / planner / confirm_gate / memory_boundary + 单测 | 意图黄金集准确率达标；越界写入被拒；单测绿 |
| N-02 | Middleware 调度 | N-01 | router / delegation / task_window / ticket / sandbox | 执行端可替换（两套桩跑通）；票据可追 |
| N-03 | Memory 三层 | N-01 | writer / poison_guard / store_backend / temperature_tier | 越权写入拒绝；双后端同契约跑通 |
| N-04 | Senses.Voice | N-01 | kws_backend / vad_tail / asr_pipeline / tts_cv3 / session_loop | KWS 参数逐项对齐基线；七态状态机事件序正确；零 Windows-only 依赖 |
| N-05 | Shell 常驻托管 | N-02 | host_shell / guardian / job_manager / child_supervisor / autostart_entry | 强杀子进程树 3s 内消失；计划任务 0 条；启动零控制台窗 |
| N-06 | Surface 四角壳 | N-03,N-05 | hud_shell / anchor_renderer / task_manager_panel / webview_bridge | 8 锚点渲染自检；150% DPI 无挤出；面板三键可用；中央零遮挡 |
| N-07 | 端到端最小闭环 | N-04,N-06 | 唤醒→理解→编排→执行→四角壳反馈 全链路 | 冷启动 window ≤541ms 基线区间；first frame ≤1530ms 区间；语音就绪 ≤15.6s 区间；残留 0 |
| N-08 | 外部能力接线 | N-07 | executor_provider 契约 + 本地执行端适配 + 顾问接口预留 | 断执行端降级可恢复；换一个提供商不改调用方 |
| N-09 | Skill 体系 | N-08 | 技能注册表 + 内置技能两条 + M1 查重门 | 未登记技能不可用；重复登记被拒 |
| N-10 | 插件接线（v1.1） | N-09 | 调度 / 组件树 / 语音管线 各一开源接线 | 每个插件附开源替代排查结论；关掉插件产品仍可用 |
| N-11 | 交付链 | N-07 | Update 通道（temporary-test-only 签名）+ Lifecycle Setup 安装包 | 篡改包被拒；回滚成功；安装/升级/卸载三链绿；零计划任务 |
| N-12 | 总验收 | 全部 | `UltimaAgent-Setup-*.exe` + 阶段报告 + 冻结 tag | 端到端冒烟 + 独立审计 PASS + 安装包在干净机可用 + DoD 四段齐全 |
| N-13 | Console 中心管理调度器（R-73；依赖 N-02） | N-02 | `task_orchestrator` / `resident_host` / `output_presenter` / `multi_end_dispatch` ＋ `usage_ledger` ＋ 档位只读视图 | 碰进程/网络/磁盘/像素的代码 **0 处**；八态只读写不定义；每任务 usage 行 `token>0`；超限只拦新派发；多端调度不碰执行端编排 |
| N-14 | 治理与约束⑤（R-73；依赖 N-01/N-02） | N-01,N-02 | 不变式断言集 / 规则库（带版本与生效范围）/ 红线审计 / 行为层提示词与评审口径 | 四类各有落点且互不顶替；改策略留版本；未登记模型拒载、记忆外发被拒；审计 provider≠开发 |


### N 卡扩卡（R-59 / R-60 / R-61 / R-66 追加验收，2026-11-13）

| 卡 | 追加交付物 | 追加验收（全绿才过） |
|---|---|---|
| **N-02** Middleware 调度 | 八态映射与门禁落地（`state_machine.py` 为唯一枚举源） | 枚举唯一计数 0 处第二套；非法迁移被拒；九点位 4–9 逐点投影对得上；冻结门只落 `BLOCKED` |
| **N-03** Memory | `mem`/`kb`/`exp` ＋ `index` 三库一索引；`store/` 分库分层分片；`volumes.json` 存储卷 | 三库检索互不串（`mem.search` 结果含 kb/exp 条数 0）；无位置元数据入 kb 被拒；新装 `kb` 条数 0；索引条数 vs 源条数 ±0；`draft` 经验不进决策路径；卷 95% 停收新片、卷满进 `CAPACITY_ALERT` 且不丢任务 |
| **N-09** Skill 体系 | 能力库：预置（随包、可停用不可卸载）＋ 扩展（可加可删）；能力×模型绑定与换绑 | 卸载预置被拒/停用可成功；任一能力绑定模型数 =1；自动改绑计数 0；模型库中 `local.llama` 条目 0；断网/删 token/错 key 分别落 `unreachable`/`no_token`/`auth_failed`；模拟 429 落 `rate_limited` 且付费探测 0 |
| **N-11** 交付链 | 预置能力随包体积预算；离线安装依赖冻结（不许现场 pip）；许可与 SBOM 台账；卸载清单单列 | 安装包内 chromium 体积 0；离线安装不联网可完成；SBOM 覆盖全部预置依赖；卸载后「模型权重保留」「记忆目录保留」与「能力清单删除」三项分别可验 |


### N 卡扩卡（R-68~R-72 缺口补口，2026-11-13）

| 卡 | 追加交付物 | 追加验收（全绿才过） |
|---|---|---|
| **N-01** Core | 上下文压缩器（10 轮／4000 token／70% 触发／保留 3 轮／摘要 ≤30%）；单线会话快照与回退（R-71）；`trace_id` 贯穿；工具与路径级权限策略表 | 压缩触发点与保留轮数对齐基线 T7；`trim_history`/`context_window` 命中 ≥1；回退与检查点一致率 100%；`trace_id` intake→回执同一值；策略表外调用被拒 |
| **N-02** Middleware | 并发配额；worktree 目录隔离（R-69）；`reworkCount` 返工计数与 BLOCKED 门（R-72） | 同时 `EXECUTING` ≤2；`cwd` 互不相同；连续 3 次审核不通过落 `BLOCKED`；两个计数器分列不合并 |
| **N-04** Senses.Voice | 热词表 loader（只读加载、禁硬编码） | 改词表不改代码即生效；硬编码命中 0 |
| **N-05** Shell | `pty_host`（ConPTY，R-68）：无窗、入 Job、标准流重定向、句柄交 Middleware | 起 PTY 不弹窗；宿主强杀 3s 内 PTY 树消失；全仓 `CreatePseudoConsole` 仅此一处 |
| **N-06** Surface | 列式看板 ＋ 时间线 ＋ 叫停／取消／恢复三键 | 三键可用且正确落八态；看板数据只读（不直接写队列）；`kanban`/`timeline` 命中 ≥1 |
| **N-08** 外部能力接线 | CLI 适配层（`plugin.executor.<name>`：Codex／Claude／Qwen／任意 CLI）＋ harness（工具调用循环／多步／重试／超时／schema） | 换一个 CLI 不改调用方；harness 跑通 3 步以上工具循环；执行返回 `token>0`（挡假执行） |

> 批次归属不变：`pty_host`、CLI 适配与 harness 属 **v1.1 批次**，v1.0 只留契约；N-13 / N-14 的 v1.0 子集＝Console 四职能＋用量账、不变式＋红线断言。

**v1.0 出包边界**：N-00～N-07 + N-11 + N-12 构成 v1.0（八原子模块全量、能唤醒能对话能编排能呈现能安装）；N-08～N-10 为 v1.1 批次，但在 v1.0 必须留好契约（不实现不算欠账，契约缺失算欠账）。**N-13／N-14 按 §二十一 21.7 归 v1.0 子集**（Console 四职能＋用量账、不变式＋红线断言）。

**派发纪律**：每张卡开工前①必须填满「设置与功能要求表」十项（见先行规则 §六，缺一不派）；②登记全局主表 `H:\UltimaAI\_shared\queue\global-queue-index.md` 并走 UltimaManager 18766 登记；同一时刻 EXECUTING ≤2，AUDIT ≤1；上一张冻结才进下一张。

**双域纪律**（先行规则 §二/§三/§五）：工程域 `UltimaAgentNext` 与客户端域（安装目录）物理隔离，单向流动；客户端域内的每一项资产都必须在 `installer/release-assets.json` 登记，未登记即打包失败。任何「往客户端文件夹加东西」的诉求先登记、后落地。

---

## 六、与 0054 / 旧仓的衔接

1. 0054 跑完 T9+T10 → 独立验收 → 打 `ultimaagent-v1-final-frozen-20261113` → 旧仓转只读；`docs` 全量留档，引用一律靠 tag 锚定。
2. Next 建仓后旧仓只读，`H:\UltimaAI\UltimaAgentNext` 为唯一活跃开发面。
3. 旧仓残留的 478 条未提交改动：冻结前由 0054 与其后的收口提交一次性收敛；确实无法收敛的，随冻结一起归档进 tag，不再逐条追。

---

## 七、纪律（写入每张卡的「禁止」段）

1. **零开发文档**：Next 只留 LICENSE + README 一页级；规格/方案/过程文档全部留旧仓，靠 tag 引用。
2. **零计划任务**：任何模块不得创建 schtasks；自启只走启动文件夹。
3. **无窗铁律**：所有子进程必须无窗；禁止前台引导、禁止弹窗。
4. **参数冻结**：KWS/CV3 参数只可按基线文档取值；改动必须同步基线文档并记录。
5. **终端无关层**：Core/Voice/Memory/Middleware/Update 禁 Windows-only 依赖（每轮 Gate 扫 0 处）。
6. **能开源不自研**：新增组件开工前附开源替代排查结论；结果写进卡片。
7. **代码 Tools 化**：新代码一律模块化封装为 Tools，禁止在业务层平铺逻辑。
8. **审计分离**：开发与审计不同实例；自证不能当验收结论。
9. **回执 8 键**：链路号/工单号/通道/执行端/完成状态/产出路径/验收证据/越界声明，缺一不算完成。

---

## 八、风险登记

| 风险 | 影响 | 处置 |
|---|---|---|
| 从零重写语音链路导致参数漂移 | 唤醒/音色回退 | N-04 Gate 强制逐项对齐基线文档；不达标不放行 |
| 8 个模块并行开发导致接口打架 | 返工 | 契约先落（N-00 定契约骨架），后续每单只实现不新增契约 |
| 老仓冻结时未收敛的 478 条改动成为悬空资产 | 追溯困难 | 冻结 tag + 归档说明，明确「不再追」 |
| v1.0 交付面被 v1.1 需求侵蚀 | 出不了包 | 出包边界写死在 N-12 卡；新增走变更流程 |
| 旧习惯性「参考旧实现」 | 隐性复制旧代码 | 每单 diff 审查：新文件路径 + 无旧包名 import |

---

## 九、下一步

1. 0054 跑完 → 独立验收 → v1 冻结 tag → 旧仓只读（不阻塞等待，进行中）。
2. 0054 冻结后立即派 **N-00**（卡已建：`tasks/queue/wo-ultimaagent-20261113-n00--next-bootstrap.md`，状态 pending）。
3. N-00 Gate 全绿后按序派 N-01。
