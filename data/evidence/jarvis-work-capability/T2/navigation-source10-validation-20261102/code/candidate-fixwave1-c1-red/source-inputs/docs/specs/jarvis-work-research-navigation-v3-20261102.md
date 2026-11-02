# Research navigation protocol 3

Task1 pure-data contract, 2026-11-03. The approved navigation design is binding.
J is strict sorted compact UTF-8 JSON: no floats, surrogates, non-string keys or coercion.
U=[source ID,final URL,normalized URL,canonical GET UUID,body SHA256,projection SHA256,domain,policy SHA256].
B=[request,session,task]. View=SHA256(J([view3,nonce,B,U,start,end,seq,dispatch UUID,adapter UUID])).
Card=N3.+SHA256(J([card3,view,kind,symbol,anchorFirst,anchorLast,citeFirst,citeLast,SHA256(J(anchorPairs)),SHA256(J(citePairs))]))[:16].

Frozen public classes contain only safe tuples/bytes; restricted collection and GET ledger stay with the writer. ScanPolicy captures actual ordered SDK scanners, mode, source/backend configuration identity and paging/extractor/render version. Preparation verifies GET result, attempt and START/END linkage, original body and reconstructed HTML projection. Scanner changes, original identity/hash and GET mismatch abort; unsupported coordinates, truncation, oversized sources, raw HTML findings and unrenderable pages are unavailable. Require three distinct available URL/body pairs.

Catalogue <=4096 bytes, pages <=3072 bytes, <=24 original positions, <=8 cards, <=8 contiguous citation lines. Full lines only; omissions reserve metadata and stabilize after trimming. No relevance ranking. Existence checks use identical renderer and fixed width IDs without publishing a winning window.

Restricted replay JSON version 3 contains catalogue (safe frozen source fields and catalogue bytes), policy JSON, collection JSON, GET records JSON, and ordered reads. Each read contains PageKey, source/start and exact wire JSON plus wire SHA256; later ledger integration must populate reads only after confirmed END and successful transport promotion. The snapshot seals SHA256 of replay_json independently of views_json. Pure-data tests construct sealed packets; they do not certify promotion. Replay rebuilds original projections, pages and card hashes and rejects stale/foreign/unissued/cross-window references. v3 rendering uses only the specific issued page. Fresh verification requires required_version=3 and snapshot; required_version=None is historical compatibility. v2 algorithms remain unchanged.

Security boundary: build_page is a deterministic safe-data renderer. Before SDK return/staging/exposure, the trusted narrow read callable MUST call scan_view(view, captured_policy). The inspector holds only catalogue plus that callable. scan_view revalidates the exact scanner objects/configuration policy, complete actual serialized wire and every decoded public string; availability stand-ins never certify a later wire. Policy seals actual navigation/witness source hashes and verifies the pinned BrowserChannel source hash. seal_snapshot is a data-packet constructor, not an issuance capability; only the later ledger can supply confirmed issued reads.

## Runtime replay appendix after combined review fix round 1

Fresh `verify_research_artifacts` and ACK require nonempty immutable runtime bytes.
`verify_issued_research_artifacts` is a separate pure-data helper for U1 tests;
it grants no runtime or ACK authority and is never a WorkService success gate.

The caller freezes `ResearchRuntimeInputs(prompt, binding_key, root, allowance,
deadline)` before the runner. Runtime verification receives this independent
frozen object explicitly. The packet's prompt is compared with that input;
the complete phase system is rebuilt from the installed SDK template/tool specs
and the fixed phase policy. A phase prefix alone is insufficient.

The runtime appendix contains exact safe native entities, both bounded metadata
response JSON strings, the observed local manifest digest, complete raw response
JSON strings and parsed raw/secured envelopes, strict/sampler schemas and four
hashes. Integer model sizes and nanosecond counters remain typed machine values;
all decoded string values pass the captured configured scanners. No identifier
or scanner exemption is introduced. Replay checks metadata bytes against each
receipt, fixed version/model/digest, exact options, envelope fields/role and
positive token/context/timing limits as well as the message/schema budget.

`events` retains lossless SDK JSON strings as diagnostics. Authority order is
`timeline` in the declared `work_tools.monotonic;ledger-sequence-v1` domain:
each record has a consecutive integer order, exact repr of the request monotonic
sample and original deadline, and its generation/SDK/adapter/receipt link.
Replay walks generation, send/return, secured validation, page promotion,
EXPECT/START/claim/END, freeze, consumed file intent and file completion in order.
SDK wall timestamps are not compared with request monotonic samples. A success
transcript permits neither extra events nor timeout/late events.

The prewrite packet ends at the claimed writer freeze, before any file intent.
Later packets embed its exact bytes, prove its hash and verify its unchanged
events/wires/timeline/send prefix. The execution block exports the consumed
intent, real file adapter records and effect. Native submitted arguments, all
visible receipt fields, resolved fixed research.md path, original file bytes/hash
and report/file/dispatch/adapter identities must agree through ACK and reopening.

The observer validates and safely serializes an event before exposing a permit;
every failure seals under the same RLock acquisition. At send admission the
final clipped timeout is installed on the same prepared HTTPX request before
reserving its send slot. A refused admission retains a safe receipt with zero
POST starts; attempted sends are never refunded. Synthetic test exports include
separate frozen inputs, prewrite bytes, pure issued replay/views, runtime appendix
and an externally checked packet manifest. Future actual acceptance remains gated.
