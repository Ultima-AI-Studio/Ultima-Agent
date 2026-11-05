# Proposed independent package review and single fixture diagnostic

This review has not been authorized or dispatched. The previous reviewer scope
covered the input-origin patch and its finding closure, not this enclosing runner.
No execution authority or actual case exists in this preparation.

Review `manifest.json`, `plan.md`, `README.md`, the two new implementation modules
and their tests. Verify all package hashes and the copied dependency provenance.
Focus on release-before-import ordering, the exact fixture/observer call graph,
exclusive consumption, cleanup on failure, metadata-only summaries, protected
identity/parent/command checks and the explicit time-limit semantics. The full
controller is an unchanged dependency: this wrapper must not invoke its product
execution, native/model preflight, effects, negative or command methods.

Do not run code/tests, create windows, call models/audio/network, modify source
or evidence, issue a release or spawn reviewers. Read-only shell/hash/AST tools
are allowed. Return findings and a manifest-bound PASS or NEEDS_FIXES to Root;
Root records the receipt with clear attribution. Reuse already established
input-origin code review; do not reopen it unless this wrapper changes its use.

If the user explicitly approves review plus one diagnostic, only PASS may be
followed by a fresh Root authority for `fixture-origin-01`. The user will see two
temporary owned test windows. There is no product/model call and no acceptance
credit. One failed or completed diagnostic ends this allocation; it does not
permit a second run or release E03/E01/E02.

Unverified by offline tests: actual Windows focus/IME timing, native API behavior,
process races and cleanup under real scheduling, and whether the original text
change reproduces. These require the authorized diagnostic; do not claim them
from mocks or logs of old cases.
