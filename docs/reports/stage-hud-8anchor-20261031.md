# UltimaAgent HUD 8 锚点布局阶段报告

- 工单：`wo-ultimaagent-20261031-0011`
- 执行：Codex，中断重入（原 session `01a19038` 在电脑强制重启时终止）
- 日期：2026-10-31（Asia/Shanghai）
- 方案：`docs/previews/hud-layout-zone-plan-20261031.md` v0.2
- 范式：`docs/paradigms/ui-kit-standard.md` §8
- 冻结锚点：`ultimaagent-hud-8anchor-20261031`
- 结论：T0、T1、T2-C1~C5/C7 PASS；T2-C6 的本地 commit/tag 已完成，但 GitHub tag 推送因网络不可达 BLOCKED，整单不得宣称完成。

## 1. 中断重入核对

重启后首先核对证据目录、工作区和运行服务。重启前的 T0 基线、T1 改造后截图、T2 原生壳截图均存在；HTML 保持 8 锚点控制器，`agent_server.py` 保持 HUD tick/Manager 只读接线。重入后追加原生壳桌面截图 `t2-native-reentry-20261031-141609.png`，并重新执行 API、SSE 和全量 pytest 验收。

共享工作区在收口期间发生外部 HEAD 漂移：另一进程创建的提交 `7998dc1` 同时带入了本单已暂存的 HUD HTML 与 6 张正式截图，并带有其自身的交互方案文档。本执行未创建、改写或回退该外部提交；本单后续提交严格只包含本单授权的 `agent_server.py` tick hunks 与本报告。该事件不改变本单产物内容与测试结果。

## 2. T0 现状盘点与方案对齐

| Gate | 结果 | 证据 |
|---|---|---|
| C1 方案与范式 | PASS | 完整读取 v0.2 方案及 UI Kit §8；8 锚点、常驻/临时、AR 安全口径一致。 |
| C2 四角壳现状 | PASS | 盘点原 4 widget、8 点吸附 map、`EVENT_CORNERS`、三档透明度、`?native=1`、SSE 重连与游标。 |
| C3 截图基线 | PASS | `t0-before-20261031-124001.png`、`t0-before-20261031-133346.png`。 |
| C4 数据源 | PASS | 8756 `/events`、`/events/history` 可用；18766 未授权返回 401，授权只读返回当前任务。 |

现状关键项：CSS 变量包含 `--edge-alpha`、`--edge-blur`、HUD 色板与间距；原 JS 包含吸附定位、透明度控制、SSE 连接/重连、`sessionStorage` 游标、事件分发、演示模式。重入时 8756 历史窗口仅含当前 sticky `tick`，完整可消费事件集合以 8 锚点映射表为准。

## 3. T1 8 锚点布局改造

| Gate | 结果 | 证据 |
|---|---|---|
| C1 8 个独立容器 | PASS | `zone-top`、`zone-left-top`、`zone-right-top`、`zone-left-middle`、`zone-right-middle`、`zone-left-bottom`、`zone-right-bottom`、`zone-bottom`。 |
| C2 按需显隐 | PASS | 五个临时区默认 `is-hidden`；空内容清除、完成态自动清空、定时收起、Escape/事件回调/`window.UltimaHud.collapseTransient()` 可极速收起。 |
| C3 SSE 重映射 | PASS | `EVENT_ANCHORS` 覆盖 Agent、工具、任务、审计、转写与预留消息事件；`ultima_hud_last_event_id` 保留断线续传。 |
| C4 AR 安全 | PASS | 中央仅空 `central-safe`；三常驻区每区不超过 3 信息点；透明度 0.14/0.55/0.85；DOM 无审批/签名组件。 |
| C5 截图 | PASS | `t1-after-20261031-133848.png`、`t1-eight-zones-20261031-133924.png`。 |

### 3.1 SSE → 8 锚点映射

| 锚点 | 事件类型 |
|---|---|
| 顶部 | 系统时钟常驻；`weather.query` 工具结果更新天气。 |
| 左上 | `tick`、`heartbeat_settings_updated`、`key_configured`、`error`。 |
| 右上 | 环境/位置/导航接口预留，不接真实导航。 |
| 左下 | `scheduled_task`、`scheduled_task_completed`、`scheduled_task_retry`、`scheduled_task_failed`、`task_advance`，以及 tick 中 Manager 当前任务。 |
| 右下 | `social_status`、`external_message`、`notification`；仅预留，不接真实消息聚合。 |
| 左中 | `memories_written`、`agent_name_updated`、`audit_record`、`processing_preempted`、`llm_retry`、`message_requeued`、`message_dropped`、`protocol_violation`，以及 Manager 当前任务反馈。 |
| 右中 | `message`、`response`、`stream_start/chunk/end`、`injector_result`、`tool_preparing/executing/call`、`command_run/output`、`focus_frame/compressed`、`browser_preview`。 |
| 底部 | `message_in`、`message_received`、`audio_created`、`tts_reply`。 |

SSE 实测返回 `event: connected`，随后事件包含 `id`；请求使用 `last_event_id`，浏览器端同时把 `evt.lastEventId` 写入 `sessionStorage`，保留 sticky + 游标续传。

## 4. T2 数据接线与回归

