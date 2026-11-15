# 三个抖音视频开源工具登记（Astryx / blender-skills / agency-agents）

- **版本**：v1.0 · 2026-11-15
- **性质**：视频线索与官方仓库对照调研；只登记代码名称、类型和 UltimaAgent 三层归类，**暂不安装、接入或修改代码**
- **覆盖范围**：用户指定的三个视频各登记一个标题主线工具；第一条视频还提及其他项目，但不在本次扩项登记
- **核对方式**：抖音视频正文/页面描述用于定位，GitHub 官方仓库 README 用于复核代码名称与类型；星级等动态数字不作为本记录事实基线

## 一、登记总表

| 视频 | 代码名称 / 官方仓库 | 开源工具类型 | UltimaAgent 归类 | 本轮状态 |
|---|---|---|---|---|
| 老萨：Meta 用了 8 年的设计系统 | **Astryx** · [meta/astryx](https://github.com/meta/astryx) | React 19+ / StyleX 设计系统；包含可访问组件、主题、模板与 CLI | **基础功能参考（UI 组件与设计规则层）**；agent-ready 文档和 CLI 可作为 eng.ui Skill 的外部参考，不等同于已接入 Skill | 仅记录 |
| 青青王-AI：94 个 Blender 技能 | **blender-skills** · [arjun988/blender-skills](https://github.com/arjun988/blender-skills) | 面向 Cursor、Claude Code、Kiro、Codex 的 94 个 Blender 专项 Agent Skills；经 Blender MCP 执行建模与生产流程 | **Skill（blender-director 与 94 个领域技能）+ 插件（Blender MCP 执行通道）** | 仅记录 |
| 哈工大 AI 工程师 Peter：一个工具等于专家团队 | **agency-agents** · [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) | 多角色 AI 专家定义与团队工作流资产；覆盖工程、设计、市场等岗位，并提供多工具安装器与桌面 App | **Skill（专家角色、交付标准与协作流程资产）**；外部安装器/桌面 App 仅作分发形态参考，不归为 Ultima 插件 | 仅记录 |

## 二、来源与类型证据

### 1. Astryx

- **视频来源**：https://v.douyin.com/gfisycQ_cMw/
- **视频定位**：标题主线为 Meta 内部使用 8 年的设计系统；视频正文提到组件、主题以及面向人和 Agent 的说明/工具。
- **官方仓库**：https://github.com/meta/astryx （旧地址 `facebook/astryx` 会跳转到 `meta/astryx`）
- **官方说明**：https://astryx.atmeta.com/blog/introducing-astryx
- **类型确认**：开源设计系统与 React 组件库，基于 React 19+ 和 StyleX，包含组件、主题、模板及 CLI；当前官方标记 Beta，MIT 许可。
- **归类边界**：它是 UI 组件/设计系统，不因带有 Agent 文档就直接归为 Ultima Skill；对 Ultima 的价值是 UI 规则、组件实现和 eng.ui 外部参考。

### 2. blender-skills

- **视频来源**：https://v.douyin.com/iecBM8Sy9Fw/ （解析后的视频 ID：`7706953664280091514`）
- **视频定位**：标题明确为“94 个 Blender 技能让 Agent 秒变游戏美术团队”。
- **官方仓库**：https://github.com/arjun988/blender-skills
- **类型确认**：官方 README 明确为 **94 Specialized Skills for Blender Artists**，由 `blender-director` 路由建模、材质、灯光、绑定、导出等专项技能，并通过 Blender MCP 在 Blender 中执行；MIT 许可。
- **归类边界**：94 个领域工作流属于 Skill；Blender MCP 是执行通道，按 ADR-011 归插件/外部工具适配层。本轮不复制技能包、不安装 MCP。

### 3. agency-agents

- **视频来源**：https://v.douyin.com/L6P-rHyB-HU/ （解析后的视频 ID：`7698348004461382921`）
- **视频定位**：页面描述明确给出工具名 **Agency Agents**，主线是把一套 AI 专家团队装进常用 AI 工具。
- **官方仓库**：https://github.com/msitarzewski/agency-agents
- **类型确认**：官方 README 描述为专用 AI agent personalities、工作流程和可衡量交付物集合，覆盖多个职能部门，并提供 Claude Code、Cursor、Codex 等工具的转换/安装脚本与桌面 App；MIT 许可。
- **归类边界**：专家身份、岗位知识、工作流程与成功指标属于 Skill 资产；安装器和桌面 App 是外部分发工具，本轮不据此新增 Ultima 插件或执行通道。

## 三、调研边界

1. 本条只完成**名称、类型、来源和分层登记**，不代表选型通过、接入完成或能力已具备。
2. 未克隆、安装或运行上述仓库，未修改 Skill Registry、插件注册表、工单状态或产品代码。
3. 后续若要采用，应分别另行完成源码/License/安全审计、与现网 A2UI 与 eng.ui 的重叠分析、Blender MCP 隔离评估，以及 agency-agents 与现有角色技能路由的查重。
