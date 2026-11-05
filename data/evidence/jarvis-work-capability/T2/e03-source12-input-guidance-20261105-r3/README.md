# E03 round1 persistent input guidance - preparation only

Original WO wo-ultimaagent-20261101-0021; unchanged candidate7975e477665c02820fa235b73d203718bd33b2c9; current qwen3-8b-uncensored only. Full delivery goal remains active. Parent manual Start case failed before CLI when secondary caret moved; user confirmed clicking elsewhere. Parent case and result-review allocations are consumed, and no new actual/release/authority is created here.

This delta changes two runtime files and one existing test mock. Start now says “开始测试（结束前请勿点击、输入或切换窗口）”. Each existing window has a STATIC child reminder “测试期间请勿点击、输入或切换窗口，等待结束通知。” at x10,y238,width660,height28, below the unchanged Edit y10..190 and Start y200..228 regions. Parent height is320 instead of280; position, width, titles, targets and original text stay fixed. Child ID1002 differs from Start1001 and Edit0. The label has WS_CHILD|WS_VISIBLE|SS_CENTER, no tab-stop or notification style, and lives until its parent is destroyed. It neither captures input nor becomes a policy target.

The persistent label does not overlap Start. CreateWindowExW places new children at the bottom of sibling Z-order; relying on a later button to cover an earlier label would be incorrect. Separate rows avoid this dependency. Native rendering/DPI visibility has not been live-verified in this revision.

No focus/admission/audit/selection/cleanup behavior changed. No input hook, input disabling, synthetic click, hidden target, caret reset, gate relaxation or model switch. Keep15s Start wait,20s fixture startup,60s proof freshness,120s admission, CLI/SDK/controller300/1800/315s. Failures stop without retry, and mechanical success alone still requires independent facts review.

The retained suite passed124 tests in6.91s after the final layout edit. No new tests merely mirror captions; the existing native wiring mock now distinguishes top-level STATIC windows from child STATIC labels. Tests open no windows or real input devices and make no model/audio calls. Static AST/hash/source checks and provenance are recorded separately. Old124-test evidence is historical; fresh verification/guidance-final-tests.log is this revision.

Prior automatic approval rejected an import-probe command and a push combination. Neither is retried. Parent formal runtime evidence is historical and cannot grant this package acceptance. Remote synchronization remains pending; local preparation review and a new explicit user allocation are prerequisites to any next case.

Primary references: [CreateWindowExW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createwindowexw), [Static control styles](https://learn.microsoft.com/en-us/windows/win32/controls/static-control-styles).
