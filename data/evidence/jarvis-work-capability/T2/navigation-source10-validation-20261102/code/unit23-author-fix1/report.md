# Source10 combined U2 + U3 implementation report

DONE_WITH_CONCERNS — code-only integration complete; independent root review remains pending. Original E02/T2 is NOT_PASSED and T3 remains closed. No model/native actual, production, harness, UI, network, audio or release allocation was consumed. Test transport is scripted HTTPX; the original SSE regression keeps its ephemeral loopback purpose.

BASE `494e544788c287defbf1208967444e733df5501a` → HEAD `0e3e0edeb6d57d7d792dd5f1e40ecad58ee60642` on `codex/jarvis-work-navigation-v3-source10`. One exact commit: `feat: integrate bounded native research navigation`. No push/tag. Normal index empty and tracked worktree clean after commit; pre-existing unrelated untracked files were never staged.

The combined root brief 16ebc829 superseded the U2-only loop prohibition. Root availability ruling 74b5c652 authorized the minimal U1 availability correction and test. Root separately authorized migration of only the two named research positives in test_work_context.py plus their scoped helper. No other context tests were edited.

## Result and evidence

- Current full command: `H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8 H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/run_code_tests_v2.py unit23-delivery-covering` with the explicit nine-file pytest argv recorded below. **418 tests, 0 failures, 0 errors, 0 skips, 54.18 s.**
- Current safe compatibility copy: **8 tests, 0 failures, 0 errors, 0 skips**. Its original preload/exclusion/import assertions remain byte-identical; only the evidence root changed. Original script SHA256 `b165772a736de13006064a25b3d26db6aaa58afdcb38d8025fe91aa49bacc5c2`, safe copy `c005bdbe4269d54e8dd4aba13c28aa3878b6e38f825adba8513c9191d04db17f`.
- Full receipt: [unit23-delivery-covering](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-delivery-covering/receipt.json) SHA256 `21757553d052ff4f85ead7964fc5620ca2a1d7ccb37d4fcf0a37ef83843daead`.
- Compatibility receipt: [unit23-delivery-compat](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-delivery-compat/receipt.json) SHA256 `af6f8f915a3d08e8ae046858ec86ed552ede4c907bb01bd357d37d86667c3bab`.
- [Independent external readback](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-delivery-readback/external-verification.json): separate stdlib-only process, no product modules imported; four fixture cases all match exact GET hashes, identities, original line coordinates, issued handles, native entities, packet manifests and literal expected Markdown bytes. It reopens each actual research.md. Largest strict messages+schema entity: 9820 bytes; largest prepared POST: 9892 bytes.
- [Exact staged paths/bytes](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-delivery-readback/staged-check.json) and [post-commit readback](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-delivery-readback/post-commit.json) prove all ten committed files equal the final tested bytes. Staged and unstaged diff-checks passed. Mixed baseline endings were restored on unchanged tool/service lines; no whitespace-only normalization is claimed as a feature.
- [SDK source snapshot](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-delivery-readback/sdk-sources.json): all six original pinned SDK files unchanged; 22 actually used SDK sources copied and SHA256-bound. Final loaded-path report has `unexpected={}`. Final test source inputs before/after match, and no protected input outside the ten allowed files changed.
- All original 65 research test names and all 285 original six-file JUnit identities remain present. Research contributes 178 cases. No skip/xfail or fresh v2 fallback was introduced. Counts are from the final receipts, not added historical passes.

Exact full pytest argv and isolated env are in invocation.json/receipt.json; raw stdout, stderr, JUnit and loaded paths remain in each immutable stage directory. The fixed interpreter is H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe with -B -X utf8. TEMP/TMP/TMPDIR, OPENJARVIS_HOME and model/cache directories are unique to each run; offline flags and source-path assertions are retained.

Exact final full pytest argv:

```json
[
  "H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe",
  "-B",
  "-X",
  "utf8",
  "-m",
  "pytest",
  "src/brain/tests/test_work_research.py",
  "src/brain/tests/test_work_context.py",
  "src/brain/tests/test_work_delivery.py",
  "src/brain/tests/test_agent_server_sse.py",
  "src/brain/browser/tests/test_browser_channel_s3.py",
  "src/brain/tests/test_interaction.py",
  "src/brain/tests/test_work_navigation.py",
  "src/brain/tests/test_work_navigation_sdk.py",
  "src/brain/tests/test_work_navigation_transport.py",
  "-q",
  "-p",
  "no:cacheprovider",
  "-p",
  "ultima_nav_pathcheck",
  "--basetemp=H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\unit23-delivery-covering\\temp",
  "--junitxml=H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\unit23-delivery-covering\\junit.xml"
]
```

Exact final compatibility argv:

```json
[
  "H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Scripts\\python.exe",
  "-B",
  "-X",
  "utf8",
  "H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\unit23-delivery-compat\\run_compat.py"
]
```

## Changed files

| File | Responsibility |
|---|---|
| `src/brain/agent_server.py` | Checked actual scanner/config preparation, retained SDK conversation, phase schemas, guarded bounded native leaf and owned-client cleanup. |
| `src/brain/tests/test_work_context.py` | Only two authorized research positives migrated to actual SDK navigation with raw provenance assertions in the restricted fixture ledger and public no-body assertions. |
| `src/brain/tests/test_work_navigation.py` | Deterministic entropy and rare placeholder-card regression; original nonce16 test retained. |
| `src/brain/tests/test_work_navigation_sdk.py` | Real name builder/registry/ToolExecutor worker, exact identity, read budgets, actual SDK IO, fault/race/concurrency and policy drift. |
| `src/brain/tests/test_work_navigation_transport.py` | Actual NativeReAct scripted transport, independent text/permuted/HTML/mixed oracles, raw/secured/history/template mutations, streaming/caps/first-failure packets. |
| `src/brain/tests/test_work_research.py` | All 65 names preserved; fresh success fixtures use actual guarded NativeReAct and issued page refs; raw assertions read restricted captured ledgers. |
| `src/brain/work_navigation.py` | Only remove misplaced actual-wire scan from placeholder renderability preflight; actual scan_view unchanged. |
| `src/brain/work_research.py` | Independent native runtime replay reconstruction and report/file/runtime linkage; historical v2 algorithms untouched. |
| `src/brain/work_service.py` | Mandatory trusted preparer, frozen material, safe catalogue prompt/public summaries, mandatory fresh runtime+v3 readback. |
| `src/brain/work_tools.py` | Request-local enrollment/permits, narrow inspector, ordered issuance, one real nested SDK file intent, late/timeout evidence. |

## Concrete interfaces and invariants

