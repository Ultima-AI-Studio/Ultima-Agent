# 0037 队列体检改造前后对比账

- 工单：`wo-ultimaagent-20261111-0037`
- run：`tasks/queue/runs/wo-ultimaagent-20261111-0037-20261111T025942414734Z`
- 改造前记录：`before.json`，2026-11-11 11:03:51 +08:00，代码 revision `9cfc7fa655747d205279dd4bfde13aae790fd650`
- 改造后记录：`after.json`，2026-11-11 11:22:09 +08:00，实现 commit `300ee2ec22d17f52de04fbf2917d00b2b60923e2`
- 同一数据源：两次都只读 `tasks/queue/queue-status.json`；本单未暂存、未提交、未改写该文件。

## 总数与 strict 语义

| 记录 | P0 | P1 | `--strict` | 解释 |
|---|---:|---:|---:|---|
| 改造前 | 0 | 153 | 0 | note 结论会把缺少事实 run 的 audit 问题降成 P1；目录/工单前缀能让空目录或无关 tag 通过 |
| 改造后 | 2 | 221 | 2 | 0019/0020 没有内容身份匹配的 `dispatch-record.json`，不再以 note 代替 run 事实；P0 是新暴露的不可验证链路，不为凑零删除 |

`--strict` 的 0→2 是预期且确定的：CLI 语义未变，仍是“有 P0 返回 2”；变化来自判据封住假阴性后真实暴露了 2 条 `AUDIT_WITHOUT_RUN`。普通 `--json/--out` 仍返回 0，运行错误返回 1，三档均有测试。

### 按 code 计数

| level / code | 前 | 后 | 差值 | 原因 |
|---|---:|---:|---:|---|
| P0 `AUDIT_WITHOUT_RUN` | 0 | 2 | +2 | 0019/0020 的 note 不再冒充 run 事实；均标 `unverifiable` |
| P1 `AUDIT_WITHOUT_RUN` | 3 | 0 | -3 | 0019/0020 升为 P0；0007 从 5 份 `dispatch-record.json` 内容身份得到真实 run 证据后消失 |
| P1 `CARD_UNTRACKED` | 19 | 18 | -1 | 0037 卡在实现 commit 进入 HEAD；不是判据放宽 |
| P1 `FROZEN_WITHOUT_RUN` | 40 | 53 | +13 | 不再把前缀空目录/session-only 目录当 dispatch run |
| P1 `LEGACY_CARD_MISSING` | 38 | 38 | 0 | 未变；全部保留 evidence |
| P1 `LEGACY_FROZEN_WITHOUT_TAG` | 38 | 39 | +1 | 0004 的前缀 tag 没有 run/note 事实映射，不再被前缀放行 |
| P1 `ORPHAN_RUN` | 11 | 63 | +52 | 52 个目录没有 `dispatch-record.json`，归属改标 `unverifiable`，不再由目录前缀猜测 |
| P1 `STALE_BLOCKER` | 4 | 10 | +6 | 3 条旧关键词误报消失；9 条无法实测的 blocked 理由显式变成 `unverifiable` |

## 消失项

| 原 issue | 原来为什么报 | 现在为什么消失 | 判读 |
|---|---|---|---|
| `AUDIT_WITHOUT_RUN / wo-ultimaagent-20261030-0007` | 旧逻辑只看空 `audit_run`，即使 note 有结论仍报 P1 | 现扫描到 5 份内容字段 `order=wo-ultimaagent-20261030-0007` 的 `dispatch-record.json`，以真实文件身份通过 | 原判据误读信号，现已纠正 |
| `CARD_UNTRACKED / wo-ultimaagent-20261111-0037` | 改造前卡尚未进入 HEAD，旧判据当时如实报告 | 实现 commit `300ee2ec` 已把卡提交，`git ls-tree HEAD` 可取得 | 事实随本单提交变化，不是原误报、不是放宽 |
| `STALE_BLOCKER / wo-orb-w9` | 旧逻辑见“审计名额”便判过期，没有验证实际阻塞链 | 新逻辑同时读到“工作树改动”约束，并实测当前工作树非净，因此该条件仍成立，不再判 stale | 原关键词误报 |
| `STALE_BLOCKER / wo-ultimaagent-20261110-0033` | 旧逻辑见“未提交改动/clean-tree/562 条/审计名额”便判过期 | `git status --porcelain --untracked-files=all` 实测仍非空，clean-tree 条件当前未消失 | 原关键词误报 |
| `STALE_BLOCKER / wo-ultimaagent-20261110-0035` | 与 0033 相同，旧逻辑把措辞命中等同于过期 | 当前工作树实测仍非空，不能声称 blocker 已过期 | 原关键词误报 |

