# 工单台账独立核对报告（2026-11-10）

- **触发**：用户要求「检查 UltimaAgent 当前任务推进情况，筛选不需要 Codex 执行、无强关联的任务」
- **方法**：按经验 `frozen-work-order-status-check-named-artifacts-and-provenance` 执行——打开工单卡抄出点名产物 → 逐项验存在性 → `git log` 追归属 → 查专属 commit 与 tag；不采信登记表状态字段
- **范围**：项目主表 `tasks/queue/index.md`、全局主表 `H:\UltimaAI\_shared\queue\global-queue-index.md`、各单 run 目录与报告

---

## 一、总体结论

全局主表**没有任何工单处于 executing**，UltimaAgent 88 条工单里真正待处理的是 12 条：

| 类别 | 数量 | 明细 |
|---|---|---|
| 已完成、只差审计/打 tag | 4 | wo-orb-w6、wo-orb-w7、wo-orb-w8、0007 |
| 技术门已过、等真人或长期验证 | 2 | 0019（WeKws）、0020（Sherpa 语音） |
| 等 Owner 门或等环境 | 3 | wo-s1-composite-window、wo-s1-engineering-packaging、wo-s1-remote-update |
| 执行端未收口 | 2 | 0027（缺 T2 报告）、wo-orb-w9（需隔离环境） |
| 已完成但在未合入分支 | 1 | 0031（产出在 `codex/m2-workorder-contract-20261108`，当前分支没有） |
| 重复请求，已关闭 | 1 | req-agent-cv3-voice-clone-20261029 |

**没有一条在跑。** 最近 15 个提交全部属于 G-ORCH 编排线（r8→r14 审计闭环），不是新工单开工。

---

## 二、逐项核对结果

### 1. 0031 —— 初核误判，实为已完成但在未合入分支（更正）

首轮按当前分支路径检查，三项点名产物全部缺失，判为虚标。**该判断错误。** 复查 `git tag --list` 发现 tag `wo-ultimaagent-20261108-0031-frozen-20261108` 真实存在，指向 `d913a9e2`，tag 说明写明「分支 codex/m2-workorder-contract-20261108」。

在该 commit 上逐项取对象，三项产物**全部真实**：

| 点名产物 | 该 commit 上的大小 |
|---|---|
| `docs\specs\work-order.schema.json` | 5,749 B |
| `scripts\validate_work_order.py` | 16,738 B |
| `scripts\freeze_work_order.py` | 6,558 B |

tag 说明另载「T0-T4 全绿，24 passed；REVISE 补票 OSS 排查已完成」。

**真实问题不是虚标，是合并策略**：这批产出留在 `codex/m2-workorder-contract-20261108`，没有合入当前工作分支 `codex/voice-fsmn-new-path`，所以在本分支按路径检查必然显示缺失。登记表写 `frozen` 是对的。

教训：核查产物存在性时，不能只查当前工作树，必须先确认该单的 feature 分支是否已合入；「当前分支没有」不等于「没做」。

### 2. wo-orb-w6 —— blocked → audit

- `done.json`：`receipt_valid: false`、`state: blocked`
- 但 `final.json` 是**中文 markdown（1,597B）**，不是 JSON → `ReceiptValidator` 解析失败，导致 `receipt_valid=false`。这是**格式问题，不是执行失败**。
- 实证：`git cat-file -t c5f9156b` → `commit`，标题「工单 WO-ORB-W6 编排层：补齐外脑封装与常驻监工」；6 个交付文件（`orchestrator.py`、`sentinel.py`、`test_orchestrator.py`、`test_sentinel.py`、联调测试、结果报告）；`14 passed in 0.24s`。
- 执行端自述：`READY_FOR_DEEPSEEK_AUDIT`，未审计、未打 tag。

判定：执行已完成，转 `audit`。

### 3. wo-orb-w7 —— 维持 audit

- commit `a5322432` 真实，标题「工单 WO-ORB-W7 编排层接线：加固回执 fail-closed 契约」
- `test_receipt_contract.py` 9 passed；五文件专项门 33 passed（1.53s）
- 同样是 final.json 写成 markdown 导致 `receipt_valid=false`

判定：已完成待审计，维持 `audit`。

