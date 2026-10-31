# HUD 鼠标穿透改造方案 hud-clickthrough-zone-plan-20261031

> 版本：v0.1 ｜ 状态：讨论定稿（待派工单） ｜ 日期：2026-10-31
> 依据：Owner 讨论（2026-10-31）：Windows 桌面 HUD 穿透交互缺陷 + 成熟解法 WM_NCHITTEST 区域级命中
> 关联：`docs/previews/hud-layout-zone-plan-20261031.md`（8 锚点布局 v0.2 定稿）、`docs/previews/hologram-avatar-plan-20261031.md`、工单 0011（HUD 8 锚点改造，禁项=不动原生壳）

---

## 一、问题描述（Owner 原话级）

Windows 桌面四角壳 HUD 的鼠标穿透是**窗口级布尔开关**（托盘"鼠标穿透"勾选）：

1. **勾选穿透**：整窗穿透——四角壳锚位也点不了，鼠标直接点到桌面图标；
2. **取消穿透**：整窗可交互——四角壳可拖动操作，但透明区域也不再穿透，点不到桌面图标，**连任务栏状态也点不了**，如同进入全屏拦截状态，只能切窗口关闭才能恢复。

**本质缺陷**：做不到"锚位可点 + 中央透传"共存，与 8 锚点 HUD 的"中央永远透传（0 遮挡 0 信息）"设计原则冲突。

---

## 二、根因（代码已定位）

- `src/host-shell/UltimaAgent.Hud/Native.cs`：`MakeClickThrough(hwnd, enabled)` 切换窗口扩展样式 `WS_EX_TRANSPARENT`（0x00000020）+ `WS_EX_LAYERED`；
- `HudWindow.xaml.cs`：`SetClickThrough(bool)` 调 `Native.MakeClickThrough`；
- `TrayManager.cs`：托盘菜单"鼠标穿透"勾选状态驱动 `SetClickThrough`。

**Windows 机制天花板**：`WS_EX_TRANSPARENT` 是窗口级样式，只有"整窗穿透/整窗拦截"两态，**不存在窗口级第三种状态**——透明区与锚位区的差异化点击只能靠区域级命中测试实现。

---

## 三、成熟解法：区域级 WM_NCHITTEST 局部穿透（不自研机制）

桌面小组件/屏幕取词/悬浮球的通用标准做法：

| 环节 | 做法 |
|---|---|
| 命中判定 | 窗口**不依赖** WS_EX_TRANSPARENT；在 WndProc 处理 **WM_NCHITTEST**，按鼠标屏幕坐标判定 |
| 锚位区 | 坐标落在 8 锚位 widget 包围盒内 → 返回 **HTCLIENT**（可交互：点击/拖动/悬停） |
| 中央/透明区 | 其余坐标 → 返回 **HTTRANSPARENT**（穿透，点击落到桌面图标/任务栏/下层窗口） |
| 区域表来源 | JS 侧把各 widget 实际 DOM 矩形经 WebView2 host object 上报原生壳；原生壳维护"可点击区域表"（锚位显隐变化时增量更新） |
| 总控开关 | 托盘"鼠标穿透"保留为总控：安全模式/AR 移动场景一键全穿透（恢复窗口级 WS_EX_TRANSPARENT），静止场景默认区域级局部穿透 |

**预期效果**：8 锚位（四角/顶/底/左右中）随时可点；中央永远透传——桌面图标、任务栏、下层窗口全部可正常操作；不再出现"全屏拦截死锁"。

---

## 四、改动范围与边界

**写域**：
- `src/host-shell/UltimaAgent.Hud/Native.cs`（新增 WM_NCHITTEST 区域命中支持，保留 WS_EX_TRANSPARENT 总控）
- `src/host-shell/UltimaAgent.Hud/HudWindow.xaml.cs`（WndProc 接入 + 区域表维护）
- `src/host-shell/UltimaAgent.Hud/TrayManager.cs`（穿透开关语义=总控，默认档位调整）
- HUD HTML 侧：widget 矩形上报（hud-live-four-corner.html 的 JS 桥，0011 改造后接入）

**禁止**：不动 Manager 内核 / agent_server 结构路由 / 8 锚点布局结构 / 全息人物资产。

**依赖**：前置=工单 0011（8 锚点布局改造）验收通过——0011 禁项=不动原生壳，本工单写域在原生壳，二者串行。

---

## 五、验收要点（候选，派单时定稿）

- [ ] 勾选总控穿透=整窗穿透（安全模式）恢复现状①
- [ ] 默认档=区域级：8 锚位可点击/拖动，中央透传区点得到桌面图标与任务栏
- [ ] 锚位显隐变化（如队列空隐）后区域表实时更新，无残留可点区域
- [ ] 无新增全屏拦截死锁路径

---

## 六、已拍板项

- [x] ① 目标态=8 锚位可点 + 中央永远透传 + 桌面/任务栏可操作（2026-10-31）
- [x] ② 解法=区域级 WM_NCHITTEST（成熟标准做法，非自研机制）（2026-10-31）
- [x] ③ 托盘穿透开关保留为总控（安全模式一键全穿透）（2026-10-31）
- [ ] ④ 工单排期（待 0011 验收后派发，按 G-PLAN-001 落盘）
