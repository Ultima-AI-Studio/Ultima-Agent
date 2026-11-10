"""Bind the explicitly allocated one-case controller to the already reviewed immutable entry."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
O=T/'e02-output-structure-controlled-preparation-20261108-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-claim-generation-r1/UltimaAgent');M=Path('H:/UltimaAI/ultima-docs-repo')
HEAD='d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b'
MANIFEST='c36908a9a99f290889cb420613a93d70611386ace39765e8b970f55f5ea1f16a'
REVIEW='112435823a9ab087ede87457026e0a78d11659e39a1cff22a2b14dafa767af5d'
QUESTION='call_c910dd9e4819410492607baac9ed63bf'
TEXT='候选 d8f8d97 的离线补修和受控入口准备已完成：1004 项产品/兼容/参考检查、350 项入口检查、独立准备审查及最终读回通过，项目/镜像已本地提交并打 tag（13699f8d / 1de72da）。是否按[执行提案](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-claim-generation-controlled-preparation-20261108-r1/execution-proposal.md)，明确分配一例当前 8B 的原题四来源研究及一次只读独立结果复核？保持原预算和完整原题验收，原入口先核验新鲜运行态，失败不重试；无需暂停键鼠。需要此次分配，因为你本轮只授权离线补修、必要独审与入口准备，并要求新候选实跑另行明确分配；当前额度为 0。'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW,text=True).strip()
assert sha(N/'manifest.json')==MANIFEST and sha(N/'review/independent-preparation-review.json')==REVIEW
final=load(N/'verification/final-readback.json');pub=load(N/'verification/publication-readback.json')
assert final['verdict']=='PASS_FINAL_LOCAL_READBACK' and final['publication_sha256']==sha(N/'verification/publication-readback.json')=='30ac8018afaf77326f0a712fa6dbd0c2051b649fb639cec210bf677515f9940a'
for root,key in ((R,'project'),(M,'mirror'),(C,'candidate')):assert git(root,'rev-parse','HEAD')==final['heads'][key]
assert git(C,'rev-parse','HEAD')==HEAD and not git(C,'status','--porcelain')
assert not git(R,'diff','--cached','--name-only') and not git(M,'diff','--cached','--name-only')
for name,h in load(N/'manifest.json')['files'].items():assert sha(N/name)==h,name
for name,h in load(N/'inputs/input-manifest.json')['files'].items():assert sha(Path(name))==h,name
for name,h in pub['file_sha256'].items():assert sha(Path(name))==h,name
assert load(N/'verification/allocated-worker-observation.json')['count']==0
assert not any((N/name).exists() for name in ('release','actual','controller-authority','native-preflight','controller-ledger.json','review/independent-result-review.json'))
save(N/'verification/actual-admission-readback.json',dict(verdict='PASS_CURRENT_IMMUTABLE_PREPARATION_AND_INPUTS',candidate=HEAD,manifest_sha256=MANIFEST,review_sha256=REVIEW,heads=final['heads'],manifest_members=394,input_files=1602,source_files=78,model_calls=0,actual_invocations=0,runtime_status='FRESH_CHECKS_DEFERRED_TO_ORIGINAL_ALLOCATED_ENTRY',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
changes={
 'call_5c06d21b59b8475b873814f857990cc3':QUESTION,
 'bf7f7a9cf0e4ba559c29daa388c00379d12d345a':HEAD,
 'bf7f7a9':'d8f8d97',
 'ea078190d78a340d3db06092bb050662a4a59e37e2f327c595199073b195eb1f':MANIFEST,
 '85dc915c2712f6af7132456904dfa4d429e97b7a85aff4de2bb762fa80c22fe4':REVIEW,
 'dff378fec3ce30f9c252a4713147bc389e22c125':final['heads']['project'],
 'jarvis-e02-output-structure-r2':'jarvis-e02-claim-generation-r1',
 'e02-output-structure-controlled':'e02-claim-generation-controlled',
 'SOURCE33_E02_OUTPUT_STRUCTURE':'SOURCE35_E02_CLAIM_GENERATION',
 'source33_preparation':'source35_preparation',
 'output_structure_evidence_one_case':'claim_generation_one_case',
 'output structure':'claim generation',
 '/root/review_e02_output_structure_actual_result':'/root/review_e02_claim_generation_actual_result',
}
bindings={}
for name in ('register_allocation.py','run_allocated_case.py','seal_allocated_result.py','register_result_audit.py'):
    source=O/'verification'/name;target=N/'verification'/name;s=source.read_text('utf8')
    if name=='register_allocation.py':
        assignment=next(x for x in ast.parse(s).body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id=='question')
        lines=s.splitlines(keepends=True);lines[assignment.lineno-1:assignment.end_lineno]=['question='+repr(TEXT)+'\n'];s=''.join(lines)
    for before,after in changes.items():s=s.replace(before,after)
    if name=='run_allocated_case.py':
        start=s.index("preflight=e.load(N/'verification/runtime-before-allocated-case.json')")
        end=s.index("(N/'release').mkdir",start)
        s=s[:start]+"# Preparation deliberately deferred live checks; the unchanged entry performs all fresh\n# identity/listener/native metadata checks inside its original clock after exclusive consumption.\nassert e.load(N/'verification/actual-admission-readback.json')['verdict']=='PASS_CURRENT_IMMUTABLE_PREPARATION_AND_INPUTS'\n"+s[end:]
    ast.parse(s)
    with target.open('x',encoding='utf8',newline='\n') as f:f.write(s)
    bindings[name]=dict(source=str(source),source_sha256=sha(source),target_sha256=sha(target))
save(N/'verification/allocation-program-bindings.json',dict(kind='CONTROLLER_ADAPTATION_FOR_EXPLICIT_ONE_CASE',question_id=QUESTION,files=bindings,changes='Only fixed candidate/path/hash/question/registration bindings. Standalone pre-grant runtime observer omitted under reviewed pending-preflight design; all mandatory checks remain in unchanged entry under original clock. No actual artifacts copied or code/budget changes.',actual_invocations=0))
print(json.dumps(dict(status='EXPLICIT_ONE_CASE_CONTROLLER_BOUND',candidate=HEAD,manifest_members=394,input_files=1602,actual_invocations=0)))
