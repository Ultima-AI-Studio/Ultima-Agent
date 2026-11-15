# 调研能力三层归类（基础功能 / 插件 / Skill）

- **版本**：v1.1 · 2026-11-15
- **性质**：调研归类（将历次调研的功能/能力按 UltimaAgent 三层架构归类），非开发决策；**暂不推进代码**
- **依据**：ADR-001 三层架构 / ADR-011 插件总线规格（plugin-bus-spec.md v1.0）/ 能力注册表（registry.md v2.9）/ 技能注册表（Skill Registry）/ A2UI DSL 规格（component-dsl-schema.md）
- **覆盖调研**：job-ai-skills-video-research-20261029（视频 8 类技能）· dsh-pet-source-audit-20261029（大肥鱼）· bailongma-source-voice-audit-20261029（白龙马）· github-research / github-research-ultima-tools（开源对标）· grok-bot-*（Codex/ORB）· video-open-source-tools-20261115（Astryx / blender-skills / agency-agents）
- **背景**：用户要求区分"所有调研内容中，哪部分是基础功能、哪部分是插件、哪部分是 Skill"，理清工程推进体系；本次只归类落盘，不改代码

---

## 一、三层定义（UltimaAgent 架构对齐）

### 判定标准

| 层 | 定义 | 特征 | 生命周期 | 管理方 |
|---|---|---|---|---|
| **基础功能（Core）** | 系统骨架：宿主薄壳 + 总线内核 + 强制驻留层 + 协议/安全基线 + A2UI DSL 规则层 | 常驻、不可热卸载、承担身份与规则；"界面规则"与"可交互组件"定义层（归墟 OS 底层框架部分） | 随主程序启动/关闭 | 宿主薄壳 + 总线内核（ADR-001/011） |
| **插件（Plugin）** | L1-L10 能力域的可热插拔实现 + MCP 适配器（外部工具/设备/模型接入）+ 专项执行通道 | 独立 module.json、独立生命周期、实现 api-contract 入口、可装卸/替换/回滚；"会做某类事"的能力实现 | 总线注册/热插拔 | 能力插件总线（ADR-011） |
| **Skill（技能包）** | Agent 消费的领域技能：eng.* 角色技能 + 业务动作的 DSL 配置 + SKILL.md 定义"怎么做" | 按任务路由、白名单双模式、运行时按需加载；"具体业务界面/业务动作"由 Skill 经 DSL 生成 | 任务时路由加载 | Skill Registry（L2） |

### 边界规则（防止归类歧义）

1. **同域跨层**：同一能力域可三层各有一块——如语音：KWS 常驻监听=基础（L0 入口）；ASR/TTS 引擎实现=插件（L6 可替换）；音色克隆配置/训练=Skill。
2. **通道 vs 技能**：执行**通道**（浏览器自动化底层、OCR 引擎、文档渲染器）= 插件；**业务动作**（"用浏览器查资料""分析这张表""生成周报"）= Skill。通道提供能力，Skill 定义用途。
3. **外部资源 vs 内部能力**：外部 SaaS/模型/设备（HeyGen、MiMo API、Unitree Go2）= 外部资源，一律经 MCP 适配器插件接入，不直接进总线（plugin-bus-spec §1.3）。
4. **规则层 vs 实例层**：A2UI DSL 协议、组件目录、UI 范式 = 基础（规则层）；具体界面实例 = Skill 经 DSL 生成的产物，不入层。

---

## 二、视频 8 类技能归类

