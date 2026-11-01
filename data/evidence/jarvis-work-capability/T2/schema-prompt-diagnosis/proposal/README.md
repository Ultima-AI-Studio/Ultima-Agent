# Unapplied proposal: expose nested report schema through the supported SDK description

Original order wo-ultimaagent-20261101-0021, T2. This directory contains a read-only diagnosis and reviewable proposal, not a third repair implementation. T2 remains BLOCKED/FAILED; the two previous bounded repairs and all failed live evidence remain part of the same history. No Owner exception has been inferred or granted by preparation of these files.

## Confirmed cause and limits

The installed OpenJarvis1.0.4 build_tool_descriptions renderer reads only each top-level parameter name/type and the ToolSpec.description. NativeReAct uses that text to construct its system message. The current report tool declares nested sections.items, facts=array/items=string and source_id enum in its parameter dictionary, but the actual formatter text omits all those nested types/values. The natural product prompt names the nested fields without their types. This is an interface visibility gap, so the first facts:string failure cannot by itself establish that the current8B model is insufficient.

Root's fresh health observation in ../finding.json is qwen3-8b-uncensored; the user's model description was Qwen3:8b. No14B model was loaded, tested or approved here. The proposal does not change model selection or assume those names denote interchangeable tags.

Separate semantic failures remain independently failing: the produced AgentManager section claimed unsupported provider implementation from parameter/TODO hints and assigned README facts to the wrong source. Showing a complete schema neither proves source entailment nor guarantees a valid model reply. No old generated document or failed receipt has been edited.

## Minimal two-file patch (NOT APPLIED)

1. src/brain/work_tools.py — four added constructor lines after the existing WorkResearchWriteTool.parameters declaration. Set an INSTANCE description to the existing generic class description plus a JSON serialization of the complete current parameter schema. Dynamic enum values therefore reflect only that instance's request-local catalogue; the class description stays unchanged. No example facts/answers, repo names, vendor change, ToolSpec parameter change, authority expansion, rendering change or relaxed error gate.
2. src/brain/tests/test_work_research.py — one parametrized regression with source counts3 and5. It runs the real existing SDK collection/NativeReAct product path with the existing mocked external I/O and a capture-only inference engine, captures the actual first inference messages, reads the system message, parses the schema visible THERE, and checks sections=array, nested facts=array/items=string and the exact current source_id enum. It does not accept checking only tool.spec.parameters. The capture engine returns final_answer without a tool, and the test asserts no delivered Markdown file. This test has been proposed only: it was not run in this diagnosis.

Patch: nested-schema-visibility.patch
SHA256: 633aa63821e4e3aa76db5b7209fdbd9b31dea615a0079de02894705f5a0d31dc

The patch is plain reviewable unified diff, not applied to source/index/HEAD. Existing source newline conventions must be respected if an exception later authorizes application. The existing ToolSpec.description field is an installed SDK interface, so no vendor patch or alternative formatter/Agent is needed. An explicit external tool-description override could replace this field; the proposed actual-first-message test deliberately does not mock away that override and would fail if it hides the schema.

Optional, separate Owner consideration: a single generic instruction could remind the composer that a TODO, accepted parameter name or import does not prove an implemented feature; claims need actual implementation/source evidence. No project/provider-specific statement is proposed. This optional wording is NOT in the supplied minimal patch and cannot be represented as a semantic fix.

## What was actually performed

Only read local source/evidence, instantiate the already bound ToolSpec, and render it through the REAL installed build_tool_descriptions before/after setting an in-memory instance description. The inert render catalogue uses the source IDs from the parent's declared-parameters.json; it is not a fetched-source or execution success claim. No WorkService, Agent.run, tool.execute, inference engine, pytest, DNS/HTTP, UI, product-output directory creation or model call was run.

formatter-before.txt reproduces the loss: only path/string, title/string and sections/array.
formatter-after-in-memory.txt shows the full nested schema using the proposed description. Its parsed nested facts type is array with string items, and its source_id enum is S1/S2/S3. This proves compatibility of the description fix with the current actual SDK formatter. It is NOT a claim that the proposed NativeReAct regression has passed; only that future test will inspect real first-inference input.

proposal-receipt.json records patch/formatter hashes, zero execute/ledger/inference/pytest/network/UI calls, and before/after source15/HEAD/index proof. Python ran with -B to avoid source __pycache__ writes. Git calls used --no-optional-locks and only rev-parse. The15 source hashes exactly match the frozen10fec03 tested-source manifest. Actual HEAD was the controller's metadata checkpoint afbbe3e4616d1f322ebc55705750014a4db2867f before and after; no HEAD/index mutation occurred here. No C: file was written. All outputs are within this H: proposal directory.

## Conditional RED/GREEN plan — not authorized or executed

If Owner explicitly approves ONE scoped exception, root must record it as cumulative repair attempt3 under this original order, preserving both prior attempts and failure state. It must not be relabeled as another fresh2/2 cycle or new order. The authorization must name the two files above and keep the current8B, vendor, permissions, renderer and gates unchanged. Without that approval, this remains only a proposal.

1. After authorization, apply ONLY the test hunk first. Use the fixed interpreter and managed checkout. Run:

   H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -m pytest src/brain/tests/test_work_research.py::test_native_react_first_messages_include_nested_report_schema -q -p no:cacheprovider --basetemp=<new-exception-evidence>/red-tmp --junitxml=<new-exception-evidence>/red.xml

   Expected RED: both source-count cases fail because the actual first NativeReAct system message lacks the full schema marker/types/enum. Capture raw exit code separately. External I/O and inference are test seams only; no live model is needed for RED.
2. Apply ONLY the four-line production hunk. Run the identical command into separate green-tmp/green.xml/log, preserving RED. Expected GREEN requires first-message nested visibility for both request-local enums, not a canned model answer.
3. Cover the two changed modules plus existing delivery/HTTP paths once: test_work_research.py, test_work_context.py, test_work_delivery.py and test_agent_server_sse.py. Keep I1 and all permission/failure cases. Supplemental legacy8 may use the already approved C-module/evidence-root wrapper if root requires it. Store exact commands, raw process exit, JUnit, code/spec/cases/supplement hashes and warnings. Do not rerun unrelated voice/UI/service suites.
4. Freeze a new two-file candidate and obtain fresh scoped review before any live gate. No14B comparison is included or approved.

## Conditional same8B E02 check — only after explicit exception and review

Keep the unchanged natural topic/harness/source-candidate sentence and the existing installed8B model path (currently identified by root health as qwen3-8b-uncensored); do not load/change model/provider. The first recheck is ONE E02 round through the normal isolated product server/CLI, same ToolExecutor prerequisites, same report schema/renderer/authority and all original fatal gates. Bind15 inputs plus the new candidate and unchanged r2/cases/supplement.

Inspect every actual SDK read and optional failure, actual first report arguments, actual SDK file write, external reopened bytes/hash, all cited source bodies and per-source facts. The known prose-adjacent URL parsing Minor remains; do not alter the frozen task to hide it. Current model/report errors remain fatal even if the model subsequently self-corrects. Semantic source mismatch remains FAIL independently of successful schema parsing. Stop immediately on mechanical or semantic failure; no repeated prompts or lucky retries.

Only root can release further original-contract three-round E01/E02/E03/negative gates after the conditional check and independent readback. Passing a schema-visibility unit test, or even one valid8B report, cannot be called T2 PASS, broad model sufficiency, Owner acceptance or release. The14B proposal remains unapproved/unexecuted; any later model comparison would need a separate explicit decision and must not replace diagnosis of this formatter gap.

