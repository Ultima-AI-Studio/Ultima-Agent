# wo-ultimaagent-20261110-0032 分支合并报告

## 1. 结论

- P1（0031）已合入：merge commit `141a88a88c0038e45375398e4d5dc0d204e484da`，tag `ultimaagent-0031-merged-20261110` 指向该提交。
- P2（0029）未合入：正式全量门出现 379 个失败，超过 20 个新增失败的中止阈值；已执行 `git merge --abort`，无 P2 merge commit、无 `ultimaagent-0029-merged-20261110` tag。
- 结项报告提交前回读的主干 HEAD 为 `9ecea595a31b0b3e3f65efaef30e934ec3c3a899`。该 HEAD 包含 P1 merge commit 及其后他线文档提交；`HEAD:src/brain/work_navigation.py` 仍不存在，0029 继续属于“主干不可见”。
- 中止判据：**触发**。没有把大面积红的 P2 合并提交进主干。

## 2. 预演与并发基线

`data/evidence/wo-ultimaagent-20261110-0032/pre-merge-conflicts.txt` 保存了完整 `git merge-tree --write-tree` 输出。初次预演与每次实际 HEAD 重检均为：P1 一处 content 冲突，P2 两处 add/add 冲突，没有未知内容冲突。

执行期间主干由他线从 `2894638f` 推进到 `a1a2bf01`，P1 合入后又推进到 `9ecea595`。每次真实 merge 前均重新执行 merge-tree 并核对冲突数；tag 使用显式 merge SHA，未误打到他线提交。

工作树存在大量他线未提交/未跟踪内容。P1 两个碰撞文件与分支 blob 相同；P2 共 127 个磁盘碰撞路径逐项记录 SHA-256 并备份，其中 4 个源码与分支不同。两次 P2 abort 后均按 manifest 恢复 127 项；4 个不同源码的原 SHA-256 全部恢复。没有 stash、clean、通配 add 或 `git checkout --`。

## 3. 冲突裁决表

| 阶段 / 文件 | 两侧差异 | 保留策略与来源语义 | 丢弃内容 | 验证 |
|---|---|---|---|---|
| P1 `scripts/dispatch-work-order.py` | 0031 分支增加 schema/DoR、`--skip-dor`、dry-run 与 dispatch record；主干增加 G-ORCH 精确命名/卡表解析、WIP/lock、receipt、tree fingerprint、sentinel 等守卫 | 同时导入 validator 与主干 receipt/G-ORCH；所有 `wo-*` 先做 DoR，dry-run 可返回；真实派发继续要求 `wo-s1-*` / `wo-orb-*` 精确卡路径；run 同时写 DoR record 并注入 receipt 契约 | 仅丢弃冲突标记，以及“用分支宽松命名直接绕过主干真实派发命名门”的组合 | `py_compile`；0031 三文件 24 passed；P1 全量 1,130 tests / 0 failures |
| P2 `docs/reports/jarvis-work-t2-current8b-interface-resume-20261102.md` | 主干为 1,902B 初始摘要；分支为 23,238B 完整演进稿，包含初始背景并追加阶段记录 | 候选树保留分支完整稿；其 blob 为 `6ba47eb6…`，等于合并前工作树内容 | 候选树丢弃被完整稿覆盖的一行旧时态表述 | 候选 blob 与分支 stage-3 blob 逐字节一致；最终因 P2 abort 未落主干 |
| P2 `src/brain/agent_tools_ultima.py` | 仅子智能体模型一行不同：主干 `qwen3-8b-uncensored`，分支 `qwen2.5:14b` | 候选树保留主干 8B，符合 `docs/specs/jarvis-work-8b-model-policy-20261102.md` | 丢弃 14B 回退行 | 候选 blob 与主干 stage-2 blob `63d1f626…` 一致；最终因 P2 abort 未落主干 |

## 4. 产物可见性与字节核验

| 产物 | 结果 |
|---|---:|
| `HEAD:docs/specs/work-order.schema.json` | 5,749B |
| `HEAD:scripts/validate_work_order.py` | 16,738B |
| `HEAD:scripts/freeze_work_order.py` | 6,558B |
| P2 候选 `src/brain/work_navigation.py` | 38,517B / 691 行 |
| 当前 `HEAD:src/brain/work_navigation.py` | 不存在（P2 abort 后未落地） |

P1 两个预存未跟踪副本与 0031 分支 blob 相同，合并后由 Git 跟踪的内容保持一致。P2 的 38,517B 只在失败候选树与 feature branch 可见，不能写成主干已可见。

## 5. 测试计数与失败历史