- `WorkService(..., research_preparer=None)` fails closed for explicit research without a callback. Startup injects `_prepare_research_navigation(collection, *, binding, ledger) -> CatalogueV3`. It acquires the existing ask lock against the original deadline, ensures the existing owner engine, calls `_checked_research_security(owner)`, freezes matching GET records from the ledger and calls U1 preparation once. No native client or metadata GET is created by preparation.
- Private trusted bridge: `ledger._prepare_navigation(binding, catalogue, collection, get_records_json, policy)` configures exactly once. `WorkCapabilities.navigation` is safe CatalogueV3; `research_json` retains the writer-only original collection; fresh `cards_json=None`. Composition has no browser/provider/replace authority. User context is deep-copied and capture frozen before collection. Public sources/available_sources/trace/tool_results are safe summaries; full GET bodies and report submissions stay in the restricted ledger/packet.
- Exact public ledger methods are `open_enrollment(binding, caller_id)`, `enroll(name, instance)`, `close_enrollment()`, `expect(seq, name, args_hash)`, `claim(seq, name, args_hash, adapter_id, *, instance)`, `confirm_end(seq, event)`, `promote_visible(generation, wire_hash)`, `freeze_for_write(generation)` and `seal(reason)`. Callback is `observe_navigation(event, *, caller_id, binding_key)` and never propagates an exception into SDK subscribers. One existing RLock owns all state.
- The actual SDK name builder constructs exactly the inspector and writer in one caller epoch; the writer captures its nested WorkWriteTool there. START has no object field. Authority comes from caller/binding/seq/args plus the worker claim of the exact enrolled object, not shared agent label native_react. SDK workers do not resolve ContextVar authority. Inspector instance contains only `_catalogue` and narrow `_read`; no raw caps, scanner, path, browser, provider or writer.
- Narrow reads count every attempt without refund, cap at six/18432 bytes, call build_page then actual scan_view before staging, and require exact successful END metadata/content before a provisional observation can participate in the next phase. No synthetic, missing, failed, late or changed history promotes. Actual PII-like final IDs still fail closed.
- `_ResearchEngineView` closes enrollment before first generation, verifies SDK max_turns >=8 without changing global defaults, retains the full actual server persona/mainbrain/skills/two-tool system, and replaces only the pinned prefix. Template f1ac2c27009f1759da22b3dfc6f301d0912ba8370f1dd3964433421910474621 / a062f71243cd4986a2f2034cf3946912196fd4f4499394815cb0d3a1c522579b checks remain explicit. Overrides/exemplars fail before POST. Every original query, assistant action, USER Observation and optional field is matched exactly.
- Phase schema starts inspect/refuse; three distinct visible card-bearing sources make writer eligible provisionally for the current sampler. The third page is promoted only after raw and secured envelopes match a fully guarded successful native turn, before worker dispatch. Further inspect on a writer-capable turn uses the 2048 budget. Writer freezes only actually issued ordered pages. ACK is final-only after independent file/report/runtime verification.
- Writer target is exactly research.md under the original request root. Resolve/render, checked_path, complete actual-policy string scan, compact <=3072-byte receipt preflight and reservation binding precede intent. Intent atomically rechecks seal/deadline and exact claimed writer/dispatch/report/file IDs; the existing real SDK FileWriteTool receives allowed_dirs=[request root] exactly once. False SDK success/wrong bytes fail. An admitted intent remains an effect after timeout/failure; no retry.
- Restricted runtime bytes are `ledger._runtime_prewrite` and `ledger._runtime_final`; pure data is `ledger.issued_snapshot`. `_runtime_packet()` links the exact U1 manifest/views with complete safe native entities, raw outer JSON, raw+secured envelopes, four separate hashes, ordered END data and transport counters. SDK floating timestamps/latencies are preserved in original JSON strings, not coerced into float-forbidden authority J. `verify_runtime_packet(..., require_ack=...)` independently rebuilds SDK system, phases, history, entity/hash/event/budget links. Fresh WorkService success unconditionally requires final runtime proof plus protocol_version=3; isolated SDK component fixtures never fabricate product success.
- `_checked_research_security` uses the existing actual configured ordered scanners and wrapper/bus/origin/credential settings. Borrow rechecks scanner identities/policy, full security-config equality, exact wrappers/client/audit/capability/rate-limiter objects. No second runtime guard or registry was installed. U1 historical replay scanner reconstruction remains its approved independent data validation.
- Failure seals once; original first failure survives secondary client/stream close errors. Exact safe timeout/failed/late SDK JSON is retained under captured policy and late adapter records are separately marked in `_late_records`. Unsafe failures retain no raw secret output. SDK timeout after intent marks the effect timed_out; pre-intent timeout gives no file effect. Only the owned leaf client closes; owner engine stays open and subscriptions are removed.

## Bounded transport

One typed native request is J-serialized once, prepared with exact bytes and identity encoding, checked, then the same prepared request is sent stream=True. Per response, one iter_raw(chunk_size=512) iterator admits only remaining prefix plus one inspected overflow sentinel. Tests deliver a real 4096-byte SyncByteStream block with 512 remaining: HTTPX download=4096, inspected=513, admitted=512, retained<=512. Header/status/encoding/Content-Length rejection consumes no application body. Last observable downloaded count is sampled once around close; missing response/counter is null, socket/TLS/peer bytes remain unknown. Partial connect/read/close charges are not refunded.

Limits: <=8 native POST starts /16 metadata GETs; POST entity <=49152 and cumulative393216 bytes; metadata admission32768/524288; chat admission65536/524288; strict secured messages+schema32768 bytes; estimator+schema+512+output<=16384; output<=256 before writer eligibility, <=2048 when writer-capable, ACK<=256. Original 260s entry deadline includes collection/lock/all turns. Prewrite send requires >55s; writer action/intent requires >=55s; prewrite read min(180,R-55), ACK min(25,R), metadata/connect/write/pool <=25 clipped to remaining. These are admission/observation bounds, not a claim of hard cancellation or peer network cap+1.

## Independent file and packet readback

| Variant | Actual artifact SHA256 | Bytes | Packet directory |
|---|---|---|---|
| text | `99c40cc2a82443f25b94d923d365b32b9f562ba53d6b07411f762faf5cf621cc` | 337 | [test_v3_native_react_observati0](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-delivery-covering/temp/test_v3_native_react_observati0) |
| permuted | `dd354073e02fae32cd56ec4a675392e44c2b093707e18c9346e809650b072163` | 337 | [test_v3_native_react_observati1](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-delivery-covering/temp/test_v3_native_react_observati1) |
| html | `3b299a15eab3e1b3cff171aa62adddb7507e5adea5f205eacc2790be7dca7fb3` | 370 | [test_v3_native_react_observati2](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-delivery-covering/temp/test_v3_native_react_observati2) |
| mixed | `ffe81b973dce3a48e12b79bfa3728d8c3d1a101a3c40889faaf67ea42fc26057` | 341 | [test_v3_native_react_observati3](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-delivery-covering/temp/test_v3_native_react_observati3) |

Each directory retains issued-snapshot.json (original synthetic GETs/projection/policy/pages), issued-views.json, runtime-replay.json, packet-manifest.json, external-readback.json and the actual research.md under its isolated request root. The external verifier uses source fixture bytes/coordinates and literal Markdown, not product renderer success, and compares complete hashes after the test process has ended. These scripted cases certify mechanical fixture linkage only.

