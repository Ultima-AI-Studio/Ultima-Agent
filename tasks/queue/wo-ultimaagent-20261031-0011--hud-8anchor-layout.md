# 工单 wo-ultimaagent-20261031-0011 ｜ UltimaAgent ｜ 工程 ｜ HUD 四角壳 8 锚点布局改造（方案 v0.2 定稿落地）

> 原单 ID：`wo-ultimaagent-20261031-0011` ｜ 显示标题：UltimaAgent｜工程｜HUD 8 锚点布局改造（四角壳+八边）
> 依据：G-DISPATCH-001 自主推进版（2026-10-28 用户拍板）｜ 上位工作流 G-TASKFLOW-001 ｜ G-PLAN-001 先方案后工单
> 方案依据：`docs/previews/hud-layout-zone-plan-20261031.md`（v0.2 Owner 拍板定稿，tag `hud-8anchor-layout-frozen-20261031`）｜ 范式：`docs/paradigms/ui-kit-standard.md` §8（v1.2）
> 用户拍板：2026-10-31 "8 锚点布局定稿 + AR 安全基线 + 全屏幕统一范式 + 鸿蒙废弃 + Windows 载体 + 审批口径"
> 北极星：贾维斯（全屏幕统一范式：Windows/AR/平板同布局，跨端零返工）
> 创建：2026-10-31 ｜ 状态：待派发

---

## 一、目标与范围

### 1.1 目标（Result）

将存量四角壳 HTML（`docs/previews/hud-live-four-corner/hud-live-four-corner.html`，现 4 widget 布局）按方案 v0.2 改造为 **8 锚点布局**，实现：
1. **8 锚点功能分区落地**：顶部=时间+天气（高频常用）；左上=系统状态（硬件/连接/上行下行/设备）；右上=环境/位置（方向/坐标/位置/导航预留）；左下=任务队列简况；右下=即时消息（微信/QQ/Telegram 提醒预留位）；左中=Agent 反馈区（主动推送）；右中=主动唤出功能区（查询/浏览/列表→展开→解读）；底部=交流转写区（ASR 文字/未来实时翻译位）。
2. **按需显隐状态机**：无任务/无消息/无交流 → 对应锚点空或隐藏，不占画面；任务完成自动清空。
3. **AR 安全基线遵守**：中央 0 遮挡；边缘常驻区信息密度 ≤3 信息点/区；唤出窗极速收起（语音/手势/注视离开）；透明度三档 0.14/0.55/0.85 保持；审批/签名永不显示。
4. **全屏幕统一范式**：HTML 布局以 8 锚点为唯一结构（不按端另设计），未来 AR/平板复用同一布局结构。

**验收即边界**：验收清单见 §四，全绿即完成，禁止就地追加需求。

### 1.2 范围冻结（边界，禁止越界）

- **只做**：8 锚点布局改造（HTML 结构/CSS 分区/JS 显隐状态机）+ 必要数据源接线（SSE 8756 现有事件 + Manager 18766 任务状态只读 + 系统 tick 扩展）+ 回归验收 + 阶段报告。
- **禁止**：
  - 禁止改动 `UltimaAgent.Hud` 原生壳（WPF 层已验收，本单只改 HTML 与数据接线；壳透传/托盘/透明度三档保持不动）；
  - 禁止实现签名/审批界面（永不进入 HUD 展示层）；
  - 禁止实现鸿蒙端任何形态（鸿蒙废弃已拍板）；
  - 禁止改造 Manager 内核能力（只读任务状态 API，不新增/修改 Manager 侧接口）；
  - 禁止新增消息聚合真实接入（右下仅预留位，微信/QQ/Telegram 真实接入为后续工单）；
  - 禁止新增导航真实接入（右上仅预留接口位）；
  - 禁止改动 KWS/ASR/TTS 参数基线（`docs/specs/kws-wakeup-params-baseline.md`）与 voice_profile/daemon 代码；
  - 禁止用中文模型名/无关依赖联网下载（本单不涉及模型）；
  - 禁止修改底部交流转写区之外的对话 UI 逻辑（W2 只出结果原则）。

### 1.3 写域（各 T 精确到文件）

