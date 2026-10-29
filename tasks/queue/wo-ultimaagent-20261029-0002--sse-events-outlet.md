# Codex 工单 · UltimaAgent｜功能｜SSE /events 事件出口（HUD 四角壳真实数据源）

> 版本：v1.0 ｜ 状态：技术验收通过（2026-10-29；待独立审计 / Owner 验收 / frozen tag）｜ 适用工具：Codex（`codex exec`，`-m gpt-5.6-sol`）
> 用法：按 T0→T4 顺序逐条执行，Gate 全绿才过，再进下一条。
> 范围依据：`H:\UltimaAI\INDEX.md`（G-TASKFLOW-001 / G-WO-NAME-001）+ `H:\UltimaAI\_shared\paradigms\UltimaAI-任务工作流范式.md` + `H:\UltimaAI\_shared\paradigms\UltimaAI-全局工单命名标准.md` + `H:\UltimaAI\_shared\paradigms\Codex-外部执行端调用范式.md`（执行适配器细则）+ `docs/INDEX.md`（项目引导索引）
> 调研依据：`docs/research/bailongma-wiring-interface-20261029.md`（SSE 协议形状 / 45 类事件清单）+ `docs/research/bailongma-hud-feature-alignment-20261029.md`（四角功能对齐）
> 北极星：**贾维斯**（UltimaAgent 一切调整向贾维斯靠拢；白龙马只作接线方式技术参考，不改其本体、不激活）
> 登记：2026-10-29 ｜ 原单 ID：wo-ultimaagent-20261029-0002 ｜ 类型：功能

---

## 0. 范围冻结

**本阶段只做（UltimaAgent SSE 事件出口）**：

1. 在 `src/brain/` 内新增**事件总线 + SSE 出口模块**：`emitEvent` 双写（内存 journal + 缓冲）、sticky 事件、`last_event_id` 断点续传、15s ping——协议形状对齐白龙马 `/events`（connected+sticky+续传+ping），**不复制白龙马源码**；
2. 在既有服务入口 `src/brain/agent_server.py`（ThreadingHTTPServer，127.0.0.1:8756，已有 /health + /ask）挂 `/events` 与 `/events/history` 路由；
3. **事件源接线（真实数据，禁止伪造）**：heartbeat/ticker.py（tick）、loop/brain_loop.py（主脑决策/工具事件）、orchestration/queue.py + audit.py（任务流转）、guardrails/audit_log.py（审计留痕）——按白龙马四角归类（w-agent/w-sys/w-msg/w-hb）推送；
4. 前端四角壳 `docs/previews/hud-live-four-corner/hud-live-four-corner.html` 数据层替换：由演示数据引擎改为 EventSource 消费真实 `/events`（保留 4 角渲染与吸附/透明度壳不变，仅换数据源），带断线重连 + `last_event_id` 续传；
5. 配套单元测试 + 全量回归通过。

**本阶段不做**：不改白龙马/大飞鱼源码；不激活白龙马付费功能；不新增 SSE 独立端口进程（挂载到既有 8756 服务）；不引入第三方 SSE 库（仅标准库，对齐 agent_server 设计约束）；不改造 Win32 窗口壳本体；不新增 45 类之外的虚构事件类型。

---

## 1. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `src/brain/events/`（新增：bus.py + journal.py） | EventBus 单测通过：emit/sticky/续传/历史缓冲 |
| T1 | `src/brain/agent_server.py`（修改） | /events + /events/history 路由实测：SSE 流式、connected+sticky、last_event_id 续传、15s ping |
| T2 | `src/brain/heartbeat/ticker.py`、`src/brain/loop/brain_loop.py`、`src/brain/orchestration/queue.py`、`src/brain/orchestration/audit.py`、`src/brain/guardrails/audit_log.py`（修改，打点接线） | 真实事件源打点：每源 ≥1 事件类型实测发出，事件载荷非空 |
| T3 | `docs/previews/hud-live-four-corner/hud-live-four-corner.html`（修改） | 四角壳真数据消费：EventSource 连 /events，四角内容由真实事件驱动，断线重连 + last_event_id 续传 |
| T4 | 总验收 | 端到端实测 + 全量回归 + 证据落盘 |

---

## 2. 任务明细（每条 T 严格三段式）

### T0 · 事件总线 EventBus（emit/sticky/续传/历史缓冲）

**文件**：
- `H:\UltimaAI\UltimaAgent\src\brain\events\__init__.py`（新增）
- `H:\UltimaAI\UltimaAgent\src\brain\events\bus.py`（新增：EventBus 核心）
- `H:\UltimaAI\UltimaAgent\src\brain\events\journal.py`（新增：环形历史缓冲 + last_event_id 索引）
- `H:\UltimaAI\UltimaAgent\src\brain\tests\test_events_bus.py`（新增测试）

