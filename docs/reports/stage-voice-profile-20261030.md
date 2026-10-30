# UltimaAgent voice-profile 阶段报告（2026-10-30）

- 工单：`wo-ultimaagent-20261030-0003`
- 执行端：Codex（`gpt-5.6-sol`）
- 专用解释器：`tools/venv-openjarvis/Scripts/python.exe`（Python 3.13.16）
- 北极星：默认 Jarvis，L2 可覆盖；语音不出本机

## Gate T0 · voice-profile.json + L1/L2/L3 装载

- [x] T0-C1 无文件时回退 L1 内置默认
- [x] T0-C2 JSON 损坏时回退 L1 内置默认
- [x] T0-C3 L2 override 生效
- [x] T0-C4 L3 运行期覆盖优先于 L2
- [x] T0-C5 `save_user_override()` 保存后回读并保留其余字段
- [x] T0-C6 缺失/非法字段逐项回退默认

证据：`docs/reports/evidence/voice-profile/t0-voice-profile-tests.txt`（8 passed）。

## Gate T1 · 唤醒词热重载

- [x] T1-C1 custom 写入 `keywords.txt`，6 个 L1 变体与 ULTIMA 行保留
- [x] T1-C2 keywords mtime 变化触发 spotter 原子重建，同一 PID 不重启
- [x] T1-C3 重建失败保留旧 spotter
- [x] T1-C4 interaction 纯唤醒回声词根从 profile 动态读取

证据：

- `docs/reports/evidence/voice-profile/t1-wakeword-reload-tests.txt`（6 passed，含主 Agent → 指定 ASR 解释器的中文 custom 转换）
- `docs/reports/evidence/voice-profile/t1-hot-reload-probe.txt`（同 PID；custom“查天气”由未命中变为命中；重载前后“贾维斯”均命中）

实测环境：`tools/venv-asr/Scripts/python.exe`，既有本地 WAV 注入；未开麦、无外部请求、未重启或停止现有 daemon。

## Gate T2 · Jarvis 人设与三条硬约束

- [x] T2-C1 默认 Jarvis persona 正常加载，原 loyal/efficient/dry-witted/British butler 骨架保留
- [x] T2-C2 L2 override 文件存在时优先
- [x] T2-C3 override 缺失时回退 Jarvis；Jarvis 文件缺失时回退内置约束模板
- [x] T2-C4 agent 回答在 interaction 层过滤营销话术并限制为不超过 2 句

证据：

- `docs/reports/evidence/voice-profile/t2-persona-tests.txt`（19 passed，含 T0/T1 回归）
- `docs/reports/evidence/voice-profile/t2-live-agent-probe.txt`（本地 `127.0.0.1` agent_server，2 句、无黑名单命中，前后 PID 不变）

## Gate T3 · 回答后统一过滤

- [x] T3-C1 营销/引导黑名单命中时替换为“收到。”
- [x] T3-C2 正常天气等短回答原样保留
- [x] T3-C3 超过 `max_sentences` 时在第 2 句完整截断
- [x] T3-C4 空输入保持空；事实性“关注/订阅/点赞数”与“给个赞”不误杀

统一出口：`InteractionLoop._respond()`，规则回复、天气回复和 agent 回复均经过同一 `filter_reply()`。

证据：`docs/reports/evidence/voice-profile/t3-reply-filter-tests.txt`（29 passed，含既有 interaction 回归）。

## Gate T4 · 总验收

- [x] T4-C1 voice-profile 专项与直接交互回归：51 passed
- [x] T4-C2 默认 L1、L2 override 缺失回退、custom 热重载与回复过滤证据齐备
- [x] T4-C3 专用解释器确认：openjarvis 与 ASR 均为 Python 3.13.16
- [ ] T4-C4 全量 `pytest src` 全绿：**BLOCKED**（725 passed + 120 subtests passed，2 failed）
- [ ] T4-C5 总验收/冻结 tag：未执行（全量 Gate 未绿，不能声明闭环）

### T4 阻塞根因

全量命令：`tools/venv-openjarvis/Scripts/python.exe -m pytest src -q --disable-warnings`。

1. `src/brain/tests/test_agent_server_sse.py::test_hud_uses_real_sse_with_resume_and_preserves_frozen_style`：HUD 当前 style SHA256 为 `f336fd77...97ab1`，测试冻结期望 `79c8490d...528d`；该 HTML 在本工单开始前已有修改，不在写域。
2. `src/brain/tests/test_queue_source.py::QueueSourceTests.test_production_library_readable_without_mutation`：生产 `tasks/tasks.json` 缺 `terminal_reason` 字段导致 fail-closed；该文件在本工单开始前已有修改，不在写域。

两项定向复测仍为 2 failed。首次全量中的毫秒时间戳偶发失败在最新全量已通过，不再计为当前阻塞。按范围冻结与 fail-closed 规则，未修改 HUD、生产任务库或测试来制造全绿。

证据：

- `docs/reports/evidence/voice-profile/t4-focused-regression.txt`（51 passed）
- `docs/reports/evidence/voice-profile/t4-full-pytest-src.txt`（725 passed，2 failed，120 subtests passed）
- `docs/reports/evidence/voice-profile/t4-preexisting-failures-rerun.txt`（范围外 2 项定向复测）
- `docs/reports/evidence/voice-profile/t4-scope-check.txt`（解释器、KWS 参数、无硬编码词根、后台进程身份、keywords 哈希）

## 越界声明

无越界。未动 W6 UI、云端 ASR 主链路、KWS 参数基线数值、TTS 克隆、第三方配置库、memory 模块、HUD 冻结样式与生产 `tasks.json`；未停止/重启既有 `agent_server` 或 voice daemon；未打冻结 tag。
