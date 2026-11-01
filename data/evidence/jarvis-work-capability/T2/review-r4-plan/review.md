# Independent T2 repair 4 design review

**REVISE** · wo-ultimaagent-20261101-0021 · exact SHA256 `91997321f47fac20cd24d654b5bfe38adc4fac13d04a7bd68f96c89a530f0c91`

Critical findings: none. Three Important findings require design revision before source release.

## I1 · Active flow needs a bounded await and this witness

Plan line 31 restricts eligible expression/return/assignment shapes to call/new and Name-position symbols. UnifiedAgent lines 44/48 are return await, 64/97 assign await this.provider calls, and 71-74 assign await this.toolRegistry.execute over four lines. Installed TypeScriptLexer emits Keyword for await/this and Name.Other for the qualified members. A literal whitelist can accept the logger or getToolDefinitions and still exclude the actual dispatch.

Specify an optional await at the operand and optional keyword this as receiver in those narrow existing shapes. Define the symbol string, final Name position, multiline completion and 8-visible-line bound. Use unrelated async qualified and multiline positives plus comment/log/string/unfinished/out-of-view negatives. Check the exact projected active donor and archived Python executor span without adding source-specific production rules. Compact numbered [line,text] JSON for the entire local TS body fits the four-source allowance (5425 characters including object fields).

## I2 · Report validation is atomic per invocation only

Plan lines 44/51 promise failure before write and no effects for rejected support. _CapabilityTool.execute catches report errors and records a failed ToolResult. NativeReAct.run (agents/native_react.py lines 352-358) appends the observation and keeps generating. WorkService checks failures only when the runner returns. A validly encoded bad span followed by a valid payload can therefore write a real file before the first failure is surfaced. A wire-envelope checker alone accepts both envelopes.

Define request-local handling of the first rejected support and distinguish failed-invocation atomicity from runner-wide no-write. To promise whole-request no-write for a rejected span, stop before the next generation/dispatch using trusted current-bound failure state. Preserve the SDK loop and every original failed event. Script a bad span followed by a would-be valid write and assert exact dispatch count, file presence and CLI2. Separately test committed write followed by malformed final as needs_attention with original bytes/IDs. Never waive an earlier fatal tool failure.

## I3 · Capture possible writes even when result is late or unsuccessful

SDK tools/_stubs.py lines 389-421 time out a worker future and cannot cancel active execution. FileWriteTool can return an error after opening/truncating a file. _WorkFileTool.execute records its result at return, and WorkService derives needs_attention from successful writes or may_have_committed. Only the window adapter currently marks a possible effect. A compose timeout/error before a success record can therefore be classified failed with no recorded possible file effect.

Define the request-bound write-attempt boundary after complete report validation and path checks, before nested SDK file mutation; preserve path/identity and uncertainty without inventing a successful write. Handle outer timeout racing the worker, including before the marker is observed, by fencing late writes or classifying the in-flight attempt as possible. Script a partial-write error and an already-running delayed SDK writer; verify needs_attention, no replay, fresh independent readback when available, and no cross-request attribution. Keep all unsupported spans rejected before entering the mutation boundary.

## Nonblocking observations

The borrowed view is feasible on this installed SDK. The owner initializes once under the ask lock. Jarvis has explicit close/context-manager teardown and no destructor; dropping an unclosed shallow view leaves the owner alive. Keep shared bus, policy and rate limiter, never use the view as a context manager. _run_agent still constructs tools and wires security with the original identity. Delegating _publishes_events avoids duplicate inference events. Confirm exception/interleaving ownership and binding in A.

Retained offline MockTransport captured four POST bodies at /api/chat, absent/json/json/absent, unchanged 8B, num_ctx 16384, num_predict 2048, real calculator 4.0. GuardrailsEngine and InstrumentedEngine precede transport. This synthetic calculator proof omits a real report write, as expected. Strict duplicate/nonfinite/envelope checks precede the SDK parser; preserve the raw published inference on every exit and require an actual final branch.

Generic query delimiter repair and existing explicit URL/canonicalization/SSRF paths are appropriately scoped. Local analysis verifies the donor path and token shapes. Retain the historical 404 and separate live official-source and factual/relationship review. Source-local eligibility and limitations cannot settle reachability or cross-project integration.

24,000 serialized characters and 2,048 output tokens are plausible caps. The full message includes schema, observations and history. Keep source and transport projections distinguishable, and minimize report evidence echoed in model observations while retaining full ledger. Installed OllamaEngine hardcodes finish_reason=stop and reports max(estimated,reported) prompt tokens; use raw available counts and mark unknown truncation honestly. Require visible evidence on every cited span and complete JSON; live adherence remains unmeasured.

Preserve R01 common service, R02 existing SDK, R03 request linkage, R04 target/capability gates, R05 readback, R06 isolation, R07 failure semantics and R08 protected defaults. No T3-T5 requirements discharged. Metadata-only root-relative protocol hash plus unchanged case requests, independent verifier, 3x E01-E03 and one E03-negative with first-failure stop are appropriate. Current scope authorizes neither source nor live gates.

Read-only review and local lexical inspection. No suite rerun, model, live I/O, UI, queue, product edit or release. Prior failed rounds retained. No Owner or freeze claim. Frozen inputs, installed SDK digests, source tokens and reviewed proof hashes are in review.json.
