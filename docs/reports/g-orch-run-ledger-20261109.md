# G-ORCH 八环节运行台账（2026-11-09 实测）

> 口径：只记录**实测证据**，不记录设计意图。每一步「是否真跑」以产物文件与进程行为为准，不以代码存在为准。
> 本次样本：`run_dir = %TEMP%\orch_live_8b8c1ef2`，需求文本「给 UltimaAgent 增加一个心跳文件写入能力」。

## 一、八环节实测状态

| # | 环节 | 应有执行者 | 载体 | 实测结果（修复后） | 状态 |
|---|---|---|---|---|---|
| ① | 任务理解 | DeepSeek | `run_stage(decompose)` 的 `REQUIREMENT UNDERSTANDING` 段 | 用**未改写的口语需求**直跑，产出复述 + **11 条歧义**（含「主循环卡死时心跳还有意义吗」），`verdict: blocked` 正确拦住 | **通** |
| ② | 拆分依赖 | DeepSeek | `orchestrate-order.py` → `run_stage(decompose)` | 产出 `decompose.json`：U1–U4 单元、依赖与写入域分析、`VERDICT` 行 | **通** |
| ③ | 工单制定 | DeepSeek | 同上 → `run_stage(work_order)` | 产出 `work_order.json`：范围冻结、D1–D6 待决策带默认值、DoR 六门各带可执行检查命令 | **通** |
| ④ | 排程确认 | DeepSeek | 同上 → `run_stage(schedule)` | 产出有效排程表（order / work_order / depends_on / wip_slot / window / gate，5 个 WO，WIP 限 3），`VERDICT: COMPLETED` 被正确提取 | **通** |
| ⑤ | 多 Agent 派发 | Codex | `dispatch-work-order.py` | 两小时内真跑 6 次；2 次被主表脏数据打断（读出端已宽进严出），1 次拿到 `receipt_valid:true` | **通** |
| ⑥ | 监控/心跳/生命周期 | sentinel | `src/brain/sentinel.py` | `.sentinel.lock` + `heartbeat.jsonl` 持续增长，进程常驻 | **通（只覆盖心跳）** |
| ⑦ | 独立审计（两轮） | DeepSeek | **新增** `scripts/audit-work-order.py` | 两个独立会话，Round 2 明示「不沿用 Round 1 结论」；实测对 w7 证据判 **两轮 FAIL**、`audit_passed:false`、exit 2 | **通** |
| ⑧ | 打 tag 提交 | 审计后的执行端 | **新增** `scripts/freeze-work-order.py` | 无 `audit.json` 或 `audit_passed != true` 一律拒绝；实测拒绝成功，`git tag --list` 零创建 | **通** |

## 二、四个断点的修法（已全部落地）

| 断点 | 根因 | 修法 | 验证证据 |
|---|---|---|---|
| ④ 排程产出无效且假报成功 | `run_stage` 把 `verdict` **硬编码为 `completed`**（只看 HTTP 状态，不看产出）；schedule 提示词没告诉模型「你没有工具」 | ① 三条 stage 提示词统一加「NO tools / 禁止输出命令与代码块」；② schedule 指定输出六列排程表；③ 新增 `_looks_like_tool_call`，命中 `<｜｜`、`DSML`、`tool_calls`、```` ```bash ``` 等标记即 raise 并写 `<stage>-failed.json`；④ 新增 `_extract_verdict`，从产出末尾读 `VERDICT:` 行 | 真跑三环节：schedule 产出 5 个 WO 的排程表、零工具标记、`verdict: completed` |
| ① 任务理解无入口 | 原始需求先被人工改写再喂入，DeepSeek 碰不到原话 | decompose 提示词要求先输出 `REQUIREMENT UNDERSTANDING`：复述需求 + 列出所有会改变范围或验收的歧义 | 用**未改写的口语需求**直跑，产出 11 条歧义，`verdict: blocked` 正确拦住 |
| ⑦ 独立审计无载体 | `AUDIT → COMPLETED` 要求 `audit_passed`，但无任何代码填充该字段 | 新增 `scripts/audit-work-order.py`：Round 1 / Round 2 两个独立会话，Round 2 被明确告知「Round 1 只是参考不是真理」，需自行重判；两轮都 PASS 才 `audit_passed: true` | 对 w7 证据真跑：两轮均 FAIL、exit 2、`audit_passed:false`；Round 2 独立发现「receipt 块为空」这一程序性拦阻 |
| ⑧ 打 tag 无载体且顺序反了 | tag 在 Codex 提交后由人工打，审计并未前置 | 新增 `scripts/freeze-work-order.py`：无 `audit.json` 或 `audit_passed != true` 一律拒绝，拒绝时不创建任何 tag | 用 FAIL 的 audit 真跑，拒绝成功，`git tag --list` 零创建 |

**密钥管道（"钥匙在、管道没接"的补口）**：`scripts/orchestrate-order.py` 原先只查 `os.environ`、不读 `config/.env`。已加 `_load_env_file()`，在密钥检查前加载 `.env`，且不覆盖已有环境变量。实测**删除环境变量**（`env_preset=False`）后仍跑通 exit 0。

## 三、跨环节地基问题

| 问题 | 现状 | 影响环节 |
|---|---|---|
| 公共账本无写入门 | 18766 登记接口实测**未监听**；各项目直接改 `H:\UltimaAI\_shared\queue\global-queue-index.md` | ⑤ 派发 |
| 读出端已宽进严出 | 未知状态归一 `unregistered` 继续生成 + 点名；畸形行容错；行尾保真；重复工单仍 fail-closed | ⑤ 已解除阻塞 |
| 全量测试无固定口径 | 28 项既有历史失败，未修、未 ignore | ⑤ 验收 |

## 四、结论

- **八个环节全部有了执行载体**：①–④ DeepSeek（`orchestrate-order.py` + `orchestrator.run_stage`）、⑤ Codex（`dispatch-work-order.py`）、⑥ sentinel（心跳）、⑦ DeepSeek 两轮（`audit-work-order.py`）、⑧ 审计通过后的执行端（`freeze-work-order.py`）。
- **仍存局限**：⑥ 只覆盖心跳与退出异常，不改任务状态；⑤ 仍依赖主表干净，而**写入门尚未落在写入端**，18766 登记接口实测未监听——这两条会继续让派发受制于别人的写入质量。
- **回归**：`tests/test_orchestrate_order.py` **13 passed**（含新增的 verdict 提取、工具调用标记检测、工具调用 fail-closed 三类判据）；`tests/test_receipt_contract.py` + `tasks/queue_engine` 合计 **16 passed**。

```powershell
cd H:\UltimaAI\UltimaAgent
# 注入 .env 的 DeepSeek 凭据后
& .\tools\venv-openjarvis\Scripts\python.exe .\scripts\orchestrate-order.py `
  --requirement '<需求文本>' --run-dir <独立目录>
# 检查三份产物
Get-ChildItem <run_dir>\stages
```
