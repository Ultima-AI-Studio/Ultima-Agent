# wo-ultimaagent-20261108-0031 结果报告

> 当前状态：T0–T3 Gate 已通过；T4 总验收待执行。本文在 T3 建立冻结门对照证据，T4 将补入总验收最终读回。

## 1. 范围与改动清单

- T0：新增机器契约 `docs/specs/work-order.schema.json` 与人读契约 `docs/specs/work-order-contract.md`；将主检出区未跟踪的本工单卡/方案逐行不变纳入分支，供自举 Gate 使用。
- T1：新增 `scripts/validate_work_order.py`、`tests/test_validate_work_order.py` 与 31 张卡回归登记 `docs/reports/wo-ultimaagent-20261108-0031-t1-regression.json`。
- T2：只在 `scripts/dispatch-work-order.py` 增加 DoR 接线、`--skip-dor`、dry-run 测试钩子和审计字段；新增 `tests/test_dor_gate.py`。
- T3：新增 `scripts/freeze_work_order.py` 与 `tests/test_freeze_work_order.py`；只执行 dry-run。
- T4：本报告最终收口与指定范围总验收，待执行。

## 2. 各 T Gate 逐项结果

### T0

- Schema 命令：`python -c "import json,jsonschema; ... Draft202012Validator.check_schema(s); print('OK')"`
- 关键输出：`OK`；契约 `sections=7 missing=[]`；兼容卡登记 `compatibility_cards=8`。
- 提交：`917c2a14212a919c796197b0f7ba750b65c85a8c`。

### T1

- 命令：`python -m pytest tests\test_validate_work_order.py -o addopts= -q`
- 关键输出：`11 passed`。
- 逐卡 CLI：`card_count=31 pass_count=31 fail_count=0`；回归 JSON 读回 `card_count=31 all_pass=True statuses=PASS`。
- JSON CLI：`exit=0 status=PASS errors=0 warnings=0`。
- 提交：`ab913e72c8bc89400c6a7b44ac855fd9259e8515`。

### T2

- 命令：`python -m pytest tests\test_dor_gate.py -o addopts= -q`
- 关键输出：`6 passed`。
- 负样本：exit 2，`dor_status=FAIL`，错误保留 `code/line/message`，未写指定 record，`runs/<order>-*` 前后集合一致。
- PASS dry-run：临时 `dispatch-record.json` 含 `dor_status=PASS`。
- `--skip-dor`：临时记录含 `dor_skipped=true` 与非空 `dor_errors`。
- 提交：`e0582871fc7520601543e8da46e9282b19f7476a`。

原派发流程行为差异仅有：

1. 卡路径由 `tasks/queue/<order>*.md` 唯一前缀优先解析，无命中才用 `--card`；多命中 fail-closed。
2. 起共享登记、锁、run 目录和 Codex 进程前新增 DoR；FAIL 新增退出码 2。
3. PASS 的 `dispatch-record.json` 新增 `dor_status: PASS`。
4. 仅 FAIL 且显式 `--skip-dor` 时新增 `dor_skipped: true`、原样 `dor_errors`。
5. 未改变既有 lock、run 命名、Codex 参数、状态推进或 worker 生命周期。

### T3

- 命令：`python -m pytest tests\test_freeze_work_order.py -o addopts= -q`
- 关键输出：`7 passed`；baseline 不符、已有 tag、证据缺失分别 exit 3。
- 0030 dry-run：HEAD/baseline `a4d968af292bbfb7000bdcc0c913b03051e1d1e1`；4 个证据文件全部非空并哈希；JSON `status=PASS`。
- 不变式读回：`BEFORE tags=249 gates=2`；`AFTER exit=0 tags=249 gates=2 tag_diff_count=0`；`DRY_GATE_EXISTS=False`。
- 提交：待本 T 提交后回填。

### T4

- 待执行，不能提前写成通过。

## 3. 正负样本矩阵

| 样本 | 数量 | 结论 | 关键错误码/说明 |
|---|---:|---|---|
| `tasks/queue/wo-*.md` 存量及本卡 | 31 | PASS | 30 张 `legacy-queue` 带 `W_LEGACY_PROFILE`，本卡 `structured-v1` 无 warning |
| 缺“本阶段不做” | 1 | FAIL | `E_NO_FORBIDDEN`，line 13 |
| 任务表 T 集合与明细不一致 | 1 | FAIL | `E_T_SET_MISMATCH`，line 45 |
| T2 缺 `**禁止**` | 1 | FAIL | `E_MISSING_DETAIL_FIELD`，line 106，消息含 T2/forbidden |
| status=`执行中` | 1 | FAIL | `E_STATUS_NOT_DISPATCHABLE`，line 3 |
| revision 非十六进制 | 1 | FAIL | `E_REVISION_FORMAT`，定位到头部行 |
| Gate 只有“代码质量良好” | 1 | FAIL | `E_GATE_WEAK`，定位到具体 T |
| freeze baseline 不符 | 1 | FAIL/exit 3 | `baseline mismatch` |
| freeze tag 已存在 | 1 | FAIL/exit 3 | `tag already exists`；无 tag 变化 |
| freeze evidence 缺失 | 1 | FAIL/exit 3 | `evidence glob 没有命中` |

