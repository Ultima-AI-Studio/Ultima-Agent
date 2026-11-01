# T2 bounded fix round 2/2 — research prerequisites and bound report design

2026-11-02. Original order wo-ultimaagent-20261101-0021. Current source remains ad1621e55314de3a79bebbb922f6a58fea7458ae. This is a design for controller interface ruling, not implementation or technical PASS. No new model, network, UI, production action, dependency installation or source edit was performed during this preflight. Existing failures/tags/receipts remain intact; no budget/history reset.

## Problem and fixed outcome

The natural E02 request on ad1621e produced one successful SDK search, zero GETs, and a file of search snippets. The product truthfully returned needs_attention. More task-specific wording would leave the necessary operation optional. Research mode must therefore execute its required read-only collection before asking the same NativeReAct main brain to compose facts. Report source references must come from a current-request immutable fetched-body catalogue instead of model-copied URLs.

Success remains actual model-generated facts, >=3 different actually cited fetched sources and bodies, real SDK file write, independent reopen/hash/content verification, and separate semantic/official-source review. Merely fetching, producing a structured response, or writing a file does not prove factual correctness. Ordinary E01 file and E03 selection/companion modes retain their current tools and I1 exact-content checks.

## Installed OSS inspection and alternative ruling requested

Inspected installed OpenJarvis1.0.4 sources locally:

- tools/_stubs.py:179 onward: ToolExecutor accepts concrete BaseTool instances, dispatches ToolCall through its bounded SDK worker pool, preserves gates/timeouts, and emits TOOL_CALL_START/END/TIMEOUT on an injected EventBus. ToolRegistry constructor capture already solves request ContextVar isolation in this product.
- agents/native_react.py:276 onward: the model selects each action and may return final_answer before any tool. No required-tool sequence switch was found for this NativeReAct path. tool_choice use found elsewhere belongs to different hybrid agents/providers; switching them would violate the retained execution choice and still does not require a search-followed-by-three-GET sequence.
- workflow/builder.py:46-60 and workflow/engine.py:39-137,239-263: existing WorkflowBuilder.add_tool accepts static JSON tool_args; WorkflowEngine tool nodes delegate directly to system.tool_executor.execute. Sequential execution aborts on any failed node. Agent nodes use system.ask instead of the current product runner/readback lifecycle. The workflow engine does not itself turn search results into a bounded deduplicated candidate list or distinguish an optional failed candidate from insufficient overall collection.
- tools/web_search.py:330-344,407 onward: the installed free SDK path obtains DDGS result dictionaries internally, then exposes formatted text (title/Source/Summary) and count/engine metadata. It does NOT expose the original structured URL array through ToolResult. Do not claim an unavailable structured-result API.

Proposed smallest reuse: a short synchronous request adapter calls the existing ToolExecutor for one mandatory search and bounded candidate GETs, then calls the existing _run_work_agent exactly once. No custom workflow DSL, graph runner, scheduler, concurrent fetch engine, model loop, retry mechanism or new registry. The installed WorkflowEngine was considered, but wrapping two dynamic phases and optional candidate failures in graphs/system shims would add machinery around the same executor without removing product-specific candidate validation. Direct executor composition is the narrower existing mechanism. Controller may instead mandate static WorkflowBuilder nodes, but dynamic candidate selection/partial-read policy still requires a small adapter and no agent node should bypass WorkService.

## Exact input interfaces and authorization

Keep WorkService constructor and submit_work signature. Extend its strict context whitelist by one DATA key:

`source_urls: list[str]` optional, valid only with research=True, 0..5 entries, each nonempty <=2048 characters. Values are candidates only. Strictly reject booleans, dictionaries, authority-bearing extra fields, userinfo, non-HTTP(S), fragments, private/metadata destinations under existing SDK SSRF checks. Existing `research` must still be strict True plus trusted startup --work-research/browser dependency. Source candidates cannot configure a method/header/engine/root/HWND/PID or confer any new permission. No default research enablement.

CLI adds repeatable `--source-url URL`, valid only with --work --research; it serializes source_urls in existing context. Existing ask_work already transports context, so agent_client.py and HTTP top-level whitelist do not change. Query can also contain explicit candidate URLs; structured source_urls are not mandatory. If both contain URLs, canonicalize/dedupe their union and reject >5 distinct candidates rather than silently expanding budget. URL extraction is normal parsing, not instruction execution; surrounding query is never interpreted as an authorization policy.

Capture-only plus research remains supported as data, subject to existing approved capture. Explicit research+replace_selection will fail before capture/network/mutation in this bounded stage: a structured multi-source report is not generally identical to a selected-text rewrite, and silently choosing one would weaken I1. Existing pure selection mode is unchanged. This combined-mode restriction needs controller ruling; there is no demonstrated combined-mode accepted baseline. No task/session/memory/recovery additions.

