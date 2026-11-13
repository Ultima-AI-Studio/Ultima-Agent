你是本次工单的执行代理。工单号 `wo-ultimaagent-20261113-0068`，标题「骨架冲突与主链半堵修复（S-001／S-002／S-003 ＋ G-03／G-05／C-17 ＋ 0057 收尾）」。

## 第一步（必须）
读 `docs/INDEX.md` 后，完整读取：
- `tasks/queue/wo-ultimaagent-20261113-0068--fix-skeleton-conflicts.md`（本单卡，逐条照做）
- `docs/reports/audit-wo-ultimaagent-20261113-0057-round2-20261114.md`（0067 审计，7 条修复的出处）
- `docs/reports/review-next-skeleton-0066.md` §3／§6（S-001／S-002／S-003 原文）
- `docs/specs/next-感知交互参数基线-20261113.md`（重点 §14.3、§15.2.1、§19.3、§21.6、§22、§25.3、§25.9、§25.11、附录 A）
- `docs/tracker/北极星架构树.html`（只读定位两个「任务编排」节点）
- `tasks/queue/wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md`（`queue-writer.py` 唯一写者口径，F-1 要对齐它）

## 执行方式
- 按 T1→T6 顺序；T1 先做 T0 快照（基线 sha256、行数、七处锚点原文、架构树两节点行号）并落盘证据。
- 每完成一 T 立即写 `docs/reports/fix-wo-ultimaagent-20261113-0068.md`（唯一新建报告），不得攒到最后。
- 改动一律「原位最小替换」，禁止格式化整份文件；每处改动保留改动前后原文与行号。
- 判据用词固定：越界＝`在声明域内`／`越界`；闭合＝`已闭合`／`未闭合`；结论＝`T6_GATE=PASS|FAIL`。

## 硬约束
- 只写 §5 写入域内的锚点；基线与架构树以外一律不碰。
- 不得新增第九态、第二写者、第二预算公式、第二个保留期数值。
- F-2 只能二选一（甲：迁移表加两行带 `compensate_failed` 门禁；乙：§25.11 改经 `FAILED` 达 retryCount≥2），不得两条并存；报告里写明选择与理由。
- F-5 先查 §22／§21.6 是否已有可复用保留期，有则只引用不复述年限。
- 不得 `git add/commit/tag/push`，不得更新队列，不得访问 `H:\UltimaAI\UltimaAgentNext`。

## 结束条件
八段齐全、§7 越界声明逐项、§8 自证含抽检回读不少于 5 条，最后两行依次为 `T6_GATE=PASS|FAIL` 与 `READY_FOR_INDEPENDENT_AUDIT`。结束后在对话里给出：F-1～F-7 各一条结论、F-2 选了哪个方案、基线行数变化、架构树改动行号。
