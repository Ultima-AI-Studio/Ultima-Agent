"""Record the authorized read-only review. No code/test/runtime activation."""
from pathlib import Path
import ast
import datetime as dt
import hashlib
import json
import subprocess
E=Path(__file__).resolve().parents[1];REPO=Path(r'H:\UltimaAI\UltimaAgent');MIRROR=Path(r'H:\UltimaAI\ultima-docs-repo')
TAG='ultimaagent-t2-e02-source13-root-entry-fix1-review-20261106'
tree=ast.parse((E/'verification/checkpoint-task1.py').read_bytes())
ns=dict(Path=Path,dt=dt,hashlib=hashlib,json=json,subprocess=subprocess,TAG=TAG)
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'accepted-checkpoint-functions','exec'),ns)
sha,load,gt,git,checkpoint,save_new=[ns[k] for k in ('sha','load','gt','git','checkpoint','save_new')]
report_path=E/'review/independent-fixed-source-review.json';review=load(report_path)
assert sha(report_path)=='3a9e31a89858bfe083f028a7a66ca482da4ef50acdbb41303134c48bcec0d450'
assert review['verdict']=='NEEDS_FIXES' and [f['id'] for f in review['findings']]==['R1-followup']
assert review['manifest_sha256']==sha(E/'entry-manifest.json') and review['package_manifest_sha256']==sha(E/'manifest.json')
for row in load(E/'manifest.json')['files']:assert sha(E/row['path'])==row['sha256']
for name,value in load(E/'entry-manifest.json')['files'].items():assert sha(Path(name))==value
assert not git(REPO,'diff','c7019252e17a83af01439e14d689ba4a12d55225','--',str(E/'code'))
assert not (E/'release').exists() and not (E/'runs').exists()
disposition=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),controller='root',
    scope='USER_AUTHORIZED_ONE_READONLY_FIXED_SOURCE_REVIEW',independent_verdict='NEEDS_FIXES',
    report_sha256=sha(report_path),manifest_sha256=review['package_manifest_sha256'],entry_manifest_sha256=review['manifest_sha256'],
    finding='R1-followup',severity='Important',root_disposition='ACCEPT_FINDING_DO_NOT_ACTIVATE',
    gate='NOT_READY_CLEANUP_HANDOFF',prior_R1='PARTIAL_NOT_CLOSED',review_allocation_consumed=1,review_remaining=0,
    code_changed_during_authorized_review=False,tests_run_during_authorized_review=0,runtime_authority=False,
    actual_case_allocation=0,actual_result_review_allocation=0,
    limitations=[dict(item=item,decision='Accepted unproven; no success or OS cleanup guarantee inferred.') for item in review['declined_to_judge']],
    next_scope='proposed_only_cleanup_handoff_repair_and_necessary_independent_reviews')
save_new(E/'verification/fixed-source-review-disposition.json',disposition)
request=E/'verification/fixed-source-review-request.json';r=load(request)
r.update(requested=True,allocated=True,consumed=True,remaining=0,verdict='NEEDS_FIXES',report_sha256=sha(report_path),
    approval_sha256=sha(E/'review/fixed-source-review-approval.json'))
request.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
document=REPO/'docs/reports/jarvis-work-t2-e02-source13-root-entry-preparation-20261106.md'
plan=REPO/'docs/plans/jarvis-work-e02-source13-cleanup-handoff-fix-plan-20261106.md'
mirrors=[]
for source in (document,plan):
    dest=MIRROR/'docs/shared/research/ultimaagent-work-capability'/source.parent.name/source.name
    if dest.exists():
        previous=load(E/'verification/fixed-document-mirror-readback.json')['mirrors']
        assert any(row['mirror']==str(dest) and sha(dest)==row['sha256'] for row in previous)
    dest.write_bytes(source.read_bytes());assert dest.read_bytes()==source.read_bytes()
    mirrors.append(dict(source=str(source),mirror=str(dest),sha256=sha(source)))