## 新增项

### 新增/升档的 P0（2 条，均保留）

| issue | 真/假/不可验证 | evidence 结论 |
|---|---|---|
| `AUDIT_WITHOUT_RUN / wo-ultimaagent-20261101-0019` | 真：缺少机器可读 run 证据；审计是否做过本身不可验证 | `audit_run=(empty)`，且所有 `dispatch-record.json` 内容身份精确匹配数为 0；note 不再代替 run |
| `AUDIT_WITHOUT_RUN / wo-ultimaagent-20261101-0020` | 真：缺少机器可读 run 证据；审计是否做过本身不可验证 | 与 0019 相同，精确匹配数为 0 |

### 新增 `FROZEN_WITHOUT_RUN`（13 条，均为真证据缺口）

这些单有目录/session/tag 等材料，但没有内容字段精确指向该单的 `dispatch-record.json`。每条均保留 P1；没有把“确实执行过”外推成“派发记录存在”。

1. `kws-siri-style`
2. `s2-combo-window`
3. `s2-tool-extend`
4. `wo-orb-w6`
5. `wo-orb-w7`
6. `wo-orb-w8`
7. `wo-s1-host-shell`
8. `wo-s1-task-text-loop`
9. `wo-ultimaagent-20261101-0014`
10. `wo-ultimaagent-20261101-0015`
11. `wo-ultimaagent-20261101-0016`
12. `wo-ultimaagent-20261101-0017`
13. `wo-ultimaagent-20261108-0026`

### 新增 `LEGACY_FROZEN_WITHOUT_TAG`（1 条，不可验证，保留）

- `wo-ultimaagent-20261030-0004`：Git 中虽有前缀相似 tag，但 run 回执与 note 均没有把任何现存 tag 映射到本单。旧逻辑仅凭前缀放行，可能是假阴性；现按 `unverifiable` 保留 P1，没有声称 tag 一定不存在。

### 新增 `ORPHAN_RUN`（52 条，事实缺口为真，归属结论不可验证）

下列每个目录的真实共同事实都是 `dispatch-record.json count=0`；因此“无法证明归属”为真，但脚本没有猜成“必然孤儿”，统一输出 `classification=unverifiable`：

1. `kws-siri-style-20261028T103200`
2. `s2-combo-window`
3. `s2-combo-window-r2`
4. `s2-combo-window-r3`
5. `s2-tool-extend-20261026T185745837Z`
6. `wo-orb-w6-20261108T125503986395Z`
7. `wo-orb-w6-20261108T125637445858Z`
8. `wo-orb-w6-20261108T133403104052Z`
9. `wo-orb-w6-20261108T133604629405Z`
10. `wo-orb-w7-20261108T142242990263Z`
11. `wo-orb-w7-20261108T152126993086Z`
12. `wo-orb-w7-20261108T152326360547Z`
13. `wo-orb-w7-20261108T155949893027Z`
14. `wo-orb-w7-20261108T160133265380Z`
15. `wo-orb-w8-20261108T170108721645Z`
16. `wo-orb-w9-20261108T172637299457Z`
17. `wo-orb-w9-20261108T173025279789Z`
18. `wo-orb-w9-20261108T175009866475Z`
19. `wo-s1-composite-window-20261021T053435036433Z`
20. `wo-s1-composite-window-20261023T231458288348Z`
21. `wo-s1-composite-window-20261023T234453835511Z`
22. `wo-s1-composite-window-20261024T000414077071Z`
23. `wo-s1-composite-window-20261024T001016601323Z`
24. `wo-s1-composite-window-20261024T001805783139Z`
25. `wo-s1-composite-window-20261024T003814394304Z`
26. `wo-s1-composite-window-20261024T005308788290Z`
27. `wo-s1-host-shell-20261021T023427316731Z`
28. `wo-s1-task-text-loop-20261021T042417690879Z`
29. `wo-s1-task-text-loop-20261021T044748126206Z`
30. `wo-s1-voice-poc-20261021T041728559262Z`
31. `wo-ultimaagent-20261101-0014-20261101T044235374932Z`
32. `wo-ultimaagent-20261101-0014-r2-20261101T051947408960Z`
33. `wo-ultimaagent-20261101-0015-20261101T044235483745Z`
34. `wo-ultimaagent-20261101-0015-r2-20261101T055445151140Z`
35. `wo-ultimaagent-20261101-0016-20261101T044235514405Z`
36. `wo-ultimaagent-20261101-0017-20261101T044614838904Z`
37. `wo-ultimaagent-20261108-0026`
38. `wo-ultimaagent-20261108-0026-20261108T045842676989Z`
39. `wo-ultimaagent-20261108-0027-20261108T060009382096Z`
40. `wo-ultimaagent-20261110-0034-t1-20261110T131134Z`
41. `wo-ultimaagent-20261110-0034-voice-real-gate-20261110T125206632Z`
42. `wo-ultimaagent-20261110-0034-w1w2-close-20261110T124721674Z`
43. `wo-ultimaagent-20261110-0035-entry-baseline-governance-20261110T135656265Z`
44. `wo-ultimaagent-20261110-0035b-work-order-20261110T140510186Z`
45. `wo-ultimaagent-20261110-0035c-e3-main-20261110T141257494Z`
46. `wo-ultimaagent-20261110-0035d-work-order-20261110T141648847Z`
47. `wo-ultimaagent-20261110-0036-mechanism-20261111T021517Z`
48. `wo-ultimaagent-20261110-0036-mechanism-20261111T021755Z`
49. `wo-ultimaagent-20261110-0036-task-system-rework-20261110T154502727Z`
50. `wo-ultimaagent-20261110-0036-task-system-rework-r2-20261110T154645289Z`
51. `wo-ultimaagent-20261110-0036-task-system-rework-r3-20261110T155000629Z`
52. `wo-ultimaagent-20261111-0037`