## Negative-purpose preservation

The original 65 test names are unchanged. Historical witness/renderer tests remain explicitly pure readback; fresh writer/ref tests use actual observed v3 handles. Fresh custom-runner positive helpers invoke the real guarded NativeReAct path through scripted transport, not direct writer success. Collection/waiver/SDK GET negatives still reach their original intended gate; unknown refs/path/source/schema failures are driven after actual inspector observations. Raw-response diagnostics and file provenance assertions moved to captured restricted ledgers, with public no-body assertions added. Old two-turn native budgets/counts were updated to three inspector turns + writer + ACK. Exact unchanged history forbids guard rewrite/redaction, so the old secured-material test now asserts prewrite rejection or post-write needs_attention instead of accepting altered SDK history. Pre-intent timeout now correctly has no file effect; post-intent timeout preserves timed_out/needs_attention.

| Original function | Preserved purpose / fresh mechanism |
|---|---|
| `test_required_reads_precede_even_an_immediate_final_answer` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_actual_report_write_cites_three_of_five_fetched_sources` | Actual SDK inspector-issued v3 refs, exact writer permission/path/one intent and independent bytes; unbound calls explicitly refused. |
| `test_optional_failed_probe_has_exact_ledger_identity` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_failed_model_action_cannot_use_probe_waiver` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_bad_collection_never_reaches_model_or_file` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_real_executor_timeout_aborts_before_runner` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_report_refuses_unbound_or_forged_citations` | Actual SDK inspector-issued v3 refs, exact writer permission/path/one intent and independent bytes; unbound calls explicitly refused. |
| `test_source_candidates_are_data_and_combined_mutation_is_early_rejected` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_unbound_report_writer_fails_without_file` | Actual SDK inspector-issued v3 refs, exact writer permission/path/one intent and independent bytes; unbound calls explicitly refused. |
| `test_cli_source_urls_remain_candidate_data` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_malformed_sdk_search_records_retain_raw_and_diagnostics` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_mandatory_search_failure_cannot_be_waived` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_cross_request_catalogue_is_rejected` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_report_independent_reopen_detects_changed_bytes` | Actual SDK inspector-issued v3 refs, exact writer permission/path/one intent and independent bytes; unbound calls explicitly refused. |
| `test_native_react_uses_bound_report_with_real_sdk_collection` | Real guarded SDK conversation/transport/schema/security negative; five-turn navigation counts and exact-history refusal updated. |
| `test_preflight_budget_stops_before_starting_next_get` | Fresh real native phase/time/output/send admission or actual SDK-loop cutoff; original deadline/negative intent preserved. |
| `test_source_url_schema_never_grants_authority` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_report_nested_writer_keeps_existing_path_boundary` | Actual SDK inspector-issued v3 refs, exact writer permission/path/one intent and independent bytes; unbound calls explicitly refused. |
| `test_sdk_false_file_success_is_not_report_completion` | Actual SDK inspector-issued v3 refs, exact writer permission/path/one intent and independent bytes; unbound calls explicitly refused. |
| `test_optional_probe_does_not_waive_unexpected_adapter_error` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_native_react_first_messages_include_nested_report_schema` | Real guarded SDK conversation/transport/schema/security negative; five-turn navigation counts and exact-history refusal updated. |
| `test_source6_nested_action_and_final_only` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_source6_double_report_is_one_mutation` | Actual SDK inspector-issued v3 refs, exact writer permission/path/one intent and independent bytes; unbound calls explicitly refused. |
| `test_source6_only_bound_tool_and_frozen_capture` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_source6_admission_boundary` | Fresh real native phase/time/output/send admission or actual SDK-loop cutoff; original deadline/negative intent preserved. |
| `test_r4a_wire_scope` | Real guarded SDK conversation/transport/schema/security negative; five-turn navigation counts and exact-history refusal updated. |
| `test_r4a_bad_final_after_write` | Real guarded SDK conversation/transport/schema/security negative; five-turn navigation counts and exact-history refusal updated. |
| `test_r4a_stop_on_rejection` | Real guarded SDK conversation/transport/schema/security negative; five-turn navigation counts and exact-history refusal updated. |
| `test_r4a_unknown_dispatch` | Real guarded SDK conversation/transport/schema/security negative; five-turn navigation counts and exact-history refusal updated. |
| `test_r4b_candidate_boundaries` | Original witness/coordinate/source-provenance assertions retained; fresh artifact positives use observed page evidence and restricted readback. |
| `test_r4b_projection` | Original witness/coordinate/source-provenance assertions retained; fresh artifact positives use observed page evidence and restricted readback. |
| `test_r4b_code_witness` | Original witness/coordinate/source-provenance assertions retained; fresh artifact positives use observed page evidence and restricted readback. |
| `test_r4b_partial_write` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_r4b_late_report` | Actual SDK inspector-issued v3 refs, exact writer permission/path/one intent and independent bytes; unbound calls explicitly refused. |
| `test_r4_unresolved_backend_refuses_before_inference` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_r4_invalid_or_invisible_span` | Original witness/coordinate/source-provenance assertions retained; fresh artifact positives use observed page evidence and restricted readback. |
| `test_r4_projected_html_evidence` | Original witness/coordinate/source-provenance assertions retained; fresh artifact positives use observed page evidence and restricted readback. |
| `test_r4_limitations_are_local_claims` | Original witness/coordinate/source-provenance assertions retained; fresh artifact positives use observed page evidence and restricted readback. |
| `test_r4_max_turns_after_committed_write` | Fresh real native phase/time/output/send admission or actual SDK-loop cutoff; original deadline/negative intent preserved. |
| `test_r4_research_exception_does_not_leak_to_ordinary` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_r4_exact_named_symbol_and_explicit_failure` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_r5_method_header_is_not_a_call` | Original witness/coordinate/source-provenance assertions retained; fresh artifact positives use observed page evidence and restricted readback. |
| `test_r5_incomplete_statement` | Original witness/coordinate/source-provenance assertions retained; fresh artifact positives use observed page evidence and restricted readback. |
| `test_r5_comment_cannot_prove_call_on_different_line` | Original witness/coordinate/source-provenance assertions retained; fresh artifact positives use observed page evidence and restricted readback. |
| `test_r5_extracted_html_text_cannot_prove_a_source_statement` | Original witness/coordinate/source-provenance assertions retained; fresh artifact positives use observed page evidence and restricted readback. |
| `test_r5_complete_statement_and_raw_identity` | Original witness/coordinate/source-provenance assertions retained; fresh artifact positives use observed page evidence and restricted readback. |
| `test_r5_completed_report_includes_sdk_result_and_effect` | Actual SDK inspector-issued v3 refs, exact writer permission/path/one intent and independent bytes; unbound calls explicitly refused. |
| `test_source6_native_boundary` | Real guarded SDK conversation/transport/schema/security negative; five-turn navigation counts and exact-history refusal updated. |
| `test_source6_real_admission` | Fresh real native phase/time/output/send admission or actual SDK-loop cutoff; original deadline/negative intent preserved. |
| `test_source6_executor_denies_before_write` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_source6_secured_material` | Real guarded SDK conversation/transport/schema/security negative; five-turn navigation counts and exact-history refusal updated. |
| `test_source6_reference_membership_and_readback` | Actual SDK inspector-issued v3 refs, exact writer permission/path/one intent and independent bytes; unbound calls explicitly refused. |
| `test_source6_reopen_validates_reference_protocol` | Actual SDK inspector-issued v3 refs, exact writer permission/path/one intent and independent bytes; unbound calls explicitly refused. |
| `test_source6_lock_wait_uses_entry_deadline` | Fresh real native phase/time/output/send admission or actual SDK-loop cutoff; original deadline/negative intent preserved. |
| `test_source7_refuses_invalid_allowance_before_native_generation` | Fresh real native phase/time/output/send admission or actual SDK-loop cutoff; original deadline/negative intent preserved. |
| `test_source7_bounded_native_author_and_ack` | Fresh real native phase/time/output/send admission or actual SDK-loop cutoff; original deadline/negative intent preserved. |
| `test_source7_http_research_refuses_coercion` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_source7_split_prefix_issued_and_reopened` | Actual SDK inspector-issued v3 refs, exact writer permission/path/one intent and independent bytes; unbound calls explicitly refused. |
| `test_source8_sampler_copy_preserves_full_authority` | Real guarded SDK conversation/transport/schema/security negative; five-turn navigation counts and exact-history refusal updated. |
| `test_source8_property_named_maxlength_is_not_a_keyword` | Original collection/search/GET/schema/candidate/CLI/failure-waiver purpose retained through actual SDK or existing pure validation. |
| `test_source8_full_length_validation_precedes_dispatch` | Real guarded SDK conversation/transport/schema/security negative; five-turn navigation counts and exact-history refusal updated. |
| `test_source9_author_declared_budget` | Fresh real native phase/time/output/send admission or actual SDK-loop cutoff; original deadline/negative intent preserved. |
| `test_source9_31_second_sdk_file_and_ack` | Fresh real native phase/time/output/send admission or actual SDK-loop cutoff; original deadline/negative intent preserved. |
| `test_source9_no_new_author_at_exhausted_reserve` | Fresh real native phase/time/output/send admission or actual SDK-loop cutoff; original deadline/negative intent preserved. |
| `test_source9_timeout_and_late_results` | Fresh real native phase/time/output/send admission or actual SDK-loop cutoff; original deadline/negative intent preserved. |

