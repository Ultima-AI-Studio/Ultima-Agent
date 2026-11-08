"""Start authorized Task3 only after exact product review and local readback."""
from pathlib import Path
import ast,hashlib,json,subprocess
B=Path(__file__).resolve().parents[1];T=B.parent;R=B.parents[4]
O=T/'e02-claim-generation-controlled-preparation-20261108-r1'
N=T/'e02-source-grounding-controlled-preparation-20261108-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
head=load(B/'verification/final-readback.json')['heads']['candidate']
assert load(B/'verification/final-readback.json')['verdict']=='PASS_FINAL_LOCAL_READBACK'
assert load(B/'review/independent-preparation-review.json')['candidate']==head
N.mkdir(exist_ok=False)
for folder in ('verification','inputs','review'):(N/folder).mkdir()
plan=R/'docs/plans/jarvis-work-e02-source-grounding-controlled-entry-plan-20261108.md'
text=f'''# E02 evidence-first and source-reserve controlled entry plan

> Use superpowers:executing-plans. Root implements inline. One independent exact plan review, then one exact preparation review; never concurrent audits. Necessary reviews are authorized by call_3d33440cc40c401ea7a2cf11c8bc2bcf.

Goal: finish already approved product plan Task3 by binding frozen {head} to the original controlled entry and publish a concrete proposal with zero actual allocation.

## Scope and fixed contracts

- Product C=C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-grounding-r1/UltimaAgent, B={B.as_posix()}, candidate {head}; require exact independent preparation PASS, local publication and final readback.
- New entry N={N.as_posix()}; predecessor O={O.as_posix()}, old product C:/Users/Administrator/.codex/worktrees/jarvis-e02-claim-generation-r1/UltimaAgent. Preserve old preparation, result and actual1496a844-668d-407a-a91b-89be246ba05b FAIL_CONFIRMED, all dependencies and15 unrelated files.
- Only current qwen3-8b-uncensored and digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330, original question, original four-source corpus9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002. CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8; service260/client300/rootwork275/cleanup310/seal315; context16384/messages32768/entity49152; writer-cap2048/read-only and ACK256. Existing writer-eligible phase rules unchanged. Full facts/citations/coverage/delivery/timing/cleanup review remains.
- No product modification, model/network/UI/audio/production service action, release/controller-authority/actual/native-preflight/actual ledger. Runtime status PENDING_FRESH_ACTUAL_PREFLIGHT. Historical seven identities/native snapshots are not current proof; original actual preflight remains unchanged.
- Root implements, at most2 guarded offline shards and1 independent reviewer. No download/install/delete/remote push. Previous push approval rejection is preserved; no alternate route.
- User cleared the goal registry during this offline repair. Do not recreate a goal. This explicit approved task continues; E02 remains0/3, T2/Owner not passed. Prior E01/E03 credit does not transfer.

## Review focus

1. All79 frozen product sources pinned under C. Model, corpus, budget and dependency metadata byte-equal to O, except candidate/path/hash binding. Product1022 checks are frozen prior evidence and not added to fresh entry count.
2. Entry/adapter/bindings function and class AST unchanged. Preparation decision uses the original content-derived binding with source_question_id identifying the real platform authorization; actual/result-review counts0 cannot pass the actual-grant predicate.
3. No historical runtime proof upgraded to current. Future allocated run must pass original fresh identity/listener/model/corpus/preflight gates within the original clock. A failure consumes that separately allocated single case, no retry.
4. Fresh original eight groups, expected350 unique checks (289adapter,16bindings,34entry,11boundary), same source hashes, no failure/error/skip, original audit guard. Fixture changes only if old sampler shape/read coverage conflicts, preserving test purposes and all negative assertions.
5. Evidence-before-claim and read opportunities do not prove fact entailment, correct page choice or full original-question coverage. Dense multi-source cards can hit the existing prompt cap; no cap enlargement. Previous written-but-content-failed report and nine fact judgments remain.

## Task1: Register, rebind, offline checks

Files: N inputs/code/harness/tests/verification/review, plan/ledger and original controls.

- Register DoR and fresh read-only codex exec worker observation; preserve current-run including T2/t2 and last_actual. Independent exact plan PASS before rebind.
- Copy only named O entry, bindings, adapter, test and guarded runners; no old grant or actual artifact. Preserve content-derived preparation binding from inception. Replace candidate/path/hash constants and79-source map. Compare inherited input metadata and core AST.
- Run base-a/base-b/recovery/export-green/failure-export-green/bindings/entry/boundary with max2 shards. Keep all failed receipts; necessary fixture migration within this scope, no deleted assertions or extra exclusions. Read back JUnit identities and hashes; record OS packets unmeasured.
- Preserve product package and prior entry/result/seal/dependencies/unrelated files. Record historical runtime references with current_runtime_verified=false.
- Prepare specific execution proposal, report and local closeout/publication/readback helpers. Seal complete checked preparation. No production or native call.

## Task2: Independent review and local publication

- Exact manifest/candidate independent review must be root-independent/PASS_PREPARATION_ONLY/actual_run_authorized=false; repair proven preparation issues only and rebind/review exact bytes if needed.
- After PASS, create original harness preparation approval; use read_ready/read_release solely to prove missing grant refusal. Never call run_once/run_released.
- Register READY_OFFLINE_AWAITING_EXPLICIT_ALLOCATION_AND_FRESH_PREFLIGHT, actual/result-review0, preserved last_actual, goal registry cleared. Mirror plan/report/execution proposal, scoped local commits and tags, final Git/disk/manifest readback.
- Preserve skill ledgers by copying; no deletion. Final proposal requests a separate one-case allocation and one independent result review, not a routine implementation permission.

## Rulings

This implements the user's approved offline scope and the reviewed product plan Task3. No additional routine confirmation. Official allOf encoding is frozen product behavior; preparation cannot claim installed native compatibility or improved research quality. Entry freshness remains separately pending. Existing content-derived decision binding avoids the predecessor's known zero-allocation identity defect without changing core functions.
'''
with plan.open('x',encoding='utf8',newline='\n') as f:f.write(text)
s=(O/'verification/register.py').read_text('utf8')
for a,b in {
    'e02-claim-generation-contract-20261108-r1':B.name,
    'e02-output-structure-controlled-preparation-20261108-r1':O.name,
    'jarvis-work-e02-claim-generation-controlled-entry-plan':'jarvis-work-e02-source-grounding-controlled-entry-plan',
    'jarvis-work-e02-claim-generation-contract-plan':'jarvis-work-e02-source-grounding-coverage-plan',
    'jarvis-work-e02-claim-generation-contract-proposal':'jarvis-work-e02-source-grounding-and-coverage-proposal',
    'd8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b':head,'d8f8d97':head[:7],
    '1004':'1022','SOURCE35':'SOURCE37','CLAIM_GENERATION':'SOURCE_GROUNDING',
    'call_5411de619a6c4de0bab414126a228c7d':'call_3d33440cc40c401ea7a2cf11c8bc2bcf',
    "goal_registry_status='blocked',goal_status='blocked'":"goal_registry_status='cleared_by_user',goal_status='none'"
}.items():s=s.replace(a,b)
ast.parse(s);(N/'verification/register.py').write_text(s,encoding='utf8',newline='\n')
print(json.dumps(dict(entry_root=str(N),plan=str(plan),candidate=head,status='AWAITING_FRESH_WORKER_OBSERVATION_AND_PLAN_REGISTRATION')))
