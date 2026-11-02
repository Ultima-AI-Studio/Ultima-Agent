# Source10 code unit 1 report

Status: DONE_WITH_CONCERNS. Pure-data Task1 implemented and committed; independent task review remains with root. E02/T2 NOT_PASSED, T3 closed; no model/actual/source allocation or external execution success is claimed.

BASE `244d2120abcd6b8d7744f74a05bd22de46a2d3a5` -> HEAD `e0b04d6a68f7851d2dfc6c516bc7701896355b69` (one commit: `feat: add canonical research navigation views`). Branch `codex/jarvis-work-navigation-v3-source10`. Exact six allowed paths committed; shared normal index empty, tracked worktree clean; unrelated untracked files untouched. No push/tag/production integration.

## Concrete interfaces and behavior

- Added frozen ScanPolicy/SourceV3/CatalogueV3/PageKey/ViewV3/IssuedSnapshotV3, strict canonical_v3, deterministic build_page, constant bounded v3_writer_schema, resolve_v3, render_v3 and restricted seal_snapshot. Module initialization imports stdlib only. Catalogue holds safe tuples/bytes and never restricted collection or GET ledger.
- prepare_navigation wrapper validates original body hash, normalized URL, request binding, original adapter ID vs S label, successful GET result/attempt and exact START/END metadata. BrowserChannel HTML reconstruction is byte-exact with script/style hiding and pinned 9d7cab extractor source; lowercased final URL suffix controls witness kind. Original coordinates and both body/projection limits are enforced.
- make_scan_policy captures actual ordered Rust-backed SDK SecretScanner/PIIScanner defaults, their source/backend identities, mode/pattern configuration, Python/HTMLParser, exact extractor and navigation/witness source bytes. validate_scan_policy(policy, expected) rechecks the same scanner objects/order and policy; replay reconstructs only the known installed default scanner classes and rejects an unknown replay backend.
- Complete-text and per-line scans/redaction-equivalence/residual checks remove whole dirty lines even in WARN/REDACT; BLOCK full findings block a source. Nonidentity HTML with any original markup finding is unavailable. Source identity strings, operation labels and catalogue are scanned.
- Pages reserve omission runs, fit whole lines in original order, cap 24 positions/3072 serialized UTF-8 bytes/8 cards, and use <=8 contiguous citation lines without gaps. Anchors retain original source9 helpers; no new relevance/fact selector or this/super fix. Availability checks legal starts with the final renderer and fixed-width IDs without exposing the winning page.
- IMPORTANT NEXT-UNIT CONTRACT: build_page alone does not authorize exposure. The trusted narrow read callable MUST invoke scan_view(view, captured ScanPolicy) before SDK return/staging/exposure. Inspector captures only safe CatalogueV3 plus that callable. scan_view checks actual complete serialized wire and each decoded public string. Availability stand-ins are not a later wire proof.
- IMPORTANT ISSUANCE CONTRACT: seal_snapshot is only a restricted packet constructor for already-issued reads. Its pure-data PageKey/wire/hash records do not prove SDK END/native request/guard transport/promotion. U2/U3 ledger owns actual event/transport confirmation and must seal and independently verify that authority before supplying a trusted IssuedSnapshotV3. No direct constructor grants runtime issuance.
- resolve_v3 recomputes source projections/anchors/pages/card IDs from the sealed original collection and GET trace/ledger, validates manifest and ordered issued data, rejects foreign/stale/unknown/v2/unissued references and window drift, and renders from each particular issued page. render_v3 is called only after resolution. It never invokes v2 _source_view.
- verify_research_artifacts adds required_version and issued_snapshot keywords. Fresh version 3 requires the trusted snapshot; unknown versions reject without downgrade. None preserves explicit historical behavior. Existing service is not switched to v3 in Task1.

## Verification and immutable receipts

Interpreter for every pytest run: `H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8`. cwd is the isolated C worktree. v1 stages used `V/code/run_code_tests.py`; final stages used root-created read-only `V/code/run_code_tests_v2.py`. V is `H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102`. Every stage has its exact argv/environment in invocation.json, stdout.log, stderr.log, junit.xml, loaded-paths.json and receipt.json with file hashes. All earlier failures are retained without overwrite.

