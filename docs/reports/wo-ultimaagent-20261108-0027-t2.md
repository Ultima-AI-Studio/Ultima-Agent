# wo-ultimaagent-20261108-0027 T2 收尾演练报告

- 工单：`wo-ultimaagent-20261108-0027`
- 阶段：T2 收尾（第三次续派）
- 日期：2026-11-10（Asia/Shanghai）
- 执行状态：`READY_FOR_DEEPSEEK_AUDIT`
- 方案口径：`docs/plans/audit-stage-gate-plan-20261108.md`
- 专用解释器：`H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe`（Python 3.13.16）

## 1. 本轮边界

本轮只完成 T2 收尾，没有重做或修改已冻结的 T0/T1。没有修改
`src/brain/guardrails/reviewer.py`、`src/brain/guardrails/receipt.py`、
`docs/tracker/北极星上线任务清单.html`，也没有修改 0026 的任何既有文件。

用户点名的 `check_stage("wo-ultimaagent-20261108-0026", "T2", Path("data/evidence"))`
按实现只会读取 `data/evidence/wo-ultimaagent-20261108-0026/T2/independent-review.json`，
而本单归档要求位于 `data/evidence/wo-ultimaagent-20261108-0027/T2/`。因此本轮以同一组
三项原始检查生成两份目录自洽的复核结论：前者供指定正例门消费，后者归档为 0027 T2
产物；两份文件各自的 `work_order` 均与所在目录一致。0026 路径下只新增该复核结论，
没有覆盖或改写 0026 既有产物。

## 2. 正例端到端演练

复核对象是 0026 的 T0/T1 两个真实提交：

| 阶段 | 提交 | 内容 |
|---|---|---|
| T0 | `46adbd1f` | 标准化独立审计提示词、加载器与测试 |
| T1 | `1ee325f4` | 统一审计报告规范、生成器与测试 |

`independent-review.json` 的角色为 `eng.audit`，`ok=true`、`blocker=0`、
`major=0`、`minor=0`，`checked` 严格且仅包含以下三项实际动作：

1. 测试复跑：`data/evidence/wo-ultimaagent-20261108-0027/T2/audit-test-rerun.log`
   - 指定解释器运行 T0/T1 两个测试文件。
   - 结果：`15 passed, 2 subtests passed`，`PYTEST_EXIT_CODE=0`。
2. 写域核对：`data/evidence/wo-ultimaagent-20261108-0027/T2/audit-write-domain.log`
   - 对 `46adbd1f`、`1ee325f4` 的 20 个路径条目逐项对照 0026 工单 `fileDomain[]`。
   - 结果：`OUTSIDE_DOMAIN_COUNT=0`、`FORBIDDEN_FILE_COUNT=0`。
3. 断言抽查：`data/evidence/wo-ultimaagent-20261108-0027/T2/audit-assertion-review.log`
   - 打开并逐方法检查 `test_audit_prompt.py` 与 `test_audit_report.py`。
   - 结果：15 个测试方法、27 个断言调用点，`EMPTY_ASSERTION_COUNT=0`；没有
     `assertTrue(True)`、`assertFalse(False)` 或同值比较式空断言。

指定正例门的原始结果落在
`data/evidence/wo-ultimaagent-20261108-0027/T2/positive-stage-gate.json`：

```json
{
  "work_order": "wo-ultimaagent-20261108-0026",
  "stage": "T2",
  "evidence_root": "data/evidence",
  "passed": true,
  "reasons": []
}
```

独立回读同时确认两份复核结论都满足 `ReceiptValidator`，且分别调用
`check_stage(0026, T2, data/evidence)` 与 `check_stage(0027, T2, data/evidence)`
都返回 `passed=true`、`reasons=[]`。

## 3. 三案反例演练

`negative-cases.py` 使用临时目录构造数据，不在仓库持久化伪造复核结论。最终输出
`negative-gate-output.json` 的 `case_count=3`、`all_refused=true`：

| 反例 | passed | started | dispatch exit | reason 命中 |
|---|---:|---:|---:|---|
| 缺少复核文件 | false | false | 2 | `不存在` |
| `blocker>0` | false | false | 2 | `blocker 未清零` |
| `role=dev` | false | false | 2 | `角色必须是 ('eng.audit', 'eng.security')` |

三案都没有启动下一阶段，证明门是 fail-closed，而不是只记录告警后继续。

## 4. 全量工程门与 JUnit 独立回读

执行命令：

```text
H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -X utf8 -m pytest src -q --disable-warnings --junitxml=data/evidence/wo-ultimaagent-20261108-0027/T2/full-engineering-gate.xml
```

本次完整日志 `full-engineering-gate.log` 跑到 `[100%]`，末尾为：

```text
1008 passed, 36 warnings, 122 subtests passed in 202.73s (0:03:22)
PYTEST_EXIT_CODE=0
```

`full-engineering-gate-readback.json` 不引用 pytest 摘要推算四项计数，而是独立解析
JUnit 直接子 `testsuite` 的属性并计算 XML SHA-256：