### 4. wo-orb-w8 —— 维持 blocked

- ACC-1~ACC-4 全部 PASS（CRLF/LF/尾随空格/中文字节一致、无 BOM、0 字节文件、重跑覆盖）
- 但执行端明示：**未提交 git、未打 tag、未跑全量测试**，产物只在 run 目录

判定：验收项达成但未交付入库，维持 `blocked`，待补提交与全量门。

### 5. wo-orb-w9 —— 维持 blocked（环境问题）

- 非代码失败：目标文件 `docs/reports/g-orch-smoke-verify-20261109.md` **已在 HEAD**（由 `30b36e7b` 跟踪），不构成工单要求的「唯一新增文件」，ACC-3 不满足
- 执行端零写入、零越界

判定：需提供隔离检出环境（目标文件未入 HEAD 且无其他工作树改动）才能重跑。

### 6. 0007 双线程伪流式 —— 项目表 executing → audit

报告 `stage-pseudo-streaming-20261030.md` 明载「**验收 PASS，待 Owner 打冻结 tag**」；T4 物理音频耦合 3+3 组对比全 PASS；L26 日志竞态已修。不是执行中。

### 7. 0019 / 0020 语音 —— 维持 audit

- 0019：离线技术门独立审计 PASS；**真人、真实采集、远场未验证**，未生产切换
- 0020：独立技术审计 PASS + 首轮真人「唤醒→时间指令→正确语音回答」通过；**远场、召回、长期误唤醒未验收**，明确未冻结

两单都过不了 Codex，缺的是**真人实测**。

### 8. wo-s1 三单 —— 维持 blocked（等 Owner / 等环境）

| 工单 | 卡点 |
|---|---|
| composite-window | T2 独立 audit PASS，整单与 Owner 门保留 |
| engineering-packaging | PK-01/02/04/05 真机 PASS；仅 PK-03 缺失分支需净机环境（本机无 VM/ISO，属环境约束非代码缺陷） |
| remote-update | 25/25 单测全绿 + 真实 Release v0.1.0 端到端冒烟 PASS；剩余 stage1-v1.0-frozen 冻结动作 |

### 9. req-agent-cv3-voice-clone-20261029 —— 关闭

该请求已被 `wo-ultimaagent-20261030-0005`（CV3 贾维斯音色，**frozen**）完整覆盖：voice-profile 增 `voice` 段（`engine=cv3` 本地默认）、`ref_audio` 默认贾维斯参考、`tts.py` `PROMPT_WAV` 动态装载、daemon 同源均已落地。重复立项无必要。

---

## 三、台账修正清单

### 项目主表 `tasks/queue/index.md`

| 工单 | 原状态 | 新状态 |
|---|---|---|
| 0026 | executing | **frozen**（T0-T2 完成，tag `ultimaagent-audit-hardening-20261108` 指向 `f0cad32b`） |
| 0027 | interrupted | **blocked**（T0/T1 已落地，T2 缺报告、无 tag） |
| 0029 | executing | **frozen**（全局表早已 frozen） |
| 0007 | executing | **audit**（验收 PASS，待 Owner tag） |
| 0007 / 0029 统计行 | 执行中=1 | 按新状态同步（0007 转待审计，0029 转已完成） |

### 全局主表 `global-queue-index.md`

| 工单 | 原状态 | 新状态 |
|---|---|---|
| 0031 | frozen | frozen（**初核误判为 blocked，已更正**：产出真实存在于未合入分支 `codex/m2-workorder-contract-20261108`） |
| wo-orb-w6 | blocked | **audit**（commit `c5f9156b` 真实、14 passed） |
| wo-orb-w7 | audit | audit（补核实结论：commit `a5322432`、33 passed） |
| wo-orb-w8 | blocked | blocked（补：ACC 全 PASS 但未提交、未跑全量） |
| wo-orb-w9 | blocked | blocked（补：目标文件已在 HEAD，需隔离环境） |
| req-agent-cv3-voice-clone | pending | **closed**（已被 0005 frozen 覆盖） |

---

## 四、发现的两个系统性问题

### 问题一：`receipt_valid` 把「格式」判成了「成败」

