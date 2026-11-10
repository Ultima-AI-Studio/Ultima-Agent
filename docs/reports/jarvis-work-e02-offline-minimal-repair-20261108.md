# E02 离线最小修复 T5 验收报告（2026-11-10 合并门补建）

## 1. 一句话结论

`codex/jarvis-e02-source-grounding-r1` 的锁定 revision `43da3f014a763b8ea3963872a8f1ce8ebea77531` 已尝试主干合并，但正式全量门触发中止判据，当前结论为阻断并待独立复审；本报告不自判 PASS。该 revision 的研究子系统定向回归在隔离 `OPENJARVIS_HOME` 下通过，但全量顺序下出现 379 个失败；同时，0029 工单卡要求的 coverage 单一实现和新增预算证明不在该 revision 中，合同缺口继续保留。

## 2. 改动清单与技术门实测

- 合入来源：`codex/jarvis-e02-source-grounding-r1@43da3f014a763b8ea3963872a8f1ce8ebea77531`。
- 分支相对共同基线 `6b70aa6f9223829682ec995fecc7d51952a3e717`：210 个文件，`+24,978 / -7`。
- 产品源码范围：`src/brain` 下 16 个非测试文件；其中 `src/brain/work_navigation.py` 为 38,517 bytes、691 行。
- 分支新增或修改的 25 个 `*test*.py` 文件在全新临时 `OPENJARVIS_HOME=C:\Users\Administrator\AppData\Local\Temp\wo-0032-openjarvis-236dc463bf2145eaba4bc5dcf97dadbc` 下实测：`1022 passed in 109.04s`，0 failed、0 errors。文件选择器为 `git diff --name-only 6b70aa6f9223829682ec995fecc7d51952a3e717 43da3f014a763b8ea3963872a8f1ce8ebea77531 -- '*test*.py'`；测试命令为 `tools\venv-openjarvis\Scripts\python.exe -X utf8 -m pytest <上述 25 个文件> -q --disable-warnings --junitxml=data/evidence/wo-ultimaagent-20261110-0032/p2-targeted-gate-isolated.xml`，stdout/stderr 落 `p2-targeted-gate-isolated.log`。
- 首轮未隔离用户级 OpenJarvis 配置时出现 `350 failed / 672 passed`，共同首因是 `Conflicting research template override`；按中止判据保守执行 `git merge --abort`。同一首失败用例在全新临时 HOME 下变为 1 passed，随后 25 文件整组 1022 项全绿。失败历史不删除、不豁免。
- 正式全量门在全新临时 `OPENJARVIS_HOME` 下回读为 2,140 tests、379 failures、0 errors、0 skipped（终端摘要：1,639 passed、379 failed、122 subtests）；JUnit SHA-256 为 `59b7b17d60de94062fb1e477cc83ae5d48da64f5cd3b03ccdcce4e058b06d4b1`。失败超过 20，已执行第二次 `git merge --abort`，P2 未提交、未打 tag。
- 已知环境抖动项 `test_jarvis_ask_real_inference` 在本次 JUnit 中存在且通过，没有豁免、删除或 skip。
- 本报告补建不修改产品功能语义，不吸收 feature worktree 的未提交源码或测试。

## 3. Coverage 契约逐项回读

0029 T1/T2 要求的目标是：任务无关输入、`UNCOVERED / PARTIAL / CAPACITY_EXHAUSTED / COVERED` 四状态、仅 `COVERED` 可写、runtime 与 replay 调用同一纯函数。

锁定 revision 的实际读回不满足该静态门：`src/brain/agent_server.py` 与 `src/brain/work_research.py` 仍各自用“具有 cards 的来源数 >= 3”计算写入资格，`src/brain/work_navigation.py` 中没有上述四状态的唯一 coverage 判定。因此本次合并门原本只拟恢复冻结分支产物在主干的可见性；但 P2 已因全量门失败中止，相关产物当前仍不可见，更不能把定向“测试通过”升级为“0029 T1/T2 合同完成”。

只读检查发现该 feature worktree 另有未提交的 coverage 实现、配套测试和报告草稿；它们不属于锁定 revision，也没有 commit/tag，故本单不擅自提交、不纳入合并信用。后续必须由原执行线先形成可审计提交，再另立兼容性合并门。

## 4. 预算证明状态

锁定 revision 中没有 0029 T3 所要求的“新增必要证据页后 `messages+schema <= 32768`”最终数值证明。本合并门没有重新选择页面、改 schema、放宽字节预算或增加调用次数。

因此 T3 仍按工单原判据记为设计缺口，待原执行线提交可复核数值；若仍无法证明 `<= 32768`，只能提交原工单规定的三选一裁定：减 schema 体积、减可渲染页数、或由 Owner 明确批准提高字节预算。本报告不代 Owner 选择。

## 5. 缺陷、未验证项、T5 对应与越界声明

| T5 要求 | 本报告对应 | 结论 |
|---|---|---|
| 一句话结论 | §1 | 阻断并待独立复审；不自判 PASS |
| 改动清单、行号或 diff stat | §2 | 已列 revision、210 文件统计、关键产物尺寸与测试证据 |
| coverage 输入/状态/资格/失败路径 | §3 | 目标已逐项列出；锁定 revision 未满足，缺口保留 |
| 预算数值或缺口三选一 | §4 | 锁定 revision 无最终数值，按缺口三选一保留 |
| 缺陷、待裁定与越界 | 本节 | 已列，越界为无 |

未验证项：真人测试未做；真实采集未做；远场测试未做。这三项均不属于本次离线合并门，不能由离线 pytest 或历史证据折算为已验证。模型调用、真实网络研究、真实入口、grant、E01/E03 信用也均未在本单新增。

遗留缺陷：0029 的 T1/T2/T3 合同交付尚未进入锁定 revision；feature worktree 的未提交内容不能作为主干产物或冻结依据。待裁定项是由原执行线先提交这些改动并完成独立复审，再建立新的兼容性合并工单。

越界声明：无。未改 `work_tools.py` / `work_service.py` 的既有语义，未改 profile、队列状态、看板、全局主表、既有冻结证据、模型默认值、依赖或预算；未播放、未录音、未调用麦克风。