## 4. 与 v01/v03 冻结门口径对照表

| 关键断言 | v01 做法 | v03 做法 | 通用脚本对应 |
|---|---|---|---|
| 基线绑定 | `HEAD == BASELINE` | 内部完成 tag/`BASE` 与 manifest 绑定 | `--baseline`，先校验 `rev-parse HEAD` 精确相等 |
| 工作树/暂存区 | 显式检查 tracked diff 与 cached diff 为空 | 通过候选源 manifest/hash 锁定获批内容 | 同时检查 `git diff --name-only` 与 `git diff --cached --name-only` |
| 目标 tag 不得已存在 | `git tag --list TAG` 为空 | 同样检查且 gate 文件也不得已存在 | `git tag --list <tag>` 非空立即 exit 3；非 dry-run gate 用独占 `x` 创建 |
| 证据存在与完整性 | 固定 W1/W2 路径、manifest SHA-256 逐项核验 | W4 round1/round2 pins、source manifest、v01 manifest 逐项核验 | 每个 `--evidence` glob 必须命中；每个文件存在、非空并写入 SHA-256 |
| JSON 技术结论 | 检查 `all_technical_pass is True`、行政 `status`/checks | 检查 `verdict=PASS`、conditions 全真 | 递归检查 `status=PASS`，`all_technical_pass`/`all_*pass=true/PASS` |
| Owner 授权留痕 | gate JSON 含 `approved_by/approved_at/authorization_text` | gate JSON 含授权原话、上下文、scope/known_limits | `--approve-text` 原样进入 `approval_text`；缺省仅标 `approved_by=owner` 且文本留空，不伪造原话 |
| Gate JSON | 写 `tasks/queue/gates/<tag>.json` 并列证据 hash | 同路径结构并含 scope/known limits | 默认同路径；可用 `--gate-json`；字段含 gate/decision/order/baseline/evidence/scope/known_limit/schema_version |
| Annotated tag | `git tag -a ... -m <gate sha256>` | 同样在 message 中绑定 receipt hash | 非 dry-run 用 `git tag -a`，message 含 gate JSON SHA-256；本单未执行该分支 |
| Tag 回读 | `rev-parse TAG^{}` 必须等于基线 | 同样回读等于 `BASE` | 非 dry-run 创建后强制 `rev-parse <tag>^{}` 等于 `--baseline` |
| 冻结后边界 | v01 保留旧 BLOCKED 限制、不自动派发 | v03 保留语音/麦克风限制、下游未派发 | `scope` + `known_limit` 明示；通用脚本不做下游派发、状态机或产品文档改写 |

## 5. 越界声明

无。未修改 `H:\UltimaAI\UltimaManager`、`src\brain\orchestration\ledger\**`、`src\brain\orchestration\queue.py`、`tasks\queue_engine\card_contract.py`、北极星 HTML 或 `scripts\tracker-live.py`；未删除测试、未放宽既有断言、未使用 skip/xfail、未新增第三方依赖、未真正创建任何 tag、未改任何基线已有 `wo-*.md` 正文。

## 6. 已知限制

1. 未跑全量 pytest：锁定基线不包含 0030 分支上的未合入 `__init__.py` / `registry.py` 及三份 ledger 测试，按工单只跑本单新增测试与 0030 指定 31 项；不伪报全量通过。
2. 0030 的 31 项回归位于独立 worktree `ultimaagent-m4-ledger-20261108`，因此在该 worktree 原地只读执行；这是隔离回归，不是将受保护 ledger 文件移入本分支后的集成测试。
3. 本单未真打 tag；T3 只证明 dry-run 生成内容、失败门和零写入/零 tag 变化。非 dry-run 分支需 Owner 独立验收后执行。
4. 未修改任何存量工单卡。为兼容 30 张历史卡，schema/validator 放宽了标题前缀、历史状态词、L2 锁定字段、T0 起始、任务表/明细并存、四段标签写法、两张计划绑定短卡无 `##` 章节及历史附录；这些放宽只存在于 `legacy-queue`，`--strict` 会把兼容 warning 升为 FAIL。
5. `approved_by` 缺省为 `owner` 角色标记；未提供 `--approve-text` 时 `approval_text` 留空，不把角色标记冒充具体授权原话。