| 文件 | 动作 | 说明 |
|---|---|---|
| `docs/previews/hud-live-four-corner/hud-live-four-corner.html` | 修改（主产物） | 4 widget → 8 锚点布局；含 8 分区结构、按需显隐状态机、SSE 事件映射 |
| `docs/previews/hud-live-four-corner/_shots/` | 只读+截图证据 | 改造前后截图对比（shot.py 复用） |
| `docs/previews/hud-layout-zone-plan-20261031.md` | 只读 | 方案依据，不修改（已冻结 tag） |
| `docs/reports/evidence/hud-8anchor/` | 新建 | 证据目录 |
| `docs/reports/stage-hud-8anchor-20261031.md` | 新建 | 阶段报告 |
| `src/brain/agent_server.py` | 只读+最小扩展 | 若需补系统状态 tick 数据点（硬件/连接/上下行）——仅允许新增 tick 字段，禁止改动 HOST/PORT/TOOLS/AGENT/路由/RU-05 结构 |
| Manager 18766 | 只读调用 | 任务状态只读（身份校验后读取当前执行任务），不写不改 |

---

## 二、DoR 就绪门（五项全绿）

| # | 就绪项 | 判定 | 证据 |
|---|---|---|---|
| 1 | 验收 Gate 可判定 | ✅ 封闭清单（§四） | HTML 结构/截图/事件/状态机逐项可检 |
| 2 | 无未决依赖 | ✅ | 方案已冻结 tag；SSE 8756 与原生壳已验收；Manager 18766 可用 |
| 3 | 写入域已声明 | ✅ | §1.3 |
| 4 | 推理强度已声明 | ✅ | T0 medium / T1 medium / T2 high / T3 low |
| 5 | 禁止项已写 | ✅ | §1.2 |

---

## 三、执行步骤（T0→T3，逐 T Gate PASS 再进下一条）

### T0 现状盘点与方案对齐（medium）

- [ ] C1 读方案：完整读取 `docs/previews/hud-layout-zone-plan-20261031.md` v0.2（8 锚点总表/映射/显示规则/AR 安全基线）与 `docs/paradigms/ui-kit-standard.md` §8。
- [ ] C2 读现状：完整读取 `docs/previews/hud-live-four-corner/hud-live-four-corner.html`（4 widget 结构、8 点吸附 map、SSE 事件映射 EVENT_CORNERS、透明度三档、`?native=1` 模式），盘点现有 CSS 变量/JS 函数清单。
- [ ] C3 截图基线：shot.py 生成改造前截图存 `docs/reports/evidence/hud-8anchor/t0-before-<ts>.png`。
- [ ] C4 数据源盘点：SSE 8756 现有事件类型（ticker/brain_loop/queue/audit/audit_log/message 等）逐一映射到 8 锚点；Manager 18766 任务状态 API 可用性确认（身份校验/当前任务字段）。
- Gate：C1-C4 全绿 → 进 T1。

### T1 8 锚点布局改造（medium）

- [ ] C1 HTML 结构改造：4 widget 容器 → 8 锚点分区（顶部/右上/左上/左下/右下/左中/右中/底部），每区独立容器 + 语义类名 + 默认显隐状态（常驻 vs 按需）。
- [ ] C2 显隐状态机：按需锚点（左下/右下/左中/右中/底部）实现"无内容即隐藏/空即隐"逻辑；任务完成自动清空；唤出/收起触发（语音/指令事件接入点 + 极速收起回调位）。
- [ ] C3 SSE 事件重映射：将现有 EVENT_CORNERS 映射更新为 8 锚点事件映射（顶部=系统 tick/连接、左中=Agent 主动推送事件、右中=任务/查询内容事件、底部=语音 ASR/翻译事件）；保留 sticky+last_event_id 断线续传。
- [ ] C4 AR 安全基线落地：中央区 0 内容（显式留空）；边缘常驻区信息点 ≤3；透明度三档 0.14/0.55/0.85 维持；无审批/签名元素。
- [ ] C5 截图中间态：shot.py 生成改造后截图存 `docs/reports/evidence/hud-8anchor/t1-after-<ts>.png`（空态：无任务/无消息/无交流时桌面应清爽）。
- Gate：C1-C5 全绿（截图核对 8 分区位置与显隐行为）→ 进 T2。

### T2 数据接线与回归（high）

