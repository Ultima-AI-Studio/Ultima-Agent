"""Read-back sealing for offline preparation only; issues no authority."""
from pathlib import Path
import json,hashlib,subprocess,xml.etree.ElementTree as ET
P=Path(__file__).parent
import run_local_role_prefix as h
core=h.frozen_core()
before=h.read(P/'preservation-before.json')
for path,digest in before.items():h.checked(path,digest)
for folder in ('preparation','preparation-r2','remaining-source-preparation','remaining-source-preparation-r2','S2-first','remaining-source-actual','local-role-design-proposal'):
 root=h.E/folder
 if root.exists():
  expected={p for p in before if Path(p).is_relative_to(root)}
  actual={str(p) for p in root.rglob('*') if p.is_file()}
  assert actual==expected,folder
for root,expected in h.read(P/'old-namespace-inventories.json').items():assert h.namespace_inventory(Path(root))==expected
assert not h.ACTUAL.exists()
source=h.read(core.ROOT/'native-read-budget-source9/source-current.json')
frozen=h.read(core.ROOT/'native-read-budget-source9/frozen-inputs.json')
assert all(h.sha(core.CHECKOUT/p)==d for p,d in source.items())
assert all(source[p]==d for p,d in frozen.items())
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=core.CHECKOUT,text=True).strip();assert head==h.HEAD
suite=next(ET.parse(P/'tests.xml').getroot().iter('testsuite')); summary=suite.attrib
assert summary['failures']==summary['errors']==summary['skipped']=='0'
assert (P/'tests.exit').read_text()=='0'
core.save(P/'preservation-after.json',dict(all_files_unchanged=True,file_count=len(before),sha256=before,
 source21=source,frozen5=frozen,head=head,old_namespace_inventories_match=True,new_actual_namespace_exists=False,
 protected_processes='No process operations performed; resource/identity observations remain a root release precondition',
 actual_network_requests=0,actual_posts=0,actual_opportunities_consumed=0))
