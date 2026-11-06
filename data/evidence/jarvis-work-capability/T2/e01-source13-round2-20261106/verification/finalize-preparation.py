"""Publish local preparation records only after the independent package review."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = Path(r'H:\UltimaAI\UltimaAgent')
MIRROR = Path(r'H:\UltimaAI\ultima-docs-repo\docs\shared\research\ultimaagent-work-capability')
TAG = 'ultimaagent-t2-e01-source13-round2-prep-20261106'
NOW = dt.datetime.now(dt.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(path, data):
    assert not path.exists(), str(path)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


manifest = load(ROOT/'manifest.json')
mh = sha(ROOT/'manifest.json')
for row in manifest['files']:
    p = ROOT/row['path']
    assert sha(p) == row['sha256'] and p.stat().st_size == row['bytes'], str(p)
rp = ROOT/'review/independent-preparation-review.json'
review = load(rp)
assert review['reviewer'] == 'root-independent' and review['verdict'] == 'PASS'
assert review['scope'] == 'e01-round2-acceptance-package' and review['preparation_only'] is True
assert review['candidate'] == manifest['candidate'] and review['manifest_sha256'] == mh
assert review['findings'] == []
assert not (ROOT/'actual').exists() and not (ROOT/'release').exists()
rh = sha(rp)
save(ROOT/'verification/review-disposition.json', dict(recorded_at=NOW,controller='root',
    decision='ACCEPT_PREPARATION_PASS',review_sha256=rh,manifest_sha256=mh,
    regrading={'Critical':0,'Important':0,'Minor':0},
    decline_dispositions=[{'item':x,'ruling':'ACCEPT_SCOPE_LIMIT',
        'effect':'No actual allocation, future runtime assurance, broader acceptance or result credit.'}
        for x in review['declined_to_judge']],
    actual_case_allocation=0,result_review_allocation=0,execution_authorized=False,T2='NOT_PASSED',goal_complete=False))
proposal = f'''# E01 round2单例执行提案（未分配）

范围：当前候选269aca5、当前qwen3-8b-uncensored的一次独立文件摘要交付；一次工作CLI、失败不重试；随后一次只读独立结果复核。E01目前1/3，本提案只推进第2轮。

准备manifest：{mh}（69文件）。独立准备review PASS，SHA：{rh}。252项离线检查通过；本地commit/tag精确读回后才请求新分配。目前实际和结果复核额度均0，没有release或authority。

固定材料：项目代号是松林；交付形式是Markdown文档；截止日期是2026年11月8日。由当前8B整理三条摘要，通过真实SDK文件工具写入本轮outputs/<服务生成新UUID>/summary.md。独审检查事实完整且无新增事实、实际写入与读回、最终路径声明、清理及保护证据，不用关键词命中代替事实审查。

只使用现有Ollama0.32.15和当前8B摘要6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。新进程仅为本轮隔离Agent服务器与CLI；不启动/重启生产服务、不下载升级模型。工作目录为本证据根actual/e01-round2，独立runtime/outputs。无窗口和音频操作，无需暂停键鼠；7保护身份及KWS/语音保持。

入口：pinned Python -B运行code/acceptance_entry.py --preflight及--run，不直接调用旧通用harness。预检只读检查候选源码/依赖、模型摘要/版本、保护身份及监听owner；root根据新的用户分配签发单case/单CLI authority。proof最多60秒、authority最多120秒；准备服务器后提交前再次校验，CLI300/SDK1800/controller315不变。过期或失败保留证据并停止，清理本轮owned身份，不刷新旧授权或自动重试。

机械通过的原始terminal仍保留待独审；独审与root登记另存。此提案不授予第3轮、E01整体、E02、T2出口或Owner通过。新鲜运行环境由未来准入再核对；此前保存的时点证据不能代替。

需要新分配的依据：用户最近明确授权的是“一次E01 round1并独立复核”，该一例和一次复核均已完成。持续推进授权覆盖本轮离线准备；本提案中的round2会新增实际模型调用和一次结果复核。
'''
assert not (ROOT/'execution-proposal.md').exists()
(ROOT/'execution-proposal.md').write_text(proposal,encoding='utf-8')
report_name = 'jarvis-work-t2-e01-source13-round2-preparation-20261106.md'
report = REPO/'docs/reports'/report_name
assert not report.exists()
report.write_text(f'''# E01 round2离线准备与独立审查

链路：wo-ultimaagent-20261101-0021 / T2；执行端root inline；独审{review['agent_identity']}。记录时间{NOW}。

结果：同候选E03三正例及目标变化负例已通过；E01 round1实际与独立事实复核通过，当前1/3。round2准备包252项离线检查、独立准备审查PASS，尚无round2实际用例、结果复核分配或authority。T2及E02仍未通过。

根因与改动：复制前轮入口后，原逻辑不会读取E01 round1凭据。新增校验要求其原始终态、独立事实/文件/最终声明/清理及root登记完整一致，再与E03四份凭据一起绑定新轮次。当前case/scope切换round2；旧round1授权、缺失封存依赖和不合格事实复核在native backend构造前拒绝。

产品候选269aca511d88412dbb9c15d23911138469a37aa2、8B及原backend/controller/adapter保持；57源码、7依赖和1346 SDK文件读回一致。25份输入副本与原件一致，父包89准备文件及41结果文件封存不变。没有修改产品源码、默认模型或语音链路。

验证：最初测试文件收集出现语法错误，证据保留且不算行为RED；修正测试语法后38/38行为测试失败，再补资格校验后38/38通过。最终252/252隔离离线检查通过，无跳过；原208项语义保留，新增44项。socket/process guard允许0、拒绝0、遗留监听0。未重跑历史产品485/8，也未运行模型、服务器、CLI、窗口或音频。

Manifest SHA-256：{mh}；69文件。独立准备审查SHA-256：{rh}，无发现；全部declined scope由root接受，实际内容、未来环境、原生推理总次数、后续用例和最终交付仍需各自证据。封存progress.md保留封存时状态，最终准备结论在本报告和review-disposition.json登记。

产出目录：{ROOT}。执行提案：execution-proposal.md。原始E01 round1结果、旧失败与protected-baseline保留；此准备没有生产进程操作或音频动作，历史保护状态仅为当时时点，不承诺持续可用。实际准入仍需新的60秒proof及120秒authority。

下一步：本地commit/tag及文档镜像字节读回后，请求一次E01 round2及一次只读独立结果复核。无测试窗口，无需暂停键鼠。本地检查点tag为{TAG}，精确提交见verification/local-checkpoint.json。

同步例外：远端push先前被自动审批以blocked by policy拒绝；本轮不重试或换通道。项目与镜像本地提交不等于远端同步。
''',encoding='utf-8')
plan = REPO/'docs/plans/jarvis-work-e01-source13-round2-plan-20261106.md'
mirrors = []
for p, subdir in ((plan,'plans'),(report,'reports')):
    dest = MIRROR/subdir/p.name
    if dest.exists():
        assert dest.read_bytes() == p.read_bytes(), str(dest)
    else:
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    mirrors.append({'source':str(p),'mirror':str(dest),'sha256':sha(p)})
save(ROOT/'verification/document-mirror-readback.json',{'recorded_at':NOW,'mirrors':mirrors,'byte_identical':True})
state_path = ROOT.parent/'current-run.json'
s = load(state_path)
s.update(phase='SOURCE13_E01_ROUND2_PREPARATION_PASS_PENDING_ALLOCATION',workflow_status='executing',
    updated_at=NOW,active_review_agent=None,active_report=str(report),blocking_condition=None,
    e01_preparation_case='e01-round2',e01_preparation_manifest_sha256=mh,e01_preparation_review='PASS',
    e01_preparation_review_path=str(rp),e01_preparation_review_sha256=rh,e01_preparation_tests_passed=252,
    acceptance_entry_case='e01-round2',acceptance_entry_root=str(ROOT),acceptance_entry_manifest_sha256=mh,
    acceptance_entry_review='PASS',acceptance_entry_authority_issued=False,acceptance_entry_user_approval=None,
    acceptance_entry_user_approval_sha256=None,e01_execution_released=False,live_gate_released=False,
    next_stage_released=False,e01_execution_proposal=str(ROOT/'execution-proposal.md'),
    e01_preparation_checkpoint_tag=TAG,e01_preparation_checkpoint_receipt=str(ROOT/'verification/local-checkpoint.json'),
    e01_user_approval=None,e01_user_approval_sha256=None,
    explicit_user_execution_status='COMPLETE_E01_ROUND1_AND_ONE_RESULT_REVIEW',
    e01_last_completed_case='e01-round1')
s['next_action_scope'].update(scope='same-candidate-e01-round2-single-case-proposal',
    actual_case_allocation=0,actual_result_review_allocation=0,authority_issued=False,
    product_model_calls=0,audio_actions=0,package_root=str(ROOT),manifest_sha256=mh,
    proposal=str(ROOT/'execution-proposal.md'),independent_preparation_review='PASS',retry_authorized=False)
state_path.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
status='当前269aca5与当前8B的E03三正例3/3及负例1/1已PASS；E01 round1实际与独审PASS，当前1/3。round2离线252项、69文件封存及独立准备审查PASS；准备完成，待新一例与一次结果复核分配，actual/authority均无。原失败与后续E02/T2/T3—T5/Owner门保留。'
wo=REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md'
lines=wo.read_text(encoding='utf-8').splitlines()
assert sum(line.startswith('- 状态：') for line in lines)==1
lines=[('- 状态：'+status) if line.startswith('- 状态：') else line for line in lines]
append=f'\n\n## 2026-11-06 E01 round2离线准备与独审PASS\n\n{status}\n\n报告：docs/reports/{report_name}。Manifest {mh}；独审SHA {rh}。本次准备不授予新模型调用或结果复核；无UI/音频操作，原保护及准入门不变。\n'
wo.write_text('\n'.join(lines).rstrip()+append,encoding='utf-8')
stage=REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
stage.write_text(stage.read_text(encoding='utf-8').rstrip()+append,encoding='utf-8')
queue=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md')
ql=queue.read_text(encoding='utf-8').splitlines();needle='| UltimaAgent | wo-ultimaagent-20261101-0021 |'
assert sum(line.startswith(needle) for line in ql)==1
ql=[needle+' executing | '+status+' |' if line.startswith(needle) else line for line in ql]
queue.write_text('\n'.join(ql)+'\n',encoding='utf-8')
qr=subprocess.run([sys.executable,'-B','-X','utf8',r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True,text=True,encoding='utf-8')
save(ROOT/'verification/queue-refresh.json',dict(recorded_at=NOW,exit_code=qr.returncode,stdout=qr.stdout,stderr=qr.stderr,
    scope='Only original0021 row updated; generated aggregates are registration rather than actual live execution count'))
assert qr.returncode==0
save(ROOT/'verification/preparation-completion.json',dict(recorded_at=NOW,manifest_sha256=mh,review_sha256=rh,
    task1='PASS',task2='PASS',task3='PASS_252_OFFLINE',task4='PASS_INDEPENDENT_PREPARATION',
    task5='DOCUMENTS_MIRRORED_PENDING_LOCAL_CHECKPOINT',actual_case_allocation=0,result_review_allocation=0,
    E01='PARTIAL_1_OF_3',E03='PASS_CURRENT_CANDIDATE_FIXED_CORPUS',T2='NOT_PASSED',goal_complete=False))
print(json.dumps({'review':'PASS','report':str(report),'mirrors':len(mirrors),'queue_exit':qr.returncode,'actual_allocation':0}))
