# 工单 wo-ultimaagent-20261031-0012 ｜ UltimaAgent ｜ 工程 ｜ HUD 天气组件接入（官方 Meteocons 动画图标 + cyan 辉光）

> 原单 ID：`wo-ultimaagent-20261031-0012` ｜ 显示标题：UltimaAgent｜工程｜HUD 天气组件接入
> 依据：G-DISPATCH-001 自主推进版（2026-10-28 用户拍板）｜ 上位工作流 G-TASKFLOW-001 ｜ G-PLAN-001 先方案后工单
> 方案依据：`docs/previews/weather-animation-icons-20261031.md`（v0.1，Meteocons Monochrome 选型 + 25 图标入库，commit 8ae54fc）｜ 布局依据：`docs/previews/hud-layout-zone-plan-20261031.md` v0.5（顶部=时间+天气）｜ 范式：`docs/paradigms/ui-kit-standard.md` §8
> 用户拍板：2026-10-31 "带动效天气元素收集成组件，以后以组件调用；手绘/文本占位必须替换为官方图标；下派由 Codex 执行"
> 北极星：贾维斯（全屏幕统一范式，天气组件跨端复用）
> 前置：0011 已收口（tag `ultimaagent-hud-8anchor-20261031` = 5cdfca3，全局主表 completed）
> 创建：2026-10-31 ｜ 状态：待派发

---

## 一、目标与范围

### 1.1 目标（Result）

将 HUD 顶部天气显示从**纯文本占位**（当前 `#hud-weather` 显示"天气待命"）升级为**官方 Meteocons Monochrome 动画图标 + 文本的天气组件**，实现：
1. **天气组件接入**：顶部锚位天气区 = 官方动画天气 SVG（来自 `assets/weather/`，25 个 Monochrome 图标按条件名映射）+ 天气文本（如"晴 24°"）。
2. **组件形态**：无背景卡片、气泡/浮窗气质（沿用布局方案视觉基线：深空 #020617 + cyan 辉光 + 四角括号 + 扫描线）；SVG 染 cyan 辉光色系（主 #22d3ee / 高光 #67e8f9 / 次 #0ea5e9）。
3. **映射表**：内置天气条件 → 图标文件名映射（rain→rain.svg、drizzle→drizzle.svg、extreme-rain→extreme-rain.svg 等，至少覆盖已入库 25 个中的降水细分：drizzle/rain/extreme-rain/partly-cloudy-day-rain/thunderstorms-rain/sleet/hail/snow 等），未知条件回退 `clear-day.svg`。
4. **接入点**：SSE 8756 `weather.query` 工具结果（现有事件已映射顶部天气，见 0011 报告 §3.1）→ 驱动图标+文本更新；无天气数据时显示占位文本（无图标）。
5. **动效降级**：`prefers-reduced-motion: reduce` 时 SVG 动画静止显示终态（react-bits 适配原则）。

**验收即边界**：验收清单见 §四，全绿即完成，禁止就地追加需求。

### 1.2 范围冻结（边界，禁止越界）

- **只做**：`hud-live-four-corner.html` 顶部天气区组件化改造（图标映射 + cyan 染色 + 无背景卡）+ 截图证据 + 阶段报告。
- **禁止**：
  - 禁止改动 8 锚点布局结构、其他 7 个锚点内容（左上系统状态/右上环境/左中/右中/左下/右下/底部）；
  - 禁止改动四角括号/扫描线等装饰 SVG（`M1 14 V1 H14` L 形与 `M0 29 H340` 扫描线属设计 token，不在本单范围）；
  - 禁止真实天气数据接入（调外部天气 API/联网抓取——weather.query 真实数据源为后续工单；本单只消费现有 SSE 事件的模拟/占位数据流）；
  - 禁止改动 `agent_server.py`、`UltimaAgent.Hud` 原生壳、Manager 18766、KWS/ASR/TTS 参数基线、voice_profile/daemon；
  - 禁止新增或删除 `assets/weather/` 下已有 25 个图标文件（只读引用；如需新增图标=另行工单）；
  - 禁止引入 React/Lottie 运行时（原生 SVG 内联落地，遵循 react-bits 适配原则）；
  - 禁止修改方案文档 `weather-animation-icons-20261031.md`（已入库，如需版本更新另走流程）。

### 1.3 写域（各 T 精确到文件）

| 文件 | 动作 | 说明 |
|---|---|---|
| `docs/previews/hud-live-four-corner/hud-live-four-corner.html` | 修改（主产物） | 仅顶部天气区（`#hud-weather` 及关联 CSS/JS） |
| `docs/previews/hud-live-four-corner/assets/weather/*.svg` | 只读 | 25 个官方 Monochrome 图标，引用不修改 |
| `docs/previews/hud-live-four-corner/_shots/` | 截图证据 | 改造前后截图（shot.py 复用） |
| `docs/reports/evidence/weather-component/` | 新建 | 证据目录 |
| `docs/reports/stage-weather-component-20261031.md` | 新建 | 阶段报告 |

---

## 二、DoR 就绪门（五项全绿）

| # | 就绪项 | 判定 | 证据 |
|---|---|---|---|
| 1 | 验收 Gate 可判定 | ✅ 封闭清单（§四） | HTML 结构/截图/映射/染色逐项可检 |
| 2 | 无未决依赖 | ✅ | 0011 已收口（tag 存在）；25 图标已入库；SSE 8756 天气事件已接线（0011 报告 §3.1） |
| 3 | 写入域已声明 | ✅ | §1.3 |
| 4 | 推理强度已声明 | ✅ | T0 medium / T1 medium / T2 medium / T3 low |
| 5 | 禁止项已写 | ✅ | §1.2 |

---

## 三、执行步骤（T0→T3，逐 T Gate PASS 再进下一条）