| 门 | 环境与结果 | JUnit SHA-256 |
|---|---|---|
| P1 指定三文件门 | 首轮 16 passed / 8 failed：1 项来自额外未跟踪 0029 卡，7 项来自硬编码 M4 worktree 路径不存在；临时 junction 与卡隔离均做哈希恢复后，提交前和提交后均为 24 passed | 日志 `p1-gate.log` / `p1-postcommit-gate.log` |
| P1 全量基线 | 1,130 tests，0 failures，0 errors，0 skipped；终端 1008 passed + 122 subtests | `1fa06bb53a481412581ed654c87c2263d7d109f8d75db42d37b7afd1b133735c` |
| P2 定向首轮 | 裸用户 HOME：350 failed / 672 passed，首因 `Conflicting research template override`；已保留 | `a33ef6db9f77d48c688296da6eebf9da5e8c468ffb666de92d7f8100279ace7f` |
| P2 定向隔离复验 | 全新临时 `OPENJARVIS_HOME`：1,022 tests，0 failures/errors/skipped | `46c0f4746310d56ed0478483e2119576ea8f6bbd8751421eed85da9a922b0ac6` |
| P2 正式全量门 | 全新临时 `OPENJARVIS_HOME`：2,140 tests，379 failures，0 errors/skipped；终端 1,639 passed + 122 subtests | `59b7b17d60de94062fb1e477cc83ae5d48da64f5cd3b03ccdcce4e058b06d4b1` |

正式 P2 失败集中在研究测试的全量顺序耦合：`test_work_research.py` 84、`test_work_navigation_transport.py` 61、`test_work_output_structure_diagnostics.py` 51、HTTP/native diagnostics 各 43 等。相同的 25 文件单独运行 1,022 项全绿，说明需要独立诊断跨测试全局状态污染或顺序依赖；本合并单禁止修改冻结产品语义，未顺手修复。已知环境项 `test_jarvis_ask_real_inference` 在正式 JUnit 中通过，未豁免、未删除、未 skip。

## 6. T5 报告与 0029 合同缺口

已补建 `docs/reports/jarvis-work-e02-offline-minimal-repair-20261108.md`，记录技术门、未验证真人/真实采集/远场及 T5 逐条映射。

锁定 revision `43da3f01` 本身仍保留 `agent_server.py` 与 `work_research.py` 两处 `>=3` 写入资格计算，未包含 0029 卡要求的唯一 coverage 四状态实现和最终预算证明。feature worktree 中存在未提交的 10 个修改文件、一个新测试和一份报告草稿，但这些不属于锁定 revision；本单没有擅自提交或吸收。

## 7. Tag 与 push

- `ultimaagent-0031-merged-20261110^{}` → `141a88a88c0038e45375398e4d5dc0d204e484da`。
- `ultimaagent-0029-merged-20261110`：未创建，因为 P2 未通过合并门。
- 指定代理 push 于 attempt 1 返回 `Everything up-to-date`、exit 0；当时远端 `codex/voice-fsmn-new-path` 已包含当前 P1 后 HEAD `9ecea595`。完整输出在 `push-attempts.log`。

## 8. 越界声明

无功能越界。未修改 `docs/tracker/北极星上线任务清单.html`、`src/brain/guardrails/reviewer.py`、`receipt.py`、0026/0027/0007/ORB 既有证据；未升级依赖、删除测试、弱化断言、修改模型默认值或改动冻结产品语义。临时 M4 junction 已删除，真实 M4 worktree保持完整。P2 两次 abort 均恢复合并前工作树内容。

## 9. 遗留问题与台账回填

1. 项目主表 `tasks/queue/index.md`：0031 应回填“已于 `141a88a8` 合入主干，tag `ultimaagent-0031-merged-20261110`”；0029 应继续为 `blocked`，原因更新为“P2 正式全量门 379 failures，已 abort，主干仍不可见；feature worktree 尚有未提交合同修复”。
2. 全局主表 `H:\UltimaAI\_shared\queue\global-queue-index.md`：同样记录 0031 merge commit/tag；0029 不得标 frozen/completed，记录主干不可见与待独立兼容性修复。18766 离线不阻塞上述人工回填。
3. 0032 本单状态应为“P1 完成、P2 blocked”，不能整单 completed。
4. 后续另立兼容性工单：先由 0029 原执行线把未提交 coverage/预算/T5 产物形成独立 commit 并复审，再诊断 full-suite 顺序污染，最后重新执行同型合并门。不得复用本次失败全量门作为通过证据。

长期合并门保持：任何工单宣布 frozen/completed 前，主干必须能直接取到工单卡点名的全部产物；只在 feature branch 或未提交 worktree 可见，只能标 blocked。
