# wo-ultimaagent-20261103-0023 — Jarvis P0 stage report

## Outcome

**BLOCKED / REVISE after the authorized bounded repair.** The KWS product-entry drift is repaired and covered by RED→GREEN evidence, but the fresh T4 full-tree run has a non-exempt real-inference failure. The work order is not eligible for commit, tag, push, closure, or freeze in this run.

## Stage receipts

| Stage | Result | Fresh evidence |
|---|---|---|
| T0 | GREEN | Baseline 932 passed + 120 subtests after process-local Ollama PATH correction; no product implementation changed. |
| T1 | GREEN after audit repair | 128-bit per-turn nonce + JSON speech/selection envelope; forged trusted/boundary markers remain data; 11 passed. |
| T2 | GREEN after audit repair | 10 multilingual injection, 8 secret, 3 uppercase samples blocked; 0/100 normal false positives; product BrainLoop seam integrated; 30 focused + 35 integration passed. |
| T3 | GREEN after bounded REVISE repair | Product `KeywordSpotter` construction now binds the frozen `threshold=0.08`, `keywords_score=2.0`, and `num_trailing_blanks=8`. Focused evidence is RED 1 failed → GREEN 1 passed. |
| T4 | BLOCKED | Fresh full tree exited 1: 979 passed, 2 failed, 120 subtests. After the already documented child-PATH correction, Ollama discovery passes but real `jarvis ask` still fails with llama-server CUDA OOM. This is outside the sole authorized timestamp-race exemption. |
| T5 | BLOCKED receipt issued | `data/evidence/jarvis-p0/T5/receipt.json`. |

## Security and license corrections

- Fixed the first audit's prompt-boundary escape by binding every envelope to a fresh 128-bit nonce absent from all inputs and serializing speech/selection as JSON strings.
- Connected PoisonGuard ahead of both tracked BrainLoop memory writes; rejected content cannot reach the delegate.
- Preserved Jarvis and DockWright fixed donor references and MIT notices. DockWright copyright matches the bundled LICENSE: `Adel Elo`.
- No AGPL or P1 module was included.

## Regression facts

- Full-run infrastructure RED: repository-local basetemp disappeared mid-run, producing 833 passed / 1 failed / 144 errors / 120 subtests; retained in `T4/full-junit.xml`.
- Full-run test-order RED: 977 passed / 1 failed / 120 subtests; the new KWS fake-module test was repaired and its original order now passes 2/2.
- Full-run existing flaky RED (reproduced twice): 977 passed / 1 failed / 120 subtests. The untracked PreferenceStore records timestamps to milliseconds, so consecutive writes can share `updated_at`; a 10-run probe produced 7 pass / 3 fail. This order did not modify or absorb that unrelated untracked tree.
- Commit-scope/current-work-order regression after audit fixes: 433 passed + 46 subtests.

## Environment and frozen boundaries

- Tests used `tools/venv-openjarvis` and `tools/venv-asr` only.
- Offline voice tests used saved WAV files only: no microphone and no playback.
- Existing voice process identity remained PID 24812 / child 24276 with creation time 2026-11-03 17:38:54; no restart occurred.
- Main-brain model, inference settings, production defaults, and frozen 0016/0017 semantics were not changed.
- The pre-existing KWS default drift was not repaired because this order explicitly forbids production-default changes.

## Git and rollback

- HEAD remains `34ac0c79bfc4252c46bd5128dcc25f5caa4c3d58`.
- No files were staged; no commit was created; tag `ultimaagent-jarvis-p0-20261103` was not created; push was not attempted.
- Before any future commit, stage only the named work-order files/hunks and exclude the pre-existing 14B→8B comment hunks in `agent_server.py` and every unrelated untracked tree.
- Because there is no commit, rollback is limited to removing only the new 0023 files and reversing only the documented integration hunks. After a future isolated commit, use a normal `git revert <commit>` rather than destructive reset.

## Required next gates

1. Restore enough local inference capacity for `qwen2.5:14b` without changing the model or inference parameters in this work order, then rerun the complete tree with the documented process-local Ollama PATH.
2. Only if the sole remaining failure is `test_preference_p2.py:52` may the main-brain timestamp-race exemption be applied; any other failure remains blocking.
3. After T4 meets that condition, main-brain performs acceptance; no third independent audit is requested or permitted.
4. Owner real experience remains a deferred acceptance item pending separately arranged physical-device validation; no complete V1 freeze may be claimed before it is supplied.

## 2026-11-04 REVISE bounded repair

- Read the authoritative KWS baseline before editing. Restored only `keywords_score` from 1.0 to 2.0 and `num_trailing_blanks` from 0 to 8 in `src/brain/voice/kws_listener.py`; `KWS_THRESHOLD=0.08` was not changed. The source comment points to `docs/specs/kws-wakeup-params-baseline.md` section 3.
- Added a regression assertion at the real `sherpa_onnx.KeywordSpotter` construction boundary. RED: exit 1 because score was 1.0. GREEN: exit 0, 1 passed with 0.08/2.0/8. Evidence: `T3/revise-kws-red-junit.xml` and `T3/revise-kws-green-junit.xml`.
- Fresh full tree using `tools/venv-openjarvis`: exit 1, 979 passed, 2 failed, 120 subtests. Evidence is retained at the requested `T4/full-green4-junit.xml` path despite the non-green result; its SHA-256 is `4718e8f5a9c7f7d5027c5d6785716e39a5ce4542a17db928a93f489a75d57dd6`.
- Diagnostic rerun with the previously established child-only Ollama PATH correction: `test_ollama_has_brains` passed; `test_jarvis_ask_real_inference` failed. Direct readback returned Ollama HTTP 500: CUDA out of memory while allocating 2,818,572,288 bytes for the `qwen2.5:14b` KV cache. No exemption applies.
- The authorized `test_preference_p2.py:52` millisecond race did not trigger in this run, so no race exemption was used and its code was not weakened.
- Voice daemon PIDs 24812/24276 and their 2026-11-03 17:38:54 creation times remained unchanged. No voice process was restarted.
- Owner real experience is **deferred** because it is currently unavailable. This report does not claim complete V1 freeze.
- Because T4 has a non-exempt failure, no files were staged and no commit, tag, or push was performed.