**写什么**：
1. `EventBus` 单例（或依赖注入）：核心方法 `emit_event(type: str, data: dict, *, sticky: bool = False)`、`subscribe(handler)`、`get_after(last_event_id: str) -> list`、`get_sticky() -> dict`；
2. 事件结构：`{"id": str(自增/时间戳+序号), "type": str, "data": dict, "ts": float}`；`id` 单调递增（同白龙马 last_event_id 断点续传语义）；
3. `journal.py`：环形缓冲上限 240 条（对齐白龙马 `/events/history?limit=240`），支持按 path（all/l1/l2/l3）过滤；
4. sticky 事件：`set_sticky(type, data)` / `clear_sticky(type)`，连接建立时先推 connected + sticky（对齐白龙马连接推送顺序）；
5. 线程安全：多线程 emit/订阅（agent_server 是 ThreadingHTTPServer，多个 /events 客户端可能同时连）。

**验收（Gate T0）**：
- [ ] 单测 ≥6：①emit→订阅者收到且 id 递增；②get_after 断点续传返回 id 之后全部；③环形缓冲超 240 截断；④sticky set/clear/连接初始推送；⑤并发 emit 100 条无丢失/无重复（线程安全）；⑥path 过滤 l1/l2/l3 正确；
- [ ] `python -m pytest src/brain/tests/test_events_bus.py -q --disable-warnings` 全绿（用专用解释器，见 T4）。

**禁止**：不引入第三方库（仅标准库 threading/json/time）；不复制白龙马源码实现；事件 id 不用 uuid（需单调可续传）。

---

### T1 · agent_server.py 挂 /events 与 /events/history

**文件**：
- `H:\UltimaAI\UltimaAgent\src\brain\agent_server.py`（修改：do_GET 新增两条路由分支）
- `H:\UltimaAI\UltimaAgent\src\brain\tests\test_agent_server_sse.py`（新增测试）

**写什么**：
1. `GET /events?client_id=<id>&last_event_id=<id>` → `text/event-stream`：
   - 连接建立：先推 `event: connected`（data 含 client_id + 服务时间），再推 sticky 事件，再推 `last_event_id` 之后的历史（对齐白龙马 connected+sticky+续传）；
   - 之后实时推新事件（data 为 JSON，含 `event: <type>` 命名事件）；
   - 15s 无事件推 `event: ping` 保活（注释心跳，客户端不断线）；
   - 断开清理订阅；
2. `GET /events/history?path=all|l1|l2|l3&limit=<n>` → JSON 数组（从 journal 读，默认 limit=240）；
3. 多客户端并发订阅不互相干扰（每客户端独立队列）；
4. HTTP 头：`Content-Type: text/event-stream`、`Cache-Control: no-cache`、`Connection: keep-alive`；分块写出（不缓冲）。

**验收（Gate T1）**：
- [ ] 实测（起 agent_server，专用解释器）：curl/HTTP 客户端连 /events 收到 `event: connected` → sticky → 历史 → 实时流；断线重连传 last_event_id 只收后续（不重发已收）；
- [ ] 15s 静默后收到 `event: ping`；
- [ ] /events/history 返回 ≤240 条且 path 过滤正确；
- [ ] 单测 ≥3：路由注册、SSE 头、历史 JSON 结构；
- [ ] 既有 /health、/ask 行为不回归（单测覆盖）。

**禁止**：不阻塞/独占主线程（SSE 长连接不得卡死 /ask）；不改 8756 端口；不新增独立进程。

---

### T2 · 真实事件源打点接线

**文件**：
- `H:\UltimaAI\UltimaAgent\src\brain\heartbeat\ticker.py`（修改：tick 事件）
- `H:\UltimaAI\UltimaAgent\src\brain\loop\brain_loop.py`（修改：决策阶段/工具事件）
- `H:\UltimaAI\UltimaAgent\src\brain\orchestration\queue.py`（修改：任务流转事件）
- `H:\UltimaAI\UltimaAgent\src\brain\orchestration\audit.py`（修改：审计结果事件）
- `H:\UltimaAI\UltimaAgent\src\brain\guardrails\audit_log.py`（修改：审计留痕事件）

**写什么**：
1. 事件类型按四角归类（对齐 bailongma-hud-feature-alignment 四角，类型名参考白龙马 45 类清单但用 Ultima 实际语义）：
   - w-agent：`message_in` / `message_received` / `stream_start` / `memories_written`；
   - w-sys：`tick`（HeartbeatTicker.tick() 每轮）/ `command_run` / `error`；
   - w-msg：`message`（对话消息）/ `stream_chunk` / `tts_reply`；
   - w-hb：`tool_executing` / `tool_call` / `task_advance`（queue 流转）/ `audit_record`（audit_log）/ `processing_preempted`；
2. 打点方式：各源模块 `emit_event(type, data)`（导入 EventBus），数据用模块真实返回值（tick 返回 dict、audit 记录、queue 状态等），**禁止伪造/编造载荷**；
3. 打点失败静默降级：事件总线异常不影响业务主链路（try/except，记 warning）；
4. 可选：内存中保留最近 N 条工具名中文化映射（复用四角壳 friendlyToolName 逻辑的前端侧渲染，后端只发原始 tool 名）。