## WorkService execution chain and source collection

Create NEW src/brain/work_research.py with narrowly named helpers:

```
collect_research(query: str, source_urls: list[str], *, binding, ledger,
                 capabilities) -> ResearchCollection
render_research_report(payload: dict, sources_json: str) -> RenderedReport
verify_research_artifacts(binding, artifacts, report_records, sources_json) -> list[dict]
```

ResearchCollection is frozen: catalogue_json (serialized immutable source records), trace tuple, attempts tuple and actual search query. RenderedReport is frozen: content, cited_source_ids tuple, source bindings. It does not call a model or grant filesystem authority. Core source record: short request-local id S1..S5, original adapter source UUID, requested/final/dedupe URL, fetched_at, decoded_body_sha256, full bounded decoded body, extracted text, read call ID and request/session/task IDs. Catalogue construction verifies body SHA and URL/body dedupe and freezes copies; do not derive source IDs from model output or reconstruct source authority from ordinary context.

Flow:

1. Validate request/context/startup capabilities and allocate existing task UUID/root/binding. For research, do not execute model yet.
2. Enter existing bind_work(binding, ledger, preflight_capabilities). Instantiate ONLY the registered ultima_work_web_search and ultima_work_http_get aliases with ToolRegistry.create while inside that binding. Construct installed ToolExecutor with those concrete instances and a private request EventBus, agent_id=binding.task_id. Workers use captured binding/capabilities, never fetch ContextVar in execute.
3. Always execute one search via SDK ToolCall. Its query is the natural query with explicit HTTP(S) URL tokens removed and whitespace bounded to2000; if no text remains, use candidate host/path terms without a literal HTTP URL. This avoids the installed search URL-fetch bypass without suppressing Jarvis.ceo text. No automatic paid engine or credential lookup.
4. Prefer explicitly supplied candidates. If none, use structured records returned by our BrowserChannel adapter around SDK search output. Because installed SDK exposes formatted records only, add a small pure parser in browser/channel.py that reads its documented/current `### title / Source: URL / Summary:` record boundaries into `results=[{title,url,snippet}]`, preserving original SDK body as provenance. It does not perform search itself, rank anew, trust snippet instructions, or call DDGS separately. Malformed records are ignored with explicit diagnostics; no URLs invented from summaries. Test the adapter against the installed SDK formatting. If explicit candidates are fewer than3, fill remaining bounded slots from search results; total attempted distinct candidate URLs <=5.
5. Execute GET candidates sequentially using the existing registered alias and installed ToolExecutor. Existing public URL/GET-only/header/SSRF/content checks remain. Never fetch local URLs, log in, post, use credentials, accept query-supplied tool parameters or treat remote content as instructions. A redirect cannot widen into private space. Canonical final URL plus decoded body hash determine distinct successful sources.
6. Retain all failed candidate reads as actual failures. They are OPTIONAL collection probes, not mandatory successful task tools: no write/mutation occurred and no failed candidate is cited. If successful unique bodies/URLs are fewer than3, end before the model/file tools, with explicit collection failure/attempts and zero fabricated outputs. Mandatory search failure/timeout is fatal even if candidate URLs exist. An optional candidate failure may coexist with overall success only if >=3 fetched distinct cited sources survive. This exact nonfatal read-probe exception is isolated to prereq GET attempts and needs controller ruling; existing model/file/mutation failures remain fatal/non-replayed.
7. Freeze successful catalogue before calling the same main brain. Use a new frozen WorkCapabilities.research_json field; enter a fresh bind_work with the SAME binding/ledger and final catalogue. Invoke existing runner exactly once with source IDs and source text excerpts as untrusted data, user task separately as instruction. No second Agent/core/model call for collection. Full source bodies remain evidence; model excerpt capped8000 characters/source, explicit truncation marker, max5 sources. Do not manufacture facts outside the model or promote search snippets to evidence.

The preflight aliases remain SDK registry registrations, not a parallel tool table. No background production scheduler or persistent source memory.

### Bounds, executor timeout and truthful traces