### T0 现状盘点与方案对齐（medium）

- [ ] C1 读方案：完整读取 `docs/previews/weather-animation-icons-20261031.md`（选型结论/组件化路径/25 图标清单/分级口径 drizzle=小雨→rain=中雨→extreme-rain=暴雨）与 `docs/paradigms/ui-kit-standard.md` §8。
- [ ] C2 读现状：完整读取 `docs/previews/hud-live-four-corner/hud-live-four-corner.html`，定位：①顶部锚点 `#hud-weather` 当前实现（文本占位）；②SSE 事件中 weather 相关处理函数（0011 已映射 `weather.query` → 顶部天气）；③现有 CSS 变量色板（--hd-* / cyan 系）。
- [ ] C3 资产盘点：确认 `assets/weather/` 下 25 个 SVG 存在且为 Monochrome（无硬编码色、含 `<animate>`）；任选 1 个（如 rain.svg）读取确认引用方式可行。
- [ ] C4 截图基线：shot.py 生成改造前截图存 `docs/reports/evidence/weather-component/t0-before-<ts>.png`。
- Gate：C1-C4 全绿 → 进 T1。

### T1 天气组件改造（medium）

- [ ] C1 图标引入：将天气 SVG 以**内联方式**接入天气区（inline SVG 保证动画与染色生效；不建议 `<img>` 引用因为无法染色动画）；为 25 个图标建立条件名 → SVG 的映射函数（至少覆盖降水细分：drizzle/rain/extreme-rain/partly-cloudy-day-rain/partly-cloudy-day-drizzle/partly-cloudy-day-snow/sleet/hail/thunderstorms-rain/thunderstorms-day-rain + 基础 clear-day/partly-cloudy-day/snow/fog/cloudy/overcast/clear-night/partly-cloudy-night/thunderstorms/thunderstorms-day/thunderstorms-night/haze/mist/dust/smoke），未知条件回退 clear-day。
- [ ] C2 cyan 染色：CSS 统一染色（主 #22d3ee / 高光 #67e8f9 / 次 #0ea5e9，辉光 filter drop-shadow），Monochrome SVG 零硬编码色故可直接染色；保持深空透明底、无背景卡片、气泡/浮窗气质。
- [ ] C3 数据驱动：接入现有 SSE weather 事件处理（0011 已接线），天气文本 = 图标 + 条件中文名 + 温度（如 "晴 · 24°"）；无数据时保留占位文本、无图标。
- [ ] C4 动效降级：`@media (prefers-reduced-motion: reduce)` 时 SVG 动画暂停/静止显示终态。
- [ ] C5 截图中间态：shot.py 生成改造后截图存 `docs/reports/evidence/weather-component/t1-after-<ts>.png`（含有天气数据态 + 空态）。
- Gate：C1-C5 全绿 → 进 T2。

### T2 回归验证（medium）

- [ ] C1 结构回归：8 锚点布局完整（顶部/左上/右上/左中/右中/左下/右下/底部），除顶部天气区外无其他锚点内容被改动。
- [ ] C2 渲染验证：打开 HTML（可加 `?demo=1` 模拟天气数据或直接注入 SSE 数据），核对：图标正常渲染、动画运行（无动画帧报错）、cyan 染色生效、无背景卡片、与四角括号/扫描线视觉协调。
- [ ] C3 映射验证：至少实测 3 种条件（如 drizzle/rain/extreme-rain）切换后图标正确切换。
- [ ] C4 降级验证：模拟 prefers-reduced-motion 后动画静止、图标终态可见。
- [ ] C5 控制台验证：无 console 错误（动效不阻塞交互）。
- Gate：C1-C5 全绿 → 进 T3。

### T3 阶段报告与回执（low）

- [ ] C1 写阶段报告：`docs/reports/stage-weather-component-20261031.md`（结论/逐 T Gate 结果/证据路径/越界声明/环境声明）。
- [ ] C2 本地提交：只含本单写域内文件，commit message 遵循 `feat(hud): ...`。
- [ ] C3 打 tag：`ultimaagent-weather-component-20261031`（指向本单 commit SHA）。
- [ ] C4 回执：按范式 §5 八字段（工单号/执行端/完成状态/根因结论/产出路径/验收证据/越界声明/环境声明）输出到 stdout。
- Gate：C1-C4 全绿 → 整单完成。

---

## 四、总验收（封闭清单，全绿才算完成）

- [ ] A1 顶部天气区显示官方 Meteocons 动画图标（非文本占位、非手绘），cyan 辉光染色，无背景卡片。
- [ ] A2 降水细分映射可用：drizzle（小雨）/rain（中雨）/extreme-rain（暴雨）三档 + 复合条件（阵雨/雷阵雨/雨夹雪/冰雹/阵雪）切换正确。
- [ ] A3 8 锚点布局与其他 7 锚点内容无回归改动（git diff 核对仅顶部天气区 + 关联 CSS/JS）。
- [ ] A4 四角括号/扫描线装饰未被改动。
- [ ] A5 prefers-reduced-motion 降级生效。
- [ ] A6 无 console 错误；动画运行正常。
- [ ] A7 截图证据齐全（t0-before / t1-after 至少各 1 张，含天气数据态）。
- [ ] A8 阶段报告 + 本地 commit + tag `ultimaagent-weather-component-20261031` 齐全。

---

## 五、验收要点（打勾清单，供主脑复核）

- [ ] 范围冻结内逐项完成（无越界：未动其他锚点/装饰/原生壳/agent_server）
- [ ] 每 T 验收清单全绿 + 自证完整
- [ ] 关联文档同步（方案文档未被修改；如需更新版本另走流程）
- [ ] 阶段报告产出 → 主脑复核 → 冻结 tag
