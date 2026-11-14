你是本次工单的执行代理。工单号 `wo-ultimaagent-20261113-0061`，标题「Autoloop P0 唯一写入口三件套（inbox＋queue-writer＋reconcile）」。

## 第一步（必须）
读 `docs/INDEX.md` 后，完整读取：
- `tasks/queue/wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md`（本单卡，逐条照做）
- `docs/plans/next-autoloop-融合实施方案-20261113.md` §3、§8、§10（inbox/writer/claim_id 设计出处）
- `scripts/dispatch-work-order.py`（T4 要把其队列直写收敛为调用 writer，参数表保持不变）
- `docs/specs/next-感知交互参数基线-20261113.md` §14.3（L510 单写口口径，只读对齐，不改）

## 执行方式
- 按 T1→T5 顺序；每完成一 T 立即写执行报告 `docs/reports/exec-wo-ultimaagent-20261113-0061.md`，不得攒到最后。
- 全部测试用隔离临时目录与夹具，不触碰真实 queue-status.json；时间阈值从既有配置/常量入口读取，不依赖当前生产数量。
- 判据用词固定：写域＝`在声明域内`／`越界`；结论＝`T6_GATE=PASS|FAIL`。

## 硬约束
- 只写卡 §5 写入域内文件；基线、tracker、其他工单卡、全局主表一律不碰。
- queue-writer.py 是 queue-status.json 的唯一写者；禁止保留派发器裸写分支或第二写路径。
- reconcile-inbox.py 全程只读，禁止自动修复；存量 claim_id 不批量改写。
- 不改 dispatch-work-order.py 现有 CLI 参数，不实现 Autoloop 外挂，不新增产品承诺。
- 不得 `git add/commit/tag/push`，不得更新队列状态，不得调 18766，不得访问 `H:\UltimaAI\UltimaAgentNext`。

## 修复轮（T6，2026-11-14 补充授权）
首轮 T5 诚实 FAIL，两个阻塞项已获写域补充授权：
- 收口 `scripts/render-queue-views.py` 的 `migrate()` 写路径：authority 不存在时 fail-closed 指向 queue-writer，不自行创建；正常渲染仍只写 index.md。
- 对齐 `tests/test_audit_slot_age.py`（Markdown 行→JSON-dict records）与 `tests/test_dor_gate.py`（删 resolve_work_order_card 引用、命名对齐），断言意图与数量不减少。
- 完成后重跑写入口扫描与扩展回归，确认写 authority 仅 queue-writer、此前 12 失败转通过、无新增失败。

## 结束条件
T1–T6 Gate 全绿；写入口扫描显示写者仅 queue-writer.py；writer `--selftest` 退出码 0；reconcile 正常/重复/孤儿夹具 diff 分别为 0/非0/非0；写域差值与卡 §5 一致。报告最后两行依次为 `T6_GATE=PASS|FAIL` 与 `READY_FOR_INDEPENDENT_AUDIT`。结束后在对话里给出：各 T 一条结论、唯一写者扫描结果、selftest 与 reconcile 退出码、写域越界声明。
