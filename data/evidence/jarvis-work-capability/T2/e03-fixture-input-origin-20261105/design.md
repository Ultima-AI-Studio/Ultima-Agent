# E03 input-origin diagnostic preparation

Original work order: wo-ultimaagent-20261101-0021; T2 remains NOT_PASSED.
This is offline diagnostic preparation under the continuing work-order objective.
It issues no product-case authority and does not reuse the consumed R31 allocation.

## Verified problem

R31 initial fixture readback is 41 UTF-16 units. Its frozen baseline is empty.
The audited EM_REPLACESEL record reports a 41-to-0 change, with 14 input/IME
records also present; isolated server/CLI startup was never reached. The current
audit labels message IDs as programmatic/input, but those labels are not actor
identities. Its received_at_utc and qpc_ns are sampled after the original WndProc
returns; nested dispatch can therefore be misread as arrival order. The actor
and the causal input remain unproven. R31's historical evidence is immutable.

## Bounded change

Copy the reviewed fixture adapter and controller into this independent preparation
folder. These are reference copies for offline patch review, not an executable
release package; no controller authority, release or runner is issued here.
Add a sidecar recorder to observe message entry before text readback/dispatch,
and exit after dispatch. Record parent entry IDs, ancestor message IDs and
entry/exit monotonic times so nested messages remain distinguishable. Keep the
legacy audit and the original WndProc arguments, return value and delivery
unchanged. Do not consume, inject, block, repair or replay input.

Use the existing Win32 GetCurrentInputMessageSource and InSendMessageEx APIs.
The sidecar retains raw enum/flag values and conservative labels. Origin 1 means
hardware OR a UIAccess application; it does not prove a human typed anything.
Origin 2 means SendInput injection by an application without UIAccess. Origin 4
means system input. Unavailable/failed observations remain unknown. These APIs
do not identify a sending process. No key values, wParam/lParam, composition
text, clipboard data, global hooks, raw text or background-window content is
recorded. The observers apply only to the two owned fixture Edit controls.

The controller requires a complete sidecar, two owned-control probes, bounded
records and matching per-control/message counts with the legacy audit. Missing
records, observation failures, invalid nesting or an incomplete stop fail the
audit. A sidecar write failure must not suppress original dispatch or skip fixture
cleanup. Live Windows API behavior remains unverified.

## Candidate-credit correction

The source12/recovery5 round1 terminal and independent review are byte-identical
copies from source10/recovery2. The original round1 authority binds candidate
118ba152b007c30d358c8bc44c51aabe8ae820f0, not the current
7975e477665c02820fa235b73d203718bd33b2c9. Preserve that historical PASS under
its original candidate; it supplies no current-candidate acceptance credit.
The separate 2026-11-02 three-round gate also binds older candidates
244d2120abcd6b8d7744f74a05bd22de46a2d3a5 / product source
7c201a3aa00c4cfccb170f6ee5102a282174f329 and must remain historical.

The fresh readback enumerates five distinct source12 same-candidate terminal
receipts, one CLI submission, zero reviewed positive cases and zero negative
passes. All five terminals failed. This enumeration is scoped to top-level
source12 actual-case folders, not copied history. Future acceptance must start
at current-candidate E03 round1 and then satisfy three consecutive positive
rounds plus the original negative gate, followed by same-candidate E01 and E02.
The R31 diagnostic has no acceptance credit even if its fixture had succeeded.

## Offline verification

Test source capture ordering, nested entry/exit relationships, unlogged parent
messages, loss/failure handling, Win32 enum conversion and payload exclusion.
Use deterministic injected API functions; do not create a window, run a product
case, call Ollama, touch microphone/audio, or change protected processes. Keep
legacy audit tests. Save red/green output and source hashes. Code readiness is
not evidence of live Windows behavior or product acceptance.

Completed offline verification: 36 focused tests passed, including AST-isolated
invocation of the actual controller audit validator. The full historical R31
suite was not rerun. Original R31 sealed artifacts (334) and candidate source
files (41) were read back with matching hashes. User input source is UNCONFIRMED:
the user could not confirm whether typing during 14:54:36-38 Beijing time.

## Remaining execution gate

After this preparation, independent review must cover the adapter, sidecar and
controller completeness check. A separately authorized single fixture-only
diagnostic can then capture missing provenance without starting the isolated
product server, work CLI or a model request. It must retain initialization,
activation and the original baseline read sequence; do not reset text or change
IME settings. Its runtime wrapper and exact write/process bounds require review
before execution. It is not supplied or released by this offline patch package.
The original E03/E01/E02 acceptance requirements, 60-second
gate and Owner gate remain unchanged. No automatic retry or baseline reset is
introduced. R31's case cap is consumed and its retry_authorized remains false.

## Primary references

- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getcurrentinputmessagesource
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/ne-winuser-input_message_origin_id
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-insendmessageex
- https://learn.microsoft.com/en-us/windows/win32/controls/em-replacesel

Read on 2026-11-05. These explain API limits, not the initiator of R31's edit.
