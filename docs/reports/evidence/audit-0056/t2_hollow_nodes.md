# T2 · 113 节点六要素逐节点检查

> 工单：wo-ultimaagent-20261113-0056  
> 节点权威：docs/reports/evidence/audit-0055/tree.json，node_count=113。  
> 规则：六要素依次为 **输入 / 输出或产物 / 状态 / 参数或阈值 / 失败路径 / 验收口径或数据落点**；缺 0 项＝有定义，缺 1–2 项＝半成品，缺 ≥3 项＝空壳。✓ 表示八份被审文件中有可定位定义，— 表示未定义。容器、路线图与明确延期节点不豁免，但在汇总中单列。

## 1. 逐节点矩阵（113/113）

| ID | 节点路径（父链） | 入 / 出 / 状 / 参 / 失 / 验 | 判定 | 缺项 | 依据 |
|---:|---|---|---|---|---|
| 000 | UltimaAgent 本体 | — / ✓ / — / — / — / — | **空壳** | 输入、状态、参数/阈值、失败路径、验收/数据落点 | tree.json nodes[0]；双域规范 §11 |
| 001 | UltimaAgent 本体 → UltimaAgent 引擎 | ✓ / ✓ / — / — / — / ✓ | **空壳** | 状态、参数/阈值、失败路径 | tree.json nodes[1]；双域规范 §11 |
| 002 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） | ✓ / ✓ / — / — / — / ✓ | **空壳** | 状态、参数/阈值、失败路径 | tree.json nodes[2]；双域规范 §11 |
| 003 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 1. Core（编排与裁决） | ✓ / ✓ / — / ✓ / ✓ / ✓ | **半成品** | 状态 | tree.json nodes[3]；详解页 §02 L185–188；基线 §16/§21 |
| 004 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 1. Core（编排与裁决） → 能力 | — / — / — / — / — / — | **空壳** | 输入、输出/产物、状态、参数/阈值、失败路径、验收/数据落点 | tree.json nodes[4]；详解页 §02 L185–188；基线 §16/§21 |
| 005 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 1. Core（编排与裁决） → 能力 → 意图理解 | ✓ / ✓ / ✓ / ✓ / — / ✓ | **半成品** | 失败路径 | tree.json nodes[5]；详解页 §02 L185–188；基线 §16/§21 |
| 006 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 1. Core（编排与裁决） → 能力 → 任务编排 | ✓ / ✓ / — / — / — / — | **空壳** | 状态、参数/阈值、失败路径、验收/数据落点 | 树节点只写“多步任务规划与执行顺序控制”；没有计划 schema、规划状态、失败分支或验收。 |
| 007 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 1. Core（编排与裁决） → 能力 → 复述确认 | ✓ / ✓ / — / ✓ / — / ✓ | **半成品** | 状态、失败路径 | tree.json nodes[7]；详解页 §02 L185–188；基线 §16/§21 |
| 008 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 1. Core（编排与裁决） → 能力 → 记忆写入裁决 | ✓ / ✓ / — / ✓ / ✓ / — | **半成品** | 状态、验收/数据落点 | tree.json nodes[8]；详解页 §02 L185–188；基线 §16/§21 |
| 009 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 1. Core（编排与裁决） → 能力 → 上下文压缩 | ✓ / ✓ / — / ✓ / — / ✓ | **半成品** | 状态、失败路径 | tree.json nodes[9]；详解页 §02 L185–188；基线 §16/§21 |
| 010 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 1. Core（编排与裁决） → 主脑（可替换推理后端） | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[10]；详解页 §02 L185–188；基线 §16/§21 |
| 011 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 1. Core（编排与裁决） → orchestrator · intent · interface_route · queue_source · capability registry | — / — / — / — / — / — | **空壳** | 输入、输出/产物、状态、参数/阈值、失败路径、验收/数据落点 | 仅列 orchestrator/intent/interface_route/queue_source/registry 名称，未给六要素契约。 |
| 012 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 1. Core（编排与裁决） → 任务规划 · 主动追问 · 结果汇报 | ✓ / ✓ / — / — / — / — | **空壳** | 状态、参数/阈值、失败路径、验收/数据落点 | tree.json nodes[12]；详解页 §02 L185–188；基线 §16/§21 |
| 013 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 2. Senses.Voice（语音进出） | ✓ / ✓ / ✓ / ✓ / — / ✓ | **半成品** | 失败路径 | tree.json nodes[13]；详解页 §02 L191–195；基线 §8–§13 |
| 014 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 2. Senses.Voice（语音进出） → 能力 | — / — / — / — / — / — | **空壳** | 输入、输出/产物、状态、参数/阈值、失败路径、验收/数据落点 | tree.json nodes[14]；详解页 §02 L191–195；基线 §8–§13 |
| 015 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 2. Senses.Voice（语音进出） → 能力 → 唤醒 | ✓ / ✓ / ✓ / ✓ / — / ✓ | **半成品** | 失败路径 | tree.json nodes[15]；详解页 §02 L191–195；基线 §8–§13 |
| 016 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 2. Senses.Voice（语音进出） → 能力 → 听写与对话 | ✓ / ✓ / ✓ / ✓ / — / ✓ | **半成品** | 失败路径 | tree.json nodes[16]；详解页 §02 L191–195；基线 §8–§13 |
| 017 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 2. Senses.Voice（语音进出） → 能力 → TTS 播报 | ✓ / ✓ / ✓ / ✓ / — / ✓ | **半成品** | 失败路径 | tree.json nodes[17]；详解页 §02 L191–195；基线 §8–§13 |
| 018 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 2. Senses.Voice（语音进出） → kws_backend · turn_worker · live_core · apm_dsp · CV3 推理 | — / — / — / — / — / — | **空壳** | 输入、输出/产物、状态、参数/阈值、失败路径、验收/数据落点 | 仅列 KWS/turn/live/APM/CV3 组件名；输入输出与组件故障切换未成契约。 |
| 019 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 2. Senses.Voice（语音进出） → 语音会话 · 尾音处理 · 音色切换 | ✓ / ✓ / — / — / — / — | **空壳** | 状态、参数/阈值、失败路径、验收/数据落点 | tree.json nodes[19]；详解页 §02 L191–195；基线 §8–§13 |
| 020 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 3. Shell（进程治理） | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[20]；详解页 §02 L198–202；基线 §15/§21.2 |
| 021 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 3. Shell（进程治理） → 能力 | — / — / — / — / — / — | **空壳** | 输入、输出/产物、状态、参数/阈值、失败路径、验收/数据落点 | tree.json nodes[21]；详解页 §02 L198–202；基线 §15/§21.2 |
| 022 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 3. Shell（进程治理） → 能力 → 进程树托管 | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[22]；详解页 §02 L198–202；基线 §15/§21.2 |
| 023 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 3. Shell（进程治理） → 能力 → 守护自愈 | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[23]；详解页 §02 L198–202；基线 §15/§21.2 |
| 024 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 3. Shell（进程治理） → 能力 → 开机自启 | ✓ / ✓ / ✓ / ✓ / — / ✓ | **半成品** | 失败路径 | tree.json nodes[24]；详解页 §02 L198–202；基线 §15/§21.2 |
| 025 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 3. Shell（进程治理） → 能力 → 子进程零窗 | ✓ / ✓ / — / ✓ / — / ✓ | **半成品** | 状态、失败路径 | tree.json nodes[25]；详解页 §02 L198–202；基线 §15/§21.2 |
| 026 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 3. Shell（进程治理） → 能力 → 终端宿主 PTY | ✓ / ✓ / — / ✓ / — / ✓ | **半成品** | 状态、失败路径 | tree.json nodes[26]；详解页 §02 L198–202；基线 §15/§21.2 |
| 027 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 3. Shell（进程治理） → GuardianService · HostTaskRegistry · JobObjectManager · ChildProcessSupervisor · ReadinessProbe · AutostartEntry | — / — / — / — / — / — | **空壳** | 输入、输出/产物、状态、参数/阈值、失败路径、验收/数据落点 | 仅列 Guardian/Registry/Job/Supervisor/Probe/Autostart 名称；单件接口未定义。 |
| 028 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 3. Shell（进程治理） → 任务托管 · 崩溃回收 | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[28]；详解页 §02 L198–202；基线 §15/§21.2 |
| 029 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 4. Surface（界面与呈现） | ✓ / ✓ / — / ✓ / — / ✓ | **半成品** | 状态、失败路径 | tree.json nodes[29]；详解页 §02 L205–209；双域规范 §11.3 |
| 030 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 4. Surface（界面与呈现） → 能力 | — / — / — / — / — / — | **空壳** | 输入、输出/产物、状态、参数/阈值、失败路径、验收/数据落点 | tree.json nodes[30]；详解页 §02 L205–209；双域规范 §11.3 |
| 031 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 4. Surface（界面与呈现） → 能力 → 四角壳 HUD · 8 锚点 | ✓ / ✓ / ✓ / ✓ / — / ✓ | **半成品** | 失败路径 | tree.json nodes[31]；详解页 §02 L205–209；双域规范 §11.3 |
| 032 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 4. Surface（界面与呈现） → 能力 → 应用内任务管理器 | ✓ / ✓ / ✓ / ✓ / — / ✓ | **半成品** | 失败路径 | tree.json nodes[32]；详解页 §02 L205–209；双域规范 §11.3 |
| 033 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 4. Surface（界面与呈现） → 能力 → 看板与干预 | ✓ / ✓ / ✓ / — / — / ✓ | **半成品** | 参数/阈值、失败路径 | tree.json nodes[33]；详解页 §02 L205–209；双域规范 §11.3 |
| 034 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 4. Surface（界面与呈现） → UltimaAgent.Hud 原生壳 · hud-live-four-corner 设计基线 · TaskManagerRenderer · taskmanager.html | — / — / — / — / — / — | **空壳** | 输入、输出/产物、状态、参数/阈值、失败路径、验收/数据落点 | 只列壳/渲染器/HTML 名称；没有运行时契约。 |
| 035 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 4. Surface（界面与呈现） → 状态反馈 · 任务可视 | ✓ / ✓ / — / — / — / ✓ | **空壳** | 状态、参数/阈值、失败路径 | tree.json nodes[35]；详解页 §02 L205–209；双域规范 §11.3 |
| 036 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 5. Memory（记忆与自学习） | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[36]；详解页 §03 L251–265；基线 §17 |
| 037 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 5. Memory（记忆与自学习） → mem · 用户记忆 | ✓ / ✓ / ✓ / — / ✓ / ✓ | **半成品** | 参数/阈值 | tree.json nodes[37]；详解页 §03 L251–265；基线 §17 |
| 038 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 5. Memory（记忆与自学习） → kb · 知识库 | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[38]；详解页 §03 L251–265；基线 §17 |
| 039 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 5. Memory（记忆与自学习） → exp · 经验库 | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[39]；详解页 §03 L251–265；基线 §17 |
| 040 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 5. Memory（记忆与自学习） → index · 索引与检索 | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[40]；详解页 §03 L251–265；基线 §17 |
| 041 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 5. Memory（记忆与自学习） → writer · poison_guard · store_backend · temperature_tier · volumes | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[41]；详解页 §03 L251–265；基线 §17 |
| 042 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 5. Memory（记忆与自学习） → 上下文注入 · 记忆检索 · 知识采集编排 | ✓ / ✓ / — / ✓ / — / — | **空壳** | 状态、失败路径、验收/数据落点 | 只列“上下文注入/检索/采集编排”，无编排状态、参数、失败和验收。 |
| 043 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 6. Middleware（执行端与票据） | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[43]；详解页 §02 L219–223；基线 §15/§24.2 |
| 044 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 6. Middleware（执行端与票据） → queue_engine（tasks/queue_engine，Python 引擎域）· state_machine（八态唯一枚举源）· router · delegation · task_window · ticket · sandbox（双层：Job ＋ 写域白名单，R-79）· worktree 隔离 · 并发配额 · reworkCount | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[44]；详解页 §02 L219–223；基线 §15/§24.2 |
| 045 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → 6. Middleware（执行端与票据） → 执行端路由 · 任务窗口管理 | ✓ / ✓ / — / — / — / — | **空壳** | 状态、参数/阈值、失败路径、验收/数据落点 | 只有“执行端路由/任务窗口管理”名称，缺状态、参数、失败、验收。 |
| 046 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ Console（引擎中心管理调度器） | ✓ / ✓ / ✓ / — / — / ✓ | **半成品** | 参数/阈值、失败路径 | tree.json nodes[46]；详解页 §02 L227–238；基线 §19/§22/§24.1 |
| 047 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ Console（引擎中心管理调度器） → 任务编排 | ✓ / ✓ / ✓ / ✓ / ✓ / — | **半成品** | 验收/数据落点 | tree.json nodes[47]；详解页 §02 L227–238；基线 §19/§22/§24.1 |
| 048 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ Console（引擎中心管理调度器） → 常驻托管 | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[48]；详解页 §02 L227–238；基线 §19/§22/§24.1 |
| 049 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ Console（引擎中心管理调度器） → 输出呈现 | ✓ / ✓ / — / — / — / ✓ | **空壳** | 状态、参数/阈值、失败路径 | 只说把状态递给 Surface，未定义事件、状态、失败和验收。 |
| 050 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ Console（引擎中心管理调度器） → 多端调度 | ✓ / ✓ / — / — / — / — | **空壳** | 状态、参数/阈值、失败路径、验收/数据落点 | 只说向设备/显示端投递，未定义设备标识、就绪、确认、重试或验收。 |
| 051 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ Console（引擎中心管理调度器） → 任务库（项目→工单卡→任务→运行实例） | ✓ / ✓ / ✓ / ✓ / — / ✓ | **半成品** | 失败路径 | tree.json nodes[51]；详解页 §02 L227–238；基线 §19/§22/§24.1 |
| 052 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ Console（引擎中心管理调度器） → dispatcher · priority_deps · 重启预算账 · 档位只读视图 · usage_ledger（用量账，R-70） | ✓ / ✓ / ✓ / ✓ / — / ✓ | **半成品** | 失败路径 | 工具集合有职责和参数，但失败回执没有闭合。 |
| 053 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ 治理与约束（⑤） | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[53]；详解页 §02 L241–247；基线 §20/§22.3 |
| 054 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ 治理与约束（⑤） → 代码断言（不入库） | ✓ / ✓ / — / — / ✓ / ✓ | **半成品** | 状态、参数/阈值 | tree.json nodes[54]；详解页 §02 L241–247；基线 §20/§22.3 |
| 055 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ 治理与约束（⑤） → 可配策略（带版本与生效范围） | ✓ / ✓ / ✓ / ✓ / — / — | **半成品** | 失败路径、验收/数据落点 | tree.json nodes[55]；详解页 §02 L241–247；基线 §20/§22.3 |
| 056 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ 治理与约束（⑤） → 防投毒 · 审计独立 · 外发红线 | ✓ / ✓ / — / — / ✓ / ✓ | **半成品** | 状态、参数/阈值 | tree.json nodes[56]；详解页 §02 L241–247；基线 §20/§22.3 |
| 057 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ 治理与约束（⑤） → 日志库（审计与留痕） | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[57]；详解页 §02 L241–247；基线 §20/§22.3 |
| 058 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ 治理与约束（⑤） → 行为学原则（五条 · 按人类生物特质） | — / — / — / — / — / — | **空壳** | 输入、输出/产物、状态、参数/阈值、失败路径、验收/数据落点 | tree.json nodes[58]；详解页 §02 L241–247；基线 §20/§22.3 |
| 059 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ 治理与约束（⑤） → 行为学原则（五条 · 按人类生物特质） → 感官分工（通道分工） | ✓ / ✓ / — / — / — / ✓ | **空壳** | 状态、参数/阈值、失败路径 | tree.json nodes[59]；详解页 §02 L241–247；基线 §20/§22.3 |
| 060 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ 治理与约束（⑤） → 行为学原则（五条 · 按人类生物特质） → 理解先于行动 | ✓ / ✓ / — / — / — / ✓ | **空壳** | 状态、参数/阈值、失败路径 | tree.json nodes[60]；详解页 §02 L241–247；基线 §20/§22.3 |
| 061 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ 治理与约束（⑤） → 行为学原则（五条 · 按人类生物特质） → 复述确认 | ✓ / ✓ / — / — / — / ✓ | **空壳** | 状态、参数/阈值、失败路径 | tree.json nodes[61]；详解页 §02 L241–247；基线 §20/§22.3 |
| 062 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ 治理与约束（⑤） → 行为学原则（五条 · 按人类生物特质） → 记忆分层 | ✓ / ✓ / — / — / — / ✓ | **空壳** | 状态、参数/阈值、失败路径 | tree.json nodes[62]；详解页 §02 L241–247；基线 §20/§22.3 |
| 063 | UltimaAgent 本体 → UltimaAgent 引擎 → 基础能力（本体承载） → ＋ 治理与约束（⑤） → 行为学原则（五条 · 按人类生物特质） → 不打扰与反馈闭环 | ✓ / ✓ / — / — / — / ✓ | **空壳** | 状态、参数/阈值、失败路径 | tree.json nodes[63]；详解页 §02 L241–247；基线 §20/§22.3 |
| 064 | UltimaAgent 本体 → UltimaAgent 引擎 → 外部能力（容器 · 三抽屉） | ✓ / ✓ / — / — / — / — | **空壳** | 状态、参数/阈值、失败路径、验收/数据落点 | tree.json nodes[64]；详解页 §04–§05 L268–309；基线 §18/§23 |
| 065 | UltimaAgent 本体 → UltimaAgent 引擎 → 外部能力（容器 · 三抽屉） → 能力库 Skill | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[65]；详解页 §04–§05 L268–309；基线 §18/§23 |
| 066 | UltimaAgent 本体 → UltimaAgent 引擎 → 外部能力（容器 · 三抽屉） → 能力库 Skill → 预置（随安装包自带） | ✓ / ✓ / ✓ / ✓ / — / ✓ | **半成品** | 失败路径 | tree.json nodes[66]；详解页 §04–§05 L268–309；基线 §18/§23 |
| 067 | UltimaAgent 本体 → UltimaAgent 引擎 → 外部能力（容器 · 三抽屉） → 能力库 Skill → 扩展（用户添加） | ✓ / ✓ / ✓ / — / ✓ / ✓ | **半成品** | 参数/阈值 | tree.json nodes[67]；详解页 §04–§05 L268–309；基线 §18/§23 |
| 068 | UltimaAgent 本体 → UltimaAgent 引擎 → 外部能力（容器 · 三抽屉） → 能力库 Skill → 知识采集 kb.collect.http / kb.collect.browser | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[68]；详解页 §04–§05 L268–309；基线 §18/§23 |
| 069 | UltimaAgent 本体 → UltimaAgent 引擎 → 外部能力（容器 · 三抽屉） → 能力库 Skill → 一能力只绑一个模型 | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[69]；详解页 §04–§05 L268–309；基线 §18/§23 |
| 070 | UltimaAgent 本体 → UltimaAgent 引擎 → 外部能力（容器 · 三抽屉） → 插件 Plugin | ✓ / ✓ / ✓ / ✓ / — / ✓ | **半成品** | 失败路径 | tree.json nodes[70]；详解页 §04–§05 L268–309；基线 §18/§23 |
| 071 | UltimaAgent 本体 → UltimaAgent 引擎 → 外部能力（容器 · 三抽屉） → 插件 Plugin → plugin.provider.<name> | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[71]；详解页 §04–§05 L268–309；基线 §18/§23 |
| 072 | UltimaAgent 本体 → UltimaAgent 引擎 → 外部能力（容器 · 三抽屉） → 插件 Plugin → plugin.executor.<name> | ✓ / ✓ / — / ✓ / — / ✓ | **半成品** | 状态、失败路径 | harness 只被描述为工具循环/重试/超时/schema；无生命周期与失败/取消契约。 |
| 073 | UltimaAgent 本体 → UltimaAgent 引擎 → 外部能力（容器 · 三抽屉） → 插件 Plugin → plugin.mcp.<name> · plugin.kb.browser · plugin.store.* | ✓ / ✓ / — / — / — / — | **空壳** | 状态、参数/阈值、失败路径、验收/数据落点 | tree.json nodes[73]；详解页 §04–§05 L268–309；基线 §18/§23 |
| 074 | UltimaAgent 本体 → UltimaAgent 引擎 → 外部能力（容器 · 三抽屉） → 插件 Plugin → 组件注册表 · 开源替代排查 | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[74]；详解页 §04–§05 L268–309；基线 §18/§23 |
| 075 | UltimaAgent 本体 → UltimaAgent 引擎 → 外部能力（容器 · 三抽屉） → 模型库 Provider | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[75]；详解页 §04–§05 L268–309；基线 §18/§23 |
| 076 | UltimaAgent 本体 → UltimaAgent 引擎 → 外部能力（容器 · 三抽屉） → 模型库 Provider → 六态可检测 | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[76]；详解页 §04–§05 L268–309；基线 §18/§23 |
| 077 | UltimaAgent 本体 → UltimaAgent 引擎 → 外部能力（容器 · 三抽屉） → 模型库 Provider → 换绑与降级 | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[77]；详解页 §04–§05 L268–309；基线 §18/§23 |
| 078 | UltimaAgent 本体 → UltimaAgent 引擎 → 外部能力（容器 · 三抽屉） → 模型库 Provider → 主脑不进模型库、不可指派 | ✓ / ✓ / — / ✓ / ✓ / ✓ | **半成品** | 状态 | tree.json nodes[78]；详解页 §04–§05 L268–309；基线 §18/§23 |
| 079 | UltimaAgent 本体 → UltimaAgent 引擎 → 交付（远程更新与安装交付） | ✓ / ✓ / — / — / — / — | **空壳** | 状态、参数/阈值、失败路径、验收/数据落点 | tree.json nodes[79]；详解页 §01/§05；基线 §14.2；双域规范 §七 |
| 080 | UltimaAgent 本体 → UltimaAgent 引擎 → 交付（远程更新与安装交付） → 7. Update（远程更新） | ✓ / ✓ / ✓ / ✓ / — / — | **半成品** | 失败路径、验收/数据落点 | 有通道/签名/灰度参数，缺原子回滚与完整验收。 |
| 081 | UltimaAgent 本体 → UltimaAgent 引擎 → 交付（远程更新与安装交付） → 7. Update（远程更新） → manifest · publisher | ✓ / ✓ / ✓ / ✓ / ✓ / — | **半成品** | 验收/数据落点 | tree.json nodes[81]；详解页 §01/§05；基线 §14.2；双域规范 §七 |
| 082 | UltimaAgent 本体 → UltimaAgent 引擎 → 交付（远程更新与安装交付） → 7. Update（远程更新） → 远程更新 · 签名校验 | ✓ / ✓ / — / — / ✓ / ✓ | **半成品** | 状态、参数/阈值 | 只有“远程更新/签名校验”能力名；回滚技能在注册表中有名无流程状态和参数。 |
| 083 | UltimaAgent 本体 → UltimaAgent 引擎 → 交付（远程更新与安装交付） → 8. Lifecycle（安装与交付） | ✓ / ✓ / ✓ / ✓ / — / ✓ | **半成品** | 失败路径 | tree.json nodes[83]；详解页 §01/§05；基线 §14.2；双域规范 §七 |
| 084 | UltimaAgent 本体 → UltimaAgent 引擎 → 交付（远程更新与安装交付） → 8. Lifecycle（安装与交付） → 零计划任务 | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[84]；详解页 §01/§05；基线 §14.2；双域规范 §七 |
| 085 | UltimaAgent 本体 → UltimaAgent 引擎 → 交付（远程更新与安装交付） → 8. Lifecycle（安装与交付） → 安装/升级链 | ✓ / ✓ / ✓ / ✓ / — / ✓ | **半成品** | 失败路径 | tree.json nodes[85]；详解页 §01/§05；基线 §14.2；双域规范 §七 |
| 086 | UltimaAgent 本体 → UltimaAgent 引擎 → 交付（远程更新与安装交付） → 8. Lifecycle（安装与交付） → Setup 链 · check-shipped-tasks · watchdog 开发机兜底 | ✓ / ✓ / — / — / ✓ / ✓ | **半成品** | 状态、参数/阈值 | 只列 Setup/check/watchdog 名称；没有状态、参数或失败恢复。 |
| 087 | UltimaAgent 本体 → UltimaAgent 引擎 → 配置内化与工程底座 | ✓ / ✓ / — / ✓ / ✓ / ✓ | **半成品** | 状态 | tree.json nodes[87]；双域规范 §三–§八 |
| 088 | UltimaAgent 本体 → UltimaAgent 引擎 → 配置内化与工程底座 → 六件配置归位 | ✓ / ✓ / — / ✓ / — / — | **空壳** | 状态、失败路径、验收/数据落点 | tree.json nodes[88]；双域规范 §三–§八 |
| 089 | UltimaAgent 本体 → UltimaAgent 引擎 → 配置内化与工程底座 → 环境变量降级 | ✓ / ✓ / ✓ / ✓ / ✓ / ✓ | **有定义** | 无 | tree.json nodes[89]；双域规范 §三–§八 |
| 090 | UltimaAgent 本体 → UltimaAgent 引擎 → 配置内化与工程底座 → tools/devtools/queue | ✓ / ✓ / — / — / — / — | **空壳** | 状态、参数/阈值、失败路径、验收/数据落点 | tree.json nodes[90]；双域规范 §三–§八 |
| 091 | UltimaAgent 本体 → UltimaAgent 引擎 → P2V 拆单（0054 收口验收后启动） | ✓ / ✓ / ✓ / — / — / ✓ | **半成品** | 参数/阈值、失败路径 | tree.json nodes[91]；双域规范 §四/§八 |
| 092 | UltimaAgent 本体 → UltimaAgent 引擎 → P2V 拆单（0054 收口验收后启动） → P2V-00 | ✓ / ✓ / ✓ / — / — / ✓ | **半成品** | 参数/阈值、失败路径 | tree.json nodes[92]；双域规范 §四/§八 |
| 093 | UltimaAgent 本体 → UltimaAgent 引擎 → P2V 拆单（0054 收口验收后启动） → P2V-01 | ✓ / ✓ / ✓ / — / — / ✓ | **半成品** | 参数/阈值、失败路径 | tree.json nodes[93]；双域规范 §四/§八 |
| 094 | UltimaAgent 本体 → UltimaAgent 引擎 → P2V 拆单（0054 收口验收后启动） → P2V-02 | ✓ / ✓ / ✓ / — / — / ✓ | **半成品** | 参数/阈值、失败路径 | tree.json nodes[94]；双域规范 §四/§八 |
| 095 | UltimaAgent 本体 → UltimaAgent 引擎 → P2V 拆单（0054 收口验收后启动） → P2V-03 | ✓ / ✓ / ✓ / — / — / ✓ | **半成品** | 参数/阈值、失败路径 | tree.json nodes[95]；双域规范 §四/§八 |
| 096 | UltimaAgent 本体 → UltimaAgent 引擎 → P2V 拆单（0054 收口验收后启动） → P2V-04 | ✓ / ✓ / ✓ / — / — / ✓ | **半成品** | 参数/阈值、失败路径 | tree.json nodes[96]；双域规范 §四/§八 |
| 097 | UltimaAgent 本体 → UltimaAgent 引擎 → P2V 拆单（0054 收口验收后启动） → P2V-05 | ✓ / ✓ / ✓ / — / — / ✓ | **半成品** | 参数/阈值、失败路径 | tree.json nodes[97]；双域规范 §四/§八 |
| 098 | UltimaAgent 本体 → UltimaAgent 客户端 | ✓ / ✓ / — / — / — / ✓ | **空壳** | 状态、参数/阈值、失败路径 | 客户端只写“调 API/订阅事件”，没有会话状态、参数、失败或验收。 |
| 099 | UltimaAgent 本体 → UltimaAgent 客户端 → Windows（已落地） | ✓ / ✓ / — / ✓ / — / ✓ | **半成品** | 状态、失败路径 | tree.json nodes[99]；双域规范 §11 |
| 100 | UltimaAgent 本体 → UltimaAgent 客户端 → macOS（待定） | ✓ / ✓ / — / — / — / — | **空壳** | 状态、参数/阈值、失败路径、验收/数据落点 | 明确待定；只有跨端目标，无 v1 契约。 |
| 101 | UltimaAgent 本体 → UltimaAgent 客户端 → 移动端（待定） | ✓ / ✓ / — / — / — / — | **空壳** | 状态、参数/阈值、失败路径、验收/数据落点 | 明确待定；8 锚点适用性也未定。 |
| 102 | UltimaAgent 本体 → UltimaAgent 客户端 → AR 眼镜端（最终形态） | ✓ / ✓ / — / — / — / — | **空壳** | 状态、参数/阈值、失败路径、验收/数据落点 | 最终形态占位；没有实现契约。 |
| 103 | UltimaAgent 本体 → UltimaAgent 客户端 → 多终端路线（Windows → Linux → 自研 AR 眼镜系统） | ✓ / ✓ / — / ✓ / — / — | **空壳** | 状态、失败路径、验收/数据落点 | tree.json nodes[103]；双域规范 §11 |
| 104 | UltimaAgent 本体 → UltimaAgent 客户端 → 多终端路线（Windows → Linux → 自研 AR 眼镜系统） → 终端无关层 | ✓ / ✓ / — / ✓ / ✓ / ✓ | **半成品** | 状态 | tree.json nodes[104]；双域规范 §11 |
| 105 | UltimaAgent 本体 → UltimaAgent 客户端 → 多终端路线（Windows → Linux → 自研 AR 眼镜系统） → 终端相关层 | ✓ / ✓ / — / — / — / — | **空壳** | 状态、参数/阈值、失败路径、验收/数据落点 | tree.json nodes[105]；双域规范 §11 |
| 106 | UltimaAgent 本体 → UltimaAgent 客户端 → 多终端路线（Windows → Linux → 自研 AR 眼镜系统） → 迁移纪律 | ✓ / ✓ / — / ✓ / — / ✓ | **半成品** | 状态、失败路径 | tree.json nodes[106]；双域规范 §11 |
| 107 | UltimaAgent 本体 → UltimaAgent 运营 | ✓ / ✓ / ✓ / — / ✓ / — | **半成品** | 参数/阈值、验收/数据落点 | tree.json nodes[107]；双域规范 §11.1 |
| 108 | UltimaAgent 本体 → UltimaAgent 运营 → 产品运营后台 | ✓ / ✓ / — / — / — / — | **空壳** | 状态、参数/阈值、失败路径、验收/数据落点 | tree.json nodes[108]；双域规范 §11.1 |
| 109 | UltimaAgent 本体 → UltimaAgent 运营 → 用户与订阅 | — / — / ✓ / — / — / — | **空壳** | 输入、输出/产物、参数/阈值、失败路径、验收/数据落点 | 明确 v1.0 不做，运行六要素仅有延期状态。 |
| 110 | UltimaAgent 本体 → UltimaAgent 运营 → 市场与增长 | — / — / ✓ / — / — / — | **空壳** | 输入、输出/产物、参数/阈值、失败路径、验收/数据落点 | 明确 v1.0 不做，运行六要素仅有延期状态。 |
| 111 | UltimaAgent 本体 → UltimaAgent 运营 → 计费与订单 | — / — / ✓ / — / — / — | **空壳** | 输入、输出/产物、参数/阈值、失败路径、验收/数据落点 | 明确 v1.0 不做，运行六要素仅有延期状态。 |
| 112 | UltimaAgent 本体 → UltimaAgent 运营 → 客服与反馈 | — / — / ✓ / — / — / — | **空壳** | 输入、输出/产物、参数/阈值、失败路径、验收/数据落点 | 明确 v1.0 不做，运行六要素仅有延期状态。 |

