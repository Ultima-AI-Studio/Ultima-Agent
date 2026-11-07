# Independent controlled-entry preparation review

Verdict: **PASS_PREPARATION_ONLY**. No blocking findings. Reviewer `root-independent`, agent `/root/review_e02_output_structure_entry`.

Candidate: `bf7f7a9cf0e4ba559c29daa388c00379d12d345a`.
Manifest SHA256: `ea078190d78a340d3db06092bb050662a4a59e37e2f327c595199073b195eb1f` (175 members independently hashed).
Plan SHA256: `88d60ff7350e541748798e0ee37a2d46cbdc2c04e9a28cdf1dba8eea99bddf8d` (matches independent plan review).

Read-only review checked the plan/specification, source-copy provenance and ledger rulings; independently hashed all 1598 input pins and all 77 source pins under the frozen root, matched B's inventory, compared the three core function/class ASTs with O, and checked the original input metadata/budgets and 15 unrelated files. B's 1192 manifest members and both predecessor preparation manifests remain intact. Saved preservation evidence separately retains both prior failed actual results; no historical acceptance is credited as a current run.

Current JUnit identities total 291 raw / 289 unique harness cases plus 16 bindings, 34 entry and 11 boundary checks = 350. All final group source snapshots match current bytes. Offline audits record no denied operations and closed probes. The retained initial export-red has exactly two obsolete v4 expectations and 32 passes; it is excluded from the final pass total. The version assertion is upgraded to v5, with three parametrized retention modes and one invalid-retention rejection. Their saved JUnit results pass. Current assertions check bytes read from the original export path against the ledger, SHA256 and 16384 cap, FULL content, EXCERPTS offsets/omission, OMITTED_POLICY no secret, failure-only/zero-credit semantics, and rejection before any raw/export receipt is created. This review did not rerun them or claim independently retained temporary raw exports.

The content-derived preparation decision is explicitly non-platform and allocates zero cases/reviews. Original read_release requires a separate grant, which is absent. Static review of closeout.py confirms that after this PASS it creates only preparation approval, reads readiness and tests missing-grant refusal without run_once. publish.py scopes local project/mirror commits and tags, checks staged paths, manifest/input hashes and preservation, and performs byte readback. final_readback.py checks published content, current aliases, original last_actual_result and absence of actual authority. No remote push or deletion is included. These programs and their future outputs have not been executed or credited by this review.

PASS — 1. Incomplete source inventory or helper paths mistaken for product paths: require all77 product source pins from B, all under the frozen root and byte-equal.
PASS — 2. Reused old release or a preparation answer accidentally granting execution: record a truthful content-derived preparation decision with allocations0 and show original missing-grant refusal without calling run_once.
PASS — 3. v5 safe content and bounded excerpts cannot cross original export path: verify actual exported bytes, hashes and original16384 cap, including FULL/EXCERPTS/OMITTED_POLICY.
PASS — 4. Contradictory v5 content/JSON/retention states: original exporter must reject invalid packet without creating raw evidence, preserve failure-only/zero-credit semantics.
PASS — 5. Historical failed test expectations or borrowed acceptance passing as fresh evidence: count current JUnit identities, preserve the two expected obsolete-v4 failures, verify same final source bytes and preserve prior actual result separately.

Declined to judge: actual research/inference or delivery improvement; current/continuous runtime liveness; fresh product acceptance (979 is frozen evidence); E02/T2/T3-T5/Owner release or acceptance; future closeout/publication/readback outcomes; remote synchronization. Runtime evidence is one saved observation of seven identities and pinned 8B/0.32.15 only.

Actual run authorized: false. Actual allocation: 0. Independent result-review allocation: 0. Acceptance credit: 0. Review performed only filesystem reads, stdlib hash/AST/XML inspection, and exclusive creation of these two review files; no tests, product imports, network, live process scans, UI, audio or service operations.