## All execution receipts and retained failures

No directory was overwritten. Every failed assertion/error is retained by name in its linked original JUnit and full stdout/stderr. Earlier random green runs were mechanical milestones only, not a waiver or fix. The unit2-green-2 rare card failure was specifically N3.5138343572083543 hitting actual PIIScanner Mastercard detection. Root-approved deterministic RED/GREEN removes only placeholder exposure scanning; actual wire scan remains strict.

| Stage | tests / failures / errors / skips | Exit | Receipt SHA256 |
|---|---|---|---|
| [unit2-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit2-red/receipt.json) | 64 / 7 / 0 / 0 | 1 | `7194421739ee0b4c2090f3282d76d3ce2ca925ce69311354d945dcb42779120c` |
| [unit2-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit2-green/receipt.json) | 64 / 1 / 0 / 0 | 1 | `32cb60468ab5d1d94885d03256afc8a76216c7e0f0844dcd7031be8251372829` |
| [unit2-green-2](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit2-green-2/receipt.json) | 65 / 1 / 0 / 0 | 1 | `c01a4455250a211f627300c1dc0a255eb2d2cb0dba78d8bf93b932fde5160c7d` |
| [unit2-green-3](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit2-green-3/receipt.json) | 76 / 0 / 0 / 0 | 0 | `3df9c675612677800061f50cc8dc81eb79d0adde1e595eadd8a690583a0a8f1a` |
| [unit2-green-4](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit2-green-4/receipt.json) | 82 / 0 / 0 / 0 | 0 | `6514bfdd9c827efb8b53d176659a15124bb98334919d81a7eafa1661000b83c3` |
| [unit2-green-5](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit2-green-5/receipt.json) | 82 / 1 / 0 / 0 | 1 | `f23cec0f5f778f44b5d6d615f69c37e9a8f51d44deaad546986d967c273f71ed` |
| [unit23-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-red/receipt.json) | 27 / 2 / 0 / 0 | 1 | `428336d37ac3601198f06d45fb2e8b388ed041c7a214d9d298c1286e5487c519` |
| [unit23-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-green/receipt.json) | 27 / 1 / 0 / 0 | 1 | `4017ae2e13693f6b39ac3f1a30d9230d828c5da85b9f8e8f2ba66386ddd6ca46` |
| [unit23-green-2](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-green-2/receipt.json) | 27 / 0 / 0 / 0 | 0 | `a25a6ff5b6453b8411663a1dabc6501cec530743fb2edc52cb84728acc72b98e` |
| [unit23-covering](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-covering/receipt.json) | 369 / 82 / 0 / 0 | 1 | `14a39b03bb9d1e0f69e87ba0d01d22ab68ee2e3b659774a89af43bc918205de4` |
| [unit23-availability-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-availability-red/receipt.json) | 83 / 1 / 0 / 0 | 1 | `12bfeee6f280a847796a4c821bbfa1a7531ea82698e33976ed49e85e053a40b7` |
| [unit23-availability-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-availability-green/receipt.json) | 83 / 0 / 0 / 0 | 0 | `f502908cd43b87b398e20324ecc32760d1cccab50bb6ad5ab169b876bbdafc09` |
| [unit23-research-fixtures](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-research-fixtures/receipt.json) | 178 / 59 / 0 / 0 | 1 | `c8bff592ca63f74e6a2637b4d4473477f99d2b9988447eaaa17854442c81b11a` |
| [unit23-runtime-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-runtime-red/receipt.json) | 2 / 1 / 0 / 0 | 1 | `4cd363cbd9fb096d9b9a6c4d0a90ad5b58355f800644225fb1be85693b58c1ad` |
| [unit23-runtime-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-runtime-green/receipt.json) | 27 / 0 / 0 / 0 | 0 | `9cd3c2e15f9bb3c872865b6731279fd79f55c4bf103545ddbd8444dc6aa08cd8` |
| [unit23-research-fixtures-2](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-research-fixtures-2/receipt.json) | 178 / 43 / 0 / 0 | 1 | `e77772f154da6b53b13e774001724cb9f4cf50699e8ec7f59e2c3880d2ad13d7` |
| [unit23-research-fixtures-3](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-research-fixtures-3/receipt.json) | 178 / 16 / 0 / 0 | 1 | `620df7e0550e6a509e0b6664d843c1a3b1547dd2d2fb3931e36e1e953e4d26d6` |
| [unit23-research-fixtures-4](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-research-fixtures-4/receipt.json) | 178 / 8 / 0 / 0 | 1 | `827783a1ab9837835b7b9d2c625efa343d0d4ea1dfb612eee9fee1afd83fecae` |
| [unit23-migration-covering](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-migration-covering/receipt.json) | 370 / 0 / 0 / 0 | 0 | `bc417af5bd5c720ebcbf95d8db05c9a6b2e3d1fbe8d2ef4b5caff86e6bdcb509` |
| [unit23-adversarial-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-adversarial-red/receipt.json) | 32 / 2 / 0 / 0 | 1 | `35616ca920af7b1776615a11d1104ceb3ea5f9ff60bb33a06037da9b7c536b85` |
| [unit23-runtime-security-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-runtime-security-red/receipt.json) | 24 / 2 / 0 / 0 | 1 | `297497c8e48cfb003b7dad9ed1cfe2c8fba184adc57890de3f1e5b30c20f8b99` |
| [unit23-runtime-security-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-runtime-security-green/receipt.json) | 49 / 0 / 0 / 0 | 0 | `d7ba08184b2ab375cd212e97af1d38b5b7ee1d61f5099520db7f9d4c84307e7c` |
| [unit23-replay-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-replay-green/receipt.json) | 49 / 1 / 0 / 0 | 1 | `ea820b4fbe1084a17922e2619d9e11c8a2adcff3416b11590fc8d381e33df5a1` |
| [unit23-replay-diagnosis](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-replay-diagnosis/receipt.json) | 1 / 1 / 0 / 0 | 1 | `c07f51f0003f35bae13707d4b0d3e0f9fae3dc9746111e1f0b5e3f35b3cd04ab` |
| [unit23-replay-green-2](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-replay-green-2/receipt.json) | 49 / 0 / 0 / 0 | 0 | `f01e24178c5ea477e3e8c7d0c136b87ac79f2be08d0d9ab408fd791ed0c7bcee` |
| [unit23-deterministic-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-deterministic-green/receipt.json) | 116 / 0 / 0 / 0 | 0 | `e35d7cfd5057d2ada8edc5bccfa0dc3329bd5f15776ea51927522e28ceaa5f66` |
| [unit23-oracle-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-oracle-green/receipt.json) | 28 / 0 / 0 / 0 | 0 | `7b18188bd240c3ecada235ac7121e2b3f1ac15a99d8cf5904b609b1e532ddeb5` |
| [unit23-boundaries-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-boundaries-green/receipt.json) | 72 / 0 / 0 / 0 | 0 | `e52508487b35921aa0657156c5b40f2c2e4d775c15a2dc16301f5cb7269ceabd` |
| [unit23-final-covering](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-final-covering/receipt.json) | 416 / 2 / 0 / 0 | 1 | `4aaff8eee0dc27152062e65e58d0330786cbb07dc19a8e2c1c1f30299be9f209` |
| [unit23-compat](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-compat/receipt.json) | 8 / 0 / 0 / 0 | 0 | `c16c30958aeae97847859a311856c615cd323094a77cc0c6d3048dc019ad64bf` |
| [unit23-final-covering-2](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-final-covering-2/receipt.json) | 416 / 0 / 0 / 0 | 0 | `a76ffa367912a7f06ded92cc093a487f62ef4d49c6ce4a10a30f1f10ac0c6280` |
| [unit23-compat-final](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-compat-final/receipt.json) | 8 / 0 / 0 / 0 | 0 | `70ff2cd93ddeb443d37a9934c60d6a2bd1927009575235bed6e215523069a116` |
| [unit23-timeout-readback-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-timeout-readback-red/receipt.json) | 1 / 1 / 0 / 0 | 1 | `665090771b11422cecde31eac5e9f0be48f44b66e443c20f9b14be61ca2482ff` |
| [unit23-timeout-readback-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-timeout-readback-green/receipt.json) | 32 / 0 / 0 / 0 | 0 | `ad664081021757227a430d78f3f64f00828af260fdef5f8977729102183195f2` |
| [unit23-close-first-failure-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-close-first-failure-red/receipt.json) | 1 / 1 / 0 / 0 | 1 | `29d84d3cbc1a5a4a851a76c1521f291b992455feef7ff375fe717f0d817c10dd` |
| [unit23-close-first-failure-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-close-first-failure-green/receipt.json) | 1 / 0 / 0 / 0 | 0 | `3409ca990923f5326259992a9c2a1a02c731a6f31f8221ed559a4312e5ae11cf` |
| [unit23-sealed-final-covering](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-sealed-final-covering/receipt.json) | 418 / 0 / 0 / 0 | 0 | `78ab32897c18bdfdb88ee0b4e3a3217cdab24966fbc2dbce85a916495914e2f2` |
| [unit23-compat-sealed](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-compat-sealed/receipt.json) | 8 / 0 / 0 / 0 | 0 | `e75789141ba63bc507643a3bbec7108529fdb25c80c5ba9bfbff133cbb2afca2` |
| [unit23-delivery-covering](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-delivery-covering/receipt.json) | 418 / 0 / 0 / 0 | 0 | `21757553d052ff4f85ead7964fc5620ca2a1d7ccb37d4fcf0a37ef83843daead` |
| [unit23-delivery-compat](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-delivery-compat/receipt.json) | 8 / 0 / 0 / 0 | 0 | `af6f8f915a3d08e8ae046858ec86ed552ede4c907bb01bd357d37d86667c3bab` |