## 2. 汇总

- 节点总数：**113**（与 tree.json.node_count 一致）。
- 有定义：**25**。
- 半成品：**47**。
- 空壳：**41**。
- 校验：25 + 47 + 41 = **113**。

| 主归属链路 | 节点数 | 有定义 | 半成品 | 空壳 |
|---|---:|---:|---:|---:|
| L1 启动与自检 | 13 | 5 | 4 | 4 |
| L2 唤醒与听写 | 7 | 0 | 4 | 3 |
| L3 理解与决策 | 10 | 1 | 5 | 4 |
| L4 执行与工具 | 25 | 11 | 9 | 5 |
| L5 记忆与温度 | 7 | 5 | 1 | 1 |
| L6 治理与更新 | 19 | 3 | 9 | 7 |
| 呈现/路线/非 v1 | 32 | 0 | 15 | 17 |

空壳数量最高的两组是 **呈现/路线/非 v1** 与 **L6 治理与更新**。前者包含容器和明确延期节点，不直接等于 v1 运行阻断；L6 的空壳集中在行为原则容器和交付技能。L4 虽只有 5 个空壳，但含 executor/harness、Console 输出、多端投递等运行时节点，开工风险更直接。L3 的空壳数也不高，但“任务编排”正处在理解到执行的主干上，影响比数量更重。

