# G-ORCH 判据基线（Phase 0 止血）

> 日期：2026-11-09 ｜ 状态：**待 Owner 确认后冻结** ｜ 效力：本文件冻结后，G-ORCH 冻结门的评审**只能**对本清单条目给 PASS/FAIL
>
> 依据：G-ORCH-001（`H:\UltimaAI\INDEX.md` 行 17）、工程铁律 §9、`dispatch-rules-v0.2-20261108.md`
>
> 生成方式：解析 11 份复审原文（`C:\Users\Administrator\AppData\Local\Temp\gorch-review-out*.md`），按"是否属于已定口径"分层，**不逐条照抄评审方措辞**。

---

## 1. 11 轮的事实（先摆清楚，避免继续误判）

| 事实 | 证据 |
|---|---|
| 11 份复审全部 `VERDICT: FAIL` | 脚本正则统计，`gorch-review-out.md` + `-v2`~`-v11` |
| **v1~v9 是自由格式意见，没有 BLOCKS 段** | 脚本解析：`blocks_count=0`（v1~v9） |
| **只有 v10、v11 收敛成 3 个固定类别** | 两者均 `blocks_count=3` |
| 这 3 类从第九轮就定性，第 10、11 轮均判"部分修，仍阻断" | v9 §「必须修的最小集合」；v10/v11 BLOCKS 首行 |
| 三类 = ①固定命令契约 ②结构化执行结果 ③卡集合与 ACC schema | v11 BLOCKS 1/2/3 |
| 第 11 轮实测 `101 passed / 0 failed / 0 skipped`（81.19s） | v11 TESTS 段 |
| 评审方自述边界：候选本地单卡预检器，**不是 maker-checker、不是防篡改证明、不是第三方认证** | v11 GATE-BOUNDARY |

**结论**：不是 11 个不同的问题，是 **3 个类别反复追 11 轮**；其中每次都能再往下细分（`is_relative_to` → 精确相等、`ACC-\d+` → 加 `$`），因为**判据没有封闭**。

---

## 2. 判据四层

| 层 | 含义 | 是否阻断 | 谁定 |
|---|---|---|---|
| **L0** | 已定口径（范式原文已写） | 是 | 范式（2026-11-08/09 Owner 拍板） |
| **L1** | 已定口径的**实现缺口** | 是 | 范式 + 本文件落实 |
| **L2** | 评审方**新增**要求（超出范式） | **否，须 Owner 拍板** | Owner |
| **L3** | 明确排除，永不纳入 | 永不 | 范式 |

---

## 3. L0 · 已定口径（引自 INDEX 行 17，不是本文件新增）

