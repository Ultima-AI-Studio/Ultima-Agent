import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent; V=R.parent; C=Path.cwd()
W=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101'
J=lambda p:json.loads(p.read_bytes())
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=J(R/'readback.json'); post=J(R/'post-commit.json')
p=W/'task-2-navigation-candidate-fixwave-report.md'
lines=['# Source10 candidate fix wave 1','',f"Base {a['base']} → commit {post['head']} on codex/jarvis-work-navigation-v3-source10. One combined implementation commit. The tracked worktree and index are clean.",'',
'## C1 — original deadline at publication','',
'WorkService calls the research ledger’s existing admit_ack after real final packet and artifact verification and source selection, immediately before publishing succeeded. It samples the original monotonic deadline even after the runner sealed the ledger. The ordinary exception path retains the completed effect, its verified artifact and public identities, and returns needs_attention. There is no replay, extra transport request or new deadline.',
'',
'The parametrized test uses actual SDK navigation, mock inference transport, configured Guardrails, browser fixture, writer and filesystem. All author and ACK requests ran at controlled time 0 with deadline 260. The wrapper first calls the original verifier and retains its result, then advances time after the real final readback. The frozen-before/after sample includes the path, digest and dispatch, report, adapter and file IDs. All three cases sent exactly 15 requests (5 chat generations), kept one completed effect and one reopened file. The first RED passed before the boundary but returned succeeded incorrectly at and after it. Final reopening yielded:','']
for x in sorted(a['c1_readback'],key=lambda x:x['after']):
    lines.append(f"- {x['boundary']} {x['after']!r} — {x['status']}, error {x['error']!r}, SHA-256 {x['artifact']['sha256']}, file {x['effect']['path']}, report {x['effect']['report_call_id']}, file ID {x['effect']['file_call_id']}, dispatch {x['effect']['dispatch_id']}, adapter {x['intent']['adapter_uuid']}.")
lines+=['','## C2 — validate the final answer before promotion','',
'The view checks for a nonblank parsed final after schema, configured scanning, raw equality and transport return checks, before assigning the secured envelope or promoting the pending page. The fourth raw chat response in the new matrix case is a one-space final; it passes through the actual parser and guard, without the history/schema mutation branch. The first RED produced the intended Empty research final answer error yet promoted pages [1, 2, 3]. GREEN confirms only [1, 2], three genuine inspect START/END pairs, four attempted generations, three secured timeline entries, no fourth dispatch, write effect, file or final runtime proof. The four valid writer chains passed.',
'','## Test process receipts','',f'Evidence root {V}. Each receipt binds the invocation, environment, times, stdout, stderr, JUnit and source maps. The fixed -B -X utf8 H venv runner hash is 60f6ea3d157969dcaa4eebef474a62642da6f02963cb8a87b405217f788ac32c. Each test receipt was independently reopened and rehashed. Ordered invocations and output identities follow.','']
for stage,r in a['receipts'].items():
    d=Path(r['path']).parent
    lines += [f"### {stage}",'',f"Receipt {r['path']} SHA-256 {r['sha256']}",'',subprocess.list2cmdline(r['argv']),'', (d/'stdout.log').read_text(encoding='utf8').strip().splitlines()[-1], '',json.dumps(r['files'],sort_keys=True),'']
lines+=['All 475 prior suite-qualified identities and the 65 original research purposes and exact source bytes are retained. All eight compatibility IDs are retained. Compatibility logged one anyio pytest assertion-rewrite warning. The full suite and compatibility suite each ran once on final bytes. Neither final suite skipped or xfailed any case.','','## External readback','']
for x in J(R/'external-verification.json')['cases']:
    folder=Path(x['folder']); manifest=J(folder/'packet-manifest.json')
    lines.append(f"- {x['variant']} — {x['artifact_bytes']} bytes at {x['artifact']}, SHA-256 manifest {H(folder/'packet-manifest.json')}. {json.dumps(manifest,sort_keys=True)}")
lines+=['','The separate stdlib fractional oracle reopened six captures and 90 prepared HTTPX request records against the final inputs, checked binary64 caps, ordering, staged and final replay and reopened file hashes. Positive and fractional readbacks ran after pytest exited.','']
for name in ['verify_external.py','external-verification.json','verify_fractional.py','fractional-verification.json','readback.json','staged-check.json','post-commit.json']:
    lines.append(f'- {R/name} SHA-256 {H(R/name)}')
lines+=['','## Commit and scope','',f"All 31 final inputs match before/after/current, all 30 tracked inputs match HEAD blobs, and {post['untracked_source_paths'][0]} remains byte-bound and untracked. All 22 installed SDK sources, frozen five, approved design, plan, protocol, prior report and review inputs were rehashed. Exact scoped diff and whitespace checks passed. Changed Git blob SHA-256 values:",'',json.dumps(post['blob_sha256'],indent=2),'',
'The code wave is ready for the original whole-candidate reviewer’s scoped rereview. Mechanical scripted SDK and transport proofs do not establish model factual quality, original-corpus acceptance, real-network success or production readiness. Task 4, real 8B execution, T2 acceptance, T3 and release remain pending. No harness, model endpoint, product default, dependency, scanner, SDK, queue, process, UI or audio changes. E02/T2 NOT_PASSED.']
with p.open('x',encoding='utf8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
(R/'report.md').write_bytes(p.read_bytes())
print(str(p),H(p))