| 视频技能 | 真实项目 | 归类 | 理由 / 现网落点 |
|---|---|---|---|
| ① 腾讯浏览器操控 | BrowserSkill / QBotClaw | **插件（L3 执行）+ Skill（业务动作）** | 「借用真实登录态+标签页归还+Agent Window」= L3 执行通道范式升级（插件层）；「查资料/填表/下载」= Skill 层业务动作。对拍 pywinauto/M12/browser-use-automation |
| ② 表格分析 | 腾讯 WorkBuddy | **Skill** | 现网 sheet skill + doubao-data-analysis 已覆盖；OCR 表格入口= L3 插件接线（image-ocr）；人机双写形态= L7 插件层参考 |
| ③ 小米配音 | OmniVoice / MiMo-V2.5-TTS | **插件（L6 引擎）+ Skill（音色）** | 零样本克隆引擎= L6 呈现域可替换引擎候选（CV3 冻结中，仅观察）；音色克隆配置/训练= voice-trainer Skill |
| ④ HeyGen 数字人 | HeyGen（商业 SaaS） | **外部资源 → MCP 适配器插件** | 外部 API，非自托管；远期视频形态经 MCP 接入，不直接进总线 |
| ⑤ video-use 自动剪辑 | video-use / AutoClip / OpenShorts | **Skill（阶段三）** | ASR 词级时间戳+场景边界+LLM 高光+自动成片 = 视频剪辑 Skill（阶段三批次挂账）；底层抽帧/拆条走 byted-mediakit-video（L3 插件） |
| ⑥ 爆火 AI 设计技能 | taste-skill / bexa / stitch-design-taste | **基础（规则层）+ Skill（口味配置）** | 设计语言/禁项清单 = 抄入 UI 范式（基础规则层）；口味分档（taste A/B/C）= W9 主题管理 Skill 预设 |
| ⑦ 电商 RPA 录制回放 | 电商 RPA 生态 | **Skill（录制回放）+ 插件（元素自愈）** | 「录一次→重放」= browser-record-replay Skill（L8 受控执行）；元素 AI 自愈 = L3 浏览器通道插件增强 |
| ⑧ OfficeCLI | iOfficeAI OfficeCLI | **插件（文档通道）+ Skill（生成动作）** | 「渲染→查看→修复」闭环 = 文档产出通道插件（L6 呈现，升级产物质量门）；一键生成文档 = Skill 业务动作 |

**小结**：8 类技能中，**纯基础 0 类、纯插件 1 类（⑦自愈部分）、纯 Skill 1 类（②）、跨层 6 类**——多数技能同时含"通道（插件）+ 用途（Skill）"两段，符合"通道提供能力、Skill 定义用途"边界规则。

---

## 三、大肥鱼（dsh-pet）源码模块归类

| 模块 | 归类 | 理由 / 现网落点 |
|---|---|---|
| 动画系统（权重掷骰+档位防连播） | **基础（ORB 表现层）** | 悬浮球自播动画=宿主薄壳渲染职责（L0 渲染），常驻不进总线；参数可抄入 ORB |
| 物理四族（弹簧/抛掷/挤压/碰撞） | **基础（ORB 表现层）** | 纯函数物理=渲染层运行时，常驻；参数表可直接移植 |
| 六档工作状态机 | **基础（状态规则层）** | 与 M04 状态共享轴同构=基础状态定义；宿主/总线共用 |
| HTTP 接口 11 领域路由 | **插件（总线形态参考）** | createPetRouter = 插件总线落地形态参考（ADR-011 总线内核的接口驱动对拍） |
| 播放记录表（accepted→终态+幂等上报+挂起等待） | **基础（状态机）+ 插件（接口实现）** | 状态规则=基础；上报接口=插件层参考 |
| 语音（Edge-TTS+串行队列+防双播） | **插件（L6 引擎）+ Skill（播报配置）** | Edge-TTS= L6 可替换引擎候选（现网 CV3 不换）；防双播/串行队列=插件实现要点 |
| 余额 provider 注册制 | **插件（L3/L8 参考）** | 第三方注册制+失败三态归一=凭证中心/执行域插件接口参考 |
| 素材管线 9 脚本 | **Skill（素材生产）** | watermark→chroma→mask→fill→normalize = 素材生产 Skill 管线 |
| 桌面端看门狗（taskbar/topmost/host-liveness） | **基础（宿主职责）** | 窗口生命周期守护=宿主薄壳职责，常驻 |

