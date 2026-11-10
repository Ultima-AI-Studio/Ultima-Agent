# E02 native HTTP diagnostics — independent plan review

Work order: `wo-ultimaagent-20261101-0021 / T2`. Reviewer: `/root/review_e02_native_http_plan`. Review snapshot: 2026-11-07T08:34:48.0256695Z.

This is a single independent, read-only review of the exact plan below. Product files were unchanged across the inspection. The reviewer ran no tests, model calls, actual cases, network requests, process/service commands, UI/audio actions or subagents. Only this report and its JSON companion are written.

- Plan: `H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-native-http-diagnostics-20261107-r1\plan.md`
- **Plan SHA256: `4d91295ad0a9582ae5808d3b841082178d6909d792aeef2e2a80b1b882cb9574`**
- Candidate: `C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent`
- Candidate base recorded by the plan: `2b42b3e19516154a26cbc895a3d9e69fabb07ab2`

The current source demonstrates a real diagnostic omission: `agent_server.py:275-345` records request digest, actual HTTP status and transport counters, while `work_research_diagnostics.py:92-132` omits those receipts. The proposed projection can close that gap without touching transport or reading an error body. In particular, non-2xx status raises at `agent_server.py:307`, before `iter_raw`.

The final plan is sufficient at this gate:

- **Provenance:** plan lines 37–39 require the last receipt, one matching `ledger._timeline` send/admission-refused event, matching `send_reserved`, bounded timeline, and fixed route triples. Generation is obtained from that event, not SDK/model content. Null, pre-send and stale-receipt cases are part of the tests.
- **No false validation:** source records a transport return before JSON/schema/security checks. Plan lines 24 and 38–39 therefore require a matching chat wire generation, request hash and `secured_envelope`, in addition to sent/2xx/no transport error. A status code alone cannot grant `validated_response`; the flag grants no factual or delivery credit.
- **Closed bounds:** plan lines 37–40 retain canonical/duplicate-key/request-binding validation and CAP 16384, reject bool-as-int and free text fields, enforce metadata/chat caps and count coherence, and constrain present generations to 1..8 and receipt indices to 0..23 for at most 24 receipts.
- **Scanner and freeze:** the current capture scans, serializes, validates and freezes once under the ledger lock. The plan preserves that behavior, fails unavailable on capture errors, and adds stream/privacy, scanner-failure and late-mutation tests.
- **Tests and authority:** the plan requires real SDK MockTransport fixtures and existing offline regressions with separate RED/GREEN receipts, then a fresh independent preparation review. It keeps the current 8B, original budgets, retry 0 and model/actual allocations 0. No transport, request/schema/replay, write, ACK or acceptance behavior change is included.

Two review comments were resolved in the final digest: the planner added explicit wire-generation/request-hash binding and unique timeline-event consistency (line 39), and corrected the zero-based receipt upper bound from 24 to 23 while requiring positive generations (line 38). **No blocking or nonblocking finding remains in the revised plan.**

Saved compatibility evidence is appropriately limited. The copied model manifest/config hashes and template hash agree with the recorded metadata. The saved template has the `enable_thinking is false` branch; pinned Ollama source maps think to `enable_thinking` and object format to a JSON schema response format. All seven saved upstream files matched their recorded size, SHA256 and computed git-blob SHA1; four also matched independently recorded expected blob IDs. The evidence does not establish installed-binary equivalence, full-weight integrity or the previous native parser's exact cause. Those limits do not block this diagnostic-only omission fix.

Before later preparation approval, the executor must prove the planned cases, including missing/duplicate/mismatched provenance; null/pre-send and metadata failures; stale or hash-mismatched wires; 200 with bad JSON/schema/scanner outcomes; 500 with an unread private/oversized stream; type/cap/coherence rejection; and scanner/CAP/freeze failures. The current diagnostic test source was inspected, but **no test result is claimed here**.

Inspected product/test file SHA256 values:

- `C:\Users\Administrator\.codex\worktrees\jarvis-e02-http-diagnostics\UltimaAgent\src\brain\work_research_diagnostics.py`: `50538f557ee3b8858b3b774cc2d510d3d8e01ce43cb57328610b8072d0c9c81c`
- `C:\Users\Administrator\.codex\worktrees\jarvis-e02-http-diagnostics\UltimaAgent\src\brain\agent_server.py`: `897940535b834ae291326860f2c60c1ef1e205d35ed92da74217bf7de4cb503d`
- `C:\Users\Administrator\.codex\worktrees\jarvis-e02-http-diagnostics\UltimaAgent\src\brain\work_tools.py`: `e1241f509b8a1b01dd3b1c7492a54bd14a68c7140da7925b2d148c67f8a4b187`
- `C:\Users\Administrator\.codex\worktrees\jarvis-e02-http-diagnostics\UltimaAgent\src\brain\tests\test_work_failure_diagnostics.py`: `48b4bf5c1a8d9528c12c8366b607c1befd1c92e200fd93497763039b1eab8ce0`

The JSON companion contains exact input/evidence hashes, inspected line ranges, rule references and per-check conclusions. It binds this review to G-TASKFLOW-001 and the requesting-code-review workflow.

Behaviors considered and declined to judge:

- Live E02 behavior or native parser/template/schema causality: no actual/model allocation and no request-bound predecessor transport export.
- Installed-binary equivalence and full 5GB model rehash: outside the declared investigation; neither is claimed.
- Continuous protected-process liveness: the saved point-in-time readiness receipt was read; this reviewer made no fresh runtime query.
- Implementation/test correctness, later preparation approval, integration/tag/push and queue/WIP closeout: subsequent execution/review obligations, outside this pre-implementation gate.

**Verdict: PASS_PLAN_ONLY** for plan SHA256 `4d91295ad0a9582ae5808d3b841082178d6909d792aeef2e2a80b1b882cb9574`. The exact revised plan may proceed to the already authorized offline implementation and verification. This receipt is not an implementation pass or a new runtime allocation. E02 remains **0/3**, T2/Owner remain unpassed, and the predecessor remains **FAIL_CONFIRMED**. Native-parser root cause remains unresolved.
