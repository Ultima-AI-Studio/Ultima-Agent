# 统一审计报告

## 报告头元信息

| 字段 | 值 |
|---|---|
| work_order | wo-ultimaagent-20261108-0026 |
| report_id | audit-hardening-t1-example-20261108 |
| generated_at | 2026-11-08T00:00:00Z |
| reviewer_role | eng.audit |
| audit_session_id | wo-ultimaagent-20261108-0026-T1 |
| source | ultima.guard.audit-report |

## 审计范围与方法

### 范围

- T0 independent audit prompt contract
- Existing deterministic reviewer semantics
- T0 stage receipt

### 方法

- Focused unittest RED/GREEN
- Existing reviewer regression
- ReceiptValidator independent readback

## 分级汇总

| severity | count |
|---|---:|
| blocker | 0 |
| major | 0 |
| minor | 1 |

## 逐项发现

| # | severity | item | detail |
|---:|---|---|---|
| 1 | minor | report-adoption | Historical free-form reports remain snapshots; new reports use the unified generator. |

## 交付门结论

- Gate: **PASS**
- 结论：**通过**
- 交付门依据：现有 `ReviewResult.ok` 与证据索引；LLM 声明不覆盖确定性 gate。

## 证据索引

| evidence_id | path | kind | summary |
|---|---|---|---|
| EV-001 | tasks/queue/runs/wo-ultimaagent-20261108-0026/T0/focused-regression.log | test | New and existing audit tests passed 28/28. |
| EV-002 | tasks/queue/runs/wo-ultimaagent-20261108-0026/T0/receipt.json | data | T0 receipt passed four-field validation. |
| EV-003 | docs/reports/wo-ultimaagent-20261108-0026-t0.md | report | T0 scope, RED/GREEN evidence, and boundaries. |

## 复测记录

| command | result | evidence |
|---|---|---|
| python -X utf8 -m unittest src.brain.guardrails.tests.test_audit_prompt src.brain.guardrails.tests.test_audit_s3 -q | PASS (28 tests) | EV-001 |
| ReceiptValidator(base=repo).validate(T0/receipt.json) | PASS (0 issues) | EV-002 |
