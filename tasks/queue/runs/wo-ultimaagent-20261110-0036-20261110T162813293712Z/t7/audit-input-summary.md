# 0036 T7 审计输入摘要

- 工单：`wo-ultimaagent-20261110-0036`
- T0–T6：均已有提交和改造前/改造后双档证据；本轮未重做。
- T7 回填：七处执行端回填结果已写入工单卡；回填残留扫描计数为 0；登记 venv 下严格校验 PASS。
- verifier 对照：当前版与锁定 revision `90a4a9d5` 旧版检查同一真实 run，均 exit 2，且六项 `blocking_failures` 完全一致；该结果只证明普通交付单 verifier 未退化，不冒充元工单 PASS。
- 路径 A：真实元工单卡经严格 validate 与 dispatch dry-run 均 exit 0；审计在本摘要落盘后实际执行；freeze 必须因真实 verifier 为 false 而 fail-closed，禁止伪造回执或放宽门禁。
- 路径 B：只读回放存量 `wo-orb-w8-frozen-20261110` annotated tag，tag object、peeled commit、tree、卡片 blob 均可解析，前后 tracked status 条目数相同，没有创建或移动 tag。
- 全量回归：登记 venv 下 `python -m pytest scripts\tests -q` 为 6 failed / 45 passed，与 T0 基线逐项一致，差异为空。
- 易变计数：T0 porcelain 565；T7 实测 560（tracked 21 / untracked 539），按卡面规则记录差异并继续，不清理任何既有条目。
- 越界：无；T7 只触碰工单卡、L117 和本 run 的 `t7/` 证据，未修改 T0–T6 产品代码。
