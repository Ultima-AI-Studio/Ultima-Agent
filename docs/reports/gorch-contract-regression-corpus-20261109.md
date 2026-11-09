# G-ORCH 契约解析回归语料 · 14 份现状复核（2026-11-09）

- 来源：上一轮用例 `Temp\contract-regression.py` 里硬编码的 `FILES` 常量（14 个路径）
- 复核脚本：`Temp\corpus-audit.py`（14 份逐份）+ `Temp\corpus-scan-all.py`（168 份全量，见 §五）
- 解释器：`tools/venv-openjarvis/Scripts/python.exe`
- 性质：**Owner 待确认的候选基线**，未冻结；确认后才转成测试 fixture
- 与 Codex 审计第 5 点对应：「14 份」的权威 ID 集合

## 一、14 份逐份实测

| # | 路径（相对仓库根） | 字节 | 卡数 | ACC 门数 | sha256[:12] |
|---|---|---|---|---|---|
| 1 | `docs/reports/evidence/w1-independent-20261021/round1/tasks/queue/wo-s1-host-shell.md` | 3821 | **5** | 0 | `5a1172a35dd4` |
| 2 | `docs/reports/evidence/w2-real-card-20261021T022119636372Z/library/queue/wo-s1-queue-engine.md` | 4696 | **5** | 0 | `3df47fca2274` |
| 3 | `docs/reports/evidence/w2-real-card-20261021T022102638240Z/library/queue/wo-s1-queue-engine.md` | 4696 | **5** | 0 | `3df47fca2274` |
| 4 | `docs/reports/wo-orb-w7-oversight-20261108.md` | 6582 | 0 | 0 | `d2055495999a` |
| 5 | `docs/reports/stage1-host-shell-20261021.md` | 1662 | 0 | 0 | `f17a18ebc38b` |
| 6 | `docs/reports/stage-pseudo-streaming-20261030.md` | 3287 | 0 | 0 | `04daf84ba495` |
| 7 | `docs/reports/stage-mainbrain-qwen3-8b-cleanup-20261101.md` | 6482 | 0 | 0 | `e3a847b991f6` |
| 8 | `docs/reports/stage-jarvis-p0-20261103.md` | 6271 | 0 | 0 | `fa6c82263c2a` |
| 9 | `docs/reports/w1-independent-acceptance-20261021.md` | 14690 | 0 | 0 | `ee372a769ab3` |
| 10 | `docs/reports/stage1-simulation-20261016.md` | 7489 | 0 | 0 | `253a820607f3` |
| 11 | `docs/reports/t0-baseline-fix-20261103.md` | 3814 | 0 | 0 | `e825414d9274` |
| 12 | `docs/reports/w2-independent-acceptance-20261021.md` | 18172 | 0 | 0 | `ecc45774f23b` |
| 13 | `docs/reports/evidence/window-t1-independent-20261024/review.md` | 8558 | 0 | 0 | `9172f027c29d` |
| 14 | `data/gorch/handoff/S7-smoke/batch/WO-README.md` | 1541 | 0 | 0 | `33bde03a68e7` |

**合计：14 份全部存在、全部可被 `order_cards` 与 `acc_rows` 解析，0 份被拒（0 误伤）；ACC 门总行数 = 0。**

## 二、这份语料的真实形状（重要）

| 分类 | 份数 | 说明 |
|---|---|---|
| 带卡表的工单 | **3**（#1、#2、#3） | 每份 5 张卡；其中 #2 与 #3 是**同一份工单的两个证据副本**（sha 相同 `3df47fca2274`），去重后 **2 份** |
| 无卡表的文档 | 11 | 阶段报告 5、独立验收 2、编排工单 1、审计复核 1、README 1、其余 2 |

## 三、它能证明什么、不能证明什么

**能证明**（也是本轮实测）：

- 收紧后的解析器对真实历史文档 **0 误伤**（14/14 解析通过）。
- 带卡工单的卡集合读取稳定（`wo-s1-host-shell.md` 读出 5 卡，与旧版逐字一致已在上轮比对过）。

**不能证明**（必须说明）：

