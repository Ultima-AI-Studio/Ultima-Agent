from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess
E=Path(__file__).resolve().parents[1];repo=Path(r'H:\UltimaAI\UltimaAgent');mirror=Path(r'H:\UltimaAI\ultima-docs-repo')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
report=repo/'docs/reports/jarvis-work-t2-e02-source13-root-entry-preparation-20261106.md'
proposal=repo/'docs/plans/jarvis-work-e02-source13-root-entry-execution-proposal-20261106.md'
with proposal.open('xb') as f:f.write((E/'execution-proposal.md').read_bytes())
mirrors=[]
for source in (report,proposal):
    dest=mirror/'docs/shared/research/ultimaagent-work-capability'/source.parent.name/source.name
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(source.read_bytes())
    assert source.read_bytes()==dest.read_bytes()
    mirrors.append(dict(source=str(source),mirror=str(dest),sha256=sha(source)))
save(E/'verification/fixed-document-mirror-readback.json',dict(mirrors=mirrors,exact=True,remote_synced=False))
state=E.parent/'current-run.json';data=load(state)
data.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE13_E02_ROOT_ENTRY_R1_FIXED_REVIEW_PENDING',
    active_report=str(report),active_review_agent=None,preparation_status='NOT_READY_PENDING_FIXED_SOURCE_REVIEW',
    preparation_review='NEEDS_FIXES_PRE_FIX_SOURCE',preparation_test_count=83,
    preparation_test_scope='Current enclosing entry full83; original binding fixed557 recorded separately; no actual profile proof',
    e02_root_entry_implemented=True,e02_root_entry_tests=83,e02_root_entry_preparation_review='NEEDS_FIXES_PRE_FIX_SOURCE',
    e02_root_entry_current_source_review='PENDING',e02_root_entry_fix='R1_OFFLINE_VERIFIED',
    e02_root_entry_manifest_sha256=sha(E/'manifest.json'),e02_root_entry_runtime_manifest_sha256=sha(E/'entry-manifest.json'),
    e02_root_entry_review_sha256=sha(E/'review/independent-preparation-review.json'),e02_execution_released=False,
    next_work='Current root-entry repair requires a new exact-source read-only independent review before runtime; original single review/fix allocation consumed.')
data['next_action_scope']=dict(scope='fixed_source_readonly_review_request_ready',next_task=3,
    actual_case_allocation=0,actual_result_review_allocation=0,preparation_review_allocation_remaining=0,
    authority_issued=False,model=data['model'],audio_actions=0)
state.write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode())
summary='E01固定3/3与E03三正一负已PASS；E02外层入口独审NEEDS_FIXES，唯一Important清理余量问题已完成一次有界修复及83项离线检查。当前源码尚待新的只读独立复核，准备门未放行；实际profile/模型/结果复核额度0，E02/T2及后续门不变。'
for path in (repo/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',repo/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'):
    raw=path.read_bytes();ending='\r\n' if b'\r\n' in raw else '\n'
    addition='\n## 2026-11-06 E02外层入口R1修复离线通过，当前源码独审待分配\n\n'+summary+'\n\n报告：docs/reports/'+report.name+'。当前284项manifest '+sha(E/'manifest.json')+'；独审原始结论与旧227项包完整保留。\n'
    path.write_bytes(raw+addition.replace('\n',ending).encode())
registry=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md');raw=registry.read_bytes();lines=raw.decode().splitlines(keepends=True);count=0
for i,line in enumerate(lines):
    if line.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |'):
        lines[i]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+summary+' |'+('\r\n' if line.endswith('\r\n') else '\n');count+=1
assert count==1;registry.write_bytes(''.join(lines).encode())
result=subprocess.run([r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe','-B','-X','utf8',r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True)
(E/'verification/queue-fixed-generation.stdout').write_bytes(result.stdout);(E/'verification/queue-fixed-generation.stderr').write_bytes(result.stderr)
save(E/'verification/fixed-status-readback.json',dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    queue_generator_exit=result.returncode,current_run_sha256=sha(state),registry_sha256=sha(registry),
    gate='NOT_READY_PENDING_FIXED_SOURCE_REVIEW',tests=83,runtime_authority=False,remote_synced=False))
assert result.returncode==0
print(json.dumps(dict(mirrors=len(mirrors),tests=83,gate='NOT_READY_PENDING_FIXED_SOURCE_REVIEW',actual_authority=False)))