- [ ] C1 接 Manager 任务状态：左中 Agent 反馈区/左下队列简况读取 Manager 18766 当前执行任务（身份校验通过后只读），无任务即空。
- [ ] C2 系统状态数据：左上系统状态区接 agent_server tick（硬件/连接/上行下行速率）；若 tick 缺字段，仅新增字段（写域声明内），禁止改 HOST/PORT/路由结构。
- [ ] C3 顶部时间/天气：时间=系统时钟（本机）；天气接 `weather.query` 工具输出（若工具可调）；右上方向/坐标/位置=预留接口位（不接真实导航）。
- [ ] C4 全量回归：`tools/venv-openjarvis/Scripts/python.exe -m pytest src -q` 全绿（工程验收必须 venv-openjarvis 解释器，禁止默认 Python312）。
- [ ] C5 端到端验收：原生壳加载 `hud-live-four-corner.html?sse=8756&native=1` 实际运行——透明不遮挡、穿透、三档透明度、空态清爽、有任务可唤出、极速收起可用、无审批/签名。
- [ ] C6 冻结 tag：commit 全部改动 → `git tag ultimaagent-hud-8anchor-20261031`（可 `git rev-parse` 解析）→ 推送 `git push --tags`（打 tag 铁律默认动作）。
- [ ] C7 阶段报告：`docs/reports/stage-hud-8anchor-20261031.md` 完整（Gate 逐条 PASS + 截图对比 + 事件映射表 + 越界声明）。
- Gate：C1-C7 全绿 → 进 T3。

### T3 回执（low）

输出八字段标准回执（见 §五），证据目录完整，无越界声明。

---

## 四、验收口径（封闭清单，全绿才过）

| Gate | 判定 | 证据位置 |
|---|---|---|
| 8 分区 | HTML 含 8 锚点独立容器，位置与方案总表一致（顶部=时间天气/左上=系统/右上=环境/左下=队列/右下=消息/左中=反馈/右中=内容/底部=转写） | t1-after 截图 + HTML 结构 |
| 显隐状态机 | 无任务/无消息/无交流时按需锚点空或隐藏；任务完成自动清空 | 空态截图 + 事件驱动实测 |
| SSE 映射 | 8 锚点事件映射生效（sticky 续传保留）；/events 实测连接正常 | t1 证据 + 事件日志 |
| AR 安全 | 中央 0 内容；常驻区信息点 ≤3；透明度三档 0.14/0.55/0.85；无审批/签名元素 | HTML 检查 + 截图 |
| 数据接线 | 左上系统状态有真实数据；左中/左下接 Manager 18766 任务状态（无任务为空） | t2 实测 |
| 回归 | venv-openjarvis pytest 全绿（0 failed） | pytest 输出摘要 |
| 端到端 | 原生壳实际加载运行通过（透明/穿透/三档/唤出/收起） | 运行记录 |
| 冻结 | tag `ultimaagent-hud-8anchor-20261031` 存在且可解析、已推送 | git tag -l + git rev-parse |

---

## 五、执行端回执（八字段，必填）

| 字段 | 值 |
|---|---|
| 链路号/工单号 | wo-ultimaagent-20261031-0011 |
| 执行端 | Codex（gpt-5.6-sol，codex exec） |
| 完成状态 | 已完成 / 阻塞 / 已终止（三选一） |
| 根因结论 | （核心结论：8 锚点布局是否按要求落地的一句话判定） |
| 产出路径 | docs/previews/hud-live-four-corner/hud-live-four-corner.html、docs/reports/stage-hud-8anchor-20261031.md、docs/reports/evidence/hud-8anchor/ |
| 验收证据 | T0-C1~C4 / T1-C1~C5 / T2-C1~C7 逐条 PASS + 截图对比 + pytest 摘要 + /events 实测 + 原生壳运行记录 |
| 越界声明 | 无=明确写"无"；含未动范围（原生壳/Manager 内核/鸿蒙/消息真实接入/导航真实接入/KWS/ASR/TTS/voice_profile/daemon/agent_server 结构与路由） |
| 环境声明 | 真机：原生壳加载 + 8756 SSE + 18766 任务状态 + 真实显隐交互实测；如仅静态 HTML 验证须写"仅静态验证，真机待验收" |

---

## 附：推理强度声明

T0 medium（现状盘点与方案对齐）｜ T1 medium（布局改造与状态机）｜ T2 high（数据接线+回归+冻结）｜ T3 low（回执）
