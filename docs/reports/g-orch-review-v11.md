# G-ORCH 冻结门复审 · 第十一轮

> 复审对象：`7810e9d9`（第十一轮改造：命令契约收紧 + 执行收据严格化 + schema 统一）
> 复审方式：Codex（gpt-5.6-sol，high reasoning，只读复核，未改文件）
> 结论：**VERDICT: FAIL** —— 三块仍各判「部分修，仍阻断」，但阻断点已从"做法不对"变成"边界没钉死"

## 一、本轮改了什么

| 项 | 落地 |
|---|---|
| 命令入口 | 只接受 `python -m pytest <targets>`；`pytest.exe` 控制台脚本一律拒（内嵌解释器无法识别） |
| 目标契约 | 至少一个目标；按首个 `::` 拆 path + node id；拒 `.` / `./tests` / `tests//x.py` / `tests/../x.py` / 绝对 / 反斜杠 / 空 node |
| 目标存在性 | 开跑前在 clean worktree 内逐个验路径存在，缺失即 `return None, why, None` |
| 报告新鲜性 | 跑前 `unlink` gate-owned 报告并复查；仍存在即拒「the gate could not prove it came from this run」 |
| 报告解析 | `ET.parse` + 四计数缺一即 `None` + 逐 `testcase` 交叉核对 + `testsuites` 求和 + skip 政策成文 |
| schema | 新增 `scripts/gorch_contract.py`（`order_cards` / `acc_rows`），dispatch / freeze / audit 三处接入 |
| 测试 | `test_verify_order.py` 29 条、新增 `test_order_contract.py` 6 条 |

实测：八目标全量 **101 passed / 77.39s**（第十轮基线 93）。复审侧在干净临时 worktree、`_clean_env()`、固定 runner/JUnit 路径下实跑同一组：**101 passed / 0 failed / 0 skipped**，pytest 81.19s，含 worktree 建立与清理 113.47s。

## 二、复审给出的剩余阻断（三项，均为「部分修」）

### 1. 固定命令契约 — 部分修

已落实：目标规范化、空目标拒、参数全拒、clean worktree 路径存在性（`verify-order.py:264/294/361`）。

未落实：解释器仍不是"唯一登记的那一个"——`:317` 接受 `python`/`python3` 多种名称，并用 `is_relative_to()` 接受 `Scripts` 下**任意层级**的同名可执行文件；`:400` 返回的是未固定身份的路径。

必须修：解析后与 `ROOT/tools/venv-openjarvis/Scripts/python.exe` **精确相等**，并在启动点再次核对/固定解析结果。

### 2. 结构化执行结果 — 部分修

已落实：新鲜报告、XML 解析、聚合与 testcase 交叉核对（`:429` / `:477`）。

未落实：

- `:361` 只证明每个目标**路径存在**，`:894` 只核对**所有目标合计**执行数 > 0。复审定向实测：一个"存在但收集零项"的文件（`scripts/gorch_contract.py`）+ 一个有效 test node → `returncode=0`、JUnit `tests=1`，**门会通过**。即零执行目标可被别的目标兜底。
- 上轮要求的 skipped/xfail/XPASS **端到端**定向政策测试仍未补：`test_verify_order.py:485` 只有合成 XML 的 skipped 计数，没有覆盖"全 skip / 混合 skip / xfail / 非 strict XPASS / strict XPASS"。

必须修：每个登记目标**分别**证明至少收集/执行了符合政策的 testcase，或收缩为"每次只能登记一个目标"。

### 3. 卡集合与 ACC schema — 部分修

已落实：三条调用链共用 `gorch_contract.py`（`dispatch:423`、`audit:164`、`freeze:380/401`）。

未落实（parser 仍用前缀猜测，不是完整表 schema）：

