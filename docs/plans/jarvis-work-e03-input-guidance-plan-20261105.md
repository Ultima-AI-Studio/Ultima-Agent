# E03 persistent input guidance preparation

Original work order wo-ultimaagent-20261101-0021. Full E01-E08 / T2-T5 / Owner goal remains active. Only current community 8B. Product candidate 7975e477665c02820fa235b73d203718bd33b2c9 and every original gate remain.

Previous goal turn: progress. The authorized manual Start case ran once, reached correct primary focus/selection, then failed before CLI because the secondary caret changed from [0,0] to [39,39]. Both texts stayed unchanged. A readonly independent result review completed; the user confirmed clicking another location/window after Start. The case and result-review allocations are consumed. Exact attribution of every native message remains unproven.

Problem addressed: the transient Start button says only to pause keyboard input. After Start it disappears, leaving no persistent in-window reminder to pause mouse clicks and window switches. Clarify this operator handoff before another controlled E03 case.

Small change, isolated wrapper only:
1. Expand the Start caption to “开始测试（结束前请勿点击、输入或切换窗口）”.
2. Add a visible, noninteractive STATIC guidance child below both the unchanged Edit and Start regions in each existing window: “测试期间请勿点击、输入或切换窗口，等待结束通知。”. Keep Start at y=200..228; put guidance at y=238..266 with unique child ID1002; increase the parent height from280 to320 to leave room. Guidance remains present before and after Start. Parent destruction handles child lifetime.
3. Keep both window titles, screen positions, width, Edit/Start regions, text, selection rules, target policy, actual Start/focus code, receipt validation, audit, native input behavior, deadline and cleanup logic unchanged. Only parent height makes room for the reminder. Do not disable mouse/keyboard, install input hooks, hide a target, reset a changed caret, or relax secondary-selection checks.
4. Retain the existing 124 offline regressions. Adjust the existing fake window factory to distinguish a top-level STATIC window from a child STATIC label, so it keeps checking the two nonactivating target windows. This reversible presentation change needs no new test that merely asserts the caption; use existing behavior regressions plus static review of layout/style/lifetime.
5. Fresh package contains the same runtime dependencies with exact provenance. Preserve parent manifest, preparation review, actual failure and result review, and the new operator confirmation as history. Never copy live release/actual allocation into the new package.
6. Seal and independently review the full small delta. No actual UI/model/audio or runtime import probe during preparation. Previous rejected push/import-probe actions are not retried through another route.

Acceptance for this preparation: 124 retained offline tests pass, all runtime modules parse, source/SDK/dependency hashes match, precise delta is reviewed, project/mirror local checkpoint recorded. Remote sync stays pending the existing automatic approval block. None of this grants E03 acceptance or a new case.

Next real proposal: one current-8B E03 round1 plus one independent result review, with operator clicking Start then leaving mouse and keyboard idle until the end notification. Original 15s Start wait, 20s fixture startup, 60s proof freshness, 120s admission and CLI/SDK/controller 300/1800/315s limits remain. Any failure stops; no retry. A new explicit allocation is required after concrete preparation.

Tasks:
- [x] Prepare the sibling package, preserve parent evidence and record exact change scope.
- [x] Add persistent reminders and update the existing mock's child-window distinction.
- [x] Run the retained offline suite and static source/package checks.
- [x] Seal and perform one fresh readonly independent preparation review.
- [x] Record current state, mirror docs, commit/tag locally and accurately record pending remote sync; prepare the next single-case proposal.

Review focus:
- Reminder is persistent after Start and is outside the unchanged Edit region.
- Reminder is a noninteractive child, does not receive tab focus or add a policy target, and dies with its existing parent.
- New text unambiguously covers mouse clicks, keyboard input and window switching until end notification.
- Runtime behavior, frozen secondary selection and all original gates/consumed allocations remain unchanged.
- Native layout is not claimed as live-verified by mocks or static analysis.

Layout ruling before sealing: do not overlap reminder and Start. Microsoft CreateWindowExW documents child creation at the bottom of sibling Z-order, so assuming a later button overlays an earlier label is unsafe. Separate vertical regions avoid that dependency; the unique label ID also follows the child-control identity rule. References: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createwindowexw and https://learn.microsoft.com/en-us/windows/win32/controls/static-control-styles .

Final preparation review PASS, no findings; manifest 0195699e7fe521d9aaa5da8ec01bedb53533cdc3a2364ea42496f142f6d07352. Reviewer receipt SHA-256 d9cff9cdfddebadcde427de48374554b7a29413c1107878f4d2bed604186d013. No new actual allocation. Local checkpoint and pending remote sync are recorded separately; sealed package plan remains the pre-review snapshot.
