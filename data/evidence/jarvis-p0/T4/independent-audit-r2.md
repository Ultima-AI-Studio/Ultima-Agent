# Independent audit — round 2

- Work order: `wo-ultimaagent-20261103-0023`
- Reviewer: independent Codex sub-agent, read-only
- Result: **Critical remediation PASS; overall REVISE**

## Closed findings

1. Prompt input now uses a collision-checked 128-bit per-turn nonce and JSON string payload. Forged speech/trusted boundary text cannot close the nonce-bound envelope. Fresh result: 11 passed.
2. `src/brain/memory_write_boundary.py` is connected to both tracked `BrainLoop` writes (`pending_interrupt` and `reflection`). Rejected content cannot call `MemoryLayers.write`; normal arguments are preserved. Fresh results: 30 guard tests and 35 integration tests passed.
3. DockWright source headers now preserve the LICENSE copyright name `Adel Elo`.

## Remaining blockers

- Product `kws_listener.py` still has pre-existing `keywords_score=1.0` and `num_trailing_blanks=0`, whereas the authoritative replay uses `2.0 / 8`; product not-worse proof is therefore not closed.
- The full working-tree run remains RED because an unrelated, pre-existing untracked PreferenceStore test compares millisecond timestamps from consecutive writes.
- No Owner real-experience evidence exists.

The reviewer therefore forbids commit/tag/freeze/closure in this run.