| ID | 判据 | 判定方式 |
|---|---|---|
| L0-01 | 声明的测试命令一律在**被验 commit 的干净 `git worktree` 检出**里跑 | 机检：临时 worktree 路径在 run-dir 外，跑完清理 |
| L0-02 | 解释器限定为登记 venv（`tools/venv-openjarvis/Scripts`） | 机检：见 L1-02 收紧 |
| L0-03 | 环境净化 `PYTEST_*`/`PYTHON*`，置 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` | 机检：子进程 env 白名单 |
| L0-04 | 参数层禁 `-p`/`--plugins`/`--rootdir`/`-c`/`--pyargs` | 机检：命令词法检查 |
| L0-05 | **gate key 集合守恒**：卡 / 顶层 `gates` / 两轮 `per_gate` 四者相等 | 机检：集合相等断言 |
| L0-06 | **全部被引用卡的哈希**在派发后未变 | 机检：派发时记 sha256，冻结时逐卡复核 |
| L0-07 | 卡路径必须是 `tasks/cards/<id>/task.md` 规范路径 | 机检：`resolve()` 后字符串相等 |
| L0-08 | 无 tag = 闭环未完成，不得报"完成" | 人工纪律 + 汇报格式检查 |

> L0 这 8 条**不需要重新讨论**。范式已经定了，只是实现有缺口。

---

## 4. L1 · 已定口径的实现缺口（本轮必须修完）

| ID | 判据 | 现状 | 位置 | 判定方式 |
|---|---|---|---|---|
| L1-01 | `commands` 非空；空命令无条件失败 | **已实现** | `verify-order.py:469-478, 758-764` | 保留现有断言，不得回退 |
| L1-02 | 解释器 `resolve()` 后与 `ROOT/tools/venv-openjarvis/Scripts/python.exe` **字符串精确相等**，启动点再核对一次 | **未实现**（现用 `is_relative_to()` 接受 `Scripts` 下任意层级，且接受 `python`/`python3` 多名） | `verify-order.py:317`、`:400` | 机检：单测断言"同名不同层级的 exe 被拒""`python3` 被拒" |
| L1-03 | 跳过/失败政策有**端到端**测试覆盖：全 skip、混合 skip、xfail、非 strict XPASS、strict XPASS | **未实现**（现只有合成 XML 计数） | `test_verify_order.py:485` | 机检：5 类各一条真实 pytest 运行断言 |
| L1-04 | 卡集合解析：**任一疑似卡行/ACC 行无法解析即整体拒绝**，不得只取合法子集 | **未实现**（①缩进卡行漏掉 ②`T2s1-…` 静默跳过 ③`ACC-1x` 被当 gate ④`ACC-X` 被静默漏掉） | `gorch_contract.py:32`、`:29`、`:85` | 机检：4 类畸形行各一条"必须 ValueError"断言 |
| L1-05 | 单卡限制必须**显式**：`len(receipt_cards) != 1` 即拒，且报错可读 | **已实现** | `freeze-work-order.py:431` | 保留；五卡工单不得冻结 |

**为什么这 5 条算"已定口径"而不是"评审新增"**：L1-04 对应 L0-05（gate key 集合守恒的前提是能正确解析全部卡）；L1-03 对应 INDEX"符合失败/跳过政策"；L1-02 对应 INDEX"解释器限定为登记 venv"——`is_relative_to()` 是把"限定"放宽成了"同一目录下任意层级"，属实现走形，不是新要求。

---

## 5. L2 · 评审方新增要求（**超出范式，须 Owner 拍板才纳入**）

| ID | 评审方要求 | 为什么算"新增" | 建议 |
|---|---|---|---|
| L2-01 | **逐目标**执行证明（每个登记目标都至少执行一个符合政策的 testcase） | INDEX 写的是"结构化测试收据证明**至少一项目标**测试实际执行"，是合计口径；"逐目标"是评审方加严 | **建议纳入**（可堵"零收集文件被别的目标兜底"，v11 有实测：`gorch_contract.py` + 一个有效 node → `tests=1` 即放行） |
| L2-02 | 拒绝 `@argfile`、`--collect-only`、`--setup-only`、`--setup-plan`、`-m`、`--ignore`、`--ignore-glob` | 范式只列了 `-p/--plugins/--rootdir/-c/--pyargs` | **建议纳入**（`@argfile` 与 collect-only 都能让"退出 0 但没执行"，属同类漏洞） |
| L2-03 | `_junit_counts()` 的 wrapper 严格限定为 `testsuite` 或 `testsuites` | 评审方 ADVISORY，自述"不单独增加阻断" | **可缓**（`verify-order.py:449` 现接受任意根元素下的直接 `testsuite`） |
| L2-04 | 抵抗提交内 `conftest.py` / `pytest.ini` 改写收集 | 评审方标注"读码推断、本轮未受影响" | **可缓**，写入边界即可 |
| L2-05 | `tools/` 全量哈希、解释器文件哈希、更强 isolated mode | 评审方自述"在'不作防篡改证明'的边界下不单独增加阻断项" | **可缓**，属 L3 范畴 |

---

## 6. L3 · 明确排除（永久不做）

| ID | 排除项 | 理由 |
|---|---|---|
| L3-01 | `audit.json` 的强 provenance（证明它确由模型调用产生、事后不可改） | 同一 Windows 账户、同一 Owner、同一可写 run 目录内**无法自证**；给同一 Owner 一个本地 HMAC 密钥也不建立独立信任。需要独立受控服务/不同信任域密钥/追加式账本 |
| L3-02 | 冻结门作为「独立 maker-checker / 防篡改证明 / 第三方认证」 | 无任何开源先例；edict 做审计轨迹、Omnigent 做 policy+sandbox、Hive 做 human-in-the-loop，都不做"门自证可信" |
| L3-03 | 对「本机 Owner 主动篡改」的防护 | 同权限主体无法被本地机制防住；只靠 Owner 人工纪律 |

---

## 7. 冻结后的评审规则（硬）

1. 评审**只对 L0 + L1（及 Owner 批准的 L2）** 逐条给 PASS/FAIL + 证据。
2. **清单外的新发现**：不得阻断，只能写进 `ADVISORY`，由 Owner 决定是否升级为 L2。
3. 每轮评审必须报：**「清单内 N 项，通过 M 项」**，不得只报 FAIL。
4. **返工上限 2 次**（对同一判据集）。超限 → 升级给 Owner，不在评审-执行之间无限循环。
5. 判据冻结后**增删条目须 Owner 书面批准**，评审方无权增删。

---

## 8. 来源索引

| 复审文件 | 贡献 |
|---|---|
| `gorch-review-out.md` ~ `-v8.md` | 自由格式意见；已被 v9 的三条最小集合收敛覆盖 |
| `-v9.md` | **三条"必须修的最小集合"**；正式门边界措辞；`audit.json` provenance 不可自证 |
| `-v10.md` | 三条的"部分修，仍阻断"判定 |
| `-v11.md` | 三条的剩余细项（解释器唯一性 / 逐目标计数 / 表 schema）；6 条 ADVISORY；GATE-BOUNDARY |