### 新增 `STALE_BLOCKER`（9 条，均不可验证，保留）

这些条目不是“已判过期”，而是旧逻辑完全沉默、现逻辑明确指出没有受支持的当前状态探针：

1. `wo-s1-composite-window`
2. `wo-s1-engineering-packaging`
3. `wo-s1-remote-update`
4. `wo-ultimaagent-20261101-0021`
5. `wo-ultimaagent-20261103-0024`
6. `wo-ultimaagent-20261108-0027`
7. `wo-ultimaagent-20261108-0028`
8. `wo-ultimaagent-20261108-0029`
9. `wo-ultimaagent-20261110-0034`

## 未变项

按“code + 工单（ORPHAN_RUN 用目录名）”对账，有 148 个身份未变：

- `AUDIT_WITHOUT_RUN` 2：0019、0020（但从 P1 升为 P0，见新增/升档段）。
- `CARD_UNTRACKED` 18。
- `FROZEN_WITHOUT_RUN` 40。
- `LEGACY_CARD_MISSING` 38。
- `LEGACY_FROZEN_WITHOUT_TAG` 38。
- `ORPHAN_RUN` 11：`_probe`、`_probe2`、`_windowprobe`、`audit-w8-20261109`、`audit-w9-20261109`、`gorch-chain-smoke-20261109`、`gorch-chain-smoke2-20261109`、`queue-engine-20261021T0830`、`smoke-gorch-20261109`、`verify-env-after-fix`、`verify-req-txt-20261109`。
- `STALE_BLOCKER` 1：`wo-ultimaagent-20261108-0030`，但现明确为 `unverifiable`，没有继续猜“已过期”。

所有未变 issue 在 after 记录中也新增了非空 `evidence`、`classification` 与 `confidence`；身份未变不代表判断方法未改。

## 仍不可靠的判据

一句话结论：`CARD_MISSING` 仍依赖规范文件名而未核卡内身份；tag 的 note-token 兜底仅为 `confidence=low`；`FROZEN_WITHOUT_RUN/AUDIT_WITHOUT_RUN/ORPHAN_RUN` 对无 `dispatch-record.json` 的历史或独立执行只能标不可验证；`STALE_BLOCKER` 除 clean-tree 外多数理由无机器探针；`VIEW_DRIFT` 仍依赖 renderer 自身覆盖面；三个 `LEGACY_` code 继承对应基础判据的这些限制。

## T2/T3/T4 自证

- 所有 after issue：223/223 `evidence` 非空。
- T2 连续 strict：两份 JSON SHA256 都为 `BA258E01D8D4DF689048305B22BF8E385F3BF6BB711936093026E850BC031F62`，两次 exit 均为 2，无抖动。
- 0025：`FROZEN_WITHOUT_TAG=0`，evidence 指向 `wo-ultimaagent-20261103-0025-frozen-20261111`，`confidence=low`（note-token 兜底）。
- 0026：`FROZEN_WITHOUT_TAG=0`，evidence 指向 run 回执中的 `ultimaagent-audit-hardening-20261108`，`confidence=high`。
- T3 新增测试：27 passed；完整 `scripts/tests`：104 passed in 7.25s。
- 反向守护：临时恢复旧前缀写法后，10 个语义 tag 回归 10 failed、exit 1；恢复当前实现后 27/27 与 104/104 全绿。
- 本单没有引入第三方依赖；实现仅使用 Python 标准库和仓库现有 `order_naming`。
