# Preparation r4 — fix round3/5

READY_FOR_INDEPENDENT_REREVIEW; actual_release=false. This package repairs only the two residual P1 findings in review-preparation-3: QUALITY2/B1 absent retained base-parent descendants, and SPEC3/B2 negative empty-set authority plus pre-validation evidence retention. The verified Unicode transport and positive consistency logic are unchanged. Original103 test purposes remain, plus10 precise residual regressions.

## Residual corrections

Owned discovery no longer skips retained parents absent from the current snapshot. It scans their possible children using the retained creation lower bound. A child predating that retained parent is impossible association and excluded; any later possible child, with no proven exit upper bound, is conservatively ambiguous and forces cleanup/overall FAIL. Evidence records exact unknown identity, parent, parent-presence state, creation bound and authority=none. Parent-number association never adds an unknown identity to the termination set. The regression invokes actual Owned.cleanup with both verified launcher/base absent and an unknown surviving child; outcome FAIL, no unknown or other terminate calls, complete ambiguity packet retained. The older-than-parent case remains PASS with zero termination authority.

Case.negative authorizes exactly zero output files. It durably saves initial baseline windows and initial inventory BEFORE asserting emptiness; unexpected unchanged files cannot become an authorized baseline. Each scenario persists reset/change commands, actual capture, changed window/range, actual foreground, refusal or unexpected error, send callback events, post-scenario windows, and full output inventory path/raw bytes/hash before validating those observations. Capture/refusal/window/inventory/release failures are explicitly recorded; unobserved later stages carry a reason. The before-send callback persists its event synchronously. Captures are released through finally, with release result/error retained. No conflicting observation is deleted, rewritten or inferred to represent real mutation.

negative-observations.json retains the complete initial and per-scenario packet, including transient observed output that may disappear before pre-cleanup. A failed initial file check stops before provider construction. Negative-evidence.json is produced only for both successful refusal/no-send/unchanged-text/empty-file scenarios; accepted_effects authorizes empty outputs and the observed final window state. Existing final consistency and pre-cleanup failure handling remain.

## Protocol and unchanged boundaries

Only required protocol revision: canonical preparation review is R/review-preparation-4/review.md. All other schema2 root authority/ledger/native-preflight/approval paths, short expiry/source/model, ordered case sequence/six positive CLI cap, predecessor review and existing product budgets remain as recorded in immutable P3/P2 documentation. Root alone issues real authority; this package creates none.

P1/P2/P3 all bytes are preserved. C HEAD244d2120abcd6b8d7744f74a05bd22de46a2d3a5/source9, frozen21/helper/fixture/query/SDK/defaults/8B/protected5 remain unchanged. No source10, product82/research293 rerun, model/native/production/external request, actual UI/window/audio, dependency/queue/git change or agent.

## Current review artifacts and verification

controller.py; test_controller.py; unchanged run_checks.py/headless_owned.py plus revision-local headless_proof.py; inputs.json; README.md. p3-to-r4.diff is the exact full P3→P4 controller diff; full-new.diff contains all new source/test/driver/docs. manifest.json binds final bytes, findings/brief inputs, tests, genuine headless and preservation evidence.

Actual focused command:

```powershell
& H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8 H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e03-resume-20261102/preparation-r4/run_checks.py final
```

113 passed in1.61s, exit0, zero socket connections. final.log/final.xml/final-receipt.json preserve output, JUnit, actual driver_argv and equivalent pytest/API args, owned TEMP/TMP/TMPDIR/OPENJARVIS_HOME/HF/XDG/offline/PYTHONPATH environment and imports. The initial original103 checks also passed and remain in initial.log/XML/receipt. No failed run occurred during this round; earlier P1/P2/P3 failures remain intact. New tests reproduce the sealed absent-parent cleanup decision, preexisting negative files and transient post-scenario files using synthetic owned inputs only; they also preserve failed capture/refusal/send/window/inventory observations and prove unchanged-empty PASS. No real orphan or UI mutation is claimed from synthetic data.

Actual harmless headless command:

```powershell
& H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8 H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e03-resume-20261102/preparation-r4/headless_proof.py
```

Two cases passed, exit0, exact original Chinese E03 and multiline E01 request+facts as inert --query args to prep-owned Python/listener. headless-discovery-proof.json binds final controller SHA8b8fb6fdf4868b3bb8cea61daaf402e5336f86167d0be84e04c455586d98706f. e03-query-final and e01-query-final retain scoped raw/decoded lossless commandlines, exact argv, listener/launcher/basechild creation/exe/parent/case args, pre-cleanup evidence, absent Python/conhost identities and closed ports; protected5 unchanged. Actual revised Owned flow was used. No live unseen orphan is manufactured; existing actual/simulated distinction persists.

No controller changes follow these final tests/proofs. Remaining limits are unchanged: semantic/no-additions acceptance stays independent; actual product/UI/model acceptance unperformed; interrupted native starts remain null/unknown under the accepted ruling. Same reviewer must independently verify the two residuals and new diff. actual_release=false.
