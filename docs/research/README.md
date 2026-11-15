# Ultima Agent 调研资料库（Research Library）

- **版本**：v1.15 · 2026-11-15
- **性质**：调研资料统一存放目录（`docs/research/`），只汇集调研事实与来源，不包含开发决策；方案、工单由调研结论演化后另行落盘
- **分工**：`docs/research/` 收调研；`docs/plans/` 收方案与决策（ADR）；`docs/references/` 收教训库/沟通汇集等引用库；`docs/reports/` 收报告
- **目录职责**：每篇调研文件来源可追溯（项目/链接/检索日期）；新调研先登记本索引，再落文件

## 一、调研文件索引

| 文件 | 主题 | 检索日期 | 状态 |
|---|---|---|---|
| [github-research.md](github-research.md) | 同类 Agent 产品 + 动效设计调研（OS-Symphony / FRIDAY / OpenUI / 语音助手 / 桌面智能体 / 动效令牌） | 2026-10-16 | 已归档（自 references 迁入） |
| [github-research-ultima-tools.md](github-research-ultima-tools.md) | Ultima 工具链调研（A2UI / Pipecat / Agent Skills / 记忆 / 设备集群 / 毒液形态） | 2026-10-16 | 已归档（自 references 迁入） |
| [orb-competitive-research-20261024.md](orb-competitive-research-20261024.md) | ORB 毒液悬浮球竞品复核 + Japlos 视频分析 + 音频点阵可视化开源方案（概览版） | 2026-10-24 | 新增 |
| [state-machine-thinking-research-20261024.md](state-machine-thinking-research-20261024.md) | 状态机细化 + 推理可视化（详细版：Friday 六态 / LiveKit 状态节拍 / Jarvis Orb / J-Space 三档路由） | 2026-10-24 | 新增 |
| [audio-visualizer-spec-research-20261024.md](audio-visualizer-spec-research-20261024.md) | 音频点阵/粒子可视化规格（详细版：LiveKit 五变体实现 / particle-core 参数 / 可执行拆解） | 2026-10-24 | 新增 |
| [desktop-companion-research-20261024.md](desktop-companion-research-20261024.md) | 桌面女友/桌宠养成（详细版：WarmSoul 双层情感 / Soul of Waifu 神经递质 / tama96 养成模型 / Open-LLM-VTuber） | 2026-10-24 | 新增 |
| [ar-vr-hud-research-20261024.md](ar-vr-hud-research-20261024.md) | AR/VR/HUD 多端形态（详细版：Open-Jarvis 全设备架构 / Clawdia 全息 / Xiora MR / Milo 双模式 + L0-L4 分层模型） | 2026-10-24 | 新增 |
| [robotics-embodied-research-20261024.md](robotics-embodied-research-20261024.md) | 机器人/具身智能（详细版：OpenGo 机器狗 / Unitree Go2 MCP / 人形基础模型 / 接入路线） | 2026-10-24 | 新增 |
| [agent-loop-param-benchmark-20261025.md](agent-loop-param-benchmark-20261025.md) | Agent 项目对照拆解（参数级）：Japlos 视频任务逻辑/UIUX 拆解 + OpenJarvis 源码设计参数（OrchestratorAgent / AgentTemplate / Skills 管道 / held-out 验收）；结论=四个结构性缺口 | 2026-10-25 | 新增 |
| [openjarvis-base-adoption-20261025.md](openjarvis-base-adoption-20261025.md) | OpenJarvis 底座采纳调研（拿来即用原则）：五原语事实基线 / 与 L1-L10 映射 / 缺口六方向可拔插模块清单（NeMo·OpenShell·Mem0·Letta·LangGraph·Dapr 等）/ 底座偏移评估 / 执行原则 | 2026-10-25 | 新增 |
| [venom-symbiote-research-20261025.md](venom-symbiote-research-20261025.md) | 毒液形态深度调研（四方向整合）：开源 shader 参数（5 项已查证源码）/ Web 黑液通用参数栈 / 电影 VFX 形态特征清单（7 特征 + 能力）/ 桌面场景应用盘点 / 标志性特征→可落地参数对照 / crazygl→真毒液 shader 改造清单（参数 patch + 三类自研结构） | 2026-10-25 | 新增 |
| [orb-transparent-window-research-20261026.md](orb-transparent-window-research-20261026.md) | 悬浮球透明无壳窗口开源实现：WinUI3+WebView2 透明=官方不支持（Issue #2992 实证）/ 7 条透明技术路线对比 / 11 个开源项目清单（VPet·BongoCat·OpenPets·BlurWindow 等）/ 可复用窗口管理参数（置顶·点透·拖拽·任务栏·z-order 循环·hover 半透明）/ 球体渲染工程化（D3D11 离屏→ULW 首选）/ 建议路线 1-2 天 | 2026-10-26 | 新增 |
| [dsh-pet-research-20261026.md](dsh-pet-research-20261026.md) | 大肥鱼桌宠开源生态调研（DeepSeek Harness dsh-pet）：动画链权重调度/事件档位候选防连播/纯函数物理层（过阻尼弹簧+抛物线甩抛+反弹+Q弹）/Agent 事件联动状态机（思考·工作·整理·等待·成功·出错）/HTTP 对外接口驱动（插件总线落地形态）/素材生产管线三件套+pet pack/双显示位；借鉴结论 6 项+不采纳 2 项 | 2026-10-26 | 新增 |
| [agent-capability-benchmark-20261026.md](agent-capability-benchmark-20261026.md) | 能力对标基准（白龙马加 Pro/11 产品×10 维度横向）：产品功能对比 + 鸡肋功能判定 + 向贾维斯靠拢的能力缺口 | 2026-10-26 | 新增（补登记） |
| [grok-bot-orb-reconstructed-20261027.md](grok-bot-orb-reconstructed-20261027.md) | Grok Bot 0.18 反编译仓库浮球组件源码拆解：纯 SVG+rAF 渲染 / 8 形状×11 色体系 / MOTION 状态机参数表（40+ 状态×4 参）/凝视·spin·bounce 交互 / 头像编辑器三模式 / 对照 orb 决策级差异 + 5 项可拔插借鉴点 | 2026-10-27 | 新增 |
| [grok-bot-codex-architecture-20261027.md](grok-bot-codex-architecture-20261027.md) | Grok Bot 0.18 反编译仓库整体架构 + Codex 接入源码拆解：推理路由器（四后端路由/串行队列/transcript 原子写）/ Codex 直连（Responses API SSE 流式 + function_call 工具循环 + usage）/ 路由 MCP 桥（只读判定注解）/ 抄入 Ultima Agent 方案要点（Codex 插件化落点与红线） | 2026-10-27 | 新增 |
| [bailongma-source-voice-audit-20261029.md](bailongma-source-voice-audit-20261029.md) | 白龙马源码语音模块审计（源码级）：ASR 5 云端+本地 Whisper（VAD+幻觉过滤）/ TTS 5 云端无本地无克隆 / KWS sherpa-onnx 独立子进程（阈值 0.35·score 3.0·6 变体"小白龙"）/ 语音策略层（连续对话+PTT 两模式）/ A-B 决策影响（借壳 A 补本地 TTS 缺口、换底座 B 语音链路重来） | 2026-10-29 | 新增 |
| [dsh-pet-source-audit-20261029.md](dsh-pet-source-audit-20261029.md) | dsh-pet（大肥鱼）源码模块审计（源码级）：动画权重掷骰+档位防连播 / 物理四族纯函数（弹簧·抛掷·挤压·碰撞参数全表）/ 六档工作状态机 / 11 领域 HTTP 路由+播放记录表 / 语音仅 TTS 半套（Edge-TTS 云端+串行队列+防双播）/ 余额 4 内置+第三方注册制 / 素材管线 9 脚本 / 桌面端看门狗；借鉴 10 项+不采纳 2 项 | 2026-10-29 | 新增 |
| [job-ai-skills-video-research-20261029.md](job-ai-skills-video-research-20261029.md) | 职业 AI 技能清单视频调研：8 类技能逐项核实（BrowserSkill 借真实登录态 / OmniVoice 零样本克隆 / WorkBuddy 表格 / HeyGen 数字人 / video-use 自动剪辑 / taste-skill 设计口味 / 电商 RPA AI+RPA 分工 / OfficeCLI 渲染查看修复闭环）+ 借鉴 8 项排序 + 现网 L0-L10 差距核对；暂不推进代码 | 2026-10-29 | 新增 |
| [capability-layer-classification-20261029.md](capability-layer-classification-20261029.md) | 调研能力三层归类（基础功能/插件/Skill）：判定标准表（常驻 vs 热插拔 vs 路由加载）+ 视频 8 类/大肥鱼/白龙马/开源对标逐项归类 + 跨层边界 7 项（语音/浏览器/表格/视频/文档/UI/状态机）+ 统计与推进含义；暂不推进代码 | 2026-10-29 | 新增 |
| [hud-window-ui-research-20261029.md](hud-window-ui-research-20261029.md) | 窗口化 HUD UI 调研（科幻/贾维斯风格）：完整开源 6 项（eDEX-UI 38.3k★ / spectre-ui / cyberpunk-ui token 级 1787 行 / jarvis-ui / Sci-Fi UI Astro / ratatui-sci-fi）+ 科幻 HUD 设计规范参数化（#020617 深空底 + cyan 辉光 + 四角括号 + 扫描线 + 毛玻璃）+ AR 眼镜侧 5 项（WIS / XRDesk / MentraOS / Android XR）+ UltimaAgent 落地取材路线；暂不推进代码 | 2026-10-29 | 新增 |
| [hud-source-audit-20261029.md](hud-source-audit-20261029.md) | HUD 开源源码审计（源码级，6 仓库已拉回 sources/）：eDEX-UI 17 class 布局 / spectre-ui recipes 划分 / cyberpunk-ui token+effects 全套参数（霓虹四色+辉光 12/30px+扫描线 2-3-4px+forced-colors）/ jarvis-ui OS 仿真组件 / astro-sci-fi-ui HudCorners 四角框 SVG 几何算法（stroke 内缩+bevel 切角）/ ratatui-sci-fi 81 组件+语义色板 9 字段；可直接抄入 5 项 + 不采纳 4 项 | 2026-10-29 | 新增 |
| [video-open-source-tools-20261115.md](video-open-source-tools-20261115.md) | 三个抖音视频开源工具登记：Astryx（React/StyleX 设计系统）/ blender-skills（94 个 Blender Agent Skills + Blender MCP）/ agency-agents（多角色专家与工作流资产）；含官方仓库对照和基础/插件/Skill 归类；仅记录，不接入 | 2026-11-15 | 新增 |