save_new(E/'verification/fixed-source-review-mirror-readback.json',dict(mirrors=mirrors,exact=True,remote_synced=False))
state=E.parent/'current-run.json';s=load(state)
s.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE13_E02_ROOT_ENTRY_CLEANUP_HANDOFF_NEEDS_FIXES',
    active_review_agent=None,active_report=str(document),preparation_status='NOT_READY_CLEANUP_HANDOFF',
    e02_root_entry_current_source_review='NEEDS_FIXES',e02_root_entry_preparation_review='NEEDS_FIXES',
    e02_root_entry_fix='R1_PARTIAL_HANDOFF_GAP',e02_root_entry_current_review_sha256=sha(report_path),
    e02_root_entry_disposition=str(E/'verification/fixed-source-review-disposition.json'),
    next_work='Proposed bounded HELLO/qualification reservation repair and necessary independent review; current user grant was read-only and is consumed.')
s['next_action_scope']=dict(scope='cleanup_handoff_repair_proposal_ready',proposal=str(plan),approved=False,
    actual_case_allocation=0,actual_result_review_allocation=0,preparation_review_remaining=0,authority_issued=False)
state.write_bytes((json.dumps(s,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode())
summary='E01固定3/3与E03三正一负已PASS；E02修复包一次只读复核已完成，NEEDS_FIXES：HELLO等待遗漏后续资格查询/迟登记成员余量。83项旧离线检查保留但不能放行；已准备同一缺口补修与必要独审提案，实际profile/模型/结果复核额度0。'
orders=[REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md']
for path in orders:
    raw=path.read_bytes();ending='\r\n' if b'\r\n' in raw else '\n'
    addition='\n## 2026-11-06 用户授权修复包只读复核完成，NEEDS_FIXES\n\n'+summary+'\n\n独审SHA '+sha(report_path)+'；下一步提案docs/plans/'+plan.name+'。本次未改执行源码、未运行测试或现场用例。\n'
    path.write_bytes(raw+addition.replace('\n',ending).encode())
registry=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md');raw=registry.read_bytes();lines=raw.decode().splitlines(keepends=True);count=0
for i,line in enumerate(lines):
    if line.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |'):
        lines[i]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+summary+' |'+('\r\n' if line.endswith('\r\n') else '\n');count+=1
assert count==1;registry.write_bytes(''.join(lines).encode())
result=subprocess.run([r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe','-B','-X','utf8',r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True)
(E/'verification/queue-fixed-review-result.stdout').write_bytes(result.stdout);(E/'verification/queue-fixed-review-result.stderr').write_bytes(result.stderr)
assert result.returncode==0
files={report_path,document,plan,state,request,Path(__file__),*orders,
    E/'review/fixed-source-review-approval.json',E/'review/fixed-source-review-consumed.json',
    E/'verification/register-fixed-source-review.py',E/'verification/fixed-source-review-disposition.json',
    E/'verification/fixed-source-review-mirror-readback.json',E/'verification/fixed-local-checkpoint.json',
    E/'verification/queue-fixed-review-result.stdout',E/'verification/queue-fixed-review-result.stderr'}
mirror_files={Path(row['mirror']) for row in mirrors};owned={REPO:files,MIRROR:mirror_files}
heads={str(repo):gt(repo,'rev-parse','HEAD') for repo in owned};foreign={}
for repo,members in owned.items():
    assert not gt(repo,'diff','--cached','--name-only') and not gt(repo,'tag','--list',TAG)
    names={p.relative_to(repo).as_posix() for p in members}
    foreign[str(repo)]={p:sha(repo/p) for p in gt(repo,'diff','--name-only').splitlines() if p not in names}
main=checkpoint(REPO,files,heads[str(REPO)],'Record E02 fixed-source review gap and scoped repair proposal')
mirror=checkpoint(MIRROR,mirror_files,heads[str(MIRROR)],'Mirror E02 handoff review finding and repair proposal')
for repo,items in foreign.items():
    for p,value in items.items():assert sha(Path(repo)/p)==value
save_new(E/'verification/fixed-source-review-result-checkpoint.json',dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    main=main,mirror=mirror,tag=TAG,review_sha256=sha(report_path),gate='NOT_READY_CLEANUP_HANDOFF',
    runtime_authority=False,code_changed=False,new_tests_run=0,mirrors=mirrors,unrelated_files_preserved=foreign,remote_synced=False,new_push_attempted=False))
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,verdict='NEEDS_FIXES',runtime_authority=False,code_changed=False,new_tests_run=0)))
