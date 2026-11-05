# Fixture-only diagnostic preparation (not released)

Original work order: wo-ultimaagent-20261101-0021. The goal remains full E01–E08
delivery. Current candidate 7975e477665c02820fa235b73d203718bd33b2c9 and current
community 8B remain unchanged. E03 has zero verified current-candidate positive
or negative passes. This diagnostic is not an acceptance case.

The wrapper is now concrete: one fixture subprocess and the original baseline
observer only, using the reviewed owned-process discovery and cleanup. It checks
a new package review and short-lived, single-use authority before loading native
runtime code. Missing or consumed release, changed bytes, wrong interpreter,
candidate drift or protected-process drift stop it. No R31 authority is reusable.

The original initialization, foreground/selection activation, initial readback
and baseline observer sequence are retained. No text reset, input injection,
IME change, product server, work CLI or model call is present in the bridge.
The 30-second watchdog only requests stop through this fixture's marker. Native
readiness and observer timeouts remain 20/15 seconds. Diagnostic COMPLETE also
requires successful cleanup, audit and boundaries within 60 seconds; cleanup
continues if late. This is not a hard process-kill deadline, and original product
acceptance limits remain unchanged.

`COMPLETE` means complete diagnostic evidence. `TEXT_CHANGED` / `UNCHANGED`
describe the observed fixture only. Incomplete audit, cleanup or boundaries yield
`INCOMPLETE / UNKNOWN`; measured text summaries remain available separately.
An unchanged fixture does not prove the intermittent problem fixed. All results
have `product_acceptance=NOT_EVALUATED`, acceptance_credit=false and no retry.
The wrapper dispatches no model requests; total shared-daemon activity is not
measured and actual_native_start_count remains null.

87 focused offline tests passed: the retained 42 input-origin tests plus 45
wrapper/bridge cases. They used injected backends/API functions and temporary
test folders, not live windows, product/model calls or real allocations.
11 Python files passed AST parsing. Eight copied dependencies, including the
seven-identity baseline, and 41 candidate source hashes were read back.

`actual/` and `release/` do not exist in this preparation. Both are Git-ignored.
Raw observer text, if a future authorized diagnostic runs, remains in its local
actual folder. Public summaries contain only identity/selection, hashes, lengths,
booleans and message-origin metadata. Do not commit raw actual-case data.

Read-only package verification after sealing:

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -B 'H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e03-fixture-only-diagnostic-20261105-r1\code\fixture_diagnostic.py' --verify
```

After a separately authorized independent package review passes, Root may issue
ONE new fixture-only authority, valid for at most ten minutes, under `release/`.
Its exact schema is enforced by `validate_authority`; it binds this manifest,
the copied independent review bytes, candidate, case, cap and zero model/product/
audio requests. The controller writes the user's exact approval and request ID
in `user_authorization`. No authority is supplied here. Root must recheck current
WIP and protected identities, announce the two temporary test windows, and keep
the user's typing/IME activity unconfirmed unless they explicitly state it.

The authorized command would be the same invocation with `--run`. Do not run it
before review and new allocation. It never issues its own release or retries a
consumed folder. A crash or failure after claim leaves the slot consumed.

Next use the trace to resolve or narrow the fixture blocker, then start the full
current-candidate E03 sequence from round1, followed by same-candidate E01 and E02.
T2, T3–T5 and Owner gates remain unchanged and unpassed.
