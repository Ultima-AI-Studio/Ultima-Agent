# Preparation r2 — fix round 1/5

Status: READY_FOR_INDEPENDENT_REREVIEW; actual_release=false. This is an evidence-controller correction, not product acceptance. All P1 bytes remain preserved. Frozen product HEAD/source21/helper/fixtures, model policy, SDK and budgets remain unchanged. E02/source10/later stages remain closed. No actual authority or R/actual case directory was created.

The binding review is ../review-preparation-1/review.md, SHA256 aa6aef1a0e20f6b9d1c3b25678d761e1babea8a12a5b57e9291f0f36726d36cc. All seven groups and subpoints are addressed, subject to the same reviewer's independent rerun/readback.

## Files and reuse

controller.py is the only revised future case controller. It imports immutable P1 public read-only/process primitives after checking P1 adapter SHA; original product helper launch/fixture/observe/CLI are reused. P1 code is never edited. Original E03 query, E01 fixture facts, real SDK product path, one work CLI per positive and original negative provider semantics remain. No arbitrary exec/HTTP payload rewrite/private SDK mutation/new model answer or dependency.

p1-to-r2.diff is the exact complete P1 adapter-to-r2-controller diff. full-new.diff contains complete new review-source files. inputs.json binds original source/runtime snapshots, full review, ruling and fix brief. manifest.json binds current controller/tests/drivers/docs/input hashes plus tests/proofs/diffs. preservation-after.json compares every original P1 file byte hash and all 21 original source hashes.

## Seven finding repairs

1. SPEC1: Canonical root-issued schema2 authority binds current package manifest, independent approval/review, ledger, source21 and native metadata. Root proof age <=60s; issued_at <= now < expires_at and admission window <=120s. Authority is rechecked before fixture and after native/listener dispatch checks immediately before the positive CLI. Initial live GET-only native version/tags/local-manifest/source/protected identity proof precedes all fixture creation, activation and observation, including negatives. Policy-dependent isolated health is correctly later, with exact listener ownership before trust and CLI. Native identity is checked again after the request; admission expiry never rewrites the admitted request's existing lifetime.
2. SPEC2: Every entered case finally attempts raw CLI parse/product preservation, completed inference extraction, fixed-root bounded file inventory with byte hex/hash, and still-live approved window readback before stopfile or process termination. Missing/invalid evidence is explicitly unknown with reason. Product-result.json preserves actual product status; terminal.json reports harness/cleanup failure separately. Client timeout/nonzero/missing inference/invalid JSON/readback errors cannot become terminal success. Actual native starts and incomplete generation remain unknown/null; shared Ollama is never stopped.
3. SPEC3: Mechanical validator binds current run/task/artifact/write/replace call IDs; SDK starts/ends/results; baseline source hash, exact selection and capture ID/time; real completed write and replace ledger evidence; one mutation intent/send; expected output set; actual final window identity/text/caret; unselected text; unrelated owned window and output inventory; service/external hash and exact companion bytes under existing CRLF/LF rule only. Synthetic partial-selection or missing-write packets fail. Negative group records approved capture, actual owned foreground and actual changed range, refusal before send, all owned texts/files unchanged and zero sends. Semantic/no-additions review stays independent.
4. SPEC4: OS Get-NetTCPConnection listener PID must resolve to exact identity-proven owned server interpreter/ancestry/full case argv/runtime/output root. This occurs before health and immediately before CLI. Port collision or matching foreign health body cannot admit a case.
5. QUALITY1: Server task_id is canonical lowercase UUID4 before any path composition. Lexical fixed output/task containment rejects outside inputs before even lstat; reparse/ADS/canonical checks precede reads. File inventory walks only the fixed owned output root without following links. Tests explicitly forbid outside inspection/read.
6. QUALITY2: Descendant discovery retains identities beyond launcher exit, using retained launcher handle creation/exit interval, actual exe and exact argv/role/case root. Parent PID alone never grants termination authority. Unknown/ambiguous discovery, cleanup failure, open port, or source/protected/model boundary failure produces terminal overall FAIL/nonzero after cleanup. Exact Windows System32 conhost children are observation-only; no termination authority is granted, and disappearance after owned Python teardown is mandatory. This exception follows root's explicit fix-round ruling. Real proof uses Owned.launch/discover/assert_listener/cleanup, not child-PID-file shortcuts or a separate termination routine.
7. QUALITY3: CLI accepts only --case; authority/ledger/preflight/approval/review locations are canonical and cannot be caller-selected. Exact ordered preconsumption and exact sibling set are required. Prior product success is insufficient: predecessor terminal overall/mechanical/cleanup/boundaries plus hash-bound independent facts/mechanical/target/file/cleanup/boundary review must PASS. Current manifest files and loaded runner hash are verified. Root alone writes real authority/ledger.

