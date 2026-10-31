# UltimaAgent HUD · 带动效天气元素收集与组件化方案

- 版本：v0.1 ｜ 日期：2026-10-31
- 上游：Owner 指示（"收集一套带动效的天气元素，做成组件形式，以后以组件调用"；参考图视觉气质=深蓝+霓虹蓝紫光效、气泡浮窗、无背景卡）
- 落地形态：Meteocons 动画天气 SVG → HUD 项目资产 → 组件化（对接 react-bits 按需取用模式）

---

## 一、选型结论

| 候选 | 说明 | 结论 |
|---|---|---|
| **Meteocons Monochrome 版**（`@meteocons/svg@0.1.0/monochrome/`） | 500+ 手绘动画天气图标；4 风格（Fill/Flat/Line/**Monochrome**）；2 输出（动画 SVG / Lottie JSON）；**MIT 可商用**；**Monochrome 版零硬编码颜色（继承父级 fill/stroke），可任意染色适配科幻风** | ✅ **选用** |
| Meteocons Fill/Line 版 | 自带暖色/彩色（琥珀黄太阳、宝蓝天、浅蓝雪） | ❌ 不符科幻风（卡通感、高饱和、暖色） |
| weather-animations（npm） | Canvas 驱动天气背景 + duotone SVG 图标（20 条件） | 备选（背景场景用） |
| weather-icons-animated（npm） | React + emotion 动画图标（Home Assistant 生态） | 不选（引 React 运行时，违反原生落地原则） |
| QWeather Icons（MIT 507） | 另一套 MIT 天气图标集 | 备选（需要更多条件时扩充） |

**选型理由**：Monochrome 版满足全部约束——①带动画（SVG 内嵌 `<animate>`，零依赖零运行时）；②MIT 可商用；③**零硬编码色值**，可统一染成 cyan 辉光色系（深空 #020617 底 + #22d3ee/#67e8f9 辉光），**完美契合 Ultima 科幻风 UI 哲学**；④CDN/npm 可直取、可本地化；⑤图标覆盖面全（晴/多云/雨/雪/雷暴/雾/霾/尘/冰雹/月相/风向/湿度/UV 等 140+）。

> 注：初版曾取 Fill 风格（暖色扁平卡通），经 Owner 质询配色后发现不符科幻风，已**全部替换为 Monochrome 版**（v0.1→修正）。

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

### 3.1 核心天气（6）

| 文件 | 条件 | 大小 | 动画校验 | 配色 |
|---|---|---|---|---|
| clear-day.svg | 晴（白天） | 1898 B | ✅（太阳辉光旋转） | 继承父级（可染 cyan） |
| partly-cloudy-day.svg | 多云（白天） | 5448 B | ✅（云飘移） | 继承父级（可染 cyan） |
| rain.svg | 雨 | 3009 B | ✅（雨滴下落） | 继承父级（可染 cyan） |
| snow.svg | 雪 | 10448 B | ✅（雪花飘落） | 继承父级（可染 cyan） |
| thunderstorms.svg | 雷暴 | 2097 B | ✅（闪电闪烁） | 继承父级（可染 cyan） |
| fog.svg | 雾 | 2401 B | ✅（雾气流动） | 继承父级（可染 cyan） |

### 3.2 降水/风雪细分（雨量分级 + 复合条件）

| 图标 | 语义 | 覆盖场景 |
|---|---|---|
| drizzle.svg | 毛毛雨 | 小雨（最弱降水） |
| rain.svg | 雨 | 中雨（默认雨） |
| extreme-rain.svg | 极端降雨 | **暴雨/大雨**（最强降水） |
| partly-cloudy-day-rain.svg | 阵雨（多云日） | 间歇性降雨 |
| partly-cloudy-day-drizzle.svg | 毛毛雨（多云日） | 阴天小雨 |
| sleet.svg | 雨夹雪 | 冬季混合降水 |
| hail.svg | 冰雹 | 强对流冰雹 |
| partly-cloudy-day-snow.svg | 阵雪（多云日） | 间歇性降雪 |
| thunderstorms-rain.svg | 雷阵雨 | 雷暴+雨 |
| thunderstorms-day-rain.svg | 雷阵雨（白天） | 日间雷雨 |

> 分级口径：Meteocons 用条件名分级（drizzle=小雨 → rain=中雨 → extreme-rain=暴雨），组件映射时可按此三档细分。

### 3.3 昼夜/天空状态（8）

clear-night / partly-cloudy-night / cloudy / overcast / thunderstorms-day / thunderstorms-night / haze / mist / dust / smoke（共 10）

来源：jsDelivr `@meteocons/svg@0.1.0/monochrome/<condition>.svg`（MIT）。**Monochrome 版无硬编码色值**，SVG 根 `fill="none"`、路径继承父级颜色——CSS 侧统一 `fill`/`stroke` 即可染成 cyan 辉光色系（建议 #22d3ee 主色 / #67e8f9 高光 / #0ea5e9 次色）。

**扩充清单（后续需要再补）**：moon-*（8 月相）、wind、humidity、uv-index、barometer、compass、sunrise/sunset、thermometer-*、tornado、hurricane、falling-stars、starry-night、pressure-* 等（完整 140+ 见 Meteocons 目录，同样取 monochrome 版）。

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
5. ✅ **风格修正：Fill 版（暖色卡通）→ Monochrome 版（零硬编码色值，可染 cyan 辉光）**——经 Owner 质询配色后替换，符合深空 #020617 + cyan 辉光科幻风（2026-10-31）。