manifest=h.read(P/'manifest.json')
manifest['test_summary']=summary
manifest['test_artifacts']={n:h.sha(P/n) for n in ('argv.json','tests.log','tests.xml','tests.exit')}
manifest['preservation_after_sha256']=h.sha(P/'preservation-after.json')
core.save(P/'manifest.json',manifest)
# Checksum receipt covers root delivery files, independently binds final manifest/tests.
checksums={p.name:h.sha(p) for p in P.iterdir() if p.is_file() and p.name!='checksums.json'}
core.save(P/'checksums.json',checksums)
report=core.CHECKOUT/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101/task-2-local-role-probe-report.md'
report.write_text(f'''# T2 local-role offline preparation

READY_FOR_INDEPENDENT_SPEC_QUALITY_REVIEW. This is throwaway experimental preparation only. No actual authority has been issued, no actual socket or model request was made, and `{h.ACTUAL}` remains absent. No opportunity was consumed. S2 and first S3 remain permanent FAIL and two spent; only a separately authorized S4 then conditional S1 could use the remaining cumulative cap of four. This does not prove the hypothesis, a product fix, a full report, or original E02 acceptance.

## Exact review and baseline bindings

- Design: `0a95e725c98a9e255059a93bb96e7305fc516c3d1b033c93d3f8a28b7fc10abb`.
- Independent design SPEC/QUALITY PASS: `e7abb30a822a1171d68d9acebb27c0f2b1507a38b34f557bba4c22aadc6c3400`.
- Frozen original core: `4122c8d0c288689f31899fc59cebf7aabbcc546c46342071134af712d4a9863e`; original launcher: `d72ae47f3e8fa74f1648413ad538e6b75e597a459a9c73ec73e8de88cb0c4aa2`.
- S2 first outcome: `597467ca6cd98cf271eaa6a5a62181a614023c591b2a87d66c75eb4df42739aa`; first S3 outcome: `c8c64b4f9fdff1c3e28d326309d605d3d4ca3d0536e7a559f7fd4a082e6aaa72`.

Both entire historical packets and complete original namespace inventories are bound. The new launcher checks every old inventory entry and rejects unexpected or missing entries, including zero-POST attempts. Old launcher bytes and their permanent stop remain unchanged.

## Minimal content and entrypoint changes

`core.diff` has three hunks only: the exact reviewed generic system substring replacement; `original_query` to `background_original_query` at the same construction position; and direct CLI refusal. All material, projection, cards, schema, citation ranges, SDK caller query/history, owners, binding, workers, scanner input/output, one-turn request option, native options, timing and deadline logic are unchanged. No further parser/guard key references needed editing: the only original-query field construction was the renamed user field. Historical `main` is retained for mechanical diff clarity but direct execution unconditionally refuses before its parsing or loading; the sanctioned launcher calls only the unchanged functions.

`launcher.diff` records changes from the frozen launcher. New mode is `local_role_sdk_prefix`; new namespace is only `local-role-actual/{{S4|S1}}/<rootunique>`; exact HEAD `{head}` and digest stay fixed. Source S2/S3, reordered/skipped/retried source, omitted existing attempts and spent/count mismatches refuse before namespace creation. Each created namespace consumes one opportunity, even zero POST. S1 needs the actual new S4 outcome with confirmed one POST/intention, nonempty facts and a separate bound independent factual PASS. Independent preparation SPEC/QUALITY PASS must bind this final manifest hash before a root authority can validate. This file issues none. Releases must be root-serialized; it is not a cross-process authority service.

The launcher adds a public HTTPX request hook that only compares, without rewriting, the impending native entity against the frozen secured projection and options. Only issued schema-token slots normalize to the ordinary UUID sentinel. Raw projection is also checked against the frozen template before reporting mechanical success. Existing `run_prefix`, `make_owner`, `socket_guard`, `observe_http` and real SDK mechanics are reused. No vendor code, HTTP entity, caller history, product or second core implementation is patched.

## Frozen input proofs

Both `S4-template.json` and `S1-template.json` were frozen before any actual exposure. Each contains full source, raw/secured messages, scanner lineage, view, omitted ranges, eligible cards and unchanged strict schema. `projection-proof.json` verifies the old/new messages differ only in the approved system substring and user field name, with identical decoded UTF-8 query bytes. Query SHA256 is `d359dcde318278823ad1e9c48b70c604f0d614152c0b0ec26b88ca310821f61e`.

S4: body `a02c228a40f321cedd495c674f2bed5ff47866d8cc0561e71d0459d479a3c365`, 367 visible/eligible lines, 48 cards. S1: body `f1ee410e63c3d7ce185242ceab66f63fbcae48a0e356454e060a562de485af77`, 205 visible/eligible lines, 48 cards. UUID sentinel is `00000000-0000-0000-0000-000000000000`; only schema-token slots vary in an actual run. Prompt text and all input/template hashes are frozen in the manifest.

## Admission and observational limitations

The same root-bound snapshot must be <=30 seconds old at admission and immediately before SDK bootstrap, with RAM >=12 GiB, commit headroom >=16 GiB and free GPU >=8 GiB, exact HEAD/digest/protected-five identity, source21 match and explicit `controller_readonly_metadata_not_trial.loaded.models == []`. Missing/stale/foreign/warm proof refuses; capacity is not guaranteed. No warming, unload, restart, keepalive change or allocated-VRAM add-back exists. No runtime metadata GET was made in preparation.

The existing readonly `W/capture-prefix-runtime.py` already supplies the named loaded-model and source21 fields. For future root release its receipt must additionally bind `run_root` to the exact new controller-unique canonical path, before hashing it into authority; its existing source_id must match. This requirement is documented here and enforced rather than modifying the capture helper or collecting live state now. Root must supply fresh observations using the same readonly semantics. Preparation does not claim current hardware/process capacity or independent hardware attestation.

Native limits stay A2048/N4/k5, predict480/ctx16384/temp0, think/stream/truncate/shift false, one native POST, two trial metadata GETs, separate single bootstrap GET, request-local one SDK turn, zero writer/ack/files and the unchanged 36-second stage slice covering projection, scanners, metadata, native load/generation, secured validation and caller END. The original t0 still precedes frozen material loading and ask-lock acquisition, and the original overall timing/reserve logic is untouched.

## Offline verification

Fresh focused run: {summary['tests']} passed, zero failure/error/skip, pytest time {summary['time']} seconds, shell exit 0. `argv.json` records exact interpreter/argv/cwd/environment; `tests.log`, `tests.xml`, `tests.exit` are the final run receipts. The runner uses the installed SDK virtual environment, disables pytest plugin autoload and bytecode, places temp/cache/SDK homes under this new preparation and denies real connect/connect_ex/DNS in autouse fixtures. All native requests are handled by HTTPX MockTransport.

Both S4 and S1 happy cases exercise the actual SDK/scanners/metadata and one real stage worker/caller END and SDK turn with no writer effects; wire hooks compare their actual mock-dispatched requests with both frozen templates. Their mechanically derived witness payloads are test fixtures only and never future prompt hints or factual oracles. The retained focused core tests prove raw schema length rejection, duplicate fields/facts, foreign/replayed/binding-tampered tokens, changed/hidden line rejection, sampler-vs-strict schema, absolute late response/END and durable POST-intent expiry with zero send. Launcher tests prove cold minima, warm/stale/missing/root/source21 proof rejection, full old packet tamper, unexpected old inventory, omitted new zero-POST namespace, source/order/cap/prior PASS binding, optimization refusal before CLI/files, and real Windows junction rejection with unchanged outside contents. Metadata cannot make a third GET and a consumed POST cannot repeat. No 293-product rerun was performed.

Initial packaging verification exposed tuple-vs-JSON-list comparison and a shared token-shape alias in the new comparator. They were corrected in the new freezer/comparator only; historical bytes and unchanged core semantics were not edited. Earlier failed receipts are retained under temp; final receipts bind the corrected code. No factual acceptance is inferred from the scripted mock.

## Preservation and delivery hashes

`preservation-before.json` and `preservation-after.json` verify {len(before)} original files unchanged, complete old preparation file inventories unchanged, complete both old attempt inventories unchanged, source21/frozen5 unchanged and exact HEAD. No protected/background process action, product/source10/SDK/default/model/KWS/OS/queue/git mutation or commit/push occurred. No new actual namespace exists.

- Final manifest SHA256: `{h.sha(P/'manifest.json')}`.
- New helper SHA256: `{h.sha(P/'run_local_role_core.py')}`.
- New launcher SHA256: `{h.sha(P/'run_local_role_prefix.py')}`.
- S4 template SHA256: `{h.sha(P/'S4-template.json')}`.
- S1 template SHA256: `{h.sha(P/'S1-template.json')}`.
- Prompt SHA256: `{h.sha(P/'prompt.txt')}`.
- Final tests XML SHA256: `{h.sha(P/'tests.xml')}`.
- Checksums receipt SHA256: `{h.sha(P/'checksums.json')}`.

All deliverables are under `{P}` plus this authorized W report. Independent preparation SPEC/QUALITY review and separate explicit root release remain required. An actual mechanical result would remain PENDING_INDEPENDENT_FACT_REVIEW; any unused, refusal, unknown/interrupted/failure or missing coverage stops the new question. Two possible prefixes cannot satisfy >=3-source original E02, full-report delivery or original S2/S3 counterfactuals. The local-role causal hypothesis remains untested.
''',encoding='utf8')
print(json.dumps(dict(status='READY_FOR_INDEPENDENT_REVIEW',manifest=h.sha(P/'manifest.json'),helper=h.CORE_HASH,launcher=h.sha(P/'run_local_role_prefix.py'),tests=summary,old_files_preserved=len(before),actual_namespace_exists=h.ACTUAL.exists(),report=str(report)),indent=2))
