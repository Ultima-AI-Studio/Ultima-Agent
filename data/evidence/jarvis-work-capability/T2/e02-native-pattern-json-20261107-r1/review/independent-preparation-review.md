# 独立准备 / whole-branch 审查

结论：**PASS_PREPARATION_ONLY**。无阻断项；本结论仅绑定离线候选与下述封存证据，不构成 actual / 结果独审 / 发布证明。

原单 wo-ultimaagent-20261101-0021 / T2；候选 6d758d9c3961f156a062e349ec4a949e2ee7a9a9，父提交 e40a55b40c223181040dbb6a09d0c4d2da5026cf。候选及旧工作区均只读核对为 clean，候选 tag 匹配。

manifest SHA256: a8a65256c90f96c8fcac5b6126633bd9e95d135a1cc079fcc1c1523cba28ff95

plan SHA256: e186e142e773cef8bc5a3b7a80d6841dc87e1f06136026a26e5833f9025d1b8b

plan review SHA256: d2ecc69b70d01a6448e2dd612db4e9d98348794a743e94658c97e6ab2872fe53

逐项独立哈希读回：新清单956成员、当前输入1576，17分片714组当前源码/封存快照均匹配。JUnit逐例781 unique PASS =775产品+6官方参考；RED29失败/6通过，中间35GREEN未累计。旧189准备成员、56结果成员、1575输入及9个无关文件均保持。此为留存测试证据独立核对，审查员未重跑测试。

- Focus 1 — PASS；src/brain/agent_server.py:217-258,424-435：Projection is raw JSON string-body grammar only. Deepcopy preserves decoded strict schema, which validates parsed envelope before writer; replay reconstructs the same projection and independently validates expected strict schema. Escaped word-boundary overacceptance is explicitly exercised and refused by decoded strict validation.

- Focus 2 — PASS；src/brain/agent_server.py:232-236：JSON units exclude raw quotes, backslashes and U+0000..001F, admit complete standard escapes and four-digit Unicode escapes, and preserve ordinary Chinese/Unicode. Dollar and Unicode operation continuations use the original identifier contract. JSON-encoded controls remain expressible at sampler layer but decoded writer single-line validation still refuses them.

- Focus 3 — PASS；src/brain/agent_server.py:220-258：Canonical prefix/suffix, operation <=200, original identifier grammar and exact re.escape roundtrip restrict projection to issued claim patterns. Unknown shapes fail closed. Properties.claim traversal leaves ID patterns and enum/const/default business data unchanged. Only agent_server.py and two test files differ; writer, navigation, source binding and replay modules unchanged. Canonical wrong-operation fixture preserves coherent-hash replay rejection.

- Focus 4 — PASS_WITH_LIMITATION；src/brain/agent_server.py:310,424-427：Existing 49152-byte HTTP entity cap, aggregate body limit, deadlines and output budgets remain. No compiled GBNF size/performance or actual native binary execution is established; report explicitly discloses this. Python reference conversion is diagnostic compatibility evidence only.

- Focus 5 — PASS_WITH_LIMITATION；preparation-report.md:5-7,15-27：Shared service log supplement is correlated by time/status/card only, not request-bound response or qualified facts. Official pinned converter and 896 prototype combinations do not count as product delivery. 781 unique retained test cases comprise 775 product and 6 reference cases; SDK writes are mocked offline writes, not actual research credit. Old actual FAIL_CONFIRMED and exhausted allocations preserved.

INFO（非阻断）：

- src/brain/agent_server.py:234 — Escaped delimiters can decode to forbidden word neighbors. Safety relies on retained decoded strict validation; sampler schema must never replace the strict response schema.

- preparation-report.md:25 — 49152 is an HTTP entity limit. Native grammar compilation size, latency and actual 8B behavior remain unmeasured; no HTTP500-resolution claim is granted.

- verification/runtime-readback.json:5 — Inherited observer identity ee1bef6 describes the read-only observer; product candidate is 6d758d9. Retained checkpoint is not fresh runtime proof or continuous-liveness evidence from this reviewer.

closeout.py / publish.py 仅静态阅读，未执行且不属于本次封存manifest；它们的hash见JSON。本结论不证明后续收口、镜像、提交或tag已成功。

本审查无目标导入、测试、网络、运行态查询、模型、UI、音频、服务操作，仅exclusive-create两份审查文件。actual/resultreview额度0，E02=0/3，T2/Owner未通过，旧实际FAIL保留。
