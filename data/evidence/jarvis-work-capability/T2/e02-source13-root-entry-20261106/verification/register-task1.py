"""Read back the one fixed offline runner and register the remaining entry work."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import xml.etree.ElementTree as ET

E = Path(__file__).resolve().parents[1]
T = E.parent
B = T/'e02-source13-profile-binding-20261106'
REPO = Path(r'H:\UltimaAI\UltimaAgent')
MIRROR = Path(r'H:\UltimaAI\ultima-docs-repo')


def load(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


before = set(load(E/'verification/fixed-runner-directories-before.json')['directories'])
after = {p.name for p in (B/'code').iterdir() if p.is_dir()}
assert len(after-before) == 1
stage = B/'code'/next(iter(after-before))
assert stage.name.startswith('profile-preparation-contracts-')
raw = load(stage/'receipt.json')
assert raw['kind'] == 'full_fixed_contracts' and raw['qualification'] == 'OFFLINE_SYNTHETIC_CONTRACTS_ONLY'
assert raw['exit_code'] == raw['pytest_exit_code'] == raw['original_profile_runs'] == 0
assert raw['runtime_released'] is False and raw['error_type'] is None
assert raw['dependencies_count'] == 1461 and raw['dependencies_unchanged'] and raw['package_unchanged']
assert raw['expected_count'] == raw['actual_count'] == 557 and raw['allowlist_exact'] is True
for name, digest in raw['raw_sha256'].items():
    assert sha(stage/name) == digest, name
pins = load(B/'profile-preparation/manifest.json')
assert set(raw['actual_test_ids']) == set(pins['test_ids']) and len(set(raw['actual_test_ids'])) == 557
cases = ET.parse(stage/'junit.xml').findall('.//testcase')
assert len(cases) == 557 and all(not any(c.find(kind) is not None for kind in ('failure','error','skipped')) for c in cases)
assert {'test_profile.py::'+case.get('name') for case in cases} == set(pins['test_ids'])
assert load(stage/'dependencies-before.json') == load(stage/'dependencies-after.json') == pins['files']
assert load(stage/'package-before.json') == load(stage/'package-after.json')
for name,digest in pins['files'].items():
    assert sha(Path(name)) == digest, name
for name,digest in load(stage/'package-after.json').items():
    assert sha(Path(name)) == digest, name
for row in load(E/'inputs/source-bindings.json')['files']:
    assert sha(Path(row['path'])) == row['sha256'], row['path']
assert sha(B/'manifest.json') == 'ec15aa82ee9ef72ff366c33eb997307e8151a97957eaa6d3f8544dc555424382'
for row in load(B/'manifest.json')['files']:
    assert sha(B/row['path']) == row['sha256'], row['path']
now = dt.datetime.now(dt.timezone.utc).isoformat()
members = [p for p in stage.iterdir() if p.is_file()] + list((stage/'snapshot').iterdir())
fixed_record = dict(recorded_at=now, verdict='PASS_OFFLINE_FIXED_RUNNER_ONLY', stage=str(stage),
    runner_receipt_sha256=sha(stage/'receipt.json'), runner_exit_code=0, exact_test_ids=557,
    failures=0, errors=0, skipped=0, dependencies=1461, dependencies_and_package_unchanged=True,
    fixed_runner_invocations=1, retries=0, actual_profile_runs=0, model_calls=0, runtime_authority=False,
    E02='NOT_PASSED', T2='NOT_PASSED',
    limitations=['No actual outer controls, worker/reader integration or actual SDK/profile invocation.',
        'Fixed runner does not install the separate run-stage.py Python audit hook; no OS/native inactivity inference.',
        'No current protected-process/service observation was taken for this offline task.'],
    files=[dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path)) for path in sorted(members)])
save_new(E/'verification/fixed-runner-readback.json', fixed_record)

report = REPO/'docs/reports/jarvis-work-t2-e02-source13-root-entry-baseline-20261106.md'
report_text = '''# E02 source13外层入口准备：固定检查入口与接口基线

原单wo-ultimaagent-20261101-0021，T2；候选269aca511d88412dbb9c15d23911138469a37aa2，仅当前qwen3-8b-uncensored。E01固定三轮3/3、E03三正例及一负例已通过。E02当前绑定包的557项离线检查和独立准备审查已PASS，本地检查点5e3ac704／镜像bc28b451，tag ultimaagent-t2-e02-source13-binding-prep-20261106；E02/T2实际能力门仍未通过。

外层入口计划已具体化，见docs/plans/jarvis-work-e02-source13-root-entry-plan-20261106.md。证据根data/evidence/jarvis-work-capability/T2/e02-source13-root-entry-20261106。Task1保存23份只读来源绑定，并完成一次原固定run_checks.py --contracts：557个唯一标识全部通过，零失败/错误/跳过，1461依赖和包文件前后无漂移，无重试。原始runner收据和JUnit已逐字/逐标识读回，见verification/fixed-runner-readback.json。这是与B较早named runner独立记账的新固定入口记录，未修改B原收据中“当时固定runner为0”的历史。

静态核对记录了六项接口：当前package_root和旧import_path首项需要显式派生绑定；venv调用角色与实际worker原生身份需要独立观察；保护集合必须使用当前7身份；两次readback和实际reader退出沿用同一275/310/315秒时钟；原生退出须先观察保留句柄已终止再读取退出码；历史metadata仍仅用于模拟transport，不能当作当前服务证明。

下一步Task2只在新E目录内联实现外层RootControls、worker/reader接线及必要只读退出观察适配，复用现有Owned和标准库机制，先行为RED再GREEN。原产品、SDK和B/profile字节冻结；不新增原生进程控制器。Task3完成整包独立准备审查与root处置后，才提出具体的一次零推理profile和一次结果复核申请。现在尚未提供外层代码、实际入口或运行authority。

本次原资料profile、产品CLI、模型、UI/音频、服务操作均0；没有刷新保护进程/11434状态。固定runner为已审查的模拟契约测试，它没有run-stage.py单独安装的Python审计hook；不据此宣称OS/native全局零活动。旧六轮修复、所有失败和耗尽额度原样保留。E02还需当前8B受控三轮与真实联网来源/事实/文件验收，T2、后续阶段和Owner不提前通过。

本地基线tag为ultimaagent-t2-e02-source13-root-entry-baseline-20261106；具体项目/镜像提交与精确读回见verification/task1-local-checkpoint.json。远端push此前被自动审批以blocked by policy拒绝，本次未重试或改通道；本地留档不等于远端同步。
'''
with report.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(report_text)
status = '当前269aca5与当前8B的E01固定3/3、E03三正例及负例已PASS；E02绑定准备及独审PASS后，原固定runner一次557/557通过，外层入口计划与23份来源/6项接口基线已完成。下一步内联实现具体RootControls并离线验证；actual/profile/模型/结果复核额度0，E02/T2及后续门未过。'
state_path = T/'current-run.json'
old_state = state_path.read_bytes()
with (E/'verification/current-run-before-task1-registration.json').open('xb') as stream:
    stream.write(old_state)
state = json.loads(old_state)
assert state['e02_preparation_review'] == 'PASS' and state['e01_current_candidate_positive_passed'] == 3
state.update(updated_utc=now, phase='SOURCE13_E02_ROOT_ENTRY_TASK1_PASS_CONTROLS_PENDING',
    active_preparation_root=str(E), active_report=str(report), next_offline_plan=str(REPO/'docs/plans/jarvis-work-e02-source13-root-entry-plan-20261106.md'),
    preparation_status='ROOT_ENTRY_IN_PROGRESS_BINDING_PREDECESSOR_PASS', preparation_review='NOT_YET_REQUESTED_FOR_ROOT_ENTRY',
    active_review_agent=None, e02_fixed_runner_runs=1, e02_fixed_runner_tests=557,
    e02_fixed_runner_readback=str(E/'verification/fixed-runner-readback.json'),
    e02_fixed_runner_readback_sha256=sha(E/'verification/fixed-runner-readback.json'),
    e02_root_entry_implemented=False, e02_root_entry_preparation_review='NOT_YET_REQUESTED',
    e02_original_profile_runs=0, e02_execution_released=False, live_gate_released=False, next_stage_released=False)
state['next_action_scope'] = dict(scope='e02-source13-root-entry-code-and-offline-contracts',
    package=str(E), plan=str(REPO/'docs/plans/jarvis-work-e02-source13-root-entry-plan-20261106.md'),
    task1='PASS_OFFLINE_FIXED_RUNNER_AND_STATIC_BINDINGS', next_task=2,
    actual_case_allocation=0, actual_result_review_allocation=0, authority_issued=False,
    implementation='root-inline', old_repair_budget_reopened=False, model='qwen3-8b-uncensored',audio_actions=0)
state_path.write_bytes((json.dumps(state,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf-8'))
appendix = '\n## 2026-11-06 E02外层入口Task1完成\n\n'+status+'\n\n报告：docs/reports/jarvis-work-t2-e02-source13-root-entry-baseline-20261106.md；计划：docs/plans/jarvis-work-e02-source13-root-entry-plan-20261106.md。固定runner收据SHA '+fixed_record['runner_receipt_sha256']+'，无重试，不代表实际profile或研究能力。\n'
for relative in ('tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md','tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'):
    path = REPO/relative
    text = path.read_text(encoding='utf-8')
    if '--work-capability' in path.name:
        text = '\n'.join('- 状态：'+status if line.startswith('- 状态：') else line for line in text.splitlines())
    path.write_bytes((text.rstrip()+'\n'+appendix).replace('\n','\r\n').encode('utf-8'))
queue = Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md')
lines = queue.read_text(encoding='utf-8').splitlines()
prefix='| UltimaAgent | wo-ultimaagent-20261101-0021 |'
assert sum(line.startswith(prefix) for line in lines) == 1
queue.write_text('\n'.join(prefix+' executing | '+status+' |' if line.startswith(prefix) else line for line in lines)+'\n',encoding='utf-8',newline='\n')
progress = REPO/'.superpowers/sdd/jarvis-work-e02-source13-root-entry-plan-20261106'
progress.mkdir(exist_ok=False)
(progress/'progress.md').write_text('# Root entry preparation progress\n\nTask1 complete: one fixed runner557/557;23 static source bindings and6 compatibility observations.\nTask2 pending: no entry code or native integration run yet.\nTask3 pending: no final preparation reviewer allocated yet.\nOriginal6 repair history preserved; new actual/profile/model/result-review allocations0.\n',encoding='utf-8')
(E/'verification/progress-task1.md').write_bytes((progress/'progress.md').read_bytes())
mirrors=[]
for source in (report,REPO/'docs/plans/jarvis-work-e02-source13-root-entry-plan-20261106.md'):
    target=MIRROR/'docs/shared/research/ultimaagent-work-capability'/source.parent.name/source.name
    target.write_bytes(source.read_bytes())
    assert sha(source)==sha(target)
    mirrors.append(dict(source=str(source),mirror=str(target),sha256=sha(source),bytes=source.stat().st_size))
save_new(E/'verification/task1-document-mirror-readback.json',dict(recorded_at=now,mirrors=mirrors))
print(json.dumps(dict(fixed_runner='PASS',tests=557,retries=0,stage=str(stage),next_task=2,actual_authority=False)))
