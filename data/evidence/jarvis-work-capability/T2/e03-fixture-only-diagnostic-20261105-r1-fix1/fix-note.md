# Source-check entry binding repair

Finding: FIXTURE-SOURCE-ENTRY-01 (P1), initial verdict NEEDS_FIXES.
Original R1 manifest: c9fa33fa2c41ea7808b846c7f1529a5021853d1454fdcb3ac7e56709c7f7b9f4.

The copied controller.source_check delegates to the candidate guard and then
reads its historical code/inputs.json. That second dependency belongs to the
old controller package and is absent in this wrapper package. The original
success-lambda fixture hid that runtime path.

Only the two bridge source-check calls change: they directly invoke the already
copied candidate_guard.verify_current_candidate. The unchanged guard verifies
the pinned HEAD/branch, source manifest, all source/dependency/SDK inventories.
verify_package independently checks this wrapper's local sealed runtime files.
No candidate verification or runtime protection is removed.

The existing test fixture now isolates the actual controller.source_check AST
definition. Added cases reproduce its FileNotFoundError, check both bridge phases
without manufacturing legacy inputs, and ensure guard rejection prevents start.
Red: three failures. Green: 90 focused cases passed. The actual standalone guard
passed a read-only current-candidate check; 11 Python files parsed successfully.

All 30 originally sealed files were copied before editing. delta-ledger.json
lists which bytes changed and which were preserved. Copied historical logs and
plan describe their original snapshots; new fix receipts are distinct files.
The R1 directory, manifest and NEEDS_FIXES are unchanged. No real fixture was
started, no live slot consumed, and no model, product or audio action performed.

The user's existing one-review/one-diagnostic authorization applies conditionally
to this same-finding closure. Same reviewer PASS and fresh WIP/protection checks
are still required before Root creates a short-lived authority for this fix1
manifest. No second live allocation is created by this repair.
