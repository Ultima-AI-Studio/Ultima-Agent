你是本次工单的执行代理。工单号 `wo-ultimaagent-20261113-0065`，标题「Autoloop 融合方案『模块归属』独立评审」。

## 第一步（必须）
1. 读 `docs/INDEX.md`，按其中导航找到下列文件并**完整读取**（不要只读摘要）：
   - `tasks/queue/wo-ultimaagent-20261113-0065--autoloop-module-placement-review.md`（本单卡，逐条照做）
   - `docs/plans/next-autoloop-融合实施方案-20261113.md`（重点 §2／§3／§11）
   - `docs/plans/next-autoloop-三单拆解-20261113.md`
   - `docs/tracker/next-基础能力架构-20261113.html`（§02 六块、§04 Console 边界、§06 六条易画错关系）
   - `docs/specs/next-感知交互参数基线-20261113.md` §二十一、§二十二、§二十五
   - `tasks/queue/wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md`／`0062--autoloop-p1-contracts.md`／`0063--autoloop-p2-cancel-observe.md`
2. 读完再动手；未读先写视为不合格。

## 执行方式
- 按卡内 T1→T5 顺序执行，**每完成一个 T 立即把该 T 的证据写入报告**，禁止攒到最后一次性写。
- 唯一允许写入的文件：`docs/reports/review-autoloop-module-placement-0065.md`（新建）。
- 报告内每一条判断都必须带坐标（文件＋行号或章节号／T 编号），并附原文片段；无坐标的判断不计入。
- 三态裁定用词固定：`维持`／`改判`／`反对`；结论等级用词固定：`通过`／`有条件通过`／`不通过`。
- 发现方案 §11 有错就直说并给落点，不要为了认同而附和；发现全对也要补一条方案未写的边界。

## 硬约束
- 不得修改任何既有文件；不得 `git add/commit/tag/push`。
- 不得访问 `H:\UltimaAI\UltimaAgentNext`；不得调用 18766。
- 不得在报告里写未经回读的行号；抽检回读不少于 5 条并在 §7 贴输出。
- 不写实现、不写代码、不新增模块、不改「模块数六块」口径。

## 结束条件
报告七段齐全、§7 自证含抽检回读与越界声明，最后一行写 `T5_GATE=PASS` 或 `T5_GATE=FAIL`。结束后在对话里给出：结论等级、六行裁定结果摘要、三卡写域结论、未决项条数。