Load-bearing REDs: unit2-red missing trusted preparation/enrollment; unit23-red missing bounded transport/fresh service fixture; availability-red forced rare placeholder card; runtime-red missing appendix; runtime-security-red unsafe schema-error echo and missing writer END file-ID linkage; timeout-readback-red SDK timeout misclassified before retaining terminal event; close-first-failure-red owned-client close replaced primary failure. Each has a subsequent targeted GREEN and the final complete GREEN.

Other failed intermediate stages are fully retained: initial legacy fixture migration/count/schema failures, one URL-bearing test claim corrected to an atomic supported claim, SDK metadata.arguments linkage correction, ToolSpec renderer reconstruction API mismatch (diagnosed from actual failing writer record and corrected to SDK descriptor wrapper), and deterministic fixture task-ID reuse choosing an earlier captured ledger (fixed by clearing fixture maps). No stale pass substituted for these failures.

Current compatibility warnings: PytestAssertRewriteWarning for pre-imported anyio, and optional voice reference unavailable/invalid fallback message. No audio was played/recorded. These are unchanged compatibility warnings, not newly claimed passes of voice functionality.

## Self-review and remaining limits

- Exact allowed paths and commit/test bytes were independently re-read; 22 SDK sources, original285 identities/65 names, protected inputs, whitespace, JUnit/paths, real worker crossing, actual SDK file call and separate-process readback all checked. No SDK/vendor/default/dependency/queue/global memory/KWS/user-file edits; no branch switch, push or tag.
- Actual generated PII-like final card IDs can still be rejected by the existing configured scanner. This intentional fail-closed availability rate is unmeasured; no scanner exemption, masking, reseeding loop, nonce/hash-format or backend change was made. Test entropy is deterministic and the original sixteen-byte nonce preservation test remains.
- Real model comprehension, original four-source E02 coverage, timing on native 8B inference, real search/GET acceptance, source10 actual budget and T3 remain unproved/unallocated. Scripted transport and synthetic literal oracles do not certify factual entailment. Production with max_turns<8 intentionally fails before composition; global defaults were not raised.
- Restricted packets live in the per-request trusted ledger. The future approved harness must capture its replay/runtime bytes via the trusted preparation boundary before discarding the request; safe public response summaries intentionally do not disclose raw GET/report packets. The four synthetic final packet exports demonstrate this readback path.
- Root owns independent integration/concurrency/transport review and publication. This report is implementer evidence, not independent approval, Owner freeze or original T2 acceptance.