- `gorch_contract.py:32` 只把**首字符就是 `|`** 的行纳入表块，缩进的疑似卡行会漏掉。
- `gorch_contract.py:29` 的 `T\d+` 没有单元格边界，`T2s1-…` 一类坏行可被静默跳过。
- `gorch_contract.py:85` 只匹配 `ACC-\d+` 前缀、不对首格做完整匹配：实测 `ACC-1x` 被接受为 gate id，`ACC-X` 与一个正常 ACC 并存时被静默漏掉。

必须修：基于明确表头/列定义解析所有数据行，对"像 T/ACC 行但不满足完整 ID 与列 schema"的行统一拒绝；补缩进行、缺分隔空格、非法 ACC 后缀、非法 ACC 数字部分、"一个正常行掩盖一个坏行"的定向测试。

## 三、复审给的可写进台账的边界措辞（原文）

> 第十一轮 `7810e9d9` 目前只能登记为「候选本地单卡冻结预检器」，尚不能登记为正式闭合冻结门。在信任本机 Git、登记的 Python/pytest 工具链及提交内测试配置/插件不会恶意改写执行的前提下，它已能在 delivered commit 的干净 worktree 中重跑八目标、生成新鲜结构化报告、核对总体执行计数，并把 verify、audit、单卡内容与 tag 绑定；但解释器唯一性、逐目标实际执行证明及表格 schema 仍未闭合。本门不是独立 maker-checker，不是对 gate 脚本、解释器、pytest loader、回执或 Git refs 的防篡改证明，也不是第三方认证；五卡工单当前只能 fail-closed，不能据此宣称正式冻结。

## 四、其他保留意见（ADVISORY，不阻断）

- `_clean_env()` 清空 `PYTHONPATH` **没有**使本轮真实八目标 import 失败（101 项在完全相同环境下通过）；其他依赖外部 `PYTHONPATH` 的工单可能失败，属 fail-closed 可移植性问题，不是误通过路径。
- 不存在的 node id 实测返回 `4` 且 JUnit `tests=0`，不会直接通过；问题是多目标合计计数、零收集文件/目录、插件改写收集后缺少逐目标绑定。
- 读码推断：`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` 不禁止提交内 `conftest.py`，`-o addopts=` 也不清 `pytest.ini` 的其他收集配置。当前八目标路径无 `conftest.py`/`sitecustomize.py`，根 `pytest.ini` 仅 `testpaths`/`norecursedirs`，故本轮实跑未受影响；未来提交内的这些文件可改写收集与报告。要抵抗作者控制测试基础设施，需隔离 reporter / 限制 loader，而非只靠 JUnit 计数。
- `_junit_counts()` 宜把 wrapper 限定为严格 `testsuite` 或 `testsuites`；`:449` 目前接受任意根元素下的直接 `testsuite`。
- 单卡限制仍是合理 fail-closed 取舍：五卡工单在 `freeze:431` 明确拒绝，不会被误冻；代价是五卡正式工单不能宣称完成正式冻结。
- `tools/` 全量哈希、解释器文件哈希、更强 isolated mode 仍建议实施，但在"不作防篡改证明"边界下不单列为本轮阻断。

## 五、结论

第十一轮把三项各自的核心做法都换掉了，方向被认可；剩下的是**同一类问题的第三层**：不是"没做"，而是"做了但边界是前缀/合计/相对路径"。三处各留一个可绕过的口子，**不能作正式冻结门，台账仍不能建**。

下一步（第 12 轮，三处各钉死一个边界）：

1. 解释器唯一性：resolve 后与登记路径**精确相等**，启动点复核，不再接受 `python3` 与 `Scripts` 下任意层级。
2. 逐目标执行证明：每个目标单独产出并核对计数（或收缩为单目标），补 skipped/xfail/XPASS 端到端测试。
3. 表 schema：按表头定义解析数据行，`ACC-\d+$` / `T\d+$` 做完整匹配，缩进行与非法后缀统一拒绝，补 5 类定向测试。