## 二、归档历史

| 日期 | 动作 |
|---|---|
| 2026-10-24 | 新建 `docs/research/` 目录；自 `docs/references/` 迁入 2 篇 GitHub 调研；新增 ORB 竞品复核调研；同步更新 4 处引用路径（capability-list / tech-decisions / theme-standard / competitor-matrix） |
| 2026-10-24 | 四轮调研统一落盘（v1.1）：新增 5 篇——状态机+推理可视化、音频点阵规格、桌面女友/养成、AR/VR/HUD、机器人/具身；同步更新 docs/README.md 目录职责（research 3→8 篇） |
| 2026-10-25 | Agent 对照拆解落盘（v1.2）：新增 1 篇——Japlos/OpenJarvis 参数级拆解（任务逻辑 + UIUX + 源码设计参数）；索引 8→9 篇 |
| 2026-10-25 | OpenJarvis 底座采纳调研落盘（v1.3）：新增 1 篇——五原语事实基线 + 可拔插模块清单 + 底座偏移评估；索引 9→10 篇 |
| 2026-10-25 | 毒液形态深度调研落盘（v1.4）：新增 1 篇——四方向整合（开源 shader / Web 前端 / 电影 VFX / 桌面场景）+ 标志性特征参数对照 + crazygl 结构级改造清单；索引 10→11 篇 |
| 2026-10-26 | 悬浮球透明无壳窗口调研落盘（v1.5）：新增 1 篇——透明技术路线 7 条对比 + 11 个开源项目 + 窗口管理参数 + 渲染工程化方案；索引 11→12 篇 |
| 2026-10-26 | 大肥鱼桌宠生态调研落盘（v1.6）：新增 1 篇——dsh-pet 动画/物理/事件联动/接口/素材管线 + 对毒液球与插件总线的借鉴结论；索引 12→13 篇 |
| 2026-10-27 | Grok Bot 浮球反编译拆解落盘（v1.7）：新增 1 篇——纯 SVG+rAF 渲染 / MOTION 状态机参数表 / 对照 orb 可拔插借鉴点；顺带补登记能力对标基准 1 篇；索引 13→15 篇 |
| 2026-10-27 | Grok Bot 整体架构 + Codex 接入拆解落盘（v1.8）：新增 1 篇——推理路由器 / Codex 直连（Responses API 工具循环）/ 路由 MCP 桥 / 抄入方案要点；索引 15→16 篇 |
| 2026-10-29 | 白龙马源码语音模块审计落盘（v1.9）：新增 1 篇——ASR/TTS/KWS 三件套完整度盘点 + 语音策略层 + A/B 决策影响；索引 16→17 篇 |
| 2026-10-29 | dsh-pet 大肥鱼源码模块审计落盘（v1.10）：新增 1 篇——七域模块源码级盘点（动画/物理/事件/HTTP/语音/余额/素材管线）+ 借鉴 10 项；索引 17→18 篇 |
| 2026-10-29 | 职业 AI 技能视频调研落盘（v1.11）：新增 1 篇——8 类技能核实 + 借鉴 8 项排序 + 现网差距核对；索引 18→19 篇 |
| 2026-10-29 | 调研能力三层归类落盘（v1.12）：新增 1 篇——基础/插件/Skill 判定标准 + 视频 8 类/大肥鱼/白龙马/开源对标逐项归类 + 跨层边界；索引 19→20 篇 |
| 2026-10-29 | 窗口化 HUD UI 调研落盘（v1.13）：新增 1 篇——科幻 HUD 开源 6 项 + 设计参数化 + AR 眼镜侧 5 项 + 落地取材路线；索引 20→21 篇 |
| 2026-10-29 | HUD 开源源码审计落盘（v1.14）：新增 1 篇——6 仓库已拉回 sources/ 并做源码级审计（结构/token/组件/色板）+ 可直接抄入 5 项；索引 21→22 篇 |
| 2026-11-15 | 三个视频开源工具登记落盘（v1.15）：新增 1 篇——Astryx / blender-skills / agency-agents 的代码名称、官方仓库、类型与三层归类；索引 22→23 篇；仅记录，不接入 |

## 三、后续调研方向（待讨论登记）

> 用户规划：先扩调研方向 → 多轮调研 → 形成具体方案 → 再生成工单卡 → 加入工单序列。此表登记候选方向，不占工单号。

| 方向 | 关注点 | 状态 |
|---|---|---|
| 多端形态架构方案 | L0-L4 分层 + 形态配置层（soul.md 式）设计 | 已纳入方案（form-expansion-plan 阶段三） |
| 羁绊系统规格 | 关系记忆 + 距离档位（默认专业/可选亲密） | 已纳入方案（阶段二） |
| 主动性行为模型 | 神经递质式自主行为（何时主动说话/表达） | 讨论中（轻量版，不做深度模拟） |
| 情绪识别→形态映射 | 28 情绪 → 形态参数映射表 | 讨论中 |
| 性格演化 | 周级反思/性格渐变（暂缓评估） | 讨论中 |
| 机械形态接入 | OpenGo 技能库+调度器模式落地评估 | 已纳入方案（阶段四，远期） |
