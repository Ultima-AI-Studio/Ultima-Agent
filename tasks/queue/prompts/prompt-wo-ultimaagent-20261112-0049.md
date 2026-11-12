# 载荷 · wo-ultimaagent-20261112-0049

> 工单：`tasks/queue/wo-ultimaagent-20261112-0049--health-provider-note-truthfulness.md`
> 权威文档清单：`docs/INDEX.md`
> 执行端：Codex

## 任务

修 `/health` 的 `provider_note` 诚实性：当前 `provider_configured=false` 时对外宣称「主脑未配置，/ask 将无法作答」，但实链路（`provider_for(_MAIN).chat`）用完整的 `impl` / `endpoint` / `model` 正常作答。**不得改 `/ask` 任何行为。**

## 硬约束（17 条，逐条不可违反）

1. 只改 `src/brain/agent_server.py` 的 `_health_payload()` 函数体（L1407-1421 区间）。
2. `provider_configured` 那一行**字节不变**，保留原计算 `bool(_MAIN.get("enabled") and str(_MAIN.get("endpoint") or "").strip())`。
3. payload **新增** `provider_answerable` 布尔字段，值 = `impl` ∧ `endpoint` ∧ `model` 三者 `str(...).strip()` 均非空。
4. `enabled` **不得**参与 `provider_answerable` 的计算。
5. A 态（三要素齐备且 `enabled` 真）→ **不写** `provider_note`。
6. B 态（三要素齐备且 `enabled` 假）→ 写 note，须含「未显式配置」+「内置默认」两义，实填 `impl` 与 `model` 的实际值，**禁止出现「无法作答」**。
7. C 态（三要素任一为空）→ 写 note，保留「无法作答」语义并**指名缺失项**（impl / endpoint / model 中哪些为空）。
8. C 态优先于 A 态：`enabled=true` 但三要素缺任一，判 C。
9. 判定只在 `_health_payload()` 内单点完成，**不得新建外部判定函数或共享 helper**。
10. **不做网络探测、不引入任何 IO**（`/health` 必须零延迟）。
11. 不改 `provider_for()` / `require_main()` / 四处分派（L718 / L1006 / L1159 / L1216）任何字节。
12. 不改 `main_settings()` / `slot_adapter.py`。
13. 不改 `/health` 其它字段：`ok` / `model` / `agent` / `tools` / `provider` / `provider_model`。
14. 测试只改 `src/brain/tests/test_provider_layer.py`：改造原 L444-457（真 C 态，断言强度**不得降低**），新增 B 态用例（`endpoint` 有值 + `enabled=false`，线上真实情形），补 C 态 impl / model 缺项断言。
15. 原 L431-441（A 态）保持不变，只可增断言不可减。
16. 队列登记只定点追加 `tasks/queue/queue-status.json` 一条，保持纯 LF / 2 空格缩进 / CRLF 0，**禁止**整文件重写。
17. 不改 `scripts/` 下任何 G-ORCH 脚本。链路脚本若报错，**停下报主脑**，不得自行修改脚本绕过。

## 执行顺序（串行，前一 Gate 全绿才进下一条）

T1 → T2 → T3 → T4

- T1：`agent_server.py` 判定改造。Gate：`git diff` 只含 `_health_payload()` 区间；`provider_configured` 行不出现于 diff；`provider_for(` / `require_main(` / `main_settings(` 引用次数与改前一致。
- T2：测试改造与新增。Gate：`pytest src/brain/tests/test_provider_layer.py -q` 全绿且 A/B/C 三态各有断言。
- T3：队列登记。Gate：`json.load` 通过、`git diff` 只含本单一条、`scripts/render-queue-views.py` exit 0、CRLF 0。
- T4：总验收六项 + 链路验收（见卡 §3 T4）。

## 停线条件（命中任一条即停，不臆测继续）

1. 发现本卡与代码事实冲突（行号、字段名、函数签名对不上）。
2. 发现本卡内部自相矛盾（不同章节对同一件事要求相反）。
3. Gate 无法用命令判定，或判定结果与卡写的期望不一致且无法自行厘清。
4. 任何改动需要越出 §1「本单只做」的写域。

停线时请明确写出：**哪一条 Gate、卡上怎么写的、实际是什么、你判断该怎么改**。不要为了让流程继续而降低判据。

## 自证模板

```
T1 已完成，Gate 全绿
- 改动行数：+N/-M，区间：_health_payload() Lxxxx-Lyyyy
- provider_configured 行 diff 命中：0
- provider_for/require_main/main_settings 引用次数：改前 X / 改后 X
- 三态文案：A=（无 note）；B="..."；C="..."
- 越界：无

T2 已完成，Gate 全绿
- pytest src/brain/tests/test_provider_layer.py -q → N passed
- A/B/C 三态断言位置：...
- 原 C 态测试 provider_configured is False 断言仍在：是

T3 已完成，Gate 全绿
- queue-status.json records: 169 → 170
- git diff 行数：+K/-0
- render-queue-views exit: 0
- CRLF: 0

T4 总验收
- 线上 /health：provider_note="..."（不含「无法作答」）
- 构造 C 态 note："..."
- 全量：N passed / M failed（基线 M 失败数对照）
- 基线 worktree 失败数：M
- /ask C1/C2 探针：改动前 ... / 改动后 ...
- 改动文件清单：...
- 越界声明：无
```

## 参考

- 需求包：`tasks/queue/requirements/req-health-provider-note-20261112.md`
- DeepSeek 三阶段：`tasks/queue/runs/req-health-provider-note-20261112/stages/`
- 权威文档清单：`docs/INDEX.md`