| Stage | tests / failures / errors / skipped | receipt SHA256 |
|---|---|---|
| unit1-covering | 333 / 0 / 0 / 0 | bb053aa19ea1a82133634796693d05776417f909b6a95e6ee379372d138c459e |
| unit1-covering-2 | 341 / 0 / 0 / 0 | 165a3f28d78516bb94b80f23c0cc868d2a5f7fc28816bd973a70f4714d0ca574 |
| unit1-covering-v2 | 341 / 0 / 0 / 0 | 04a1e78596ac2db22b15b4028c188bb1a2cadf66d7ce5f59eccb976992a37a33 |
| unit1-covering-v2-final | 341 / 0 / 0 / 0 | b4184da221c2ebbcdc1b2bdf6db95f01e3d88b79df74636bfde545be49be1c60 |
| unit1-green | 29 / 1 / 0 / 0 | f6ebfdac0733ad449c05814fd112ce82b547fa5cbbb022a7972c37cb21702ded |
| unit1-green-2 | 45 / 0 / 0 / 0 | 31f6d2f286a80e282ede6077d8061f11cd04cd327dea928555d84740ada9d611 |
| unit1-green-3 | 48 / 0 / 0 / 0 | a2d45dc5f5af29248b041ebd3236f8c0204258f8d3983d71f1790259847cc3b3 |
| unit1-green-4 | 55 / 0 / 0 / 0 | b97dc2e5d24861adcd7e8c31cc22921bc7ed5acf4d4816cabc4541fbfa52ec10 |
| unit1-green-5 | 56 / 0 / 0 / 0 | 208eb8a5781795b60857f74d86f3663f5cbede91bf9d01416a097f43dd7b00d2 |
| unit1-red | 29 / 29 / 0 / 0 | 01a91169af25a6427bcaf963b2a9757bf55e72996eae9d3861bfe48d1b0752e2 |
| unit1-red-2 | 45 / 3 / 0 / 0 | 8dc6d61724ef44fffbc284dc8a68148530c287163b56a325319d68fd92398fc8 |
| unit1-red-3 | 48 / 1 / 0 / 0 | 9a9eec028f7f6f1adc7bedad26dfded3b9b263a12a46c425d998abb0db045cb6 |
| unit1-red-4 | 56 / 1 / 0 / 0 | 0f5a1726c0a0f40ea5c6859926ee050f05cb8aef4585ca3baecdd717b301cb47 |

First RED unit1-red has 29 assertion failures, zero errors: the absent v3 module triggers the explicit feature-missing assertion. No typo/import error was used as RED. unit1-green retained one schema-error normalization failure. unit1-red-2 retained three failures: schema normalization, escaped-string complete-wire scanning, and missing GET END success check. unit1-red-3 retained missing actual rule source hashes. unit1-red-4 retained Python TokenError propagation instead of source unavailability; each was fixed and rerun in a new stage.