**小结**：大肥鱼模块中，**基础 5 类（动画/物理/状态机/播放表状态/看门狗）、插件 3 类（HTTP 总线形态/语音引擎/余额）、Skill 1 类（素材管线）**——符合其"桌宠表现层"定位：大量表现层逻辑属基础渲染/状态职责。

---

## 四、白龙马语音模块归类

| 模块 | 归类 | 理由 / 现网落点 |
|---|---|---|
| ASR（5 云端+本地 Whisper） | **插件（L6/L0 引擎）** | ASR 引擎=可替换插件；现网 faster-whisper 已接入（L7 语音入口） |
| TTS（5 云端，无本地无克隆） | **插件（L6 引擎）** | TTS 引擎=可替换插件；现网 CV3 已冻结，不换 |
| KWS（sherpa-onnx 独立子进程） | **基础（L0 入口）+ 插件（引擎实现）** | KWS 常驻监听= L0 语音入口基础职责；sherpa-onnx 具体引擎=可替换插件实现 |
| 语音策略层（连续对话+PTT 两模式） | **基础（交互规则层）** | 对话模式策略= L7 交互规则，常驻 |
| A-B 决策影响（借壳 A 补本地 TTS / 换底座 B 语音链路重来） | **架构决策** | 属 plans/ADR 范畴，不入三层归类（归类只针对功能模块） |

**小结**：白龙马语音链路分层清晰——**基础 2 类（KWS 入口职责/交互策略）、插件 3 类（ASR/TTS/KWS 引擎实现均可替换）**。印证"引擎插件化、入口常驻"的语音分层原则。

---

## 五、开源对标（github-research 系列）归类

| 对标项 | 归类 | 理由 / 现网落点 |
|---|---|---|
| OS-Symphony 架构（domain/context/exec/status） | **基础（架构范式）** | 分层范式=ADR-001 同构参考，已内化 |
| FRIDAY / OpenJarvis / Open Felix / GPT4All | **基础（形态对标）** | 本地助手功能面=产品形态参考，非模块 |
| OpenUI（defineComponent+Zod） | **基础（规则层）** | 与 A2UI DSL 同思路，A2UI 已采用为组件树基底 |
| **Google A2UI**（声明式 UI 协议+预批准组件目录） | **基础（规则层，直接采用）** | L4/ui-kit 组件树基底=规则层（ADR-007 冻结） |
| **Pipecat / LiveKit**（实时语音编排管线） | **插件（L6 编排）** | 语音编排管线= L6 可替换实现候选（现网语音链已自建，观察） |
| **Copilot Agent Skills 开放标准**（skills/SKILL.md+gh skill） | **Skill（注册标准）** | L2 技能注册对齐开放标准=Skill 层标准 |
| **pywinauto**（MS UI Automation） | **插件（L3 执行通道）** | 本机执行通道= L3 插件，直接采用 |
| **Cognee/MemLayer/Mem0/Zep/Letta** | **插件（L9 记忆底座）** | 记忆引擎=可替换插件（Mem0 已接入现网） |
| **CrewAI / LangGraph / agentkanban** | **插件（L4 编排）** | 编排状态管理= L4 插件候选（现网自建 LangGraphStateMachine） |
| **Grok Bot Codex 直连**（s6-codex-plugin） | **插件（L3 执行端）** | Codex 执行端=已抄入插件（codex_provider.py，16 项测试） |
| Glances / LibreHardwareMonitor | **插件（L3 数据源）** | 硬件监控= L3 数据源插件候选 |
| shadcn/ui（技能给编码智能体消费） | **Skill（编码技能）** | 组件技能= eng.ui 消费的技能资产 |
| HA 实体模型 / unitree Go2 / NVIDIA XR AI | **外部资源 → MCP 适配器插件** | 设备接入一律经 MCP 适配器（plugin-bus §1.3） |

**小结**：开源对标中**基础 4 项（架构范式/形态/A2UI 规则层）、插件 8 项（语音/执行/记忆/编排/数据源/Codex）、Skill 3 项（技能标准/编码技能）、外部 MCP 3 项**——印证"规则层常驻、引擎/通道插件化、业务用途 Skill 化"的设计取向。

