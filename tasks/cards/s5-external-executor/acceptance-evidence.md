# s5-external-executor 验收证据

- 日期：2026-10-27（Asia/Shanghai）
- 结论：COMPLETED
- 实现：真实外部模型路由 `src/brain/loop/external_executor.py`（ExternalModelExecutor，DeepSeek OpenAI 兼容 chat/completions）
- 契约：TD-05 execution-param-contract v0.1-draft §3 运行时调用链（14B 下发带参数 → 外部模型返回带参数明细 → 四查三态审计不变）
- 接线：BrainLoop(executor=ExternalModelExecutor().run) 注入即接线，既有回路零改动；ExternalExecutorStub 保留为离线回退
- 凭证：key 仅从环境变量 DEEPSEEK_API_KEY 读取（不硬编码、不落盘、不经日志）

## 实际命令与结果

1. `python -m unittest src.brain.loop.tests.test_external_executor_s5 -v` → **10/10 OK**（ACCEPT-1~4 + ACCEPT-6 注入全链）
2. 回归 `python -m unittest src.brain.loop.tests.test_loop_s4` → **11/11 OK**（不倒退）
3. 真实冒烟（DEEPSEEK_API_KEY 就绪，90s 超时，tempfile 隔离）：
   - `status=approved` 全链通过（受理→意图→领域→范式→规划→派发→闸门→执行→审计→编排→表达→呈现→记忆归档）
   - 四查：direction PASS / permission PASS / consistency PASS / structure PASS
   - 真实模型响应：model=deepseek-flash、tokens=514、四段 trace 解析完整、over_limits=None
   - 审计留痕 16 条、memory_archived=True

## ACCEPT-1~6

| ID | 结果 | 证据 |
|---|---|---|
| ACCEPT-1 | PASS | key 缺失→确定性错误码 credential_missing（fail 回执，不崩溃） |
| ACCEPT-2 | PASS | 桩 transport 下六字段 execution_report 齐全（model/actual_turns/tokens/trace/self_check/over_limits） |
| ACCEPT-3 | PASS | 四段 trace 结构化解析（THOUGHT/ACTION/OBSERVE/FINAL）；缺段显式占位声明不编造 |
| ACCEPT-4 | PASS | 鉴权 401→auth_failed / 限流 429→rate_limited / 网络→network_failed / token 超限→max_tokens 显式声明，均不穿透异常 |
| ACCEPT-5 | PASS | 真实 DeepSeek 冒烟 approved 全链（见上），请求体携带全部执行参数（model/max_tokens/temperature/messages），Authorization 仅 Bearer 环境变量 key |
| ACCEPT-6 | PASS | 回归 11/11 全绿 + 回执 ReceiptValidator 复核 + tasks.json 置 COMPLETED |

## 关键实现约束

- 下发带参数：_build_messages 注入 max_turns/temperature/max_tokens/output_protocol/tools_allowlist/permission_scope/acceptance_gate 全七参数；
- 返回带明细：report 六字段含真实 model/轮次/token/trace/自评/超限记录；
- 超限不静默截断：tokens_out > max_tokens 时 over_limits.declared=True 显式声明；
- HTTP 走 urllib（零第三方依赖），transport 可注入测试桩；测试全 tempfile / mock 环境变量，未污染真实库。
