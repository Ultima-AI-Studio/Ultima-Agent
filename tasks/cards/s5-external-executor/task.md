# 任务卡：s5-external-executor
- **task_id**：s5-external-executor
- **标题**：真实外部模型路由接线冒烟（M01 决策回路真实执行端，A 类）
- **优先级**：90（P0）
- **reasoningEffort**：medium
- **category**：core　**skill**：engineering
- **依赖**：s4-brain-loop（BrainLoop executor 接线点已就绪）
- **登记核验**：已查注册表与产品对齐报告（product-alignment-s4-20261027.md §五维度1）；TD-05 执行参数契约 v0.1-draft §3 运行时调用链：14B 下发带参数、外部模型返回带参数明细、四查三态审计不变；BrainLoop.executor 参数即接线点（现默认 ExternalExecutorStub 确定性桩）；环境变量 DEEPSEEK_API_KEY 已配置（不硬编码、不落盘）。

## goal
真实外部模型路由接线冒烟（M01 决策回路的真实执行端）：
1. 新增 ExternalModelExecutor：OpenAI 兼容 chat/completions 客户端，接 DeepSeek（base_url=https://api.deepseek.com、model=deepseek-chat），key 仅从环境变量 DEEPSEEK_API_KEY 读取（凭证不硬编码、不落盘、不经日志）；
2. 契约对齐：run(task, params) → execution_report 六字段（model / actual_turns / tokens / trace[THOUGHT/ACTION/OBSERVE/FINAL] / self_check / over_limits）；下发带 ExecutionParams 七参数（TD-05 §2 基线默认 max_turns=5 / temperature=0.3 / max_tokens=8192），输出按 output_protocol 四段结构化；
3. 超限与失败语义：轮次/token 超限显式声明（over_limits 不静默截断）；网络/鉴权/超时失败 → 确定性错误码回传（不抛裸异常穿透审计）；
4. 冒烟：真实 DeepSeek 调用一轮，验证 approved 全链（下发带参数 + 返回带参数明细 + 四查通过 + 审计留痕），证据落 acceptance-evidence；
5. 兼容性：BrainLoop 注入 executor 即接线（零改动既有回路），ExternalExecutorStub 保留为离线回退。

**禁止**：
- 禁止硬编码/落盘 API key（仅环境变量）；
- 禁止修改 TD-05 参数基线值与冻结组件；
- 禁止向 fileDomain 之外写文件；
- 禁止将真实调用作为常驻单元测试（单测用桩，冒烟单独执行并留证）。

## acceptance[]
- [ ] ACCEPT-1：ExternalModelExecutor 可构造（key 缺失时明确报错、不崩溃）
- [ ] ACCEPT-2：桩模式下 run() 返回六字段 execution_report（mock httpx，无网络）
- [ ] ACCEPT-3：四段 trace 结构化解析（THOUGHT/ACTION/OBSERVE/FINAL 齐全）
- [ ] ACCEPT-4：失败语义（鉴权/网络/超时 → 确定性错误码，不穿透异常）
- [ ] ACCEPT-5：真实冒烟一次（DEEPSEEK_API_KEY 存在时）approved 全链通过，证据落盘
- [ ] ACCEPT-6：回归不倒退（test_loop_s4 11/11 + 相关回归）+ 回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / tasks / docs）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：真实外部模型路由接线冒烟（A 类，P0） |
