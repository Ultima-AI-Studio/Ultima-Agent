"""Seal fix round 1/5; read only P1/history and append authorized W report."""
from pathlib import Path
import json,hashlib,difflib,xml.etree.ElementTree as ET
import run_local_role_prefix as h
P=Path(__file__).parent;A=P.parent/'local-role-preparation';core=h.frozen_core()
old=h.read(P/'preservation-before.json');prior=h.read(P/'p1-preservation-before.json')
for path,digest in {**old,**prior}.items():h.checked(path,digest)
assert {str(p) for p in A.rglob('*') if p.is_file()}==set(prior)
assert not (P.parent/'missing').exists()
assert not h.ACTUAL.exists()
for root,entries in h.read(P/'old-namespace-inventories.json').items():assert h.namespace_inventory(Path(root))==entries
for name in ('S4-template.json','S1-template.json','prompt.txt','projection-proof.json'):assert (P/name).read_bytes()==(A/name).read_bytes()
core.save(P/'p1-preservation-after.json',dict(all_files_unchanged=True,file_count=len(prior),sha256=prior,
 original397_unchanged=True,original397_sha256=old,templates_byte_identical=True,actual_namespace_exists=False,actual_opportunities_consumed=0))
lines=[]
for name in ('run_local_role_core.py','run_local_role_prefix.py','test_local_role.py','test_core_boundaries.py','freeze_local_role.py'):
 lines.extend(difflib.unified_diff((A/name).read_text('utf8').splitlines(True),(P/name).read_text('utf8').splitlines(True),fromfile='P1/'+name,tofile='P2/'+name))
(P/'p1-to-p2.diff').write_text(''.join(lines),encoding='utf8')
suite=next(ET.parse(P/'tests.xml').getroot().iter('testsuite'));summary=suite.attrib
assert int(summary['tests'])==76 and summary['failures']==summary['errors']==summary['skipped']=='0'
assert (P/'tests.exit').read_text()=='0'
p1_cases={x.attrib['name'] for x in ET.parse(A/'tests.xml').getroot().iter('testcase')}
p2_cases={x.attrib['name'] for x in ET.parse(P/'tests.xml').getroot().iter('testcase')}
assert len(p1_cases)==72 and p1_cases<=p2_cases
core.save(P/'test-purpose-preservation.json',dict(all_original72_retained=True,original=sorted(p1_cases),added=sorted(p2_cases-p1_cases)))
m=h.read(P/'manifest.json');m.update(test_summary=summary,fix_round='1/5',independent_review_required=True,
 p1_manifest_sha256=h.sha(A/'manifest.json'),fix_review_verdict_sha256=h.sha(h.E.parent/'local-role-preparation-review-1/verdict.json'),
 fixes=['F1 canonical proof before intent/final deadline/admission/client send; no HTTP hook','F2 append failure disposition while retaining complete returned core packet'],
 dispatch_semantics='native_posts counts public HTTPX send calls, not server delivery; durable intents and post admissions separate; unknown no-core-return counters/effects remain null',
 test_artifacts={n:h.sha(P/n) for n in ('argv.json','tests.log','tests.xml','tests.exit')})
# Bind the extra receipts and relevant independent finding without cycles.
for name in ('p1-to-p2.diff','p1-preservation-before.json','p1-preservation-after.json','test-purpose-preservation.json','seal_r2.py'):
 m['frozen_files'][str(P/name)]=h.sha(P/name)
for name in ('review.md','verdict.json','reproduction.json'):
 path=h.E.parent/'local-role-preparation-review-1'/name;m['frozen_files'][str(path)]=h.sha(path)
