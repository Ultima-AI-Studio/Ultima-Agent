# Original T2 E03 / same-candidate E01 preparation

Status: DONE_WITH_CONCERNS, pending root independent review. This package contains no case authority and no actual-case directory. Preparation does not establish E03/E01 acceptance or T2 PASS. Only the existing fixed qwen3-8b-uncensored model/digest is eligible.

## Scope and reuse

Base: C checkout HEAD 244d2120abcd6b8d7744f74a05bd22de46a2d3a5, frozen source21-before.json, helper SHA256 8eafd9931adf2278032fd79a210b1fc0dbdcc6f80ca5ca5e35bb8e99d3e8b9f0. Product and SDK files remain unchanged. `acceptance_adapter.py` imports the original helper's public launch / wait_for / external_readback hooks and starts its unmodified fixture/observe CLI. The original WorkContextProvider handles negative checks. Positive requests use the normal isolated agent_server and original CLI, with exact original E03 query and frozen E01 request/facts.

The original round_case cannot be safely called wholesale: it permits E02, loops externally, records a hardcoded model name, waits 900 seconds, does not bind a release/case ledger, and only checks launcher cleanup. The new evidence-only controller narrowly copies that lifecycle, excluding research, adding pre-effect guards, GET-only metadata/model proof, identity-tree receipts, bounded wait, external validation, and exact cleanup. `adapter-vs-original.diff` shows the complete original helper versus this adapter; fixture/observe implementations are reused rather than duplicated. `full-new.diff` records all new review source files against empty files. No private SDK mutation, arbitrary exec, HTTP payload rewrite, prompt tuning, defaults change, or invented model answer.

## Exact bindings and authority

One case per invocation in this exact sequence:
`e03-round1`, `e03-round2`, `e03-round3`, `e03-negative`, `e01-round1`, `e01-round2`, `e01-round3`.
Each has the fixed exclusive folder `R/actual/<case>`; optimized Python, E02, unknown cases, traversal, reparse points, existing case folders, source/SDK drift, changed model proof, skipped/duplicated cap ledger, or incomplete prior independent reviews fail closed. Root must preconsume the selected case in its ledger before invocation. The adapter never writes root's ledger, issues authority, loops cases, retries work, or releases the next case. Existing failed case directories cannot be reused. Six positive work CLI invocations maximum; negatives use zero CLI/model calls. A failed or ambiguous request stops progression; root must retain consumed state and not invent a new name.

Root creates the ledger and one authority only after independent review; these examples are schemas, not approval:

```json
{"consumed":["e03-round1"],"released_case":"e03-round1"}
```

```json
{
  "schema":1,"issuer":"root","case":"e03-round1",
  "folder":"H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\e03-resume-20261102\\actual\\e03-round1",
  "runner_sha256":"HASH_OF_FINAL_ADAPTER",
  "source21_sha256":"HASH_OF_FROZEN_SOURCE21_BEFORE_JSON",
  "model":"qwen3-8b-uncensored",
  "digest":"6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330",
  "ledger_sha256":"SHA256_OF_UTF8_JSON_DUMPS_LEDGER_SORT_KEYS_TRUE_DEFAULT_SEPARATORS",
  "prior_reviews":[]
}
```

For every preceding case, `prior_reviews` must contain exactly ordered entries with `case`, `reviewer:"root-independent"`, `receipt_sha256`, and `mechanical`, `facts`, `target`, `file`, `cleanup` all `"PASS"`. Root decides the applicable negative/ E01 dimensions and must inspect the genuine receipts/readbacks, actual target identity/text, file bytes/hash, all supplied facts/no additions and complete cleanup; assertions in authority are attestations, not proof the adapter can generate. Root must also inspect no boundary-error / cleanup-refresh-error, all cleanup absent, port closed, protected5 unchanged, and source/model still stable. Any ambiguity prohibits another release.

Invocation template, only after root releases the exact case:

```powershell
& H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8 H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e03-resume-20261102/preparation/acceptance_adapter.py --case e03-round1 --folder H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e03-resume-20261102/actual/e03-round1 --authority ROOT_ISSUED_AUTHORITY.json --ledger ROOT_OWNED_PRECONSUMED_LEDGER.json
```

