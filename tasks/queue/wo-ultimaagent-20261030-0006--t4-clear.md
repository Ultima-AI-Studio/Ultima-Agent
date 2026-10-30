# Codex 工单 · UltimaAgent｜架构｜0003 T4 阻塞清理（HUD 冻结哈希重冻结 + 队列读取容缺）

> 版本：v1.1 ｜ 状态：**已完成**（T0-T2 全 PASS；主脑复核通过，0003 T4 转绿；2026-10-30 冻结 commit 12330ea + tag wo-ultimaagent-20261030-0003-frozen-20261030）｜ 适用工具：Codex（`codex exec`，`-m gpt-5.6-sol`）
> 用法：按 T0→T2 顺序逐条执行，Gate 全绿才过，再进下一条。
> 范围依据：`H:\UltimaAI\INDEX.md` + `H:\UltimaAI\_shared\paradigms\UltimaAI-任务工作流范式.md` + `docs/INDEX.md`
> 阻塞依据：`wo-ultimaagent-20261030-0003` T4 全量回归 2 个范围外既有失败（2026-10-30 Codex 回执，未越界修复）
> 北极星：**贾维斯**（一切调整向贾维斯靠拢；本单为 0003 冻结清障，不扩展产品范围）
> 登记：2026-10-30 ｜ 原单 ID：wo-ultimaagent-20261030-0006 ｜ 类型：架构

---

## 0. 范围冻结

**本阶段只做（0003 T4 阻塞清理，两项范围外既有失败）**：

1. **HUD 冻结样式哈希重冻结**：`docs/previews/hud-live-four-corner/hud-live-four-corner.html` 在 0002 冻结后为「原生壳模式」（`?native=1`，body 透明仅显四角面板）做了预期内演进（git diff：+9/-3，含 `html.native-hud` 透明样式与 URL 参数检测脚本），`src/brain/tests/test_agent_server_sse.py::test_hud_uses_real_sse_with_resume_and_preserves_frozen_style` 冻结哈希仍为旧值 `79c8490d...` → 更新冻结哈希为当前值 `f336fd77...`，并核对测试其余断言（EventSource/真实模式/事件类型）仍全绿；
2. **队列读取容缺**：`tasks/tasks.json` 第 42 条 `voice-136-pseudo-streaming`（state=QUEUED）无 `terminal_reason` 字段——状态机仅在终止态写入该字段（`tasks/queue_engine/state_machine.py`），QUEUED 记录缺该字段是**合法状态**；`src/brain/queue_source.py` `_parse_record` 用 `record["terminal_reason"]` 硬取触发 KeyError → fail-closed 整队列读取失败。修复：读取端改为 `.get("terminal_reason")` 容缺（缺省=None），并核对 `tasks/queue_engine/storage.py` 的 REQUIRED_FIELDS 不强制 QUEUED 记录必须含 terminal_reason；数据文件本身**不改**；
3. 修复后重跑 0003 专项回归（51 passed）与全量 `pytest src`（0003 时 725 passed + 120 subtests / 2 failed → 应 2 failed 清零、无新增失败）→ 0003 T4 转绿。

**本阶段不做**：不改 HUD HTML 内容本身（演进样式是预期内的，只重冻结哈希）；不改 tasks.json 数据（QUEUED 缺字段合法）；不扩展 0003 范围（不新增 voice-profile 功能）；不处理 0004/0005；不引入第三方库。

---

## 1. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `src/brain/tests/test_agent_server_sse.py`（修改：冻结哈希） | 单测全绿：test_hud_uses_real_sse_with_resume_and_preserves_frozen_style 通过，其余断言不受影响 |
| T1 | `src/brain/queue_source.py`（修改：容缺）+ `tasks/queue_engine/storage.py`（核对）+ 新增测试 | 单测全绿：QUEUED 无 terminal_reason 记录可读；终止态记录仍要求字段类型正确；全量读取不再 fail-closed |
| T2 | 总验收 | 0003 专项 51 passed + 全量 pytest src 全绿（2 failed 清零、无新增）+ 证据落盘 |

---

## 2. 任务明细（每条 T 严格三段式）

### T0 · HUD 冻结哈希重冻结

**文件**：
- `H:\UltimaAI\UltimaAgent\src\brain\tests\test_agent_server_sse.py`（修改：第 164-166 行冻结哈希常量）

**写什么**：
1. 用专用解释器运行 `python -c "import hashlib,re; page=open(r'H:\UltimaAI\UltimaAgent\docs\previews\hud-live-four-corner\hud-live-four-corner.html',encoding='utf-8').read(); style=re.search(r'<style>(.*?)</style>',page,re.S).group(1); print(hashlib.sha256(style.encode('utf-8')).hexdigest())"` 取当前 style SHA-256；
2. 将测试中冻结期望更新为该值（当前为 `f336fd77a4cbdfd963ee2305bae28181565cc364f78cf69b94ebb5ef5ba97ab1`）；
3. 核对测试其余断言（`new EventSource(eventsUrl)`、`clearDemoContent();connectSSE();`、`ultima_hud_last_event_id`、`setTimeout(connectSSE,3000)`、`eventSource.addEventListener`、四角分支、真实/演示模式、7 类事件）与 HTML 现状一致——若有个别断言因 native 模式演进不再适用，如实报告差异并只修断言本身，**不改 HTML**。

