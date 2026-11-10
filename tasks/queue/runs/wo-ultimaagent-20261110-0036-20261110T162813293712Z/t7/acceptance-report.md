# wo-ultimaagent-20261110-0036 · T7 总验收报告

## 1. 结论

T0–T7 按现行卡面全部完成。T7 没有把普通交付单 `verify-order.py` 的六项结构性失败伪装成 PASS，而是按 Gate T7 第 3 条完成当前版/锁定版同 run 对照，并用逐 T 证据、两轮审计、回归基线、真实 fail-closed 复现与存量 frozen tag 只读回放组成元工单独立验收路径。

方案文件 `docs/plans/plan-ultimaagent-task-system-rework-20261110.md` 已存在，T7 取证时 SHA-256 为 `dbeccedb95eb24a916a6b5df202150c9acb60b33a5c01baa9aeb96c358080eca`。

## 2. 门号逐条结果

| 门号 | 结果 | 提交 / 核心结论 | 证据 |
|---|---|---|---|
| T0 | PASS | `9cf482051b90526cfb4d8ea7f067522f97189693`；只读基线，`t3_cutover_commit` 初值为 `null` | `../baseline-snapshot.json` |
| T1 | PASS | `03d8df297e9a89d9ee9f51cef07bfc13dfd4e698`；JSON 唯一权威、双表派生、名额改读 JSON | `../t1/pre-change.json`、`../t1/post-change.json` |
| T2 | PASS | `fbd685659f1c36a735281710161d7b52cb078c8f`；写域内干净 + 实际路径反向防漏 | `../t2/pre-change.json`、`../t2/post-change.json` |
| T3 | PASS | 切换 `26bcb9dc26659ae11a7986ef4bb4522ba8103842`；回填 `7edf8c9516718d5257f6fe3e61ab13bb968e1d31` | `../t3/pre-change.json`、`../t3/post-change.json` |
| T4 | PASS | 实现 `78bc5442`；回填 `3fef13fa`；互斥 Gate 能在派发前被定位 | `../t4/pre-change.json`、`../t4/post-change.json` |
| T5 | PASS | 实现 `8a05eb17`；回填 `faa4f9d5`；单一冻结入口，三组 move-only 归档 | `../t5/pre-change.json`、`../t5/post-change.json` |
| T6 | PASS | 实现 `6762a970`；回填 `ce0e4c12`；`S-REVIEW.max_tokens=8192`，长输出正常收尾 | `../t6/pre-change.json`、`../t6/post-change.json`、`../t6/work-order-probe/stages/work_order.json` |
| T7 | PASS | 七处回填完成；严格 DoR PASS；双版 verifier 差异 0；路径 A/B 已复现；回归与 T0 一致 | `pre-change.json`、`verifier-comparison.json`、`regression.json`、`path-b-frozen-replay/receipt.json`、本报告 |

## 3. Gate T7 逐条判定

1. **回填残留**：扫描计数 `0`。
2. **DoR**：登记 venv 置于 PATH 首位后，字面执行 `python scripts\validate_work_order.py tasks\queue\wo-ultimaagent-20261110-0036--task-system-rework.md --strict`，输出 `PASS`，exit `0`。系统 Python 缺 `jsonschema`，该环境差异已在 `pre-change.json` 原样记录，未安装依赖、未改测试。
3. **普通交付单 verifier 对照**：当前版与锁定 revision `90a4a9d5` 旧版对同一 `T165817586641Z` run 均 exit `2`、`verified=false`，六项失败集合和顺序完全一致，差异计数 `0`。详见 `verifier-comparison.json`。
4. **双路径**：
   - 路径 A run：`tasks/queue/runs/wo-ultimaagent-20261110-0036-20261110T165817586641Z`。严格 validate exit `0`，dispatch `--dry-run-dor` exit `0`，两轮 audit 的 T0–T7 均 PASS 且 `audit_passed=true`；freeze 使用真实 `done.json` / `verify.json` 后 exit `2`，原样 fail-closed，未创建 tag。该终点正是 Gate 第 3 条裁定的元工单结构性缺口，不是伪造的成功冻结。
   - 路径 B run：`tasks/queue/runs/wo-ultimaagent-20261110-0036-20261110T162813293712Z/t7/path-b-frozen-replay`。只读回放 `wo-orb-w8-frozen-20261110`：annotated tag object `6227e582...` 可剥离到 commit `acf9ea8c...`、tree `9b24d430...` 与卡片 blob `6a47f57e...`；前后 tracked status 条目均为 `21`，未创建、移动或重打 tag。
5. **改造前 / 改造后并列**：T1–T7 均有双档；所有差异都在下节枚举，没有静默差异。
6. **全量回归**：`python -m pytest scripts\tests -q` 为 `6 failed / 45 passed`，与 T0 登记 venv 基线逐项一致，新增失败 `0`。
7. **写域干净**：T7 产物提交后对本单写域执行 scoped porcelain；最终结果记录在 `post-change.json`。写域外既有条目不参与判定。