core.save(P/'manifest.json',m)
for path,digest in m['frozen_files'].items():h.checked(path,digest)
core.save(P/'checksums.json',{p.name:h.sha(p) for p in P.iterdir() if p.is_file() and p.name!='checksums.json'})
report=core.CHECKOUT/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101/task-2-local-role-probe-report.md'
previous=report.read_bytes();previous_hash=core.sha(previous)
argv=h.read(P/'argv.json')
append=f'''

# Fix round 1/5 · P2 offline preparation

READY_FOR_INDEPENDENT_SPEC_QUALITY_REVIEW. P1 above remains immutable historical preparation and was independently REVISE for Important F1/F2. This appendix supersedes its dispatch-hook and post-audit-error mechanics only. P2 resides exclusively at `{P}`; old S2/S3 remain permanent FAIL, cumulative spent stays 2/4, no S4 release/authority or actual namespace exists. Independent review is still required.

## Reviewed defects and bounded correction

Independent review `T2/local-role-preparation-review-1/review.md`, verdict and reproduction were read before this correction. F1: "post-admission template verification permits late POST and overcounts hook rejection". F2: "post-run raw audit failure overwrites detailed outcome". Root accepted both Important findings and explicitly allowed the necessary mechanical guard diff in the owned helper, beyond its two already-approved visible input changes.

For F1, a controller-captured canonical-proof callable is passed through the owned `run_prefix`/`NativeLeaf` boundary. It verifies exact raw projection, secured projection and typed native entity before request construction, durable POST intent and final send admission. The HTTPX request hook is removed completely. Proof completion has an immediate absolute-deadline stamp; request construction/serialization is also before intent/final admission. Intent I/O remains durable and inside budget. Fresh remaining time and request timeouts are computed after all proof/construction/intent I/O, before the public send. No extra template I/O, expensive comparison or newly added callback exists after final admission. No vendor method or HTTP entity is patched or rewritten.

`native_post_intents` records consumed send intents, `native_post_admissions` records final admitted POSTs, and `native_posts` counts calls to public HTTPX send; its explicit `native_dispatch_count_kind` prevents treating this as server delivery confirmation. Observer rows are transparent send observations and never a fallback native-post count. A rejected projection or expired canonical proof records zero intent, admission, send and MockTransport calls; namespace consumption would still be permanent if an actual namespace had existed. Network errors remain ambiguous about delivery rather than silently becoming success or permitting retry.

For F2, the outer handler preserves the entire returned core packet in place, appends `audit_failures`, records `mechanical_status_before_audit`, sets overall FAILED and allows normal owner closure. Stage payload, consumed/confirmed state, observations/effects, raw/secured envelopes, SDK events/result, timeline, wire and intent/admission/send counters remain intact. When there is no returned observed packet, counters/effects remain unknown/null, with an explicit unknown observation; the launcher does not infer zero effects or dispatch from observer rows.

`p1-to-p2.diff` is the readable exact P1/P2 code/test/freezer difference. `core.diff` also compares the frozen original core with P2 and identifies the authorized mechanical guard additions. Prompt, query, source, visible lines, cards, strict/sampler schemas, model/config/options, authorization gates, security scanners and actual SDK stage/tool/END logic are unchanged. Both S4/S1 template files, prompt text and projection proof are byte-identical to P1; no source-specific hint or factual oracle was introduced.

## Fresh focused verification and exact receipts

Final command through the same installed environment:

```text
H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B {P}/freeze_local_role.py
H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B {P}/run_offline_tests.py
```

The runner's exact subprocess argv is:

```json
{json.dumps(argv['argv'],ensure_ascii=False,indent=2)}
```

Exact relevant final stdout:

```text
{(P/'tests.log').read_text('utf8').strip()}
```

Exit 0; {summary['tests']} passed; failures/errors/skips all zero; XML time {summary['time']} seconds. `argv.json` binds exact cwd/env, including owned temp/cache/SDK-home, offline flags, disabled pytest plugin autoload and bytecode. `tests.log`, `tests.xml` and `tests.exit` are fresh P2 receipts. No 293-product rerun occurred. The autouse real socket/DNS deny remains enabled; all SDK/native HTTP requests use installed HTTPX MockTransport.

All 72 P1 test purposes are retained (`test-purpose-preservation.json`). Four new cases cover delayed canonical proof (35.99 -> 37 with d36, zero transport/observer/intent/admission/send); mismatched projection with zero transport/observer/intent/admission/send; strict positive canonical proof dispatch within budget; and a real installed-SDK completed packet subjected to forced post-audit failure, saved/reopened with all stage, wire, SDK/timing, counters, envelopes and closure intact. A labelled synthetic nonempty-effects sentinel verifies that the fallback cannot erase observed effects. Existing delayed-intent expiry, late response/END, metadata/POST caps, real SDK S4/S1 and all old admission/reparse/security purposes continue passing. The two previous green P2 receipts are retained under `temp` because later counter labeling and nonempty-effects verification warranted the final fresh run.

## Immutable preservation and scope

P1 exact complete file set and hashes: {len(prior)} files unchanged. The original397 hash map also remains unchanged, including old preparations, full S2/S3 packets, source21/frozen5. Old namespaces still match complete frozen inventories. Both template byte identities are independently checked by the freezer and sealer. `p1-preservation-before.json` and `p1-preservation-after.json` retain the evidence. No actual socket/GET/POST/model request, opportunity consumption, OS/background process action, product/default/SDK/KWS/git/queue change or commit/push was performed.

Scope transparency: one new builder text file was accidentally staged at `E/missing`, immediately moved into P2 before execution, and the builder removed after use. No outside file remains, no historical file was overwritten and all historical hashes match. Remaining writes are P2 plus this report append. The pre-append report prefix SHA256 is `{previous_hash}` and is retained verbatim.

## P2 final hashes and remaining concerns

- Manifest: `{h.sha(P/'manifest.json')}`.
- Helper: `{h.sha(P/'run_local_role_core.py')}`.
- Launcher: `{h.sha(P/'run_local_role_prefix.py')}`.
- S4 template: `{h.sha(P/'S4-template.json')}`.
- S1 template: `{h.sha(P/'S1-template.json')}`.
- P1-to-P2 diff: `{h.sha(P/'p1-to-p2.diff')}`.
- Final JUnit XML: `{h.sha(P/'tests.xml')}`.
- Checksums receipt: `{h.sha(P/'checksums.json')}`.

No authority is issued. Existing independent preparation review and separately root-bound fresh cold observations remain preconditions; root must serialize releases and bind the exact new manifest/review/hashes. Two remaining possible prefixes cannot establish original >=3-source E02 or any S2/S3 counterfactual. Native dispatch counters do not prove server delivery; mock mechanical success does not establish factual or coverage PASS. Local-role hypothesis remains untested. No new actual namespace exists.
'''
with report.open('ab') as out:out.write(append.encode('utf8'))
assert report.read_bytes()[:len(previous)]==previous
print(json.dumps(dict(status='READY_FOR_INDEPENDENT_REVIEW',manifest=h.sha(P/'manifest.json'),helper=h.sha(P/'run_local_role_core.py'),launcher=h.sha(P/'run_local_role_prefix.py'),p1_files_unchanged=len(prior),old397_unchanged=True,tests=summary,actual_namespace_exists=h.ACTUAL.exists(),report_sha256=h.sha(report)),indent=2))
