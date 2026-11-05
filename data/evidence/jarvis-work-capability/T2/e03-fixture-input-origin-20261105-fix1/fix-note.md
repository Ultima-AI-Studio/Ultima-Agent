# ORIGIN-PREFIX-01: bounded correction within the same independent review

This is an offline correction of the one P2 finding returned by the user-authorized
reviewer `/root/review_fixture_origin_preparation`. No second reviewer, new work
item, live case, model call or execution authority is created. Original manifest
90926b30faaed229eee1e8b206b506ac53a39fa7fe9b0a17a8bb2d751717515b and its
NEEDS_FIXES result remain intact in the sibling preparation folder.

The original validator accepted three inconsistent traces: hiding a recorded
parent's ancestor; describing the same unlogged ancestor with different message
identities; and describing an unlogged ancestor with incompatible prefixes in
two descendant records. The new negative tests first reproduced these failures.

The fix assigns each observed or referenced entry ID one canonical description:
message ID, HWND, receiving thread and the full ancestor prefix. Every mention
of that entry must agree. Existing identity, interval, stop and count checks
remain. The recorder, adapter and controller behavior are unchanged.

Six additional cases cover the three contradictions and three valid recorded /
unlogged nesting variants. The focused offline suite now passes 42 tests (all
36 previous cases retained). No Windows fixture or model was run. Raw RED and
GREEN logs are preserved. This is preparation, not a live fix claim.

The same reviewer should check only ORIGIN-PREFIX-01 and fix-introduced risks,
bound to this folder's manifest. The 25/32/334/41 original hash checks and the
candidate-credit correction were independently confirmed in the first review;
they remain preserved. Review does not release a runtime wrapper or execution.

Compatibility note retained from that review: current-run schema 2 intentionally
keeps the old 466-field state in an immutable snapshot. Historical one-time
source10 scripts which read removed fields must use that snapshot or migrate
before any future reuse; they have no replay authorization. No current product
or queue consumer was found, but all external consumers were not proven absent.