The E03 fixture initially selects its whole frozen text, exactly as the original harness. External validator reconstructs replacement with UTF16 offsets, proves prefix/suffix unchanged (vacuous when original selection spans all text), checks both owned window identities and unrelated owned text, checks actual file bytes/hash and exact replacement equality using only existing CRLF/LF equivalence. It does not assert semantic/factual PASS. Negative group preserves original semantics: capture approved A, switch to owned Other or change A selection, call original provider, require both refusal and no before-send callback and all owned text unchanged. No model/server/CLI for negatives.

## Environment, model, source and cleanup proof

Every child gets owned TEMP/TMP/TMPDIR/OPENJARVIS_HOME/HF/XDG paths, HF offline, NO_PROXY localhost/127.0.0.1/::1, no inherited HTTP(S)/ALL proxy, C checkout PYTHONPATH. No global environment change. No secrets are logged. Native model host must be default localhost:11434 or 127.0.0.1:11434. Metadata uses proxy-free/no-redirect GET of isolated /health and native /api/version,/api/tags; local model manifest bytes must hash to the fixed digest. No metadata POST or warming. Model and server health are captured before the sole positive CLI. Source21, old R files, SDK source hashes, HEAD and protected5 are checked around each case. Config source proof records the actual installed SDK and frozen isolated constructor behavior, not a new runtime config endpoint.

Own launcher descendants are discovered with read-only CIM and Win32 creation/exe identity. This handles H venv redirector + base-python double PID. Only owned tree identities are persisted. Fixture prefers stopfile; actual child terminates before launcher if needed with exact retained creation/exe checks; waits are bounded, cleanup receipts retained, server port closed proof recorded. Protected5/Ollama/shared inference processes are never stopped. Two preparation headless proofs exercised real redirector stopfile and exact child identity termination without UI/model/network.

## Fresh checks and limitations

Authoritative covering command is recorded literally in covering-exact-receipt.json: pinned Python -B -X utf8 -m pytest src/brain/tests/test_work_context.py src/brain/tests/test_work_delivery.py -q -p no:cacheprovider with owned basetemp/JUnit. 82 passed; loaded C product files and hashes in covering-exact-imports.json. Root explicitly allowed test-owned ephemeral loopback transport/CLI and mklink-junction negative cases under owned test tree. Production ports 8756/11434 and external socket connections are blocked by prep-only sitecustomize audit hook. No real model/UI/audio. Initial equivalent pytest.main covering run and receipt are retained; exact-command repeat resolved literal command requirement. Focused adapter checks: 29 passed, zero socket connections. Initial adapter collection found psutil absent; no dependency installed, implementation switched to stdlib CIM/ctypes before passing checks.

Material concerns for independent review:

* Actual existing SDK native HTTP timeout is 1800 seconds; original agent_client is 300 seconds. E01/E03 have no WorkService 260-second deadline (260 is research-only). Adapter leaves defaults unchanged and waits at most 315 seconds for the CLI then preserves logs and tears down only its owned service tree. This cannot claim shared model generation has stopped after a disconnected HTTP request; a timeout prohibits another case and requires fresh root resource/metadata review without stopping Ollama.
* Original frozen nonresearch product exposes completed `inference_end` events, not HTTP start events or incomplete inference counts. Adapter counts completed events (1..10 and exact event model), records incomplete/start/native HTTP counts as null. NativeReActAgent original path calls `_generate(messages)` without tools kwargs; Ollama's tools-only 400 retry is therefore inapplicable. No controller retry is added. Interrupted/failing inference count remains unknown, not zero. If root requires exact interrupted POST accounting, this package alone cannot prove it without a separately reviewed read-only observation method; do not release a live case until resolved.
* Actual isolated config behavior is established from unchanged CLI argv + hashed product/SDK constructor sources; /health reports model/agent/tools but no per-instance max_turns/engine-timeout config fields. No added server instrumentation or private SDK hooks. Root must decide whether this existing source/runtime proof meets admission.

No actual positive/negative UI acceptance, model POST, production service request, new model, external request, source10, queue change, commit or push occurred during preparation. No E02 or later stage gate is released.
