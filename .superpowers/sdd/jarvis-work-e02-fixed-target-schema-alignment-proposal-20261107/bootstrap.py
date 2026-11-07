from pathlib import Path
import datetime as dt,hashlib,json,subprocess
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
OLD=T/'e02-native-write-diagnostics-20261107-r1';N=T/'e02-fixed-target-schema-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-fixed-target-schema/UltimaAgent');PY=R/'tools/venv-openjarvis/Scripts/python.exe'
L=R/'.superpowers/sdd/jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert not N.exists() and subprocess.check_output(['git','rev-parse','HEAD'],cwd=C,text=True).strip()=='6cb9284c9f2bf60f2538d7cb34a124cc0bbf3696'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=C)
subprocess.run(['git','switch','-c','codex/jarvis-e02-fixed-target-schema'],cwd=C,check=True)
for name in ('inputs','harness','code','tests','verification','offline','review'):(N/name).mkdir(parents=True,exist_ok=False)
files=['harness/'+p.name for p in (OLD/'harness').iterdir() if p.is_file()]
files+=['code/'+x for x in ('entry.py','bindings.py')]
files+=['tests/'+p.name for p in (OLD/'tests').glob('*.py')]
files+=['inputs/'+x for x in ('input-manifest.json','scope.json','unrelated-working-tree.json')]
files+=['verification/'+x for x in ('offline_pytest.py','run_entry_checks.py','run_boundary_checks.py','run_binding_checks.py','product_pytest.py','run_product_checks.py')]
for name in files:
    raw=(OLD/name).read_bytes()
    if name in ('verification/product_pytest.py','verification/run_product_checks.py'):
        raw=raw.replace(b'jarvis-e02-write-diagnostics',b'jarvis-e02-fixed-target-schema')
    (N/name).write_bytes(raw)