One search, at most5 different candidate GETs, no retries. Request-local preflight start budget120s; stop before starting another read after deadline. Proposed trusted GET per-hop HTTP timeout5s (SDK's existing <=5 redirects remains), read alias ToolSpec timeout35s, search ToolSpec timeout30s. This bounds a normal GET below its SDK worker timeout and leaves time inside existing300s work transport for model composition. No caller timeout parameter. Controller must approve this narrow internal timeout change; alternatively retain old timing and explicitly accept possible transport timeout without replay. Deadline checks cannot kill a third-party function already running; if ToolExecutor times out, abort collection/model, record the SDK timeout, never start file/UI side effects, and let only the SDK bounded daemon reader finish. No claim of durable cancellation.

All preflight actual SDK start/end/timeout events are captured at occurrence from the private EventBus, with request/session/task IDs. A per-invocation wrapper records the actual ToolCall.id and links its new adapter ledger call_ids; the SDK's own raw event does not include call_id, so do not invent one inside its data. Return trace has phase='research.preflight' plus real events, followed by the unchanged NativeReAct trace phase. Preflight invocation records contain mandatory-search vs optional-candidate classification and actual success/error. Failed candidates remain visible in attempts/warnings, not silently converted to successes. Model/tool writing events occur only after collection succeeds.

## Source-bound report ToolSpec and real file path

Register `ultima_work_research_write` in the SAME existing SDK ToolRegistry. Its parameters are strict, additionalProperties=false at every object, also checked in execute:

```
{
  "path": "research.md",
  "title": "model-generated title",
  "sections": [
    {"source_id":"S1", "heading":"model-generated heading",
     "facts":["model-generated source-supported factual paragraph"]}
  ]
}
```

path/title/sections required; title1..200 characters; sections3..5; source_id dynamically enumerates ONLY this request's frozen catalogue IDs; section heading1..200; facts1..6 nonempty strings each<=2000 characters. No url/body/root/request/task/method/header/engine fields. Reject duplicate section source IDs, missing/unknown/cross-request IDs, fewer than3 distinct referenced source URL/body identities, NUL/control newlines in heading/title, and HTTP URLs/Markdown links in generated text fields that could create extra citations. Facts are plain text paragraphs rendered safely as Markdown bullets; model supplies the factual wording. Do not autogenerate a summary from source literals or hardcode topic facts.

Renderer produces title then each section heading, exact stored final_url and its model facts. A URL is rendered only from the immutable source record. It records cited IDs/body hashes and rendered-content hash. Merely GETting five candidates does not force five sections: a valid3-source report succeeds; extra uncited candidate bodies remain attempts/provenance, not document citations. All actually cited sources count; an unGET source ID cannot be rendered.

Report tool constructor captures normal capabilities/ledger AND constructs its nested WorkWriteTool while on the bound request caller thread. This is essential: constructing that writer later in the SDK worker would lose ContextVar authority. execute validates/render_report, then delegates to that captured existing writer -> SDK FileWriteTool. Relative/absolute path checking and write-only schema remain. This is a formatting adapter over the same filesystem tool, not a fixture-save route. Its ledger result links report call ID -> nested real file-write call ID/path/rendered content SHA/cited IDs/source-body hashes. There is still an actual SDK file tool call and no file when model never invokes the report tool.

Research-mode model tool list becomes calculator, think, ultima_work_research_write and ultima_work_file_read. Do not expose unrestricted or ordinary file_write in research mode so an unbound free-form document cannot bypass structured citations. Read aliases need not be exposed again after preflight; collection is already complete and catalogue immutable. E01/E03 keep their existing tool list and exact companion check. Unbound report construction/execution rejects. If the model returns a verbal answer or arbitrary text without report execution, task fails; no code parses an injected final answer into a canned file.

After runner, service selects only current-request successful report records linked to actual file-write records, runs existing verify_artifacts, independently reopens those files and checks exact rendered content/hash and source bindings again. Final `sources` includes actually CITED source records (>=3); add `research_attempts`/`available_sources` provenance for fetched-but-unused and failed candidates. Do not require every fetched source URL in the document. If later ordinary file reads/other tool failures occur, or report validation/write/readback fails, preserve any confirmed file and return truthful failed/needs_attention using existing effect evidence. No replay or response-style rerun.

## Exact file additions/changes requested

- NEW src/brain/work_research.py: collection adapter, immutable catalogue, pure report renderer and independent report-source verifier. Keeps product source collection/rendering out of dense service/Win32 modules.
- NEW src/brain/tests/test_work_research.py: SDK-executor prerequisites, source/ID/report/readback tests and actual NativeReAct replay; actual network/model seams only at external boundaries.
- MODIFY work_tools.py: frozen research_json capability, registered report adapter, captured nested writer and true call linkage; read ToolSpec timeout if approved. Existing non-research adapters/I1 unchanged.
- MODIFY work_service.py: strict optional source_urls, always-run research prerequisites before runner, research final tool list, cited-only validation/provenance, merge actual phase traces, combined mutation/research rejection if approved.
- MODIFY browser/channel.py: parse the current SDK rendered search result records into explicit candidate data; trusted fixed GET timeout if approved. No vendor changes/new retrieval engine or direct DDGS implementation.
- MODIFY cli.py: repeated --source-url data option with research requirement, existing context transport. agent_client.py/server HTTP whitelist signatures unchanged.
- MODIFY tests/test_work_context.py: update research deterministic runners to consume prereq catalogue/report tool, keep all UI/I1 cases intact. tests/test_work_delivery.py only if necessary shared tool-list expectations change; E01 defaults must stay the same.
- MODIFY tests/work_context_acceptance.py: keep natural topic/known candidate input; extend manifest with new source files and optional source-ID/rendered-report receipt collection. No answer/schema recipe in live task. Existing own-window lifecycle stays unchanged.
- SDD same task-2-report.md plus this design; later docs report only after actual work/receipts. No extra source file without controller ruling.

No work_context.py/voice/memory/session/queue/global registry source change. Protect original process identities and all previous artifacts. No new agents.

## TDD and gate plan after controller ruling

No implementation/testing/live run before design approval. Interpreter stays H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe; cwd managed C: checkout. New evidence T2/fix-round-2/<run>.

RED command: python -m pytest src/brain/tests/test_work_research.py src/brain/tests/test_work_context.py src/brain/tests/test_work_delivery.py -q --junitxml=<run>/red.xml. Write assertions before implementation, and capture actual process exit in a receipt rather than masking it with a trailing shell display command.

Required failures/tests:

1. A model runner that immediately returns final_answer still observes real SDK search+required GET calls occurred first; noGET path cannot reach runner. Actual ToolExecutor/ToolCall and constructor-bound registry aliases execute, only SDK HTTP/DDGS I/O substituted.
2. source_urls/query URL input is data only; explicit approval still required; unknown authority fields rejected; no method/header/paid engine bypass. NoURLs searches use parsed SDK result candidates; malformed/insufficient/duplicate URLs or duplicate bodies fail before model and file creation.
3. GET successes>=3 plus one failed optional candidate retain its failure and can produce a valid3-citation report; search failure, executor timeout or<3 unique successes never reach model. No unbounded candidates/automatic retry. Captured events demonstrate actual chronological SDK begin/end and IDs across worker threads.
4. Real NativeReAct with deterministic inference emits structured report tool call; actual SDK writes and independent reread happen. Human facts come only from inference payload. Unknown/cross-request IDs, forged URL, fewer than3 IDs, unauthorized path, tamper/unreadable/fake file success, and only verbal completion all cannot succeed.
5. Four/five fetched sources and exactly3 cited source sections succeed; final sources corresponds to actual citations, unused sources preserved only as availability/attempts. Renderer exact URLs map to immutable same-request bodies/hash; bogus extra URLs rejected. No fixture-specific facts in product.
6. E01/E03 old paths, UTF16/focus/selection negatives and all8 I1 companion instances remain green. Mixed research/mutation rejection occurs before any action if approved. CLI source-url requires explicit work+research and stays plain data.

GREEN covering command same focused files plus test_agent_server_sse.py. Add cli/context cases there or in test_work_research.py. Supplemental eight legacy tests use the already approved evidence-local compatibility wrapper with exact identity comparison to T1 and C module-path proof. Do not rerun unrelated voice/whole-machine suites. Capture raw test process exit/output/XML, source/spec/sample hashes and all failures.

Commit one fix2 candidate after focused/covering checks, report code/test evidence to controller for scoped final re-review. No live gate before release. This is the final bounded repair; unresolved failures remain explicit for controller adjudication, not another prompt/round reset.

After release: same frozen candidate E01/E02/E03 each3 rounds, run one round at a time and stop on first failure. E02 natural topic+optional known source candidates uses required SDK reads then same live model structured report, at least3 actually cited official documents/bodies independently fetched/hash-compared and facts manually matched per section. E03 includes actual selected text, exact companion equality and separate observer process; two owned-window focus/selection negative scenarios rerun. All outputs unchanged after generation. Independent PID/lock/window cleanup and source-unchanged manifests. Technical gate/Owner/freeze remain controller-owned.

## Specific controller rulings needed

1. Prefer direct existing ToolExecutor composition over adding WorkflowEngine graphs for this bounded dynamic collection, with the installed API/limitations above.
2. Approve new work_research.py/test_work_research.py and precise helpers, strict optional source_urls/CLI data option, and immutable short-ID report schema/tool.
3. Approve formatted-SDK-record parsing as the current installed SDK's missing structured-result adapter; no direct new search implementation or vendor modification.
4. Approve optional candidate failure handling only when >=3 actually cited successful sources survive; all mandatory search/model/write/mutation failures remain visible/fatal.
5. Approve cited-only>=3 source validation, fetched-unused provenance, and structured-report-only writable tool in research mode. Do not count merely fetched bodies or force citations for irrelevant candidates.
6. Approve private bounded HTTP/read timeouts and120s prereq start budget; no caller expansion, retry or worker-cancellation claim.
7. Approve explicit early rejection of research+replace_selection while pure E01/E03 and capture-only research remain intact.

Await interface ruling before TDD or source implementation. ad1621e and all earlier failed/successful attempts remain preserved.
