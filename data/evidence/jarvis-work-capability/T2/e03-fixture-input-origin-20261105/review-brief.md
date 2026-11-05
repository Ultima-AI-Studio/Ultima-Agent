# Read-only independent review request (not dispatched)

Original work order: wo-ultimaagent-20261101-0021. Current candidate:
7975e477665c02820fa235b73d203718bd33b2c9. Only current 8B; T2 NOT_PASSED.

Review the files pinned by preparation-manifest.json, the adapter/controller
diffs against R31 and the evidence-credit correction. Do not modify product,
preparation or source evidence. Do not start a window, subprocess, microphone,
model, test suite or live case. Do not issue authority or reinterpret a prepared
copy as a released controller. This request is prepared, not authorized/dispatched.

Check these concrete risks:

- Observation order precedes the legacy readback and original WndProc; nested
  and unlogged parent messages can be reconstructed without actor overclaims.
- Original arguments, return values, errors and fixture cleanup are preserved.
- Recorder failure, incomplete sidecar and mismatched legacy counts cannot pass.
- No message payload, typed content or unrelated window is captured.
- Win32 metadata limits, live API uncertainty and observer timing effects are
  explicitly retained; fake-interface tests are not presented as live proof.
- The source10 PASS cannot be transferred to current source12. Recompute the
  reported candidate-bound counts from the pinned original receipts; keep all
  historical passes/failures under their original candidate.
- No changed candidate source, released case authority, budget extension,
  inference, audio action or acceptance credit is hidden in this preparation.

Return PASS or NEEDS_FIXES with concrete file/line findings and exact reviewed
manifest SHA-256. PASS would cover offline code/evidence preparation only.
Any future fixture-only runtime wrapper needs its own review and explicit
allocation before a live diagnostic. The original E03 three rounds + negative,
same-candidate E01, then E02 order remains required.
