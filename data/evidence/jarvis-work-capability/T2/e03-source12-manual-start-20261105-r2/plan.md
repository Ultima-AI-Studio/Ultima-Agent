# E03 fixture explicit start handoff plan

Original work order wo-ultimaagent-20261101-0021, T2; current candidate 7975e477665c02820fa235b73d203718bd33b2c9; current community 8B only.

Previous goal turn: progress. One authorized case ran and produced new input-clear evidence; one independent result review completed. It remains FAIL with no product inference, and both allocations are consumed.

New evidence: the operator confirms typing during the 20:19:45 activation. The previous foreground UI thread 19560 is the continuing Doubao process 27192 main thread (created 2026-11-04T16:31:54.8373861Z). The non-reproducing fixture-only case used continuing Chrome UI thread 1924. These identities locate the focus handoff, not the sender of the clear. The fixture currently uses AttachThreadInput to borrow foreground focus, then selects all text before its message pump. It can redirect ongoing typing into the selected sample.

Goal: make the acceptance setup wait for an explicit owned Start-button action and released keyboard keys before selecting the sample. Preserve the real E03 product path and all success/failure gates. No product source change is required.

Design:
1. Create both owned fixture windows with WS_EX_NOACTIVATE | WS_EX_APPWINDOW. Keep the original text/identity/policy and two target controls. Add one Start button inside the primary window; it is not a product write target.
2. Waiting must not activate a fixture or attach another thread's input queue. The existing 20-second fixture-start ceiling remains; the button wait is at most 15 seconds, checks stop, and pumps bounded message batches.
3. Accept only the primary window's own button notification. This is operator scheduling intent, not new security authority; the external root-issued case authorization still applies.
4. At accepted Start, sample only whether any keyboard key remains held. Do not log keys or payloads. A held key, timeout, stop, or failed native activation ends this case without any product submission.
5. Activate by ordinary SetForegroundWindow/SetFocus on the owned target, verify actual focus, then select the original sample. Remove AttachThreadInput entirely. A refused activation fails; no fallback input injection.
6. A manual-start receipt binds the fixture PID, primary HWND and readiness/start times. Backend verifies it before accepting initial fixture readback. The receipt does not refresh native/source proof or extend its 60-second age / 120-second authority lifetime.
7. Preserve runtime checks, same model/candidate, exact one CLI, original 300/1800/315 timeouts, effect reconciliation, exact-owned cleanup, all audits and independent fact review.
8. Further input or focus/selection drift still causes the original failure. This setup is not a guarantee against typing after Start.
9. No actual/release/authority is created by preparation. Previous actual failures and all sealed packages remain intact. A later single case needs its own explicit allocation.

Implementation files: new code/fixture_manual_start.py and tests; minimal fixture_adapter.py, acceptance_backend.py and RUNTIME_FILES changes. Reuse all other reviewed code and test bodies; record precise provenance and diff.

Task:
- [x] Write offline tests for exact button matching, timeout/stop, held-key rejection, no activation before click, no AttachThreadInput, callback restoration, and owned receipt validation; observe intended RED.
- [x] Implement the small native Start control and ordinary owned focus activation.
- [x] Verify real adapter wiring via isolated function definitions and mocked native calls; tests must open no windows, query no input devices and invoke no model.
- [x] Run the existing focused suite plus the meaningful new regressions once after fixes. Verify hashes/AST/candidate cleanliness; do not reuse old PASS as current evidence.
- [ ] Seal the package, run fresh independent preparation review under the original work-order gate, address concrete findings, and preserve all prior verdicts.
- [ ] Record current status, mirror the plan/report, commit/tag/push. Prepare the one-case operator handoff proposal; do not run it without a new explicit allocation.

Review focus:
- Waiting windows do not steal focus or share the previous application's input queue.
- Only the own button triggers handoff; an unready/held-key/timeout path cannot reach product startup.
- Parent subclass callback lifetime/restoration and button cleanup remain correct on success and failure.
- Runtime proof expiry is unchanged even while waiting for the operator.
- No test weakens fixture content/selection, target identity, current model, mechanical/factual gates or failure history.
- Offline native mocks are not live proof of mouse click handling or Windows focus permission.

Primary API references:
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-attachthreadinput
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow
- https://learn.microsoft.com/en-us/windows/win32/winmsg/extended-window-styles
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/ne-winuser-input_message_origin_id
