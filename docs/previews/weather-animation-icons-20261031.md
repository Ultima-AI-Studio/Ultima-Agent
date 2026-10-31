# UltimaAgent HUD · 带动效天气元素收集与组件化方案

- 版本：v0.1 ｜ 日期：2026-10-31
- 上游：Owner 指示（"收集一套带动效的天气元素，做成组件形式，以后以组件调用"；参考图视觉气质=深蓝+霓虹蓝紫光效、气泡浮窗、无背景卡）
- 落地形态：Meteocons 动画天气 SVG → HUD 项目资产 → 组件化（对接 react-bits 按需取用模式）

---

## 一、选型结论

| 候选 | 说明 | 结论 |
|---|---|---|
| **Meteocons**（Bas Milius） | 500+ 手绘动画天气图标；4 风格（Fill/Flat/Line/Monochrome）；2 输出（动画 SVG / Lottie JSON）；**MIT 可商用**；npm `@meteocons/svg`/`@meteocons/lottie`；旧版包 `@bybas/weather-icons@2.0.0` jsDelivr CDN 直取 | ✅ **选用** |
| weather-animations（npm） | Canvas 驱动天气背景 + duotone SVG 图标（20 条件） | 备选（背景场景用） |
| weather-icons-animated（npm） | React + emotion 动画图标（Home Assistant 生态） | 不选（引 React 运行时，违反原生落地原则） |
| QWeather Icons（MIT 507） | 另一套 MIT 天气图标集 | 备选（需要更多条件时扩充） |

**选型理由**：Meteocons 满足全部约束——①带动画（SVG 内嵌 `<animate>`，零依赖零运行时）；②MIT 可商用；③4 风格适配 HUD 透明深色底（**Monochrome 单色最适合 cyan 辉光哲学**）；④CDN/npm 可直取、可本地化；⑤图标覆盖面全（晴/多云/雨/雪/雷暴/雾/霾/尘/冰雹/月相/风向/湿度/UV 等 140+）。

## 二、组件化路径（对接 react-bits 模式）

1. **收集**：核心天气条件 SVG 下载至 HUD 项目资产目录（已做，见 §三）。
2. **组件封装**：按 react-bits 适配原则——原生落地、单文件自包含、不引 React 运行时。封装为 `weather-widget` 组件（HTML/CSS/SVG 内联）：
   - 天气气泡（右上角锚位）：图标 + 城市 + 当前温度 + 高低温 + 天气描述（无背景卡片，浮窗/气泡形态）
   - 迷你天气（顶部时间区承接态）：仅图标 + 温度（导航互斥迁入时）
   - 一周预报行：5 日图标 + 高温/低温（紧凑单行，参考图气质）
3. **动效规格**：SVG 自带动画（太阳旋转/云飘移/雨滴下落等）；组件级过渡 150-300ms；`prefers-reduced-motion: reduce` 时静止显示终态（react-bits 降级原则）。
4. **接入点**：右上角=天气常驻位（单功能互斥切换）；顶部=迷你天气承接位；均无背景卡、气泡/浮窗形态。
5. **数据**：weather.query 工具已有（agent_server），组件只做展示层，不接真实天气源（真实接入属后续工单）。

## 三、已收集资产（2026-10-31）

存放：`H:\UltimaAI\UltimaAgent\docs\previews\hud-live-four-corner\assets\weather\`

| 文件 | 条件 | 大小 | 动画校验 |
|---|---|---|---|
| clear-day.svg | 晴（白天） | 783 B | ✅（太阳辉光旋转） |
| partly-cloudy-day.svg | 多云（白天） | 1237 B | ✅（云飘移） |
| rain.svg | 雨 | 2048 B | ✅（雨滴下落） |
| snow.svg | 雪 | 3201 B | ✅（雪花飘落） |
| thunderstorms.svg | 雷暴 | 1024 B | ✅（闪电闪烁） |
| fog.svg | 雾 | 1373 B | ✅（雾气流动） |

来源：jsDelivr `@bybas/weather-icons@2.0.0/production/fill/all/<condition>.svg`（MIT）。当前采用 **Fill 风格**；后续如需 cyan 单色辉光可切换 Monochrome 风格（`@meteocons/svg` 提供）。

**扩充清单（随时可补）**：clear-night、partly-cloudy-night、overcast、drizzle、sleet、hail、haze、dust、smoke、mist、tornado、hurricane、moon-*（月相）、wind、humidity、uv-index、barometer、compass、sunrise/sunset、thermometer-* 等（完整 140+ 见 Meteocons 目录）。

## 四、落地工单规划（G-PLAN-001）

- **前置**：工单 0011（8 锚点布局改造）验收通过（002 冻结门依赖 0011 验收，避免写域冲突——0011 正在改 hud-live-four-corner.html）。
- **组件工单（待派发）**：
  - 写域：`docs/previews/hud-live-four-corner/assets/weather/` + `hud-live-four-corner.html`（组件封装）+ 阶段报告
  - 任务：①封装 weather-widget 组件（气泡形态、无背景卡、SVG 内联动效）②迷你天气承接态 ③一周预报行 ④prefers-reduced-motion 降级 ⑤验收=右上角/顶部锚位视觉符合形态基线
  - 推理强度：medium（UI 组件落地）
- **后续扩展工单**：真实天气数据接入（weather.query → 组件数据源）；Lottie 版（AR 端预留，如需原生 App 端）。

---

## 五、已拍板项

1. ✅ 选型 Meteocons（MIT、带动画 SVG、4 风格、CDN 直取）作为 HUD 天气动效元素源。
2. ✅ 只取气泡/浮窗元素，无背景卡片（沿用布局方案 v0.5 视觉样式提炼结论）。
3. ✅ 组件化=react-bits 模式（原生落地、自包含、不引 React 运行时、动效可降级）。
4. ✅ 首批 6 个核心天气图标已收集入 HUD 资产目录（已校验带动画）。