## 4. 六项 blocking_failures 原样记录与结构性说明

当前版与旧版原样输出均为：

```text
receipt_valid
terminal_state_legal
tree_unchanged
order_manifest
declared_files_landed
declared_command_plan
```

- `receipt_valid`：真实派发回执把本单最终消息按普通交付契约判为无效；T7 禁止改写或补造生产 `done.json`。
- `terminal_state_legal`：真实回执为 `blocked`；普通交付单冻结只接受 `audit` / `frozen`，而本元工单此前依规则在 Gate 冲突处 BLOCKED 停机。
- `tree_unchanged`：普通交付契约要求派发终态树与回执记录一致；本单职责正是改动任务系统自身，且卡面/状态视图在恢复过程中继续发生有授权变化，结构上不能用“树未变”自证。
- `order_manifest`：0036 是改造前形成的分阶段元工单卡，没有普通交付 verifier 要求的 `gorch-manifest` 块；T7 禁止为绿灯反向改造该 verifier 契约。
- `declared_files_landed`：缺少上述 manifest 后，普通 verifier 的保守解析没有得到可绑定到单次派发的文件清单；跨 T、跨提交的元改造不能伪装成一次普通派发落地。
- `declared_command_plan`：卡面把各 T 命令写在阶段 Gate 中，没有普通 verifier 可执行的 manifest command plan；元工单的逐 T 双档与总验收由本报告独立对账。

结论：六项失败证明“元工单缺独立验收路径”，不是本轮脚本退化；旧版同样六项是反向证据。该缺口已同时写入 `docs/references/lessons-log.md` 的 L116（督导方既有）和 L117（本轮追加）。

## 5. 双档差异清单

- T1：前档无 `queue-status.json`、派发/名额读 Markdown；后档由 JSON 唯一权威派生双表。前档辅助解析曾漏一行（156 / frozen 111），后档用完整 marker 复核为 157 / frozen 112；状态改判数 `0`，这是已上报的取证修正。
- T2：前档要求全仓 tracked tree 干净且无反向防漏；后档只判声明写域，同时拒绝实际改动越界。`audit_passed is True` 与 truncated 拒绝保持不变。
- T3：前档按 16000 / 40000 字符常量截断、`visible` 为布尔；后档完整对象注入、对象边界拆分、sha256 字节对账、`visible` 为清单。两轮同身份审计结构不变。
- T4：前档矛盾规则数 0；后档有 `porcelain-delta-count-after-commit`，0035 命中 1，0036 / 0033 命中 0，输入 hash 前后相同。
- T5：前档 4 个冻结 `.py` 入口并存，根目录有实测 15 个 now 脚本 / 63 个 prompt；后档只留 `freeze-work-order.py`，其余 move-only 归档，三组 manifest hash 前后相同。
- T6：`S-REVIEW.max_tokens` 从 4096 变为 8192；`S-MAIN` / `S-EXEC` 差异为空；work_order 实跑 `tokens.out=2840` 且有 `VERDICT:` 收尾。
- T7：回填残留从 3 变为 0；系统 Python 的缺依赖失败改由登记 venv 下字面命令 PASS；当前/旧 verifier 的六项失败差异为 0；普通 verifier 不适配项全部显式上报。

## 6. 易变环境计数

T0 快照为 porcelain `565`（tracked `19` / untracked `546`）；T7 只读实测为 `560`（tracked `21` / untracked `539`），总量差 `-5`。依卡面规则，这类易变计数只记录、不停机；本单没有清理任何既有改动。

## 7. 改动文件清单

- 核心脚本：`scripts/audit-work-order.py`、`dispatch-work-order.py`、`freeze-work-order.py`、`render-queue-views.py`、`validate_work_order.py`、`verify-order.py`、`scripts/tests/test_engineering_dispatch.py`、`src/brain/slot_adapter.py`。
- 状态源与视图：`tasks/queue/queue-status.json`、`tasks/queue/index.md`、`H:\UltimaAI\_shared\queue\global-queue-index.md`。
- 回滚与归档：`tasks/queue/_backup/20261110-0036/`；`tasks/queue/archive/20261110-0036/` 下 3 个冻结遗留、15 个一次性派发脚本、63 个提示词快照；三个 `scripts/*.archived.md` 指针。
- 方案与卡面：`docs/plans/plan-ultimaagent-task-system-rework-20261110.md`、`tasks/queue/wo-ultimaagent-20261110-0036--task-system-rework.md`。
- 经验记录：`docs/references/lessons-log.md`（保留 L116，只追加 L117）。
- 证据：`tasks/queue/runs/wo-ultimaagent-20261110-0036-20261110T162813293712Z/` 的基线、T1–T7 双档、work_order probe 与本报告；路径 A 的 `audit.json` 留在真实 `T165817586641Z` run。

## 8. 越界声明

无。T7 未修改 T0–T6 产品代码，未清理写域外既有改动，未伪造 `done.json`，未创建或移动冻结 tag，未把普通 verifier 的失败改写成 PASS。