## 3. 物质性空壳/半成品（净新增）

| 编号 | 节点位置与判定依据 | 后果 | 严重度 | 一句话修法 |
|---|---|---|---|---|
| H-01 | 节点 6 Core→能力→任务编排：仅有“多步任务规划与执行顺序控制”，六要素仅输入/输出可推定，缺状态、参数、失败、验收；缺口复核 16 项没有覆盖“计划对象本身的契约” | 意图即使识别成功，也没有可交给 Console/Middleware 的稳定计划产物；多步任务无法保存、续跑或判失败 | **BLOCKER** | 定义 versioned plan schema、step 状态/依赖/补偿、规模上限、规划失败码和从计划到派发的验收夹具。 |
| H-02 | 节点 50 Console→多端调度：只有“向多用户设备/显示端投递”，缺状态、参数、失败与验收；同时盘点 F1 已定 v1.0 单用户，但节点仍承诺多用户设备 | 调度器无法确定目标设备、在线性、投递确认或失败重试，兑现“多端调度”时会丢消息或重复投递 | **HIGH** | v1 明确收窄为单用户多显示端，并补 device_id/session_id、ready/ack/timeout/dedup 契约；多用户留版本门。 |
| H-03 | 节点 49 Console→输出呈现 与节点 98 UltimaAgent 客户端：只写“递状态/调 API/订阅事件”，两者均为空壳；不是盘点 E3 或缺口 D10 的 UI 实现问题 | 引擎有状态、客户端也存在，但中间没有事件 envelope、订阅恢复或顺序规则，Surface 无法可靠收到最终状态 | **HIGH** | 固化 Engine→Client 事件总线 schema（event_id、version、sequence、snapshot cursor、ack/reconnect）并给跨重启补发验收。 |
| H-04 | 节点 72 plugin.executor.<name> 为半成品：有输入/输出和“重试/超时/schema”字样，缺执行生命周期与失败/取消契约；真实 harness 未接是已知 D2，本条只登记“设计仍未达到可实现定义” | 即使后续实现 D2，也会因各适配器自行解释启动、流式输出、取消和终态而不能互换 | **HIGH** | 先冻结 executor SPI：prepare/start/stream/cancel/finalize、标准错误码、deadline、幂等与 receipt schema，再接真实 harness。 |
| H-05 | 节点 80/82 Update 与“远程更新·签名校验”：均为半成品，缺原子回滚状态与参数；与 T1 G-08 同根，**交叉引用不重复计数** | 签名通过仍不能保证更新可恢复 | **BLOCKER（计入 G-08，不另增总数）** | 按 G-08 补 A/B 槽更新事务与首启健康门。 |