- **不能证明 waiver 路径可用**。14 份里 `ACC = 0` 的全都是；其中 `卡数 > 0` 的是 #1~#3（去重后 2 份），**恰好就是问题 1 的 fail-open 形状**。但「解析不拒」只能证明解析器不误伤，不能证明「无表时的拒绝或豁免分支」正确——后者代码尚未存在。
- 因此「14 份零误伤」只是**回归安全网**，不是 waiver 功能的验收证据。要验 waiver，必须另造样本（见 §四）。

**口径修正**（此前表述不准）：

上一轮我说「14 份真实工单」，实际是 **14 份历史取证语料**，其中只有 3 份是工单（去重 2 份），其余 11 份是报告/验收/README。它们走的是「整篇文档解析」路径，只有带卡表的才进入卡/ACC 逻辑。

## 四、建议（待 Owner 确认后执行）

1. **把这 14 份冻结成静态 fixture**：路径 + 上表 sha256 快照，测试断言「这 14 条路径全部解析成功、0 拒」，并断言**候选数量变化时测试失败**（不自动纳入新文件，需 Owner 决策）。
2. **另建 waiver 判据样本**：一份**新建**的「有卡、无 ACC 门」工单（不进历史语料），用于第 6 步「有效 waiver 通过 audit+freeze」的正向/负向用例。它不该混进这 14 份。
3. **不要**把这 14 份用于断言「可以重新 freeze」——Codex 第 7 步已明确：历史冻结 tag 无需追溯重验。

## 五、全量扫描（168 份）：真实任务库里 17 份落在 fail-open 形状

为确认「这 14 份之外还有没有同形状的工单」而做的全量扫描，结果如下。

| 目录 | 份数 | 有卡有门 | **有卡无门** | 无卡无门 | 拒读/不可读 |
|---|---|---|---|---|---|
| `tasks/queue/*.md` | 74 | **0** | **17** | 57 | 0 |
| `tasks/cards/**/task.md` | 94 | 0 | 0 | 94 | 0 |
| 合计 | 168 | **0** | **17** | 151 | 0 |

**17 份「有卡无 ACC 门」的真实工单**（括号内为卡数）：

| 工单 | 卡数 |
|---|---|
| `wo-orb-w1` / `w2` / `w3` / `w4` / `w5` | 各 4 |
| `wo-orb-w6` | 2 |
| `wo-orb-w7` | 3 |
| `wo-orb-w8` / `w9` | 各 1 |
| `wo-s1-composite-window` | 3 |
| `wo-s1-engineering-packaging` | 1 |
| `wo-s1-host-shell` | 5 |
| `wo-s1-mvp-freeze` | 3 |
| `wo-s1-queue-engine` | 5 |
| `wo-s1-remote-update` | 3 |
| `wo-s1-task-text-loop` | 3 |
| `wo-s1-voice-poc` | 2 |
| **合计 17 份** | **52 张卡** |

### 由此产生的三条修正

1. **整个任务库 0 份工单写过 ACC 门表**（「有卡有门」= 0）。判据门这道机制在真实工单上从未被使用过，不是个别遗漏，是整层空转。
2. **问题 1 的严重性要上调**：不是「从未被真实工单触发」。真实情况是 **17 份工单、52 张卡正处在 fail-open 形状里**，只是正常审计链（`audit-work-order.py:268-275`）在到达冻结门前就把它们拒了。冻结门一旦被旁路调用（旧回执、手工回执），这 17 份都能被冻。
3. **这 17 份就是 waiver 的真实适用清单**：如果按 Codex 第 5 步「空 ACC 一律拒绝」，这 17 份将来重新冻结全部会被拒；要么给 52 张卡补 ACC 表，要么走 waiver。这个量级（52 张卡）是决定「历史是否追溯」的实际依据。

## 六、未做

- 未修改任何代码或测试（fixture 落盘需 Owner 确认口径后再走工单）。
- **未逐份打开这 17 份判断「哪些卡本身确实无可验收行为」**——这是 waiver 适用性的关键判断，需要人读卡内容，本轮只做了形状统计（卡数/门数），没有做语义判断。
- 未核对这 17 份的冻结状态（哪些曾用旧版 freeze 冻过），若要判断「历史是否追溯」需要补这一步。
