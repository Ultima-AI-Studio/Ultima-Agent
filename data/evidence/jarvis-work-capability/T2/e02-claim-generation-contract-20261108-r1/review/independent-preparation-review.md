# 独立整分支与离线准备审查

结论：**PASS_PREPARATION_ONLY**。候选 `d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b`，父 `bf7f7a9cf0e4ba559c29daa388c00379d12d345a`。依据 requesting-code-review/code-reviewer.md 模板独立只读审查整分支、精确计划/spec、证据包及后续脚本。

Manifest SHA256 `fc1e26d41c508c79c24d7f29738aa054db10e98a99198b279af69c2b2d2b0b95`；计划 SHA256 `1e26155fc2bf9a256d9cd4ed694a3537ad9deca6f7915381f2412ad41d09c0ea`。

## Strengths

生产改动仅移除代码claim精确operation前的可选自由文本，并同步共享阶段提示。解码strict、证据映射、writer、预算、读回和ACK保留；旧说明在前的表达仍可通过原strict。测试迁移保留了转义、Unicode、美元、边界及无写入用途，新增重放旧提示的负例。报告没有把生成约束改进混同事实或交付通过。

## Issues

Critical：0。Important：0。Minor：0。未发现阻断本次离线准备的新增问题。

## 独立核验

逐字节核对1434个manifest成员、1599输入、78源码及对应git blob；候选HEAD/父/tag一致、工作树干净。47份最终来源SHA在22组回执一致。直接解析JUnit，1004项且去重仍1004：994产品、4兼容、6参考转换，失败/错误/跳过均0；两个既有delivery排除保留。35项父基线、RED19中14预期失败/5正向通过、初次GREEN19+35也已核对。审计无denied，预期探针关闭。本审查没有重新执行测试。

175旧准备、56旧结果、31实际seal、1192父产品准备成员，1598旧输入、1567依赖与15无关文件均逐字节保持。旧实际完整正文直接重算SHA、3818字符、50/49重复及JSON pos1339/line45/column22；原实际仍失败且无artifact。

## Review Focus

1. PASS: exact operation extraction/canonicality is unchanged; the only pattern change removes optional prefix. Dollar, dot and Unicode operation cases have positive and prefix-negative coverage. Decoded strict acceptance of prose-first legacy claims remains unchanged.

2. PASS: complete JSON escape/character units are unchanged; raw quote/control/backslash negatives remain. Escaped boundary versus decoded strict distinction is explicit. Existing SDK tests retain no-write assertions and quoted Chinese/backslash write/readback/ACK replay. No fragment repair or partial JSON writing introduced.

3. PASS_WITH_LIMITATION: no finite 2000 repeat added. Strict decoded maxLength stays unchanged. Six reference checks include actual projected patterns and writer envelope; reference output 9685 grammar bytes/3993 sampler bytes. This is Python b10488 reference conversion only, not native compatibility, token fit or performance proof.

4. PASS: exact four-file branch diff and unchanged top-level AST outside the two intended functions preserve source/ref, question, transport budget, writer and ACK. Shared phase prompt is used by generation and replay; coherently rehashed old directive is rejected. Full 994-product-test suite plus 4 compatibility and 6 reference checks independently counted.

5. PASS_PREPARATION_ONLY: negative observations retain financing/TODO/effect-claim mismatches and unread S4. Actual failure remains failed with no artifact; preserved complete text independently hashes to 1f6b669b10cd3418e3ea6279a0c5253ec239184a6eab2efa1642d47963cec4de, length3818, repetitions50/49, JSON error pos1339/line45/column22. Semantic entailment/full original-question delivery remain unproven; no actual allocation or credit.

## 后续脚本与计划裁定

静态检查verify_offline.py、closeout.py、publish.py和final_readback.py：验收绑定精确证据/独审、保留旧失败和零分配；仅本地登记、精确路径发布及读回，无远端push或实际入口授权。closeout/publication/final-readback回执目前均不存在，因此不提前认定完成。Task2“五文件”按Task1明确四路径计数；原生有限重复只参考可转不构成恢复依据；已完成TDD回执读取用于ledger验证，后续1004为新运行；skill证据保留及拒绝动作不重试均合理。

## Declined to judge

空（[]）。尾部/非代码自由文本、引用错配、S4和完整覆盖风险均已评价并明确保留；没有以范围之名默默排除实际影响。

## Recommendations / Assessment

可继续已授权的精确离线收尾与Task3入口准备；本结论只针对产品准备。后续发布和入口必须绑定本候选及精确manifest。实际/model额度0、结果复核额度0、接受信用0；E02仍0/3，T2/Owner未通过。

This reviewer performed only local stdlib byte/XML/AST/JSON inspection and read-only git; no pytest, product/controller imports, native DLL, model/network calls, live process scans, UI/audio or service actions.

Test results are fresh implementation-run sealed receipts independently checked here, not tests rerun by this reviewer. Python operation audits are not OS packet capture; eager guard and exit receipts support offline scope only.

Unbounded suffix and noncode fields remain capable of exhausting the existing output budget; removing the prefix is not proof of eliminating model repetition or guaranteeing 2048-token completion.

Native finite-repeat compatibility/performance, semantic citation entailment, S4 inspection, complete original-question coverage and true-network gate remain unproven. These risks were evaluated and retained, not silently declined.

Saved protected identities establish recorded points only, not continuous liveness. No live process inspection performed.

closeout.py, publish.py and final_readback.py were reviewed statically only. Their output receipts do not exist at review time; local publication/mirror/readback and Task3 entry preparation are pending and receive no completion credit. Prior rejected push/deletion not retried.