| 项 | 值 |
|---|---:|
| tests | 1130 |
| failures | 0 |
| errors | 0 |
| skipped | 0 |
| testcase 节点数 | 1008 |
| tests - testcase 节点数 | 122 |
| XML bytes | 139873 |
| XML SHA-256 | `9d2a3c5d78083d629c7fdb83e3a89e823f7f875e6faaf9f292c8fc954d00847d` |

`tests=1130` 是 JUnit suite 属性口径；其中 1008 个普通 testcase 加 122 个
pytest-subtests。四项验收计数以 JUnit 属性为准，节点数和差额同时留存，避免混淆。

本轮没有出现 `test_jarvis_ask_real_inference` 失败，因此不需要启动三次独立探针或
定点复跑，也没有把任何失败直接豁免。

## 5. 全部失败尝试与修复历史

最终绿没有覆盖以下失败或不完整证据：

1. `negative-gate-attempt1-import-error.log`
   - 首次直接运行反例脚本时，仓库根不在 `sys.path`，报
     `ModuleNotFoundError: No module named 'src'`。
   - 后续在脚本启动处从 `__file__` 解析仓库根并前置到 `sys.path`；最终三案真实运行且
     `all_refused=true`。首次失败日志保留未删。
2. `full-engineering-gate-attempt1.log`
   - 首轮只输出到 `[42%]`，没有 100% 摘要、退出码或完整 JUnit，不能作为通过证据。
   - 现存证据不足以区分超时与进程被杀，因此不虚构根因。本轮改为直接重定向到文件并
     留足运行时间，202.73 秒后完整到 100%、退出 0；attempt1 原文件保留未删。
3. `full-engineering-gate-readback-attempt1-node-count-mismatch.json`
   - 首次独立回读错误地要求 JUnit `tests` 属性必须等于 `<testcase>` 节点数，因
     `1130 != 1008` 返回失败。
   - 根因通过差额 122 与 pytest 摘要中的 `122 subtests passed` 精确对应而确认。
     最终回读改为按 JUnit suite 四项属性计数，并把 testcase 数与差额作为附加信息；
     失败回读另名保留。
4. 提交后完整验证捕获的既有 `PreferenceStore` 毫秒时间戳竞态
   - 第一次提交后全量验证：`full-engineering-gate-post-commit-attempt1-known-preference-flake.log`，
     结果为 `1 failed, 1007 passed, 122 subtests passed`；唯一失败是
     `TestPreferenceStore.test_upsert_idempotent`，两次紧邻写入的 `updated_at` 都是
     `2026-11-10T03:20:56.802+00:00`。
   - 源码根因可直接定位：`src/brain/memory/preference.py` 使用
     `datetime.now(timezone.utc).isoformat(timespec="milliseconds")`，测试又要求两次连续调用的
     时间戳不相等。同一竞态已在 `stage-jarvis-p0-20261103.md`、
     `stage-input-channel-20261030.md`、`stage-asr-correction-20261101.md` 留有历史记录。
   - 本轮 `preference-upsert-flake-probe.log` 的 10 次独立定点探针为 8 pass / 2 fail，
     证明其为时间分辨率竞态；第二次提交后全量验证
     `full-engineering-gate-post-commit-attempt2.log` 再次只在同一点失败，结果为
     `1 failed, 1007 passed, 122 subtests passed`。
   - 该 memory 实现与测试均不在本单提交范围，且当前为未跟踪的并发写域，故没有越界改
     产品代码、测试、断言或增加 skip。未改代码的第三次提交后全量验证
     `full-engineering-gate-post-commit.log` 完整到 100%，结果恢复为
     `1008 passed, 122 subtests passed`、`PYTEST_EXIT_CODE=0`。

## 6. 回执、越界与依赖声明

`data/evidence/wo-ultimaagent-20261108-0027/T2/receipt.json` 是合法 JSON，含用户要求的
14 个顶层字段、17 条 evidence、5 条 acceptance。独立回读结果：缺失字段 0、
`ReceiptValidator` issues 0，且正文同时包含 `READY_FOR_DEEPSEEK_AUDIT`、
`自检 PASS`、`PYTEST_EXIT_CODE=0` 与 `1008 passed`。

没有做自动调度器，没有触碰模块4 多 Agent 编排，没有引入新依赖，没有改产品默认值，
没有重启 daemon，没有调用麦克风、录音或真实模型。共享工作区其他线的修改没有被
回滚、覆盖或加入本单暂存区。

## 7. 提交、tag 与推送

正例复核日志、两份 `independent-review.json` 与正例门结果按契约单独精确暂存为
`[audit]` 提交；本报告与其余 T2 执行证据再精确暂存为本单收尾提交。全程禁止使用
`git add -A`、`-u`、`.` 或通配。tag 名固定为
`ultimaagent-audit-stage-gate-20261108`，只指向最终本单收尾提交。
推送使用工单指定的 7897 代理覆盖命令，最多三次；实际 tag SHA 与 push 结果以本次
最终交接输出为准，不在提交前预写成功结论。

## 8. 结论

T2 四项验收均有当前证据：正例独立复核与阶段门通过、三案反例全部拒绝、全量工程门
0 failures/0 errors、合法 JSON 回执与完整失败历史均已落盘。当前状态为
`READY_FOR_DEEPSEEK_AUDIT`，看板回写仍归主脑。