**验收（Gate T0）**：
- [ ] `H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest src/brain/tests/test_agent_server_sse.py -q --disable-warnings` 全绿；
- [ ] 证据：哈希计算输出 + 测试输出落盘 `docs/reports/evidence/cv3-0006-t4-clear/`（如目录名按工单语义命名 `t4-clear/`）。

**禁止**：不改 HUD HTML 文件内容；不改测试断言语义（只更新哈希常量，必要时按现状对齐断言但不删事件类型覆盖）。

---

### T1 · 队列读取容缺

**文件**：
- `H:\UltimaAI\UltimaAgent\src\brain\queue_source.py`（修改：`_parse_record`）
- `H:\UltimaAI\UltimaAgent\tasks\queue_engine\storage.py`（核对：REQUIRED_FIELDS）
- `H:\UltimaAI\UltimaAgent\src\brain\tests\test_queue_source.py`（新增测试）

**写什么**：
1. `_parse_record` 中 `terminal_reason = record["terminal_reason"]` → `terminal_reason = record.get("terminal_reason")`（缺省 None；类型校验保留：非 None 必须为 str）；
2. 核对 `tasks/queue_engine/storage.py`：REQUIRED_FIELDS 若含 `terminal_reason` 且对所有状态强制 → 调整为「终止态必填、非终止态可选」（QUEUED/RUNNING 等中间态允许缺省）；storage 校验语义与 state_machine 写入语义一致（state_machine 仅终止目的地写该字段）；
3. 新增单测 ≥3：①QUEUED 记录无 terminal_reason 字段 → 读取成功且值为 None；②terminal_reason 为数字等非法类型 → 仍拒绝（QueueReadError）；③含合法 terminal_reason 的终止记录正常读取；④全量快照含该 QUEUED 记录不再 fail-closed。

**验收（Gate T1）**：
- [ ] 新增单测 ≥3 全绿（`python -m pytest src/brain/tests/test_queue_source.py -q --disable-warnings`，专用解释器）；
- [ ] 实测：专用解释器跑 `from src.brain.queue_source import load_queue_snapshot; s=load_queue_snapshot(); print(s.total, s.failed)` → 成功返回（不再 fail-closed），`voice-136-pseudo-streaming` 在列。

**禁止**：不改 `tasks/tasks.json` 数据；不改 state_machine 写入语义（终止态仍写、中间态不写）；不删除 QueueReadError 对非法类型的校验。

---

### T2 · 总验收

**文件**：本工单（更新状态）+ `docs/reports/` 阶段报告 + 证据目录

**写什么**：
1. 0003 专项回归：`tools\venv-openjarvis\Scripts\python.exe -m pytest src/brain/tests/test_voice_profile.py src/brain/tests/test_voice_wakeword_reload.py src/brain/tests/test_persona_constraints.py src/brain/tests/test_reply_filter.py -q --disable-warnings` → 51 passed 全绿；
2. 全量回归：`tools\venv-openjarvis\Scripts\python.exe -m pytest src -q --disable-warnings` → 725 passed + 120 subtests passed / **0 failed**（2 failed 清零）、无新增失败；
3. 阶段报告 `docs/reports/stage-0003-t4-clear-20261030.md`：Gate 逐条核对、修复前后失败对照（Before: 2 failed / After: 0 failed）、证据路径、越界声明（未动：HUD HTML 内容 / tasks.json 数据 / 0003 范围 / 0004-0005 / 第三方库）；
4. 证据落盘 `docs/reports/evidence/t4-clear/`：哈希计算、queue_source 单测、快照读取实测、专项回归、全量回归输出；
5. 回执 8 字段按 Codex 范式 §5 输出；完成后通知主脑复核 0003 T4 转绿并走 0003 冻结门。

**验收（Gate T2）**：专项 51 passed + 全量 0 failed + 阶段报告逐项勾选 + 回执 8 字段齐全 + 越界声明如实。

---

## 3. 给编码代理的任务粘贴模板

```
T0 HUD 冻结哈希重冻结：已完成；style SHA-256=f336fd77...97ab1，HUD HTML 未改，6 passed
T1 队列读取容缺：已完成；新增4项边界测试，10 passed + 2 subtests；生产快照42条可读且 tasks.json 哈希未变
T2 总验收：已完成；0003原专项51 passed；fresh全量731 passed + 120 subtests / 0 failed；阶段报告与证据已落盘
```

---

## 4. 验收要点

- [x] 范围冻结内逐项完成（无越界：未动 HUD HTML 内容 / tasks.json 数据 / 0003 范围 / 0004-0005 / 第三方库）
- [x] 每 T 验收清单全绿 + 自证完整
- [ ] 0003 T4 已技术转绿（2 failed 清零、无新增稳定失败）且阶段报告已产出；待主脑复核 → 0003 冻结 tag
