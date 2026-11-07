# E02 输出结构诊断精确计划独立审查

结论：**NEEDS_FIXES**。本次仅审查离线诊断准备计划，未运行测试、导入产品、调用模型或网络，也未操作服务、UI、音频或既有进程。`actual_run_authorized=false`，`acceptance_credit=0`，实际研究与结果独审分配均为0。

- 原单：wo-ultimaagent-20261101-0021 / T2。
- 审查人：/root/review_e02_output_structure_plan；独立于计划实施者，无下级代理。
- 计划：H:/UltimaAI/UltimaAgent/docs/plans/jarvis-work-e02-output-structure-diagnostics-plan-20261108.md。
- 精确计划SHA256：`2e2c66d390f8f12dd6633df4c7f4beea756e296dbb381acff6c6f4ba7f21a633`。
- 提案SHA256：`d5bf87f4158b37e326a67f696c6817a3eef6f301f3f7796d6109d00093a5df42`。
- 冻结父：`0421a54cab572be013c3f7ad562e86406bfe8e52`，位于 C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-budget/UltimaAgent。

先读取本轮scope、DoR、registration；随后独立读回计划/提案SHA、父HEAD和登记四文件SHA，均一致。旧失败与旧结果独审仅作背景，不转授本轮准备或验收信用。

## 必须补正的两项

**PLAN-IF-01 / P2，计划第33行：原接口参数数目错误。**

父源码 `src/brain/work_research_diagnostics.py:121` 的签名是 `record_native_response_rejection(ledger, transport, raw_bytes, raw, max_tokens, reason)`，共六个位置参数；leaf调用位于 `src/brain/agent_server.py:435-440`。计划“保留前七个参数”须改为六个，并写清仅新增 keyword-only `request_context=None`。保持原参数顺序及异常语义。

**PLAN-BIND-02 / P2，计划第34-39行：新结构快照的响应摘要来源未写闭合。**

计划的 `build_output_structure(raw, entity, strict_schema, ack, max_tokens, scan)` 没有原始 `raw_bytes`，却要求输出含 `response_sha256`。父源码 `agent_server.py:427-437` 保留了实际收到的字节；`work_research_diagnostics.py:112-138` 已用这些字节计算响应SHA/长度，并与transport receipt核对。解析后的dict重新序列化会改变空格、键顺序或转义，不能当作收到的原始响应摘要。

修订应明确：先生成并核对原native记录，再将同一原拒绝的generation、receipt、request/response SHA及长度传递或合并到结构snapshot。新结构中的响应SHA/长度直接继承经核对的真实raw_bytes元数据，禁止重序列化raw推导；实际entity的SHA/长度也须与同一receipt匹配。可保持builder不接raw_bytes，但要写清recorder与attachment各自责任。补充非canonical外层JSON字节绑定断言，保留现有native摘要断言。仅扩展失败可回退原v4；原native记录本身失效仍按既有UNAVAILABLE。

## 已覆盖的计划边界

- 保持当前8B及digest、原题四来源、调用/字节/时间/输出预算、所有来源/事实/引用/覆盖/文件门和旧失败。实际研究、模型调用与结果独审额度均为0。
- length即使含完整JSON仍拒绝；JSON状态与有限结构统计不成为成功凭据。严格解析失败不保留异常原文，未知字段只保留受限状态/计数。
- 文本先完整安全扫描；thinking不留正文；片段最多3个，含字符偏移、省略量及明确模式。严格schema与sampler摘要分开。
- 按完整canonical packet字节计16384上限，覆盖中文/转义/片段拼接扩张与恰好边界；从FULL降到片段、无文本或完整原v4，不删除旧页证据。
- v5闭合验证及v3/v4兼容、公共摘要不泄露正文；原失败异常、正常成功写入/ACK重放及写后ACK拒绝的真实效果保留。
- RED/GREEN、原native用途保全、旧包/export与相关回归；固定90秒组限/最多2并行/原两排除；同字节快照、精确diff、manifest、fresh准备独审、本地commit/tag与读回。

这些是计划覆盖结论，未验证产品实现或实际运行效果。正式研究仍需新的明确分配。

## 已撤销的审查疑点

早期消息误将 `test_work_failure_diagnostics.py:37` 的v4断言归到共享helper。精确读取确认 `private_packet` 位于66-71行，只校验summary/raw/cap/SHA并解码；第37行属于正常final-before-write时限测试，其包按计划继续为v4。本项撤销，不计阻断、不要求扩大测试写域。文件SHA256：`666411f29e4d2975ce8bbfdba7714530e0010cb6feda51c1d5ad94681034d8c9`。

只创建本JSON/Markdown回执，产品、计划、旧证据和既有登记未修改。未进行live进程/WIP复测；相关边界仅据本轮磁盘记录核对。修订后应以新计划SHA进行限定复核；本回执不覆盖未来字节，也不构成准备包或结果验收PASS。