---

## FIX round 1 of 5 — F1–F7 implementation and evidence

DONE_WITH_CONCERNS — all seven requested fixes implemented and verified; the same independent reviewer has not yet approved this round. The original SPEC/QUALITY REVISE is retained. No model, harness, actual, production or T3 release is claimed. Original E02/T2 remains NOT_PASSED.

Original report is preserved as the complete first **43651 bytes**, byte-for-byte, SHA256 `0bd8a4e9f3e64ebc475dbd3c5e67e2581ab0cd50f20e3dd8d21c7bf803182587` (archive `H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-author-r1/report.md`). This appendix supersedes any earlier implementation-complete implication; it does not rewrite the original report or evidence.

FIX1 BASE `0e3e0edeb6d57d7d792dd5f1e40ecad58ee60642` → HEAD `facd68d8f94b4adcfd136e489e9ff81580d2dc0d`. One precise commit: `fix: enforce research runtime replay and atomic permits`. Existing branch unchanged; no push/tag. Nine changed authorized files (four product modules, four scoped test files, and the authorized v3 runtime ABI appendix). work_navigation.py, test_work_context.py, original five frozen inputs, reviewed plans and installed SDK22 are unchanged in this round. Normal index empty and tracked worktree clean after commit.

### Finding resolution

| Finding | Concrete change / intended runtime failure gate | RED → covering GREEN |
|---|---|---|
| F1 Critical | Observer catch/seal and first failure remain inside the same RLock acquisition; configured-policy scan and lossless safe JSON serialization precede permit publication. Controlled real SDK worker handoff at the actual timeout catch boundary proves zero file calls before intent, retained timed_out effect/late record after admitted intent, and no exposed START permit after serializer failure. | [unit23-fix1-f1-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f1-red/receipt.json) → [unit23-fix1-f1-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f1-green/receipt.json) |
| F2 Important | Canonical submitted arguments equal the original native writer action. Every original visible receipt field, fixed resolved research.md path, SHA256, report/file/dispatch/adapter/sequence/request identity agrees with the consumed intent, real file adapter/effect records and reopened bytes. Both coherent changed-title/file and altered generation/binding/file/effect counterfactuals are rejected. | [unit23-fix1-f2-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f2-red/receipt.json) → [unit23-fix1-f2-fields-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f2-fields-green/receipt.json) |
| F3 Important | Replay checks ordered START/END pairs and the actual generation/send/return/secured/promote/EXPECT/claim/freeze/intent/file sequence in one declared monotonic domain, not SDK wall timestamps. Independent frozen caller inputs bind original prompt/root/allowance/deadline; full phase text is exact. Embedded prewrite bytes are hashed, revalidated and compared as unchanged events/wires/timeline/receipt prefixes. | [unit23-fix1-f3-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f3-red/receipt.json) → [unit23-fix1-f3-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f3-green/receipt.json) |
| F4 Important | Retain exact bounded version/tags JSON bytes and observed local manifest digest, bind their receipt hashes/status/path/order, and replay fixed version/model/digest. Reapply exact native options, whole supported outer envelope/model/role/unknown-field/positive count/context/timing policy and strict/sampler budgets. Real-shaped model-size/nanosecond integers are preserved; all decoded strings use unchanged real SDK scanners. | [unit23-fix1-f4-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f4-red/receipt.json) → [unit23-fix1-f4-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f4-green/receipt.json) |
| F5 Important | The final clipped timeout is installed on the SAME prepared request under the admission lock immediately before reservation/send, with metadata cap. Safe refused-admission receipts are created before rejection and record send_reserved=false with zero POST starts; genuine attempts are never refunded. Controlled integer build-time advances test 60s to56s (new1s timeout, not old5s) and to54s (refused), GET and POST. | [unit23-fix1-f5-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f5-red/receipt.json) → [unit23-fix1-f5-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f5-green/receipt.json) |
| F6 Important | Restore r5_between_snapshots to delaying the admitted real SDK FileWriteTool. Release/join occurs when service reads compose_error AFTER taking its frozen outcome. Assert original timed_out effect/path/IDs/bytes, stable first failure and response, separate late adapter terminal IDs and no next-request leakage. Separate pre-intent case still proves zero write. | [unit23-fix1-f6-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f6-red/receipt.json) → [unit23-fix1-f6-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f6-green/receipt.json) |
| F7 Important | Fresh ACK/service/verifier require nonempty exact bytes, rejecting absent/None/empty/bytearray proof. Service checks before publishing artifacts. Explicit verify_issued_research_artifacts is a pure U1 data helper with no runtime/ACK authority; historical v2 algorithms remain unchanged. All genuine positive service fixtures still run real guarded SDK NativeReAct/worker/file IO. | [unit23-fix1-f7-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f7-red/receipt.json) → [unit23-fix1-f7-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f7-green/receipt.json) |

F2 also has a separate retained `unit23-fix1-f2-fields-red` (4 failures) followed by 106 SDK/transport passes. Those tests mutate each original field independently, after a genuine successful ACK, so rejection is not caused by a missing preparer or invalid fixture. F7 RED distinguishes the actual null/mutable proof acceptance from the absent/empty proof error/artifact-publication contract; all are now rejected explicitly before service artifact publication.

### Current-byte final gates