Final exact pytest argv:
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
  "-q",
  "-p",
  "no:cacheprovider",
  "-p",
  "ultima_nav_pathcheck",
  "--basetemp=H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\unit1-covering-v2-final\\temp",
  "--junitxml=H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\unit1-covering-v2-final\\junit.xml"
]
```

Final v2 runner SHA256: `60f6ea3d157969dcaa4eebef474a62642da6f02963cb8a87b405217f788ac32c`. Before/after input maps match and raw source copies exist under `unit1-covering-v2-final/source-inputs`. Loaded candidate modules resolve under C and SDK modules under H installed site-packages; unexpected map is empty for every recorded stage. Final stdout and stderr contain no warnings; no skip/error/failure. Final covering is 285 historical tests +56 navigation tests =341. Historical safe compatibility baseline was 8 PASS, not rerun for this pure-data unit; it retained the preexisting anyio PytestAssertRewriteWarning and missing optional voice-reference fallback diagnostic. The historical six-file baseline was freshly 285 PASS.

## Mutation coverage and self-review

- Independent strict J/H oracle checks view/ref identity, nonce/B/U/seq/canonical dispatch and adapter UUID changes, line bytes and collisions. Rejects floats/surrogates/non-string keys/coercion, unknown/unissued/foreign/v2 handles and manifest/view/wire/key drift.
- Real configured SDK scanners cover BLOCK/WARN/REDACT, Unicode/CRLF/LF, redaction disagreement/residual findings, dirty-line gaps, raw HTML findings and escaped complete-wire strings. Every documented suffix and forbidden HTML .ts/.py/.unknown cases are parameterized. Source caps 256KiB and1024 lines, page24 positions, cards8, and exact serialized3072/catalogue4096 bytes have -1/at/+1 cases.
- Later legal-start existence and middle-window replay outside v2 visibility are tested; line-only pages issue no cards. Duplicate source, GET mismatch/truncation, projection/body drift, unsupported coordinates, empty/oversized/all-redacted/unrenderable sources reject before any composition. Tests deny socket.connect/getaddrinfo and use isolated temporary file roots. A real temporary file is rendered, freshly reopened with required_version=3 and rejected after tampering. These are pure-data/file tests, not SDK write-dispatch or model execution proof.
- Static self-review proves the original work_research prefix through renderer is byte-identical to BASE: 25553 bytes, SHA256 `e79a99ab2443640410e8d1a653e9233ed83d9e54a521a02a7882ec66cf1edf50`. All23 existing definitions except verifier dispatcher retain identical AST; no v2 algorithm was changed. source_pack/card output is compared before/after navigation and historical285 regression suite is green. Original frozen product files/work_verifier remain unchanged.
- Targeted committed product/test/spec diff --check is clean. The two approved docs retain exact41998861/a8419b77 hashes. Full doc whitespace check reports existing implementation-plan CRLF trailing characters at157-159 and extra EOF blank line; preserved rather than altering approved bytes.
- Auxiliary self-review first used invalid encoding name utf8-sig (LookupError), corrected to utf-8-sig; it did not change product/test bytes. PowerShell newline append initially caused trailing CR at new-file boundaries; only our new product/test/spec were normalized to LF, then fresh v2 coverage bound final bytes.
- Brief specified only v3 spec; initial draft used shorter filename research-navigation-v3.md. Authority readback identified exact allowed filename, so it was renamed byte-for-byte to jarvis-work-research-navigation-v3-20261102.md before commit. Current v2 and final v2 both passed341. Final duplicate doc-only rerun had already started when root ruled static evidence sufficient; it was retained, no further test repetition.

## Final exact file hashes

| Path | SHA256 |
|---|---|
| docs/plans/jarvis-work-research-source-navigation-design-20261102.md | 41998861f1a0eeaad1800f61d19642656b0e19fa4b74dcf0e79366d6dc4c0eef |
| docs/plans/jarvis-work-research-source-navigation-implementation-20261102.md | a8419b773d7cf67f1b9754cdf4475aba32b1f6be8591335792f9d1122f3e6195 |
| docs/specs/jarvis-work-research-navigation-v3-20261102.md | 46a6e05571056720effc35d3b98ceeecae46af7a07eae9328b9a029abc11442f |
| src/brain/tests/test_work_navigation.py | aa47106786a331b36ca6aa51e4d192fdb27691503e066bc62fd750f27d96dab0 |
| src/brain/work_navigation.py | ab32d5831f385402149752ddefefa868117a95703cc9900aa88803e706ab8b69 |
| src/brain/work_research.py | 6772f852cd3ee468e79461ee579c0444b486918e1bf4e5f53f17496da7ce3b4d |

Independent readback/static manifest: `V/code/unit1-final-proof.json`. Earlier pre-LF self-review remains `V/code/unit1-self-review.json` and is explicitly not the final file-byte manifest.

## Remaining gates / concerns

Root must review the exact commit before U2. The narrow final-wire scanner and ledger-authoritative issuance obligations above are mandatory for runtime wiring, not claims already proven here. Replay currently recognizes the installed default SecretScanner and PIIScanner; any other scanner identity fails closed until explicitly supported and tested. No configured defaults, SDK, production H code, KWS/audio/voice, queues/memory, network/models/dependencies or budget gates were changed. E02/T2 and later Owner/release gates remain unpassed.