w6/w7 的 `final.json` 是执行端写的中文交付说明（markdown），`ReceiptValidator` 按 JSON 解析失败 → `receipt_valid=false` → 整单被判 `blocked`。结果：**活干完了，台账说它没干**。

这不是单点故障：0026 的 `T0/receipt.json` 是标准 JSON，所以过了；ORB 线执行端不知道回执必须 JSON，所以全挂。**回执格式缺一道派发时的机器校验**。

### 问题二：产出留在 feature 分支，主干不可见

0031 的 schema/validator/冻结门做完了、tag 也打了，但停在 `codex/m2-workorder-contract-20261108` 没合入 `codex/voice-fsmn-new-path`。后果：**在主干上按路径核查会误判成没做**（本次就误判了一次），后续工单也无法直接引用这套契约。合并动作目前没有归口机制，谁合、什么时候合、合并门是什么，都没有约定。

### 问题三：状态字段仍由执行端自填

0026 时期判定的「执行者=判定者=验收者=进度宣布者四合一」尚未解决——0027 立项要做的就是这件事，但 0027 自身卡在 T2（缺收口报告），机制还没落地。所以现在台账状态仍要靠本报告这种人工核对来拉回真实。

---

## 五、过程中的两处失误（如实记录）

### 失误一：`git checkout` 抹掉未提交改动

核对项目主表时，用 `git checkout -- tasks/queue/index.md` 回滚一次误改，**连带抹掉了该文件未提交的两行改动**（0029 的统计行与明细行）。已按被覆盖前的原文逐字重建，`20261108-0029` 现出现 2 次（统计 1 + 明细 1），统计值同步为 `6 | 0 | 0 | 0 | 0 | 1`。

教训：**对含未提交改动的工作区文件，不能用 `git checkout` 做「回滚」**——要改先读全量、只做局部替换，或先 stash。

### 失误二：只查主干就判定「没做」

0031 的产物在 feature 分支上，首轮只查当前工作树，据此写了「三项产出全缺、无 commit、无 tag」的结论，并据此改了全局表状态。复查 tag 名称匹配词（先前用 `*workorder*`/`*work-order*` 漏掉了 `0031-frozen-20261108`）后才发现误判，已恢复 `frozen`。

教训：判定「产物不存在」之前，必须先查该单的 **feature 分支**与**全部 tag**（用 `--list "*0031*"` 这类按工单号匹配，不要猜命名），再下结论。

---

## 六、下一步分流

### 不需要 Codex（主脑直接干，本次已完成 6 条状态修正）

- 已完成：0026/0029 转 frozen、0027 转 blocked、0007 转 audit、CV3 请求关闭、0031 维持 frozen（初核误判已更正）
- 待做：w6/w7 独立审计（复跑 + 看 diff 越界）、w8 补提交判定、0007 打 tag

### 需要 Codex

| 任务 | 内容 |
|---|---|
| 0027 T2 收尾 | 补 `wo-ultimaagent-20261108-0027-t2.md`、跑全量门、打 tag |
| 0031 分支合入 | 把 `codex/m2-workorder-contract-20261108` 的 schema + validator + 通用冻结门合入主干，否则后续工单引用不到 |
| 回执格式硬化 | 派发载荷里加一条：`final.json` 必须是 JSON，否则 receipt 必失败（可与 0027 合并） |

### 需要用户拍板

- w6/w7 审计通过后是否直接打 tag 冻结
- 0007 是否现在打 `ultimaagent-pseudo-streaming-20261030` tag
- wo-s1 三单是否走「部分验收 + 遗留项另立」收口

---

## 八、本轮补充执行（同一次任务内继续推进）

核对完成后，用户授权连续推进，把三类里「不需要 Codex」的部分一次做完。结果如下。

### 8.1 ORB 三单全部冻结

