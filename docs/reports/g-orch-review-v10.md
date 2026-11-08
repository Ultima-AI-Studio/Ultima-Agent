# G-ORCH 冻结门复审 · 第十轮

> 复审对象：`70bc12b4`（第十轮改造 + `pytest.exe` 入口修正）
> 复审方式：Codex（gpt-5.6-sol，high reasoning，只读复核，未改文件）
> 结论：**VERDICT: FAIL** —— 三块「部分修，仍阻断」

## 一、本轮改了什么

| 项 | 落地 |
|---|---|
| 机检命令 | 工单只报解释器 + 测试目标；任何 `-`/`@` 开头 token 一律拒；gate 自己追加 `-o addopts=` 与 `--junitxml` |
| 执行判据 | 从「退出码 0」改为「JUnit 收据：executed>0、failures=0、errors=0」 |
| 零命令 | `declared_command_plan` 无条件失败，manifest 写 `commands: []` 不再畅通 |
| 卡集合 | 恢复五段结构 + `len(cards)!=1` 即拒（多卡 audit 落地前的 fail-closed 取舍） |
| 测试 | 参数类 9 种全拒、`_gate_argv` 两入口形态、真 venv 夹具、4 条卡集合定向回归 |

实测 `93 passed / 76.63s`（本机）；复审侧复跑 `48 passed / 73.05s`（verify + freeze 两文件）。

## 二、复审给出的剩余阻断（三项，均为「部分修」）

### 1. 固定命令契约 — 部分修

已修：所有工单参数被拒；选项由 gate 生成。

未修：

- 去掉 `-m pytest` 后**没有检查 body 非空**：`python.exe -m pytest` 零目标返回接受，被拼成无显式目标的 pytest 命令。
- 目标**没有拆分 node id 后规范化**，也没有确认路径存在、位于 clean worktree 内；实测 `.`、`./tests`、`tests/x.py::test_y` 全部被接受。
- 仍接受 `pytest.exe` 入口：「只固定了 launcher 路径，不能验证其内嵌的实际 Python」。

必须修：只接受登记的 `python.exe -m pytest`；至少一个目标；按首个 `::` 拆分 node id，规范化并在临时 worktree 内验证存在、未越界；明确目录目标与 node id 是否允许并写进测试。

### 2. 结构化执行结果 — 部分修

已修：报告存在 + `tests-skipped > 0` + `failures == errors == 0`；freeze 现场重跑 verifier。

未修：

- `.gorch-junit.xml` **运行前没有删除或确认不存在**：若该文件已在提交里，gate 无法证明读到的报告由本次运行产生。
- `_junit_counts` 用正则读第一个 `<testsuite>`，缺失属性默认记零，不校验 XML、不比对 `testcase` 数量与汇总。
- skipped/xfail 只有隐式行为：允许任意数量，只要求另有一个非 skipped 项；非 strict XPASS 也可能计为通过。

必须修：每次运行用新鲜、运行前不存在的 gate-owned 报告；严格解析 XML 并与 testcase 状态交叉核对；明确 skipped/xfail/XPASS 政策并加定向测试。

### 3. 卡集合与 audit 范围 schema — 部分修

已修：receipt 卡路径必须规范等于 `tasks/cards/<id>/task.md`；重复 receipt id 拒；多卡 receipt 拒。

未修：

- dispatch（`dispatch-work-order.py:418`）与 freeze（`freeze-work-order.py:395`）**各自用正则重新枚举卡**，不是共享解析/校验函数。
- 两处都**静默忽略「像任务行但未匹配」的行**，并用 `set`/`dict.fromkeys` 吞掉 order 内重复 card id。
- audit 的 gate parser 会跳过不满足三列或 ACC id 形态的疑似行（`audit-work-order.py:158`），freeze 又另写一份不同解析（`freeze-work-order.py:372`）。

必须修：抽出 dispatch/freeze 共用的 order-card schema、audit/freeze 共用的 ACC schema；疑似表格行解析失败、重复 id、空字段、部分漏行一律拒，并补定向测试。

## 三、复审给的可写进台账的边界措辞（原文）

> 截至提交 `70bc12b4`，G-ORCH 只能登记为「本地、同一账号与同一工具链信任域内的候选预冻结控制」：它会在 clean detached worktree 上重跑其接受的 pytest 命令，读取 pytest 自报的聚合结果，现场重验 receipt/tree/audit 绑定，并在当前单卡范围内拒绝多卡冻结。由于显式测试目标契约、执行报告新鲜性/严格 schema、卡集合及 audit 范围 schema 尚未闭合，本版**不得登记为正式冻结放行依据**。即使上述阻断修复，它也只是本地流程质量门：**不是**独立 maker-checker，**不是**密码学或防篡改证明，**不是**第三方认证，也不证明测试覆盖充分、登记 toolchain 未被同权限主体替换，或仓库内代码无法影响 pytest 的收集与报告。

## 四、其他保留意见（ADVISORY，不阻断）

- `-o addopts=` 只清配置里的 addopts；已提交的 `conftest.py`、`pytest.ini` 仍可改收集/报告。
- 未用 Python isolated mode，仓库根 `sitecustomize.py` 可能在 pytest 前生效（读码推断）。
- `tools/` 被 `.gitignore` 忽略，runner 未做哈希固定；台账需声明「同一信任域」。
- 五卡工单（`wo-s1-host-shell.md`：10 次表格引用 / 5 张唯一卡）当前必定被拒；复审**认可**单卡限制这一 fail-closed 取舍，最小替代是「每卡独立 audit 记录 + freeze 校验 order ids == receipt ids == audit ids」。
- 现有测试未覆盖空目标、目标规范化、预存/畸形 JUnit、skipped/xfail 政策、疑似卡表行、order 重复 id，因此**不能用测试全绿反推三块闭合**。

## 五、结论

第十轮把「黑名单」换成了「白名单 + 执行收据 + 单卡」，方向被认可，但三处仍各留一个可绕过的口子。第九轮的最小集合尚未全部闭合，**不能作正式冻结门，也不宜直接建台账**。

下一步（第 11 轮，按上表三项逐条）：
1. 目标契约收紧：只接受 `python.exe -m pytest`、至少一个目标、node id 拆分与 worktree 内存在性校验。
2. 执行报告收紧：跑前删除报告、严格 XML 解析 + testcase 交叉核对、skipped/xfail 政策成文并加测。
3. schema 统一：抽共享 order-card / ACC 解析，dispatch/freeze/audit 三处接入，畸形行与重复 id 一律拒。
