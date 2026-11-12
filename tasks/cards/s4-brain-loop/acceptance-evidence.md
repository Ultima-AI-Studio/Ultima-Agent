# s4-brain-loop 验收证据

- 日期：2026-10-27（Asia/Shanghai）
- 结论：COMPLETED
- 实现：主脑决策回路 `src/brain/loop/brain_loop.py`（M01）+ 执行参数契约 `src/brain/loop/params.py`（TD-05 落地）
- 冻结组件：未修改任何冻结组件；复用 TaskQueue / ParadigmGate / ScopePolicy / AppendOnlyAuditLog / MemoryLayers / BehaviorMapper 真实实例

## 实际命令与结果

1. `python -m unittest src.brain.loop.tests.test_loop_s4 -v`
   - `Ran 11 tests` → `OK`（ACCEPT-1~7 + Correctors 单测）
2. 回归 `python -m unittest src.brain.guardrails.tests.test_guardrails_s3 src.brain.orchestration.tests.test_orchestrator_s3`
   - `Ran 37 tests` → `OK`（既有闸门/编排不倒退）
3. 全部测试数据落 tempfile 临时目录，未污染真实库

## ACCEPT-1~7

| ID | 结果 | 证据 |
|---|---|---|
| ACCEPT-1 | PASS | 全链端到端 approved：任务到"回执"阶段、审计留痕 15+ 条（loop.* 事件）、记忆归档 working/reflection、呈现 state=idle |
| ACCEPT-2 | PASS | 下发执行参数七字段齐全（max_turns/temperature/max_tokens/output_protocol/tools_allowlist/permission_scope/acceptance_gate） |
| ACCEPT-3 | PASS | 返回 execution_report 缺字段（缺 trace/self_check 等）→ 结构查打回 replanned |
| ACCEPT-4 | PASS | 四查各自可触发：方向查（自评 gate=fail→replanned）、权限查（ACTION 越界工具→rejected）、一致性查（与记忆冲突标记命中→rejected）、结构查（缺字段→replanned） |
| ACCEPT-5 | PASS | 路由分工接口：executor 可替换（custom-router 注入后 approved，report.model=external-router） |
| ACCEPT-6 | PASS | 入口兼容：cli/voice/im 三入口均 approved |
| ACCEPT-7 | PASS | 回执字段完整（query/entry/status/execution_params/execution_report/verdicts/loop_trace/reason），ReceiptValidator 复核 0 issues |

## 关键实现约束

- 14B 主脑=编排者：下发带参数 + 审计返回；深度执行外发（本批次 ExternalExecutorStub 确定性桩，真实外部模型路由=替换 executor 即接线）；
- 审计校正四查三态：方向/权限/一致性/结构 → approved / replanned（打回带校正指令）/ rejected（拒绝+降级原因）；
- 缺 trace 视为结构问题（structure 兜底打回），仅真实越权动作判 rejected；
- 每环写审计（AppendOnlyAuditLog append + hash 链），audit_ids 收集 _hash。