| Gate | 结果 | 证据 |
|---|---|---|
| C1 Manager 18766 | PASS | 未授权 `/api/v1/tasks?project_id=UltimaAgent` 返回 401；通过本机 `CredentialStore` 身份校验后只读返回 3 条活动任务，包含本工单；只向 HUD 暴露工单号、截断标题、状态，不暴露能力令牌。 |
| C2 系统 tick | PASS | 8756 sticky `tick` 实测含 `hardware=16C · 32GB`、`connection=Agent + Manager`、真实 `down_bps/up_bps`、`manager_ok=true`、`manager_tasks`、`queue_count`。未改 HOST/PORT/TOOLS/AGENT/路由/RU-05。 |
| C3 时间/天气/位置 | PASS | 顶部本机系统时钟每秒刷新；`weather.query` 的 `tool_call` 结果更新天气；右上只显示方向/坐标/导航预留。 |
| C4 全量 pytest | PASS | `tools/venv-openjarvis/Scripts/python.exe -m pytest src -q`，Python 3.13.16；最终 `786 passed, 36 warnings, 120 subtests passed in 62.85s`，退出码 0。 |
| C5 原生壳 E2E | PASS | `UltimaAgent.Hud.exe` + WebView2 实际运行，壳只读加载 `hud-live-four-corner.html?sse=8756&native=1`；透明桌面叠加、中央不遮挡、SSE 实时任务、空态/有任务显隐、极速收起接口、三档常量、穿透能力、无审批签名均核对。证据见两张 T2 截图。 |
| C6 commit/tag/push | BLOCKED | 本单收口提交 `5cdfca31309ab3b74050340f5badab1ce9c9cb0e` 只含授权 tick hunks；本地 tag `ultimaagent-hud-8anchor-20261031` 可解析到该 SHA。免代理 `push --tags` 两次均因 `github.com:443` 连接超时失败；全局代理回退也因 `127.0.0.1:1080` 未监听失败。 |
| C7 阶段报告 | PASS | 本文件。 |

第一次全量回归得到 `784 passed / 2 failed`：`test_preference_p2` 是未跟踪的另一工作域中毫秒时间戳竞态（5 次复现 4 过 1 失败），`test_ollama_has_brains` 是强制重启后当前 shell PATH 缺少已安装的 Ollama。未越界修改相关代码；把已存在的 `C:\Users\Administrator\AppData\Local\Programs\Ollama` 补回测试进程 PATH 后，两项目标测试通过，完整全量复跑绿。

### 4.1 原生壳证据

- `t2-native-e2e-20261031-134255.png`：重启前原生壳多屏透明叠加。
- `t2-native-reentry-20261031-141609.png`：重入后 `UltimaAgent.Hud.exe` 仍实际运行，HUD 在真实桌面上显示顶部/左上/左中等边缘信息，中央保持透传。
- 只读壳代码仍定义 click-through 与三档 `AlphaSafe=0.14`、`AlphaNormal=0.55`、`AlphaBold=0.85`；本单未改 WPF 文件。

## 5. 证据目录

`docs/reports/evidence/hud-8anchor/`

| 文件 | 用途 |
|---|---|
| `t0-before-20261031-124001.png` | T0 原四角壳基线。 |
| `t0-before-20261031-133346.png` | T0 重拍基线。 |
| `t1-after-20261031-133848.png` | T1 8 锚点空态/改造后。 |
| `t1-eight-zones-20261031-133924.png` | T1 八区演示态位置核对。 |
| `t2-native-e2e-20261031-134255.png` | T2 重启前原生壳端到端。 |
| `t2-native-reentry-20261031-141609.png` | T2 重入后原生壳端到端。 |

临时 `probe*.png` 与临时 `shot.py` 已定点清理；正式证据保留。

## 5.1 冻结与续推状态

- 本地 commit：`5cdfca31309ab3b74050340f5badab1ce9c9cb0e`。
- 本地 tag：`ultimaagent-hud-8anchor-20261031` → `5cdfca31309ab3b74050340f5badab1ce9c9cb0e`。
- 远端状态：未确认存在；2026-10-31 本轮网络不可达。
- 网络恢复后续推命令：`git -c http.proxy= -c https.proxy= -c http.https://github.com.proxy= push --tags`，随后用 `git ls-remote --tags origin refs/tags/ultimaagent-hud-8anchor-20261031` 核验。

## 6. 越界声明

无越界修改。本执行未修改 `UltimaAgent.Hud` WPF 原生壳、Manager 内核/API、冻结方案、KWS/ASR/TTS 参数、voice_profile/daemon、鸿蒙端、真实消息聚合或真实导航；未改 `agent_server.py` 的 HOST/PORT(8756)/TOOLS/AGENT/工具注册/路由/RU-05 结构。`agent_server.py` 同文件中另一工单的 `ask_once` 事件改动保留在工作树但明确未纳入本单提交。

## 7. 环境声明

- Windows 真机桌面，多显示器；原生 `UltimaAgent.Hud.exe` + WebView2 实际运行。
- Agent SSE：`127.0.0.1:8756`，Python 3.13.16 venv。
- Manager：`127.0.0.1:18766`，身份校验后只读。
- pytest：`tools/venv-openjarvis/Scripts/python.exe`，未使用默认 Python 3.12。
