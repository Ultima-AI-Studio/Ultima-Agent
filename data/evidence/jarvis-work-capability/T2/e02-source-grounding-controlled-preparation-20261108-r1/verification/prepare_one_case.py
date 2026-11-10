"""Bind the user's newly allocated single case; keep the frozen entry unchanged."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
O=T/'e02-claim-generation-controlled-preparation-20261108-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-grounding-r1/UltimaAgent')
M=Path('H:/UltimaAI/ultima-docs-repo')
HEAD='43da3f014a763b8ea3963872a8f1ce8ebea77531'
MANIFEST='f019de1da34ca272a48172493ad857b228d449d0e4bd817c1f8bfd9bba8d1eec'
REVIEW='6618da921a0e7c92d69fd0f08d41d63ec7bd292e5ed4c095cbfc706d9506be3b'
QUESTION='call_7004c6eafaca48e3a6f19dd87f59d024'
TEXT='候选 43da3f0 的离线补修、1,022 项产品相关检查、350 项入口检查、独立准备审查及本地提交/tag/镜像读回已完成（项目 9ffd50ea，镜像 923d12f）。是否按[执行提案](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-source-grounding-controlled-preparation-20261108-r1/execution-proposal.md)，明确分配一例当前 8B 的原题四来源研究，以及一次只读独立结果复核？保持原预算和完整验收要求，先走原入口的新鲜运行态核验，失败不重试，无 UI、音频或生产服务操作。需要此次分配，因为你明确要求新候选实跑另行分配，当前额度为 0。全局汇总因另一工单的非法状态未刷新，已单独保留失败记录，本工单登记正确。'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True,creationflags=subprocess.CREATE_NO_WINDOW).strip()
assert sha(N/'manifest.json')==MANIFEST and sha(N/'review/independent-preparation-review.json')==REVIEW
final=load(N/'verification/final-readback.json');pub=load(N/'verification/publication-readback.json')
assert final['verdict']=='PASS_FINAL_LOCAL_READBACK' and final['publication_sha256']==sha(N/'verification/publication-readback.json')=='8b26e706c45b85f5af637104ae79ab6a14f500d06dbd199c9f40d6ac50e86cc2'
for root,key in ((R,'project'),(M,'mirror')):
    git(root,'merge-base','--is-ancestor',final['heads'][key],'HEAD')
    changed=set(git(root,'diff','--name-only','-z',final['heads'][key],'HEAD').split('\0'))-{''}
    own={Path(p).relative_to(root).as_posix() for p in pub['file_sha256'] if Path(p).is_relative_to(root)}
    assert not changed & own
assert git(C,'rev-parse','HEAD')==HEAD and not git(C,'status','--porcelain')
assert not git(R,'diff','--cached','--name-only') and not git(M,'diff','--cached','--name-only')
for name,h in load(N/'manifest.json')['files'].items():assert sha(N/name)==h,name
for name,h in load(N/'inputs/input-manifest.json')['files'].items():assert sha(Path(name))==h,name
for name,h in pub['file_sha256'].items():assert sha(Path(name))==h,name
worker=json.loads((N/'verification/allocated-worker-observation.json').read_text('utf-8-sig'))
assert worker['this_order_worker_count']==0 and worker['count']==worker['foreign_worker_count']<=2
assert not any((N/p).exists() for p in ('release','actual','controller-authority','native-preflight','controller-ledger.json','review/independent-result-review.json'))
save(N/'verification/actual-admission-readback.json',dict(verdict='PASS_CURRENT_IMMUTABLE_PREPARATION_AND_INPUTS',candidate=HEAD,manifest_sha256=MANIFEST,review_sha256=REVIEW,heads=final['heads'],manifest_members=179,input_files=1606,source_files=79,model_calls=0,actual_invocations=0,runtime_status='FRESH_CHECKS_DEFERRED_TO_ORIGINAL_ALLOCATED_ENTRY',worker_observation_sha256=sha(N/'verification/allocated-worker-observation.json'),recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
changes={
 'call_c910dd9e4819410492607baac9ed63bf':QUESTION,
 'd8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b':HEAD,'d8f8d97':'43da3f0',
 'c36908a9a99f290889cb420613a93d70611386ace39765e8b970f55f5ea1f16a':MANIFEST,
 '112435823a9ab087ede87457026e0a78d11659e39a1cff22a2b14dafa767af5d':REVIEW,
 '13699f8d7b523b420cd5c67f0a992e5e581a0125':final['heads']['project'],
 'jarvis-e02-claim-generation-r1':'jarvis-e02-source-grounding-r1',
 'e02-claim-generation-controlled':'e02-source-grounding-controlled',
 'e02-claim-generation-contract-20261108-r1':'e02-source-grounding-coverage-20261108-r2',
 'SOURCE35_E02_CLAIM_GENERATION':'SOURCE37_E02_SOURCE_GROUNDING',
 'source35_preparation':'source37_preparation','claim_generation_one_case':'source_grounding_one_case',
 'claim generation':'source grounding',
 'ultimaagent-e02-claim-generation-candidate':'ultimaagent-e02-source-grounding-candidate',
 '/root/review_e02_claim_generation_actual_result':'/root/review_e02_source_grounding_actual_result',
 'c4caa739-c466-44f3-866b-0c57ea8c5e40':'1496a844-668d-407a-a91b-89be246ba05b',
}
bindings={}
for name in ('register_allocation.py','run_allocated_case.py','seal_allocated_result.py','register_result_audit.py','verify_result_preservation.py'):
    source=O/'verification'/name;target=N/'verification'/name;s=source.read_text('utf8')
    for before,after in changes.items():s=s.replace(before,after)
    if name=='register_allocation.py':
        node=next(x for x in ast.parse(s).body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id=='question')
        lines=s.splitlines(keepends=True);lines[node.lineno-1:node.end_lineno]=['question='+repr(TEXT)+'\n'];s=''.join(lines)
        s=s[:s.index("q=Path('H:/UltimaAI/_shared/queue')")]+"save(N/'verification/allocation-queue-refresh.json',dict(status='NOT_RERUN_KNOWN_INVALID_OTHER_ORDER_STATE',aggregate_regenerated=False,prior_failure_sha256=sha(N/'verification/queue-refresh.json'),canonical_registration_updated=True))\nprint(json.dumps(dict(question_id=decision['question_id'],actual_allocated=1,review_allocated=1,invoked=0),ensure_ascii=False))\n"
    if name=='register_result_audit.py':
        s=s[:s.index("q=Path('H:/UltimaAI/_shared/queue')")]+"save(N/'review/result-audit-queue-refresh.json',dict(status='NOT_RERUN_KNOWN_INVALID_OTHER_ORDER_STATE',aggregate_regenerated=False,prior_failure_sha256=sha(N/'verification/queue-refresh.json'),canonical_registration_updated=True))\nprint(json.dumps(dict(summary=summary,result_manifest_sha256=sha(manifest_path),review_allocated=1,actual_remaining=0),ensure_ascii=False))\n"
    if name=='verify_result_preservation.py':
        old="for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==h,name"
        assert old in s
        s=s.replace(old,"for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():\n        if name!='docs/tracker/北极星上线任务清单.html':assert sha(R/name)==h,name")
        s=s.replace('foreign_files=15,previous_actual_preserved=True','foreign_files=15,strict_foreign_files=14,dynamic_observation_only=1,previous_actual_preserved=True')
    ast.parse(s)
    with target.open('x',encoding='utf8',newline='\n') as f:f.write(s)
    bindings[name]=dict(source=str(source),source_sha256=sha(source),target_sha256=sha(target))
save(N/'verification/allocation-program-bindings.json',dict(kind='CONTROLLER_ADAPTATION_FOR_EXPLICIT_ONE_CASE',question_id=QUESTION,files=bindings,changes='Fixed candidate/path/hash/question/registration bindings; original run entry and its clock/preflight unchanged. Retain reviewed dynamic non-input HTML observation exception. Do not rerun known-broken global aggregate generator; canonical own row still updated and failure recorded. No actual artifacts copied, no product/budget changes.',actual_invocations=0))
print(json.dumps(dict(status='EXPLICIT_ONE_CASE_CONTROLLER_BOUND',candidate=HEAD,actual_invocations=0)))