- **449 passed, 0 failures, 0 errors, 0 skips, 74.54s**: [unit23-fix1-covering](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-covering/receipt.json) SHA256 `6ab46371fdf362fae9781515c5441e06798cefbf2299bd8a841867b24e85de4b`.
- **8 passed, 0 failures, 0 errors, 0 skips**: [unit23-fix1-compat](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-compat/receipt.json) SHA256 `641a777d97897c703ca7d4774336234d71799fa45254529872885c2f7bd7da63`. Only the safe copy evidence root changes; original preload/exclusion/import assertions retained. Original runner SHA256 `b165772a736de13006064a25b3d26db6aaa58afdcb38d8025fe91aa49bacc5c2`, copied runner SHA256 `c202d5eab45be18c8fa5082afaffd90ca86d0a44501411c4c595772883f3f90d`.
- Exactly one full original6+new3 run and one safe compatibility run were performed after all FIX1 source changes. Both receipt source-before/after maps match. No source edits followed those gates. No broad suite was run after each individual fix.
- [Independent four-case external readback](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-readback/external-verification.json), script [verify_external.py](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-readback/verify_external.py), actual command `H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8 H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-readback/verify_external.py` returned0. The oracle imports only stdlib; compares literal expected Markdown, independent fixed schemas/phase text, pinned actual SDK template and actual C persona/mainbrain, frozen original inputs, GET→page/ref→wire→intent/file/effect→ACK, metadata bytes/model identity, typed large machine counters, send-time timeout/order and sealed prewrite prefix.
- [Read-only exact ACK phase counterfactual](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-readback/phase-counterfactual.json), script [verify_phase_counterfactual.py](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-readback/verify_phase_counterfactual.py), command `H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8 H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-readback/verify_phase_counterfactual.py` returned0. It changes only the ACK system suffix AFTER the sealed prefix, recomputes message/entity/send-byte hashes, leaves raw envelope/prewrite/file unchanged, and is rejected specifically as `Runtime exact phase system drift`. This isolates the exact-phase gate from the earlier prewrite-prefix integrity gate; no production builder supplies the expected answer.
- All prior 418 current-candidate JUnit identities remain in the449 final run; original285 regression identities and original65 research names remain. The original research case count stays178. No skip/xfail or test-success bypass was added. U1 pure-data reopening assertions now call the explicitly named pure helper; fresh ACK/service never use that helper as a substitute for runtime proof.
- [Byte/scope/protected input readback](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-readback/readback.json), [exact staging](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-readback/staged-check.json) and [post-commit byte readback](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-readback/post-commit.json) show the exact authorized file set and every committed blob equal to final tested inputs. `git diff --check` and staged diff-check passed. The source maps retain raw byte hashes, including allowed-file line-ending changes; no protected file was normalized.
- [SDK22 pin readback](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-readback/sdk-sources.json): all22 match the immutable original snapshot. Final loaded-path map `unexpected={}`. All protected source inputs outside the FIX1 allowlist compare unchanged against the original0e3 final map.

Exact final pytest argv:

```json
[
  "H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe",
  "-B",
  "-X",
  "utf8",
  "-m",
  "pytest",
  "src/brain/tests/test_work_research.py",
  "src/brain/tests/test_work_context.py",
  "src/brain/tests/test_work_delivery.py",
  "src/brain/tests/test_agent_server_sse.py",
  "src/brain/browser/tests/test_browser_channel_s3.py",
  "src/brain/tests/test_interaction.py",
  "src/brain/tests/test_work_navigation.py",
  "src/brain/tests/test_work_navigation_sdk.py",
  "src/brain/tests/test_work_navigation_transport.py",
  "-q",
  "-p",
  "no:cacheprovider",
  "-p",
  "ultima_nav_pathcheck",
  "--basetemp=H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\unit23-fix1-covering\\temp",
  "--junitxml=H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\unit23-fix1-covering\\junit.xml"
]
```

Exact safe compatibility argv:

```json
[
  "H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Scripts\\python.exe",
  "-B",
  "-X",
  "utf8",
  "H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\unit23-fix1-compat\\run_compat.py"
]
```

The fixed H interpreter, isolated TEMP/TMP/TMPDIR/OPENJARVIS_HOME/cache roots, offline flags, paths and exact environments are recorded in each invocation/receipt. Raw stdout/stderr/JUnit/loaded paths are retained beside them. Compatibility keeps its one pre-imported-anyio rewrite warning and optional voice-reference fallback diagnostic; there was no audio playback or recording. The pure replay probe imports the real product verifier and also emitted the same optional-voice fallback message.

### Refreshed four-case sealed exports

| Case | Artifact SHA256 | Runtime SHA256 | Prewrite SHA256 | Order records |
|---|---|---|---|---|
| [text](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-covering/temp/test_v3_native_react_observati0) | `99c40cc2a82443f25b94d923d365b32b9f562ba53d6b07411f762faf5cf621cc` | `7fcdfbcfbf8ff68d60066525f4e3c8536f86953c9c1de6b9fa05ea9a8f72a708` | `a6dee85240fccb19723f998eab4f1962a69de88a54c1fa6f2b73889ad264760c` | 62 |
| [permuted](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-covering/temp/test_v3_native_react_observati1) | `dd354073e02fae32cd56ec4a675392e44c2b093707e18c9346e809650b072163` | `2cea128b9bcdf31812723593c1b70227868ff02cd24e30dfbe91acef1d8a5647` | `df3d8e10ff55c6f0dd544f3b07cc556e7e5ebadf584ca75475f9dbde2924eb2d` | 62 |
| [html](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-covering/temp/test_v3_native_react_observati2) | `3b299a15eab3e1b3cff171aa62adddb7507e5adea5f205eacc2790be7dca7fb3` | `38dfcc892a8dde7debeef3e87cd974e8cd2c413ff4407821c60c3a8548679d23` | `55a512705778ee95c1037971f3e047ca5f66f4f104d27ae11314e47f63ee1247` | 62 |
| [mixed](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-covering/temp/test_v3_native_react_observati3) | `ffe81b973dce3a48e12b79bfa3728d8c3d1a101a3c40889faaf67ea42fc26057` | `44fff8b6aedad159c0467d740e90d38630c684c649efb798a070523c786c7fe2` | `f3d737c5ef7de3e33605a60f0d8fada3268e7fd9c7f349bae6d2a7d34ebd79fd` | 62 |

Each NEW FIX1 positive directory retains `runtime-inputs.json`, `prewrite-packet.json`, `issued-snapshot.json`, `issued-views.json`, `runtime-replay.json`, `packet-manifest.json`, `external-readback.json` and actual `research.md`. Original418/8/four exports were not changed. The stdlib oracle reopens actual files after the test process ends and recomputes original GET/body/identity hashes and N3/view IDs directly from fixture bytes, line coordinates, nonce and UUIDs. It verifies both typed metadata model-size4987654321 and retained nanosecond integer timing fields without scanner changes or opaque-ID exemptions.

### Runtime ABI and atomicity details for scoped rereview

