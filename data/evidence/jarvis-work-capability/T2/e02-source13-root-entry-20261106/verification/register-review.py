from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess
E=Path(__file__).resolve().parents[1]
def save(path,value):
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
state=E.parent/'current-run.json';raw=state.read_bytes()
with (E/'verification/current-run-before-root-review.json').open('xb') as f:f.write(raw)
data=json.loads(raw)
data.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE13_E02_ROOT_ENTRY_OFFLINE_PASS_PREPARATION_REVIEW',
    e02_root_entry_implemented=True,e02_root_entry_tests=81,e02_root_entry_preparation_review='IN_PROGRESS',
    active_review_agent='/root/review_e02_source13_root_entry',preparation_status='ROOT_ENTRY_OFFLINE_PASS_REVIEW_PENDING')
data['next_action_scope']=dict(scope='one_readonly_whole_entry_preparation_review',next_task=3,
    actual_case_allocation=0,actual_result_review_allocation=0,authority_issued=False,model=data['model'],audio_actions=0)
state.write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf-8'))
registry=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md');raw=registry.read_bytes()
with (E/'verification/global-registry-before-root-review.md').open('xb') as f:f.write(raw)
text=raw.decode('utf-8');lines=text.splitlines(keepends=True);count=0
for i,line in enumerate(lines):
    if line.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |'):
        newline='\r\n' if line.endswith('\r\n') else '\n'
        lines[i]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | E01固定3/3与E03三正一负已PASS；E02外层入口81项离线检查通过，封存并本地提交83312d5，正在进行一次只读独立准备审查。原profile与产品不变；实际profile/模型/结果复核额度0，E02/T2及后续门未过。 |'+newline;count+=1
assert count==1
registry.write_bytes(''.join(lines).encode('utf-8'))
result=subprocess.run([r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe','-B','-X','utf8',
    r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True)
(E/'verification/queue-review-generation.stdout').write_bytes(result.stdout)
(E/'verification/queue-review-generation.stderr').write_bytes(result.stderr)
save(E/'verification/review-registration.json',dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    root='/root',reviewer='/root/review_e02_source13_root_entry',scope='read_only_preparation',review_cap=1,
    runtime_authority=False,actual_case_allocation=0,actual_result_review_allocation=0,
    queue_generator_exit=result.returncode,registry_sha256=hashlib.sha256(registry.read_bytes()).hexdigest()))
assert result.returncode==0,result.stderr.decode('utf8',errors='replace')
print('One preparation reviewer registered; actual allocations remain zero.')