| 工单 | 动作 | 证据 |
|---|---|---|
| wo-orb-w6 | 独立审计通过 → frozen | 提交零越界（6 文件 813 行全新增，全在写域）；复跑 **20 passed**；代码复核确认 orchestrator 真 HTTP + tenacity 重试 + fail-closed 留原文 + 九字段产物，sentinel 只读 + 复用 dispatcher 身份/锁 + 三判据连续 3 tick 才报 + recovered 恢复；tag `wo-orb-w6-frozen-20261110` |
| wo-orb-w7 | 独立审计通过 → frozen | 提交零越界（3 文件）；复跑 **12 passed**；修的是两个真 bug——`status` 非字符串（`[]`/`{}`）触发 unhashable TypeError 让派发器崩、文本回执裸子串让 `wo-orb-w7x` 串成 `wo-orb-w7`；tag `wo-orb-w7-frozen-20261110` |
| wo-orb-w8 | 验收同步后冻结 | 产物早在 `02d10db7`（HEAD 已含 `requirement.txt` 逻辑）；但验收测试已过期 **3 failed**——`fake_run_stage` 缺 `model` 参数、工具标记断言未跟上实现（`"tool_calls"` 要带引号、` ```bash ` 被有意排除）；修完 **16 passed**；tag `wo-orb-w8-frozen-20261110` |

### 8.2 0029 从 frozen 改回 blocked（第二例「主干不可见」）

T1-T4 产物在分支 `codex/jarvis-e02-source-grounding-r1`：`src/brain/work_navigation.py` 691 行 / 38,517B，**主分支完全没有该文件**；T5 要求报告 `jarvis-work-e02-offline-minimal-repair-20261108.md` **全仓缺失**。

结论：`frozen` 不成立（报告未落盘 + 主干不可见），已改 `blocked`。这与 0031 是同一类问题的第二个实例，说明「产出留在 feature 分支」不是孤例。

### 8.3 0007 维持 audit（不能冻结）

报告 `stage-pseudo-streaming-20261030.md` 在（3,287B，T4 物理音频耦合 3+3 组全 PASS），但代码改动（daemon `_LOG_LOCK`）仍在工作树未入库。产出入库不完整就不能打冻结 tag。

### 8.4 回执判据硬化（本次最有复用价值的一处）

- **根因**：`_classify_text` 只认「自检 PASS」这一条字面文案，而执行端实际写的是「14 passed」/「PYTEST_EXIT_CODE=0」。w6/w7 因此 `receipt_valid=false`、整单被判 blocked。
- **改法**：通过证据放宽到 `14 passed` / `PYTEST_EXIT_CODE=0` / `自检 PASS` 三种写法；本次是否通过由 `exit_code=0` + 执行端 READY 声明共同决定，正文里叙述的历史失败（「修复前 3 failed」「28 项既有债」）不再否决。
- **真实回执复验**：w6 `blocked/false → audit/true`、w7 同样转 `audit/true`；w8/w9 保持 blocked（符合事实）。
- **附带修掉一处结构缺陷**：commit `1952160b`（「主脑代做一行」）把测试 `def test_text_receipt_requires_complete_work_order_boundary` 的 def 行替换掉了、函数体留在原处，等于把两个测试粘成一个。已补回 def 行。
- 单测 **18 passed**；tag `ultimaagent-receipt-hardening-20261110`。

### 8.5 仍然要 Codex / 等人的

| 项 | 卡在哪 |
|---|---|
| 0027 T2 收尾 | 缺 `0027-t2.md` 正式报告 + 未打 tag |
| 0019 / 0020 语音 | 缺真人实测（远场、召回、长期误唤醒） |
| wo-s1 三单 | 等 Owner 门 / 等净机环境（本机无 VM/ISO） |
| wo-orb-w9 | 需隔离检出环境（目标文件已在 HEAD） |
| 0031 / 0029 分支合入 | 合并归口未约定 |

## 九、取证命令附录

```powershell
# 产物存在性
@("docs\specs\work-order.schema.json","scripts\validate_work_order.py","scripts\freeze_work_order.py") | ForEach-Object { $f="H:\UltimaAI\UltimaAgent\$_"; if (Test-Path -LiteralPath $f) {"存在 $_ $((Get-Item -LiteralPath $f).Length)"} else {"缺失 $_"} }
# 归属
git log --oneline -3 -- "scripts/freeze-work-order.py"
# commit 真实性
git cat-file -t c5f9156b; git log -1 --format="%s" c5f9156b
# 回执字段
Get-Content tasks\queue\runs\<run>\done.json -Raw
```