---

## 六、跨层边界说明（易混淆项）

| 项 | 基础功能 | 插件 | Skill |
|---|---|---|---|
| **语音链路** | KWS 常驻监听（L0 入口） | ASR/TTS 引擎实现（L6 可替换） | 音色克隆配置/voice-trainer |
| **浏览器** | —— | 执行通道（pywinauto/BrowserSkill 范式，L3） | 查资料/填表/下载等业务动作 |
| **表格** | —— | OCR 引擎接线（image-ocr，L3） | sheet skill + data-analysis 分析动作 |
| **视频** | —— | byted-mediakit-video 抽帧/拆条（L3） | video-use 式剪辑成片技能（阶段三） |
| **文档** | —— | 文档渲染通道（OfficeCLI 闭环，L6） | 一键生成文档业务动作 |
| **UI/设计** | A2UI DSL 规则层 + UI 范式（W9 token 基底） | —— | 设计口味预设（taste A/B/C 配置） |
| **状态机** | 工作状态机状态定义（基础规则） | 上报接口实现 | 状态文本/气泡文案配置 |

---

## 七、归类统计与推进含义

| 层 | 视频 8 类 | 大肥鱼 | 白龙马 | 开源对标 | 合计倾向 |
|---|---|---|---|---|---|
| 基础功能（Core） | 0 | 5 | 2 | 4 | 11 |
| 插件（Plugin） | 1+跨层 6 | 3 | 3 | 8 | 15+ |
| Skill（技能包） | 1+跨层 6 | 1 | 0 | 3 | 5+ |
| 外部资源（MCP 适配） | 1 | 0 | 0 | 3 | 4 |

**推进含义（调研层面结论，暂不实施）：**
1. **基础功能**：A2UI 规则层 + UI 范式 + 状态机定义 = 已冻结/常驻，不随调研改动；
2. **插件**：语音引擎（ASR/TTS/KWS）、浏览器通道、记忆底座、文档通道是"可替换实现"清单——现网已冻结的（CV3、Mem0、s6-codex-plugin）不动，仅观察/对拍；
3. **Skill**：视频 8 类多数落到 Skill 层业务动作（表格分析/浏览器动作/剪辑/录制回放/文档生成），进入阶段三批次规划时按 Skill 立项；
4. **外部资源**：HeyGen、MiMo API、设备集群一律 MCP 接入，不直接进总线。

---

## 八、三个视频开源工具补充（2026-11-15）

> 详细来源与证据见 [video-open-source-tools-20261115.md](video-open-source-tools-20261115.md)。本节只补三层归类，不表示已安装或接入。

| 工具 | 类型 | 归类 | 边界 |
|---|---|---|---|
| **Astryx**（meta/astryx） | React 19+ / StyleX 设计系统、组件库、主题与 CLI | **基础（UI 组件与设计规则参考）+ eng.ui Skill 外部资料** | Agent-ready 文档不等于 Ultima Skill；不改变 A2UI 冻结规则层 |
| **blender-skills**（arjun988/blender-skills） | 94 个 Blender 专项 Agent Skills + Blender MCP 执行 | **Skill（领域技能包）+ 插件（Blender MCP 通道）** | 技能路由与执行通道分开；未安装技能包或 MCP |
| **agency-agents**（msitarzewski/agency-agents） | 多角色专家定义、团队工作流与多工具安装器 | **Skill（角色与协作流程资产）** | 安装器/桌面 App 属外部分发工具，不据此新增 Ultima 插件 |

---

## 九、变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-29 | 新建；将视频 8 类 + 大肥鱼 + 白龙马 + 开源对标功能按基础/插件/Skill 三层归类，含判定标准与跨层边界；暂不推进代码 |
| v1.1 | 2026-11-15 | 补充 Astryx / blender-skills / agency-agents 三项视频工具归类；仅登记，不安装、不接入 |
