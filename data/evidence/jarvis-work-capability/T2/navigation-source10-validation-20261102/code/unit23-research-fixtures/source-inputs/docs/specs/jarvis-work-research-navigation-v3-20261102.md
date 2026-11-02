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