## 4. 已检查且不报错的重点节点

- 节点 10 主脑：brain.infer 输入、推理输出、registered/active/revoked 与健康态、运行参数、失败梯子、§16.7 验收均能定位，判 **有定义**。
- 节点 22/23 Shell 进程树托管与守护自愈：起停输入、进程事实输出、预算状态、20s/3次/300s、上抛与 ActiveProcesses==0 验收齐，判 **有定义**。
- 节点 36/40 Memory 与 index：三库输入输出、层/卷状态、阈值、离线/容量告警及 §17.7 门齐，判 **有定义**；跨卷提交缺口已单独记 G-07，不把整节点降为空壳。
- 节点 57 日志库：四类输入、log.query、保留状态/阈值、LOG_CHAIN_BROKEN 和哈希链验收齐，判 **有定义**；它与全卷满的冲突留给 T3。
- 节点 76/77 provider 六态与换绑降级：输入、输出、状态、退避参数、失败路径和 §18.8 验收齐，判 **有定义**。

## 5. T2 Gate

- 逐节点判定：**113/113**，无抽样。
- 有定义/半成品/空壳分别计数，且总和与 node_count=113 相等。
- 每个缺项均有节点路径和具体文档/节或 tree.json nodes[id] 位置；未把“有名字”视作“有定义”。

