# Manager + Console 组合方案 manager-console-combined-plan-20261031

> 版本：v0.1 ｜ 状态：方向定稿（Owner 拍板） ｜ 日期：2026-10-31
> 依据：Owner 选型讨论拍板（Manager=内核/路由层、Console=监督展示层、互补组合=UltimaAgent 任务管理器）+ G-PERSIST-001 每次沟通提炼落盘
> 上位范式：G-TASKFLOW-001（任务工作流）、G-DISPATCH-001（自主派发）、G-PLAN-001（先方案后工单）
> 关联：`H:\UltimaAI\UltimaManager\docs\architecture.md`（Manager 架构）、`H:\UltimaAI\UltimaConsole\docs\产品策划方案-REQ-CONSOLE-001.md`（Console v0.3 方向）、`docs\previews\hud-layout-zone-plan-20261031.md`（HUD 8 锚点定稿）

---

## 一、定位结论（Owner 拍板）

**UltimaAgent 任务管理器 = Manager（内核/路由层）+ Console（监督展示层）互补组合，生成全新能力应用。**

| 组件 | 层 | 职责 | 不可替代性 |
|---|---|---|---|
| **UltimaManager** | 内核/路由层 | 任务路由、准入、状态跟踪、独立审计、回执核验、队列（manager.db + 18766 服务） | 任务怎么流转、谁执行、怎么验收——能力内核 |
| **UltimaConsole** | 监督展示层 | 任务/状态/队列的监督呈现（Windows HUD 8 锚点方向，v0.3 已定稿） | 状态怎么看得见、怎么交互——展示外壳 |

**选型判据回顾**：Manager 是"任务管理器的基础能力模块（或路由）"的主体——任务从登记→派发→执行→审计→验收→冻结的全流程由 Manager 内核承载；Console 不重复实现路由/内核，只做监督展示层。两者互补而非竞争。

---

## 二、组合架构（示意）

```
┌─────────────────────────────────────────────────┐
│              UltimaAgent 任务管理器               │
│                                                 │
│  ┌───────────────┐        ┌──────────────────┐  │
│  │  UltimaManager │        │   UltimaConsole  │  │
│  │  （内核/路由）  │        │  （监督展示层）    │  │
│  │                │        │                  │  │
│  │ · 任务队列/路由 │◄─18766─►│ · HUD 8 锚点显示  │  │
│  │ · 准入/状态     │  只读   │ · 当前任务/状态    │  │
│  │ · 独立审计/回执 │        │ · 队列简况        │  │
│  │ · manager.db   │        │ · Agent 反馈区    │  │
│  └───────────────┘        └──────────────────┘  │
│                                                 │
│  （Agent 侧 SSE 8756 事件流 = 状态/进度数据源）      │
└─────────────────────────────────────────────────┘
```

**接线原则**：Console/HUD 只读 Manager 状态（18766 任务状态只读 API），不做写操作、不复制内核逻辑；Manager 不内嵌展示层，只管状态与路由。两者通过既有服务边界耦合。

---

## 三、与 HUD 8 锚点的衔接

HUD 四角壳 8 锚点（方案 `docs/previews/hud-layout-zone-plan-20261031.md` v0.2 定稿）作为 Console 监督展示的落地产物：

| HUD 锚位 | 数据来源 | 说明 |
|---|---|---|
| 左下·任务队列简况 | Manager 18766 任务状态只读 | 队列空即隐 |
| 左中·Agent 反馈区 | Manager 任务状态 + Agent 主动推送 | 日程/通知/临期/告警 |
| 左上·系统状态 | agent_server tick | 硬件/连接/上下行 |
| 顶部·时间天气 | 系统时钟 + weather.query | 高频常用 |

组合后的任务管理器：内核（Manager）管"事"，HUD（Console 展示层）管"看见"，Agent 北极星管"人机交互"。

---

## 四、已拍板项清单

- [x] ① Manager = 内核/路由层（任务流转/准入/审计），Console = 监督展示层（呈现/交互），互补组合（2026-10-31）
- [x] ② 组合目标 = UltimaAgent 任务管理器（全新能力应用，非简单合并）（2026-10-31）
- [x] ③ Console 不做 Windows 原生端、不做鸿蒙端，展示层 = HUD 8 锚点方向（2026-10-31，已同步 Console v0.3）
- [x] ④ HUD 只读 Manager 18766，不写不改内核（2026-10-31，已进工单 0011 写域）
- [x] ⑤ 审批口径：过程 0 审批（AI 主动思考/修正/优化），最终交付一道审批；HUD 永不显示审批/签名（2026-10-31）

---

## 五、落地路径（后续工单规划）

| 序号 | 方向 | 前置 | 说明 |
|---|---|---|---|
| 1 | Manager 内核可用性修复 | 已完成 | completed 白名单修复（fix-20261031-registry-completed-state.md，commit 5c16f9e） |
| 2 | HUD 8 锚点布局改造 | 进行中 | 工单 0011（T0-T3，Codex 执行中），接 Manager 18766 只读 |
| 3 | 组合联调 | 0011 验收通过 | HUD × Manager 状态链路端到端验证（任务显示/队列/反馈区） |
| 4 | 全息人物内容层增强 | 组合联调后 | 方案 `docs/previews/hologram-avatar-plan-20261031.md`（三态 + 成熟方案拼装） |

> 注：以上为方向规划，正式工单按 G-PLAN-001 逐项落盘派发。
