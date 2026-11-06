from pathlib import Path
import datetime as dt, hashlib, json, subprocess
R=Path('H:/UltimaAI/UltimaAgent'); T=R/'data/evidence/jarvis-work-capability/T2'
OLD=T/'e02-source13-child-admission-20261107-r1'; N=T/'e02-source13-native-metadata-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-native-metadata/UltimaAgent')
PY=R/'tools/venv-openjarvis/Scripts/python.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert not N.exists()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=C,text=True).strip()=='269aca511d88412dbb9c15d23911138469a37aa2'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=C)
subprocess.run(['git','switch','-c','codex/jarvis-e02-native-metadata'],cwd=C,check=True)
for d in ('inputs','harness','code','tests','verification','offline','review'):(N/d).mkdir(parents=True,exist_ok=False)
files=['harness/'+x for x in ('adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md','manifest.json')]
files+=['code/'+x for x in ('entry.py','bindings.py')]
files+=['tests/'+p.name for p in (OLD/'tests').glob('*.py')]
files+=['inputs/'+x for x in ('input-manifest.json','scope.json','unrelated-working-tree.json')]
files+=['verification/'+x for x in ('offline_pytest.py','run_entry_checks.py','run_boundary_checks.py','run_binding_checks.py')]
for name in files:(N/name).write_bytes((OLD/name).read_bytes())
save(N/'inputs/copy-origin.json',dict(source=str(OLD),files={name:sha(OLD/name) for name in files}))
save(N/'inputs/granted-scope.json',dict(source='user_explicit',question_id='call_3471155e77c74b8db30c1278112c74d2',answer='授权补修、独审，通过后单例研究并复核（推荐）',
    conditional_actual_case_allocation=1,result_review_allocation=1,retry=0,preparation_review='necessary_independent',product_base='269aca511d88412dbb9c15d23911138469a37aa2',product_root=str(C),
    model='qwen3-8b-uncensored',no_UI=True,no_audio=True,no_production_service_operations=True,old_E01_E03_credit_transfers=False,recorded_at=dt.datetime.now(dt.timezone.utc).isoformat()))
oldproof=OLD/'native-preflight/E02-controlled-1.json'
(N/'inputs/saved-root-native-preflight.json').write_bytes(oldproof.read_bytes())
save(N/'inputs/predecessor.json',dict(root=str(OLD),manifest_sha256=sha(OLD/'manifest.json'),result_manifest_sha256=sha(OLD/'review/result-inputs/result-manifest.json'),
    result_review_sha256=sha(OLD/'review/independent-result-review.json'),saved_native_preflight_sha256=sha(oldproof),two_failures_preserved=['7530ef7f-ad0b-4151-bf2f-800c54ac9449','81c77cfd-9339-48b8-bae1-f67ec7d05cb4']))
save(N/'inputs/state-before.json',json.loads((T/'current-run.json').read_bytes()))
types=PY.parent.parent/'Lib/site-packages/ollama/_types.py'
save(N/'inputs/installed-type-readback.json',dict(path=str(types),sha256=sha(types),list_response_declares_capabilities=False,show_response_capabilities='Optional[List[str]]',
    evidence_basis='Saved native /api/tags models contain arrays of strings; not inferred from ListResponse schema',network_requests=0))
plan=R/'docs/plans/jarvis-work-e02-source13-native-metadata-compat-proposal-20261107.md'
with plan.open('a',encoding='utf8',newline='\n') as f:f.write('''
## 2026-11-07 用户授权与执行分解

用户call_3471155e77c74b8db30c1278112c74d2已授权补修、必要独审、通过后一例研究及独立结果复核。此前“尚未实施/签发”描述为提案形成时状态；具体运行分配只在准备PASS后签发一次。

## Task 1: 严格兼容与离线准备

从269aca5建立新的托管隔离候选；用保留的原生metadata响应RED→GREEN。仅修改checked_native_identity与必要测试，支持可省略的字符串数组capabilities；保留closed keys、类型、版本、8B身份/本地manifest与重复记录拒绝。运行相关离线产品、研究transport、旧入口回归；重绑新候选、保存旧失败、影响分析和原预算；封存后独立准备审查及本地commit/tag/镜像。不得调用模型或操作UI/音频/生产服务。

## Task 2: 条件单例与结果复核

仅Task1独审PASS后，消费一次用户分配，原题四来源当前8B运行一次，失败不重试。保存原始首结果、SDK/transport、文件与cleanup、保护身份，随后一次只读独立事实/结果复核。按实际结论登记，E01/E03旧信用不挪用，E02/T2不自动升级。提交/tag/镜像、最终读回。

## Review Focus

capabilities类型/unknown keys/版本/摘要/重复模型拒绝；保存响应仅root GET而非产品GET的归因边界；新候选的所有导入/子进程cwd/manifest/源码绑定完整；共享P4/P1、原生transport、原时限、七保护身份、未知后代cleanup保留；真实模型回答不被fixture替换；旧E01/E03信用不挪用。
''')
status='原单T2：用户已授权原生metadata最小兼容补修，新隔离候选离线准备中；独审PASS后仅一例当前8B原题四来源研究及一次结果复核，失败不重试；E02仍0/3。'
order=R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md'
lines=order.read_text('utf8').splitlines(keepends=True);ix=[i for i,s in enumerate(lines) if s.startswith('- 状态：')];assert len(ix)==1
lines[ix[0]]='- 状态：'+status+'\n'
append='\n## 2026-11-07 原生metadata兼容授权接续\n\n'+status+'\n方案：docs/plans/'+plan.name+'。新证据：'+str(N)+'。\n'
order.write_text(''.join(lines)+append,encoding='utf8')
stage=R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md';stage.write_text(stage.read_text('utf8')+append,encoding='utf8')
s=json.loads((T/'current-run.json').read_bytes());s.update(phase='SOURCE14_E02_NATIVE_METADATA_OFFLINE_PREPARATION',workflow_status='authorized_metadata_compat_preparation',stage_queue_state='EXECUTING',active_review_agent=None,goal_status='active',e02_execution_released=False,live_gate_released=False,next_stage_released=False,active_evidence=str(N),active_plan=str(plan),active_candidate_root=str(C),actual_case_allocation_remaining=0,result_review_allocation_remaining=0)
(T/'current-run.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
queue=Path('H:/UltimaAI/_shared/queue/global-queue-index.md');lines=queue.read_text('utf8').splitlines(keepends=True)
ix=[i for i,s in enumerate(lines) if s.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(ix)==1
lines[ix[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+status+' |\n';queue.write_text(''.join(lines),encoding='utf8')
r=subprocess.run([str(PY),'-I','-B','-X','utf8','H:/UltimaAI/_shared/queue/queue-status-gen.py'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
(N/'verification/queue-preparation.stdout').write_bytes(r.stdout+r.stderr);assert r.returncode==0
print(json.dumps(dict(new_root=str(N),product_root=str(C),copied=len(files),registered=True),ensure_ascii=False))
