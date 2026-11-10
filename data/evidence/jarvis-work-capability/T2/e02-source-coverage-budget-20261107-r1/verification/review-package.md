# Independent whole-candidate review package

Base ee1bef61f04169c64978538dbc4ba799ef7be6c0 -> e40a55b40c223181040dbb6a09d0c4d2da5026cf at C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-coverage/UltimaAgent. Exact diff: code/candidate.patch. Spec: current direct user instruction + plan.md and inputs/direct-user-decision.json. Tests: verification/offline-post-commit-readback.json, original JUnit/audit/source snapshots selected there. Prior evidence: inputs/predecessor.json and verification/preservation-after.json.

## Review Focus (verbatim)

确认覆盖约束只缩小inspect合法source_id，不选择事实或固定页序；边界剩余2/缺2和剩余1/缺1必须到达第三来源机会。不能用卡为空/未确认页抬高覆盖。可用catalogue必须来自受信ledger和已验证snapshot，不能从模型prompt扩大权限。真实SDK的旧错误序列要拒绝，新合法八POST序列应实际write/ACK并通过重放；仅mock返回成功不合格。prewrite严格未交付与postwrite ACK区分；部分effect不能虚称无文件。所有预算和原生请求构造/HTTP诊断不变，旧失败不覆盖。


## Rulings and test-only adaptation

# SDD ledger — plan: H:/UltimaAI/UltimaAgent/docs/plans/jarvis-work-e02-source-coverage-budget-plan-20261107.md

- Task 1: pending exact plan review.
- Task 2: pending implementation and current offline proof.
- Ruling: create a new managed worktree from ee1bef6 because the old isolated checkout is sealed failure evidence; never overwrite old candidate.
- Ruling: no installs, model/live cases or broad live baseline; use pinned existing dependencies and guarded offline RED/GREEN/regressions.
- Pre-flight: Task2 depends on Task1 visible pages/read-count contract; generation/replay must consume the same current schema helper.

- Plan gate: PASS_PLAN_ONLY, exact hash 1f5e5776f7db9b5c406bc85c6670af50d1a4ba43ce145718067fb6e48a4de5ab; independent review SHA 3725311fa2063f79505c61840ed233d152245a1780e77d389a4ed97f9bf1af6b.
- Task 1/2 RED: coverage-red 39 assertion failures / 1 pass, zero errors; fifth same-source actually consumed read6 on old code, false completion reached final.
- Target GREEN: 40 passed with six reads, write, ACK and independent replay; diagnostics 31 passed after legal-final fixture update. Full affected regressions running under unchanged offline guard.
- Ruling: retain maximum-length private diagnostic coverage in verified ACK plus synthetic artifact failure; arbitrary prewrite text is now rejected by the requested contract. No old negative tests removed.
- Ruling: use equivalent Windows-native ledger and pinned guarded runner instead of Bash workspace wrappers; preserve evidence and worktree rather than deleting them.

- Ruling: regression transport blank_final expected the old later whitespace error. New prewrite enum correctly rejects earlier as Invalid native research envelope. Update only that expected error/comment in test_work_navigation_transport.py; keep all no-write, no-ACK, pending-page-no-promotion assertions. This necessary third test-file adaptation adds no product behavior and costs no weaker gate. Initial transport 103 PASS/1 stale assertion FAIL retained. Re-run guarded current-source suite after this test-byte change for exact final snapshots.

- Task 1: complete implementation; commit e40a55b40c223181040dbb6a09d0c4d2da5026cf; final current-byte guarded verification 746 unique PASS (740 product + 6 export).
- Task 2: complete implementation and tests; independent whole-candidate preparation review pending. Source changes: four product modules, three necessary test files.


Review all seven changed files and exact frozen manifest/pins. Do not run tests, model, actual case, service/process/UI/audio/network actions, or mutate product/index/HEAD. Write only independent-preparation-review.json/.md after read-only review. Record declined-to-judge behaviors explicitly. The offline-only package must not earn actual acceptance credit.
