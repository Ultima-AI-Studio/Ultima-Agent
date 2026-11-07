from pathlib import Path
import datetime as dt,hashlib,json,subprocess
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
OLD=T/'e02-fixed-target-schema-20261107-r1';N=T/'e02-source-reference-schema-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-reference/UltimaAgent');PY=R/'tools/venv-openjarvis/Scripts/python.exe'
L=R/'.superpowers/sdd/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert not N.exists() and subprocess.check_output(['git','rev-parse','HEAD'],cwd=C,text=True).strip()=='900b944165c0175b91492e3fe5b31d96aabdcd5c'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=C)
subprocess.run(['git','switch','-c','codex/jarvis-e02-source-reference'],cwd=C,check=True)
for name in ('inputs','harness','code','tests','verification','offline','review'):(N/name).mkdir(parents=True,exist_ok=False)
files=['harness/'+p.name for p in (OLD/'harness').iterdir() if p.is_file()]
files+=['code/'+x for x in ('entry.py','bindings.py')]
files+=['tests/'+p.name for p in (OLD/'tests').glob('*.py')]
files+=['inputs/'+x for x in ('input-manifest.json','scope.json','unrelated-working-tree.json')]
files+=['verification/'+x for x in ('offline_pytest.py','run_entry_checks.py','run_boundary_checks.py','run_binding_checks.py','product_pytest.py','run_product_checks.py')]
for name in files:
    raw=(OLD/name).read_bytes()
    if name in ('verification/product_pytest.py','verification/run_product_checks.py'):
        raw=raw.replace(b'jarvis-e02-fixed-target-schema',b'jarvis-e02-source-reference')
    (N/name).write_bytes(raw)
save(N/'inputs/copy-origin.json',dict(source=str(OLD),files={name:sha(OLD/name) for name in files}))
save(N/'inputs/granted-scope.json',dict(source='user_explicit',question_id='call_33506a697ec545c6b2a396ff83086672',answer='授权补修、独审，通过后单例研究并复核（推荐）',conditional_actual_case_allocation=1,result_review_allocation=1,retry=0,preparation_review='necessary_independent',product_base='900b944165c0175b91492e3fe5b31d96aabdcd5c',product_root=str(C),model='qwen3-8b-uncensored',no_UI=True,no_audio=True,no_production_service_operations=True,old_credit_transferred=False,recorded_at=dt.datetime.now(dt.timezone.utc).isoformat()))
save(N/'inputs/predecessor.json',dict(root=str(OLD),manifest_sha256=sha(OLD/'manifest.json'),result_manifest_sha256=sha(OLD/'review/result-inputs/result-manifest.json'),result_review_sha256=sha(OLD/'review/independent-result-review.json'),prior_registration_sha256=sha(OLD/'review/result-registration.json'),all_prior_failures_preserved=True))
save(N/'inputs/state-before.json',json.loads((T/'current-run.json').read_bytes()))
save(N/'inputs/diagnosis-readback.json',dict(prior_static_readback_path=str(OLD/'verification/reference-contract-readback.json'),prior_static_readback_sha256=sha(OLD/'verification/reference-contract-readback.json'),current_schema_sha256=sha(C/'src/brain/work_navigation.py'),writer_sha256=sha(C/'src/brain/work_tools.py'),sampler_sha256=sha(C/'src/brain/agent_server.py'),observed_rejection='FOREIGN_REFERENCE',exact_reference_and_sources='UNKNOWN_NOT_EXPORTED',minimum='Correlate visible source and evidence enums in generation and independent replay; original writer checks retained.',actual_calls=0))
plan=R/'docs/plans/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107.md'
with plan.open('a',encoding='utf8',newline='\n') as f:f.write('\n## 2026-11-07 新范围已授权\n\n用户call_33506a697ec545c6b2a396ff83086672已批准本提案的补修、离线回归、必要独审、PASS后一例原题四来源当前8B研究及一次结果复核；失败不重试。以上未实施/未授权文字记录提案提出时的状态，以本次接续为准。\n')
with (L/'progress.md').open('x',encoding='utf8') as f:f.write("# SDD ledger — plan: docs/plans/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107.md\n\nUser grant call_33506a697ec545c6b2a396ff83086672: source-reference schema alignment, necessary review, one conditional current8B case and result review, retry0.\n\nPre-flight: Task1 produces correlated schema and independent replay plus frozen candidate/readiness; Task2 consumes identical pinned bytes once.\n\nRuling: preserve frozen900b944 and previous evidence; native-created new worktree operation6ba6a53b-e91b-4c90-9ab6-388a82ea2ed9 completed with no registration error. Retain workspaces/ledgers per user evidence requirements. Cost: extra storage, no old evidence mutation.\n")
status='原T2/E02：已授权新候选来源与证据schema关联、离线回归和必要独审；PASS后仅一例当前8B原题四来源及结果复核，当前未释放。全部旧失败完整保留。'
order=R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md';stage=R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
lines=order.read_text('utf8').splitlines(keepends=True);ix=[i for i,v in enumerate(lines) if v.startswith('- 状态：')];assert len(ix)==1;lines[ix[0]]='- 状态：'+status+'\n'
append='\n## 2026-11-07 来源引用schema授权接续\n\n'+status+'\n方案：docs/plans/'+plan.name+'。证据：'+str(N)+'。\n'
order.write_text(''.join(lines)+append,encoding='utf8');stage.write_text(stage.read_text('utf8')+append,encoding='utf8')
s=json.loads((T/'current-run.json').read_bytes());s.update(phase='SOURCE17_E02_SOURCE_REFERENCE_SCHEMA_PREPARATION',workflow_status='authorized_source_reference_schema_preparation',stage_queue_state='EXECUTING',active_review_agent=None,user_authorized_work_resumption=True,e02_execution_released=False,live_gate_released=False,next_stage_released=False,active_evidence=str(N),active_plan=str(plan),active_candidate_root=str(C),actual_case_allocation_remaining=0,result_review_allocation_remaining=0,next_action_scope=dict(question_id='call_33506a697ec545c6b2a396ff83086672',conditional_actual_case_allocation=1,conditional_result_review_allocation=1,authority_issued=False,retry=0))
(T/'current-run.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
queue=Path('H:/UltimaAI/_shared/queue/global-queue-index.md');lines=queue.read_text('utf8').splitlines(keepends=True);ix=[i for i,v in enumerate(lines) if v.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(ix)==1
lines[ix[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+status+' |\n';queue.write_text(''.join(lines),encoding='utf8')
r=subprocess.run([str(PY),'-I','-B','-X','utf8','H:/UltimaAI/_shared/queue/queue-status-gen.py'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
(N/'verification/queue-preparation.stdout').write_bytes(r.stdout+r.stderr);assert r.returncode==0
print(json.dumps(dict(new_root=str(N),product_root=str(C),copied=len(files),registered=True),ensure_ascii=False))