save(N/'inputs/copy-origin.json',dict(source=str(OLD),files={name:sha(OLD/name) for name in files}))
save(N/'inputs/granted-scope.json',dict(source='user_explicit',question_id='call_409cc146033c4184879042b1abac6383',answer='授权补修、独审，通过后单例研究并复核（推荐）',conditional_actual_case_allocation=1,result_review_allocation=1,retry=0,preparation_review='necessary_independent',product_base='6cb9284c9f2bf60f2538d7cb34a124cc0bbf3696',product_root=str(C),model='qwen3-8b-uncensored',no_UI=True,no_audio=True,no_production_service_operations=True,old_credit_transferred=False,recorded_at=dt.datetime.now(dt.timezone.utc).isoformat()))
save(N/'inputs/predecessor.json',dict(root=str(OLD),manifest_sha256=sha(OLD/'manifest.json'),result_manifest_sha256=sha(OLD/'review/result-inputs/result-manifest.json'),result_review_sha256=sha(OLD/'review/independent-result-review.json'),prior_registration_sha256=sha(OLD/'review/result-registration.json'),all_prior_failures_preserved=True))
save(N/'inputs/state-before.json',json.loads((T/'current-run.json').read_bytes()))
save(N/'inputs/diagnosis-readback.json',dict(prior_static_readback_path=str(OLD/'verification/target-contract-readback.json'),prior_static_readback_sha256=sha(OLD/'verification/target-contract-readback.json'),current_schema_sha256=sha(C/'src/brain/work_navigation.py'),writer_sha256=sha(C/'src/brain/work_tools.py'),sampler_sha256=sha(C/'src/brain/agent_server.py'),observed_rejection='INVALID_TARGET',supplied_path='UNKNOWN_NOT_EXPORTED',minimum='Narrow v3_writer_schema.path to exact research.md enum; sampler retains enum; unchanged writer guard and all evidence gates.',actual_calls=0))
plan=R/'docs/plans/jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107.md'
with plan.open('a',encoding='utf8',newline='\n') as f:f.write('''
## 2026-11-07 已授权接续

用户call_409cc146033c4184879042b1abac6383明确授权本补修、必要独审、通过后一例当前8B原题四来源研究及一次结果复核；失败不重试。本范围不再重复询问。旧失败及旧候选信用保留。

## Task 1: 固定目标schema补修与离线准备

从6cb9284新建隔离候选。先添加schema合法/非法路径与真实SDK mock transport用例，保存RED；仅收紧v3_writer_schema.path为现有字面research.md的enum，保持长度约束。证明native format和本地strict schema都保留enum、错误路径在writer派发前拒绝、合法交付/ACK/读回通过；原writer路径拒绝与事实/引用/END/时限原门保持。完成受影响回归、候选重绑、独立准备审查和本地commit/tag/镜像。

## Task 2: 已授权的单例和结果复核

准备PASS及提交读回后签发一次TTL120秒分配，原题/四来源/当前8B实跑一例；失败不重试。保留原始首结果、完整可用证据、清理和保护身份，做一次只读独立结果复核并按实际结果登记、提交/tag/镜像。不得把离线通过、旧候选信用或准备PASS作为研究通过。

## Review Focus

schema与writer都只允许research.md；native sampler和strict replay使用同一enum且没有改写响应；错误参数在派发前拒绝、合法完整链路保留；唯一现有产品源文件变化限于schema；原8B/语料/预算/时限/保护/清理门和所有历史失败不变。
''')
with (L/'progress.md').open('x',encoding='utf8') as f:f.write('''# SDD ledger — plan: docs/plans/jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107.md

User grant call_409cc146033c4184879042b1abac6383: minimum schema fix, necessary review, one conditional current8B case and one result review; retry0.

Pre-flight: Task1 produces a frozen new candidate, exact input bindings and independent preparation PASS; Task2 consumes the exact identities once. No authority yet.

Ruling: create a new isolated worktree despite already being in a worktree because the accepted proposal requires preserving frozen6cb9284. Retain previous evidence and this ledger, overriding generic workspace cleanup. Cost if wrong: extra retained storage, no old evidence mutation.

Task1 Ruling: retain maxLength2048/minLength1 and add enum only; the existing native sampler removes maxLength but preserves enum. No response normalization, path expansion, writer relaxation or prompt changes. Cost if wrong: no research credit unless fresh strict/native integration and live case meet original gates.
''')
status='原T2/E02：已授权新候选固定research.md schema对齐、离线回归和必要独审；PASS后仅一例当前8B原题四来源及结果复核，当前未释放。旧四次失败完整保留。'
order=R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md';stage=R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
lines=order.read_text('utf8').splitlines(keepends=True);ix=[i for i,v in enumerate(lines) if v.startswith('- 状态：')];assert len(ix)==1;lines[ix[0]]='- 状态：'+status+'\n'
append='\n## 2026-11-07 固定目标schema授权接续\n\n'+status+'\n方案：docs/plans/'+plan.name+'。证据：'+str(N)+'。\n'
order.write_text(''.join(lines)+append,encoding='utf8');stage.write_text(stage.read_text('utf8')+append,encoding='utf8')
s=json.loads((T/'current-run.json').read_bytes());s.update(phase='SOURCE16_E02_FIXED_TARGET_SCHEMA_PREPARATION',workflow_status='authorized_fixed_target_schema_preparation',stage_queue_state='EXECUTING',active_review_agent=None,user_authorized_work_resumption=True,e02_execution_released=False,live_gate_released=False,next_stage_released=False,active_evidence=str(N),active_plan=str(plan),active_candidate_root=str(C),actual_case_allocation_remaining=0,result_review_allocation_remaining=0,next_action_scope=dict(question_id='call_409cc146033c4184879042b1abac6383',conditional_actual_case_allocation=1,conditional_result_review_allocation=1,authority_issued=False,retry=0))
(T/'current-run.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
queue=Path('H:/UltimaAI/_shared/queue/global-queue-index.md');lines=queue.read_text('utf8').splitlines(keepends=True);ix=[i for i,v in enumerate(lines) if v.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(ix)==1
lines[ix[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+status+' |\n';queue.write_text(''.join(lines),encoding='utf8')
r=subprocess.run([str(PY),'-I','-B','-X','utf8','H:/UltimaAI/_shared/queue/queue-status-gen.py'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
(N/'verification/queue-preparation.stdout').write_bytes(r.stdout+r.stderr);assert r.returncode==0
print(json.dumps(dict(new_root=str(N),product_root=str(C),copied=len(files),registered=True),ensure_ascii=False))