- Independent authority inputs are frozen `ResearchRuntimeInputs(prompt, binding_key, root, allowance, deadline)` in WorkService before its runner. `verify_runtime_packet(..., runtime_inputs=...)` and fresh artifact verification explicitly receive those independent inputs; a packet cannot supply its own expected prompt. The fixed target remains research.md under the independently captured request root.
- Runtime `timeline` uses consecutive integer order and lossless `repr` strings for samples in `work_tools.monotonic;ledger-sequence-v1`, all bound to the original deadline. SDK floating wall timestamp/latency JSON remains lossless diagnostic text and is never compared across clock domains. Success must follow generation → three send/return pairs → secured validation → optional previous-page promotion → EXPECT/START/claim → read END, or writer freeze/intent/file completion/END, then final-only ACK. Extra, timeout, reordered or late events cannot form a successful proof.
- START event data is validated, scanned and serialized BEFORE the permit is exposed; both ordinary exceptions and timeout seal inside the SAME observer RLock acquisition. F1 controlled tests use the actual callback catch boundary and real SDK worker/file operation, including an intentional handoff that deterministically exposed the old gap.
- Final packets embed the exact prewrite bytes, recompute their hash, recursively validate the one nonnested prefix and compare immutable scalar bindings plus exact events/wires/timeline/send prefixes. The independent intent and adapter/effect evidence bind native authored arguments, all original visible receipt fields, original body/path/hash and exact IDs. Coherent alternate report/file data cannot replace the authored/ACKed file.
- Each successful wire retains exact version/tags response JSON and the observed local manifest SHA256. Replay verifies those bytes against metadata receipts and fixed0.32.15/current8B/digest, exact options with no extras, complete supported outer message/model/role/fields/count/timing limits and both strict/sampler policies. Decoded author/metadata strings pass the configured scanner policy. Machine numeric fields remain validated integers; there is no scanner mask, alternate scanner or resampling loop.
- At final send admission, the newly computed clipped timeout replaces `prepared.extensions["timeout"]` on the same prepared entity. Its exact JSON is retained with the same admission clock sample. Refusal records exist even when no send starts; attempted counters/bytes are never refunded. No JSON/entity is rebuilt after approval.
- `verify_issued_research_artifacts` is explicitly pure data and grants no runtime/ACK authority. The public fresh wrapper requires nonempty exact bytes and independently checks runtime before invoking pure data reconstruction. Service checks the final proof before artifact publication; None, absent, empty and mutable bytearray all produce failure/needs_attention with the original completed effect retained.

### Complete FIX1 execution receipt index

| Stage | Tests / failures / errors / skips | Exit | Receipt SHA256 |
|---|---|---|---|
| [unit23-fix1-f1-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f1-red/receipt.json) | 3 / 3 / 0 / 0 | 1 | `f4e8622fe7979447b3028e86b4dbad8b23b809c8e32e198b673f1e137ddf8627` |
| [unit23-fix1-f1-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f1-green/receipt.json) | 32 / 0 / 0 / 0 | 0 | `5cc661da2125b39c16f45c6bdd4c5fb99ba8bb32c6a295f203bd01b3c607d7a3` |
| [unit23-fix1-f2-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f2-red/receipt.json) | 1 / 1 / 0 / 0 | 1 | `806100ca892c68e9336b34b9bff74011e5ba8ecd6663a13708164a4e29eecab4` |
| [unit23-fix1-f2-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f2-green/receipt.json) | 79 / 0 / 0 / 0 | 0 | `0d7e4e23ff0984885bd7ab731836d5c24edddb3c9ea9f2ab9399565d243a7336` |
| [unit23-fix1-f3-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f3-red/receipt.json) | 4 / 4 / 0 / 0 | 1 | `6d0b76a0d93160a6d083f10cd346060f4245893f7339424e0aaa9abca076ad9c` |
| [unit23-fix1-f3-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f3-green/receipt.json) | 83 / 0 / 0 / 0 | 0 | `a0e3463c5b3186b39e92b65105e8a3302841be3b47df3ab1ae9db29afd65625e` |
| [unit23-fix1-f4-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f4-red/receipt.json) | 8 / 8 / 0 / 0 | 1 | `3c1d86bd9bf46aa92f17716d74f05e0d8b1c78fe764dcd8068a9b1ebc826e80d` |
| [unit23-fix1-f4-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f4-green/receipt.json) | 91 / 0 / 0 / 0 | 0 | `96c42e561614648bba37b2ba191adccf9aa64a876a94094081bfab94912044de` |
| [unit23-fix1-f5-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f5-red/receipt.json) | 4 / 4 / 0 / 0 | 1 | `5a6971d45a0c489f39ed4eba22ebb040f40aca33452b1a9ca3153725e79a6231` |
| [unit23-fix1-f5-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f5-green/receipt.json) | 95 / 0 / 0 / 0 | 0 | `56e004e9b1e09c5e1cafcdf69283b54f32fd4b16abdef55b4ddef60026f17c4a` |
| [unit23-fix1-f6-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f6-red/receipt.json) | 3 / 1 / 0 / 0 | 1 | `5567b88ea10f99bdffffcca5e5274184afa6412259abfce507a581e55908e588` |
| [unit23-fix1-f6-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f6-green/receipt.json) | 35 / 0 / 0 / 0 | 0 | `761a6a13f9fae748273cf902dd0c76b76b5c19a138870642fa9a66f20c5eef68` |
| [unit23-fix1-f7-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f7-red/receipt.json) | 7 / 7 / 0 / 0 | 1 | `5b969bba91574dd2bc701eca556b143a7a80e894cb47c1dc8e4d4faaa1b53645` |
| [unit23-fix1-f7-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f7-green/receipt.json) | 166 / 0 / 0 / 0 | 0 | `416cd34bb7a5493d940046f1dd0a2c2329c4465aaff0eef449b3e32208a8a0be` |
| [unit23-fix1-f2-fields-red](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f2-fields-red/receipt.json) | 4 / 4 / 0 / 0 | 1 | `99130b7b57f84d7b9c220da1aece9b25ae2af6d82160a8aed951aff6dd5befad` |
| [unit23-fix1-f2-fields-green](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-f2-fields-green/receipt.json) | 106 / 0 / 0 / 0 | 0 | `2ff2f925ab300fbb8e8c1a26f62f4a3aa0b57c4445ef899d238e4b59cca4c87e` |
| [unit23-fix1-covering](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-covering/receipt.json) | 449 / 0 / 0 / 0 | 0 | `6ab46371fdf362fae9781515c5441e06798cefbf2299bd8a841867b24e85de4b` |
| [unit23-fix1-compat](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/unit23-fix1-compat/receipt.json) | 8 / 0 / 0 / 0 | 0 | `641a777d97897c703ca7d4774336234d71799fa45254529872885c2f7bd7da63` |

Every first RED and its named assertions remain in the original stage JUnit/logs; no directory was overwritten. All targeted covering GREENs passed on the first covering invocation after their corresponding fix. The complete final gates are new receipts and do not sum historical passes.

### Remaining concerns / release status

- This is implementer FIX1 completion evidence, not independent approval. Root must have the SAME reviewer check F1–F7 and any new fix breakage against the exact commit and packet exports before publication/acceptance.
- Current configured scanner can still reject an actual PII-like generated final reference; this existing intentional fail-closed availability limitation remains unmeasured. No source/nonce/scanner exemption was added.
- Actual model factual behavior, original four-source E02 coverage, real search/GET/native timing/harness qualification and T3 remain unallocated/unproved. Only current qwen3-8b-uncensored digest6d7230a9… remains authorized; no alternate weights, fallback, download, defaults, queues, memory, production, audio or UI changes.
- The scoped changes are fully committed, index empty, tracked worktree clean; pre-existing unrelated untracked files remain untouched. No push or tag by the implementer.