**验收（Gate T2）**：
- [ ] 每源 ≥1 真实事件类型验证：手动触发（跑 ticker.tick() / 建一条 queue 任务 / 写一条 audit_log）后 /events 收到对应类型事件且 data 与真实返回值一致（证据截图/输出）；
- [ ] 打点不改变业务行为：既有单测（ticker/queue/audit_log/brain_loop）零回归；
- [ ] 事件总线异常时业务不中断（模拟总线抛错，业务函数仍正常返回）。

**禁止**：不新增事件类型到 45 类之外自造（如确需新增，须在阶段报告登记）；不改各源模块对外 API 签名（只在关键点插入 emit）；不伪造载荷。

---

### T3 · 四角壳前端消费真实 SSE

**文件**：
- `H:\UltimaAI\UltimaAgent\docs\previews\hud-live-four-corner\hud-live-four-corner.html`（修改：数据层替换）

**写什么**：
1. 保留四角壳整体（吸附 8 点位 / 透明度三档 / AR 字号 / 四角布局 / 控制条）不变，**只替换演示数据引擎为真实 EventSource**；
2. 新增 `EventSource('http://127.0.0.1:8756/events?client_id=hud-corner&last_event_id=<sessionStorage 存储>')`：
   - 收到 `connected` 时重置连接状态显示；
   - `event: <type>` 按四角归类渲染到对应角（type→corner 映射表，w-agent/w-sys/w-msg/w-hb）；
   - 心跳波形从 `tick` 事件驱动（每 tick 推一个脉冲）；
   - AI 活动派生逻辑保留（前端从 tool_* 事件 60s 窗口统计）；
   - 聊天气泡从 `message` 事件驱动（最多保留 3 条）；
   - 行动日志从 `tool_executing/tool_call/task_advance` 事件驱动（最多 5 条）；
3. 断线重连：`onerror` 时 3s 重连（对齐白龙马 3s 重连），重连携带 sessionStorage 中 `last_event_id` 续传；
4. 保留「演示数据/已暂停」按钮语义改为「演示模式/真实模式」切换（真实模式=连 /events；演示模式=原有引擎，便于无后端时预览）。

**验收（Gate T3）**：
- [ ] 起 agent_server 后浏览器打开四角壳，四角显示真实事件内容（非演示数据）；
- [ ] 断线（停 agent_server）→ 重连（重启）后只收 last_event_id 之后新事件，不重放已显示内容；
- [ ] 无后端时演示模式仍可独立预览（页面不因后端缺失空白）；
- [ ] shot.py 自检页面无结构错误（可选，作为视觉回归参考）。

**禁止**：不改四角壳样式/吸附/透明度参数（已定稿）；不在前端硬编码白龙马事件类型名（用映射表）；不引入第三方前端库（原生 EventSource）。

---

### T4 · 总验收

**文件**：本工单（更新状态）+ `docs/reports/` 阶段报告 + 证据目录

**写什么**：
1. 全量单测回归：`H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest src -q --disable-warnings`（**Agent 专用解释器，禁止用系统 Python312**）→ 全绿 + 无新增失败；
2. 端到端实测（专用解释器起 agent_server）：/events 连上收 connected+sticky+历史+实时；/events/history 返回 ≤240；断线重连续传；截图/输出存证据目录；
3. 阶段报告 `docs/reports/stage-sse-events-outlet-20261029.md`：Gate 逐条核对（T0-C1~C6/T1-C1~C4/T2-C1~C3/T3-C1~C4/T4 全量），证据路径、越界声明（无=明确写"无"；含未动范围：白龙马源码/大飞鱼/Win32 壳/8756 端口）；
4. 证据落盘 `docs/reports/evidence/sse-events-outlet/`：单测输出、/events 实测输出、/events/history 样例、断线重连证据、前端截图；
5. 回执 8 字段按 Codex 范式 §5 输出。

**验收（Gate T4）**：总验收清单全绿；阶段报告存在且逐项勾选；回执 8 字段齐全；越界声明如实。

---

## 3. 给编码代理的任务粘贴模板

```
T0 事件总线：已完成，Gate T0 全绿（8 passed；t0-events-bus-pytest.txt）
T1 /events 路由：已完成，Gate T1 全绿（connected/sticky/历史/实时/15.01s ping；t1-sse-live-output.txt）
T2 事件源打点：已完成，Gate T2 全绿（五源真实事件 sources_verified=5；t2-real-source-events.txt）
T3 四角壳真数据：已完成，Gate T3 全绿（last_event_id=47、重连无重复；t3-reconnect-evidence.txt + t3-hud-real-mode.png）
T4 总验收：指定 Python 3.13.16 全量回归 699 passed、36 warnings、120 subtests passed；真机 8756 /health、/events、/events/history 均 200（t4-full-pytest.txt + t4-8756-final.txt）
```

---

## 4. 验收要点

- [ ] 范围冻结内逐项完成（无越界：未动白龙马/大飞鱼源码、未激活白龙马、未改 8756 端口、未动 Win32 壳本体）
- [ ] 每 T 验收清单全绿 + 自证完整
- [ ] 关联文档同步（SSE 协议形状对齐 wiring 文档、四角归类对齐 alignment 文档）
- [ ] 阶段报告产出 → 主脑复核 → 冻结 tag（`wo-ultimaagent-20261029-0002-frozen-<date>`）
