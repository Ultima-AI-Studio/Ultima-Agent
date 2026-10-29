# SSE /events 事件出口阶段报告

- 工单：`wo-ultimaagent-20261029-0002`
- 执行端：Codex
- 专用解释器：`H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe`（Python 3.13.16）
- 北极星：贾维斯；白龙马仅作为 SSE 接线协议形状参考

## Gate T0 · EventBus

- [x] T0-C1 emit 后订阅者收到且 ID 单调递增
- [x] T0-C2 `get_after` 只返回游标之后事件；未知游标回放现存历史
- [x] T0-C3 journal 超过 240 条后仅保留最新 240 条
- [x] T0-C4 sticky set/get/clear
- [x] T0-C5 10 线程并发 emit 100 条，无丢失、无重复 ID
- [x] T0-C6 history 对 all/l1/l2/l3 正确过滤

证据：`docs/reports/evidence/sse-events-outlet/t0-events-bus-pytest.txt`（8 passed）。

## Gate T1 · /events 与 /events/history

- [x] T1-C1 `/events` 实测顺序为 connected → sticky → history → live
- [x] T1-C2 `last_event_id` 重连后固定 sticky 先发，首个非 sticky 事件仅为游标后的新事件
- [x] T1-C3 默认 15 秒静默保活实测为 15.01 秒；SSE 头与分块 flush 正确
- [x] T1-C4 `/events/history` 返回 JSON 数组、path 过滤正确、limit 上限 240；`/health` 与 `/ask` 回归通过

证据：`t1-agent-server-pytest.txt`（13 passed）与 `t1-sse-live-output.txt`。

## Gate T2 · 真实事件源打点

- [x] T2-C1 ticker、brain_loop、queue、workflow audit、append-only audit_log 五源均经 `/events` 收到真实非空载荷
- [x] T2-C2 既有集成测试与新增接线测试合计 27 passed
- [x] T2-C3 模拟事件总线抛错后业务函数仍返回原真实结果

证据：`t2-real-source-events.txt` 与 T0/T1 测试输出。

## Gate T3 · 四角壳真实 SSE 数据层

- [x] T3-C1 默认真实模式连接 `http://127.0.0.1:8756/events`，四角由真实源事件驱动
- [x] T3-C2 sessionStorage 保存 `last_event_id`，`onerror` 关闭旧连接并在 3 秒后携游标重连
- [x] T3-C3 演示引擎保留并可由按钮切换；真实模式会先清空静态演示条目
- [x] T3-C4 `<style>` SHA-256 与改动前一致，四角布局/吸附/透明度/AR 字号未改；原生 EventSource、无第三方库

证据：`t3-hud-pytest.txt`、`t3-reconnect-evidence.txt`、`t3-hud-real-mode.png`。截图为 1440×900 真机浏览器，真实 8756 事件驱动，游标已到 47。

## Gate T4 · 总验收

- [x] T4-C1 指定 Python 3.13.16 执行 `pytest src`：699 passed，36 warnings，120 subtests passed
- [x] T4-C2 真机 8756：`/health` 200、`/events/history` 200、`/events` 首帧 connected 且 Content-Type 正确
- [x] T4-C3 controlled 8756 已实测 sticky/history/realtime/15s ping、断线重连与五源真实事件；Chrome 真实模式截图落盘
- [x] T4-C4 阶段报告、逐 T Gate、证据目录与工单模板回填齐全

证据：`t4-full-pytest.txt`、`t4-8756-final.txt`，并关联 T0–T3 全部证据。

## 根因结论

既有 8756 agent_server 只有 `/health` 与 `/ask`，缺少线程安全事件 journal、SSE 路由、真实源打点和 HUD EventSource 数据层，导致四角壳只能展示演示数据。本工单在不增加端口/进程与第三方依赖的前提下补齐该链路。

## 产出路径

- 后端：`src/brain/events/`、`src/brain/agent_server.py`
- 真实源：`src/brain/heartbeat/ticker.py`、`src/brain/loop/brain_loop.py`、`src/brain/orchestration/queue.py`、`src/brain/orchestration/audit.py`、`src/brain/guardrails/audit_log.py`
- 测试：`src/brain/tests/test_events_bus.py`、`src/brain/tests/test_agent_server_sse.py`
- 前端：`docs/previews/hud-live-four-corner/hud-live-four-corner.html`
- 报告/证据：本文件与 `docs/reports/evidence/sse-events-outlet/`

## 环境声明

真机 Windows 环境实测：指定 Python 3.13.16、127.0.0.1:8756、Chrome 156 headless（1440×900）。非“仅预期”。当前为技术验收通过，独立审计、Owner 验收与 frozen tag 尚未执行，不冒充冻结。

## 越界声明

无。未动范围：白龙马源码（未修改、未激活、未复制）、大飞鱼源码、Win32 壳本体、8756 端口配置、全局主表语义、第三方依赖、发布与 frozen tag。
