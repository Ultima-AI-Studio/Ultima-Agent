你是本次工单的执行代理。工单号 `wo-ultimaagent-20261113-0067`，标题「0057 执行结果独立审计（主链 §二十五）」。

## 第一步（必须）
读 `docs/INDEX.md` 后，完整读取：
- `tasks/queue/wo-ultimaagent-20261113-0067--audit-0057-main-chain.md`（本单卡，逐条照做）
- `tasks/queue/wo-ultimaagent-20261113-0057--next-fix-a-main-chain.md`（被审单的验收口径，11 编号映射）
- `docs/reports/audit-wo-ultimaagent-20261113-0056.md`（11 条 BLOCKER 原始定义）
- `docs/specs/next-感知交互参数基线-20261113.md`（重点 §15.2.1、§16.4、§17、§19.2、§22、§25 全部）
- `docs/reports/review-next-skeleton-0066.md`（三条已知冲突 S-001/S-002/S-003）
- `tasks/queue/runs/wo-ultimaagent-20261113-0057-20261113T152402246487Z/`（before.json、dispatch-record.json、final.json）

## 执行方式
- 审计独立：不看执行方自述结论，自己跑 diff、自己 grep 判据、自己判「是否真堵」。
- 按 T1→T6 顺序，每完成一 T 立即写入 `docs/reports/audit-wo-ultimaagent-20261113-0057-round2-20261114.md`（唯一新建文件）。
- 每条判定必须带坐标（章节号或行号）与原文片段；「已堵」必须能 grep 到判据原文。
- 三态用词固定：边界＝`未改（成立）`／`被改（越界）`／`无法判定`；覆盖＝`已堵`／`半堵`／`未堵`；Gate＝`可机检`／`半机检`／`不可机检`；一致性＝`一致`／`矛盾`／`无锚点`。

## 硬约束
- 不得修改任何既有文件；不得 `git add/commit/tag/push`（只读用 `git diff/log/sha256sum` 类命令）。
- 不得访问写入 `H:\UltimaAI\UltimaAgentNext`。
- 不得把执行方报告里的自证当作通过理由；可引用但必须标注「仅对照」。
- 统计数字一律以清单实际统计为准，不写预期数。

## 结束条件
九段齐全、§9 含抽检回读不少于 5 条与越界声明，最后两行依次为 `T6_GATE=PASS|FAIL` 与 `FREEZE_RECOMMENDATION=可冻结|修复后再冻结|打回`。结束后在对话里给出：结论等级、11 条覆盖判定分布、Gate 可机检分布、S-003 是否落在 §25.11、冻结建议。