## Canonical root protocol — no authority included

Root-controlled paths:

* R/controller-authority/<case>.json
* R/controller-ledger.json
* R/controller-native-preflight/<case>.json
* R/controller-preparation-approval.json
* R/review-preparation-2/review.md
* R/actual/<case>/{terminal.json,independent-review.json}

Fixed order: e03-round1, e03-round2, e03-round3, e03-negative, e01-round1, e01-round2, e01-round3. Six positive CLI invocations total, zero negative CLI/inferences, no loop/retry. Root preconsumes one case before issuing its authority. Existing/failed case names cannot be reused, and no unknown sibling is allowed.

Ledger schema2: {"schema":2,"consumed":["e03-round1"],"released_case":"e03-round1"}.
Approval schema2: schema, overall=PASS, reviewer=root-independent, preparation_manifest_sha256, review_sha256 (canonical review file's raw SHA256).
Preflight: recorded_at ISO UTC, source21_sha256 (raw frozen snapshot file hash), head, model, digest, version (GET JSON object), tags_sha256 (SHA256 of UTF8 json.dumps(tags,sort_keys=True) with default separators), manifest_sha256. It binds exact current version/tags/local manifest and is <=60s old at admission/dispatch. Root alone prepares the real preflight.
Authority schema2: schema=2, issuer=root, case, folder (exact Windows str(Path) form), issued_at, expires_at (<=120s apart), model, digest, preparation_manifest_sha256, approval_sha256, ledger_sha256 (raw canonical ledger file hash), native_preflight_sha256, prior_reviews. Each ordered predecessor review entry has case, terminal_sha256 and review_sha256. Independent-review.json has reviewer=root-independent, terminal_sha256, and facts/mechanical/target/file/cleanup/boundaries all PASS. Exact JSON schemas are enforced by required fields and canonical paths; additional unused fields do not grant capabilities.

Root invocation after independent preparation approval and fresh admission:

```powershell
& H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8 H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e03-resume-20261102/preparation-r2/controller.py --case e03-round1
```

The authority expiry admits effects/dispatch only. Product CLI timeout300, SDK HTTP timeout1800, maxturn10 and normal work allowance2048 remain untouched; controller CLI wait315. Source constructor proof plus actual serving PID/health establishes the existing config path. No 260-second research deadline is invented for E01/E03.

## Verification and preserved failures

80 focused checks pass, covering all original 29 purposes plus seven-group regressions. run_checks.py runs test_controller.py with owned environment/basetemp/JUnit and production/external socket refusal. The unchanged product82 suite was already independently reviewed and was not rerun. adapter-receipt.json records actual driver argv plus equivalent pytest argv/env, exit, imports and zero socket connections.

headless-discovery-proof.json records two final real local-only cases: normal redirector/basechild discovery with OS listener proof, and identity retention after actual launcher exit; both use controller's actual Owned path and mandatory cleanup, all Python/conhost identities absent, port closed, protected5 unchanged. The native Windows redirector also exits its child when forcibly terminated, so no live unseen orphan is claimed. A deterministic exited-launcher/live-child snapshot test covers that unavailable branch, including creation-order/argv/exe/stale-parent rejection.

Preserved earlier failures:

* normal-discovery and normal-discovery-attempt2 retain FAIL cleanup packets: real CREATE_NO_WINDOW launcher also owns conhost.exe, initially classified ambiguous. Both Python identities and port were cleaned. Root then allowed exact System32 conhost as observation-only with mandatory disappearance, never kill authority.
* normal-discovery-attempt3 succeeded; exited-launcher-discovery-attempt3 retains the failed headless driver assumption that a live child would survive launcher termination. Actual cleanup PASS/closed port proves no residue; no false orphan claim.
* attempt4 and final folders retain successful corrected lifecycle proof. Final proof binds current controller SHA.
* During focused-test development an aliasing fixture issue and a fake-effects mock missing its persisted evidence file caused failures; corrected mock data and controller's explicit effects persistence were verified by the final suite. P1 evidence was untouched throughout.

Remaining limits: interrupted native-start counts stay null as accepted by root/reviewer; factual meaning/no-additions acceptance remains independent; live product/UI/model behavior remains untested here. All real execution still requires the original reviewer's scoped re-review and root-owned fresh admission. actual_release=false.
