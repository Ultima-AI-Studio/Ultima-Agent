"""Publish genuine independent PASS as preparation only; never issue runtime release."""
from pathlib import Path
import ast
import datetime as dt
import hashlib
import json
import subprocess

E=Path(__file__).resolve().parents[1];REPO=E.parents[4];MIRROR=Path(r'H:\UltimaAI\ultima-docs-repo')
TAG='ultimaagent-t2-e02-source13-handoff-pass-20261106'
BASE='7a0b6afb7a5e55390d2bd8e035272db04f902a6a'
tree=ast.parse((E/'verification/checkpoint-task1.py').read_bytes())
exec(compile(ast.Module(body=[node for node in tree.body if isinstance(node,ast.FunctionDef)],type_ignores=[]),'checkpoint-functions','exec'))
def replace(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
review_path=E/'review/independent-handoff-source-review.json';review=load(review_path)
assert sha(review_path)=='44ed6b920ff39b3aa7974effd3e2470f73bfc21b58c34009c98bff8ce75ea4b9'
assert review['verdict']=='PASS' and review['reviewer']=='root-independent' and not review['findings'] and review['runtime_authority'] is False
assert sha(E/'entry-manifest.json')==review['manifest_sha256'] and sha(E/'manifest.json')==review['package_manifest_sha256']
assert not (E/'release').exists() and not (E/'runs').exists()
manifest=load(E/'manifest.json');entry=load(E/'entry-manifest.json')
for row in manifest['files']:assert sha(E/row['path'])==row['sha256'],row['path']
for path,digest in entry['files'].items():assert sha(Path(path))==digest,path
assert gt(REPO,'rev-parse','HEAD')==BASE
candidate=Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-e03-source13\UltimaAgent')
assert gt(candidate,'rev-parse','HEAD')=='269aca511d88412dbb9c15d23911138469a37aa2'
assert not gt(candidate,'status','--porcelain','--untracked-files=no')
code_before={p.name:sha(p) for p in (E/'code').glob('*.py')}
receipt=load(E/'offline/handoff-full-green/receipt.json')
assert receipt['package_after']==code_before and receipt['counts']==dict(tests=89,failures=0,errors=0,skipped=0)

archive=E/'history/reviewed-handoff-7a0b6af';archive.mkdir(parents=True,exist_ok=False)
names=list(dict.fromkeys([row['path'] for row in manifest['files']]+['manifest.json','entry-manifest.json']))
for name in names:
    dest=archive/name;assert dest.resolve().is_relative_to(archive.resolve())
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as stream:stream.write((E/name).read_bytes())
    assert sha(dest)==sha(E/name)
dispositions=[dict(item=item,root_ruling='Retain as unproven; preparation does not establish this behavior.',
    cost_if_wrong='A later authorized native/profile/model acceptance gate can fail; actual authority and acceptance remain closed.') for item in review['declined_to_judge']]
disposition=E/'verification/handoff-root-review-disposition.json'
save_new(disposition,dict(controller='root',verdict='PASS_PREPARATION_ONLY',review_sha256=sha(review_path),
    manifest_sha256=review['manifest_sha256'],reviewed_package_manifest_sha256=review['package_manifest_sha256'],
    original_review_path=str(review_path),findings=[],declined_judgment_dispositions=dispositions,
    current_source_tests=89,actual_authority=False,actual_case_allocation=0,actual_result_review_allocation=0,
    E02='NOT_PASSED',T2='NOT_PASSED',publication_scope='control records only; runtime source bindings unchanged',
    current_run_metadata_recovery='PowerShell case-insensitive JSON conversion rejected t2/T2; restored exact committed JSON with Python; only active_review_agent changed before this disposition. No product state or evidence changed.'))
canonical=E/'review/independent-preparation-review.json';canonical.write_bytes(review_path.read_bytes())
assert sha(canonical)==sha(review_path)
replace(E/'verification/code-preparation-gate.json',dict(verdict='PASS_PREPARATION_ONLY',manifest_sha256=review['manifest_sha256'],
    review_sha256=sha(canonical),actual_authority=False,reviewed_package_manifest_sha256=review['package_manifest_sha256'],
    disposition_sha256=sha(disposition),full_offline_tests=89))
ledger=REPO/'.superpowers/sdd/jarvis-work-e02-source13-cleanup-handoff-fix-plan-20261106/progress.md'
with ledger.open('a',encoding='utf-8',newline='\n') as stream:
    stream.write('\nFinal review: root-independent PASS; R1-followup resolved; zero Critical/Important/Minor. Exact entry38/package344 rehashed, zero mismatches; reviewer ran0 tests/native operations.\n')
    for item in dispositions:
        stream.write('Final: Ruling: '+item['item']+' — '+item['root_ruling']+' — '+item['cost_if_wrong']+'\n')
    stream.write('Ruling: Publish the independent PASS byte-for-byte only after preserving all reviewed inputs; keep runtime38 bindings identical — unchanged controls require a canonical review and matching root gate — mismatched bytes would deny future release; no actual release is created.\n')
with (E/'verification/handoff-final-ledger.md').open('xb') as stream:stream.write(ledger.read_bytes())
members={E/row['path'] for row in manifest['files']}
members.update({review_path,disposition,E/'verification/handoff-final-ledger.md',Path(__file__),
    E/'review/handoff-review-assignment.json',E/'verification/handoff-review-checkpoint.json',E/'verification/verify-handoff-checkpoint.py'})
published=dict(schema=2,scope='e02-source13-root-entry-handoff-preparation-published',recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    runtime_authority=False,entry_manifest_sha256=sha(E/'entry-manifest.json'),independent_review='PASS_PREPARATION_ONLY',
    independent_review_path=str(review_path),independent_review_sha256=sha(review_path),
    reviewed_prepublication_manifest_sha256=review['package_manifest_sha256'],reviewed_prepublication_archive=str(archive),
    files=[dict(path=p.relative_to(E).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(members)])
replace(E/'manifest.json',published)
publication=E/'verification/handoff-publication-readback.json'
save_new(publication,dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    canonical_review_exact_bytes=canonical.read_bytes()==review_path.read_bytes(),
    reviewed_prepublication_manifest_sha256=sha(archive/'manifest.json'),published_manifest_sha256=sha(E/'manifest.json'),
    runtime_manifest_unchanged=sha(E/'entry-manifest.json')==review['manifest_sha256'],runtime_bindings=len(entry['files']),
    code_unchanged=code_before=={p.name:sha(p) for p in (E/'code').glob('*.py')},
    archived_files=len(names),published_files=len(published['files']),actual_authority=False,release_directory_exists=False,
    verdict='PASS_PREPARATION_PUBLICATION_READBACK',tests_not_rerun=True))
report=REPO/'docs/reports/jarvis-work-t2-e02-source13-root-entry-preparation-20261106.md'
raw=report.read_text(encoding='utf-8')
raw=raw.replace('当前精确源码独立复核待完成，准备门为 `NOT_READY_PENDING_HANDOFF_SOURCE_REVIEW`。',
    '当前精确源码已获新独立 reviewer **PASS**，无 Critical／Important／Minor 问题项；准备门为 **PASS_PREPARATION_ONLY**。')
raw=raw.replace('当前包 344 项，manifest SHA-256', '独立复核的封存输入包 344 项，manifest SHA-256')
raw=raw.replace('当前精确源码交给新 reviewer 只读审查。审查 PASS 也仅允许准备门通过；',
    '独立复核已确认 R1-followup 解决，并重新核对 344 项包文件和 38 项运行输入，零差异。该 PASS 仅使准备门通过；')
raw+=f'''
## 独审通过及最终登记

独立报告：`review/independent-handoff-source-review.json`，SHA-256 `{sha(review_path)}`。reviewer 未执行测试或现场操作；89 项通过来自本轮 root 的新离线运行。原两份 NEEDS_FIXES 对应其历史源码，仍保存在完整历史包内。

root 逐项接受五类未裁定范围继续未证明：实际 Windows 行为/保护进程存活，真实 profile/SDK/模型研究能力及后续门，原生网络观测，任意系统/文件/未知树故障与 5 秒余量是否充分，以及对抗任意 Python 的隔离。代价是之后实际验证仍可能失败，不因此提前记 E02 通过。

独审通过后只发布控制记录：原独审 PASS 字节原样复制到规范入口，root gate 绑定精确运行输入和报告哈希；运行输入仍为 `{sha(E/'entry-manifest.json')}`。经审查的发布前包完整保存在 `history/reviewed-handoff-7a0b6af`。发布后包 {len(published['files'])} 项，SHA-256 `{sha(E/'manifest.json')}`；其中显式记录独审所审查的发布前包，不冒充对新内容的另一份独审。

交付核验见 `verification/handoff-publication-readback.json`；最终项目/镜像 commit 与 tag 见 `verification/handoff-pass-checkpoint.json`。本轮全部准备完成；下一步只能是用户另行明确分配的原资料单次零推理接线验证及一次独立结果复核，实际分配和 release 目前均为零。
'''
report.write_text(raw,encoding='utf-8',newline='\n')
# Keep the reviewed execution proposal immutable; its current readiness is supplied by this companion note.
readiness=REPO/'docs/plans/jarvis-work-e02-source13-profile-execution-readiness-20261106.md'
readiness.write_text(f'''# E02 单次零推理接线验证就绪说明

HELLO 清理余量交接补修已通过 89 项离线检查及精确源码独立准备复核；准备门 PASS_PREPARATION_ONLY。原执行提案 `jarvis-work-e02-source13-root-entry-execution-proposal-20261106.md` 的操作范围与命令保持，其“等待独立复核”是封存当时状态，由本说明更新。

原题、四来源、source13 产品候选 `269aca511d88412dbb9c15d23911138469a37aa2`、当前 8B 配置和原 275/310/315 秒最大截止保持。一次 root/profile、一个新 reader、两次原读回；一次只读独立结果复核，失败不重试。正常 SSRF 可对 `raw.githubusercontent.com` 做受限 DNS；不调用模型、资料 HTTP、11434、UI、音频或服务操作。仅清理本例登记的准确进程身份，逐项复查七个保护身份。

接线验证成功仍不计入 E02 真实 8B 研究三轮。之后的模型实跑另有原验收门。当前实际运行分配 0、结果复核分配 0；没有 release。需要后续用户明确批准，因为本次授权明确只涵盖离线修复与准备复核。

独立报告 SHA-256 `{sha(review_path)}`；运行输入 manifest `{sha(E/'entry-manifest.json')}`；发布后包 `{sha(E/'manifest.json')}`。封存审查输入与旧失败完整保留。无需暂停键鼠。
''',encoding='utf-8',newline='\n')
mirrors=[]
for source in (report,readiness):
    dest=MIRROR/'docs/shared/research/ultimaagent-work-capability'/source.parent.name/source.name
    dest.write_bytes(source.read_bytes());assert sha(source)==sha(dest)
    mirrors.append(dict(source=str(source),mirror=str(dest),sha256=sha(source)))
save_new(E/'verification/handoff-pass-document-readback.json',dict(mirrors=mirrors,exact=True,remote_synced=False))
state=E.parent/'current-run.json';data=load(state)
data.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE13_E02_HANDOFF_PREPARATION_PASS_RUNTIME_UNALLOCATED',
    active_review_agent=None,active_report=str(report),preparation_status='PASS_PREPARATION_ONLY',preparation_review='PASS',
    e02_root_entry_preparation_review='PASS',e02_root_entry_current_source_review='PASS',e02_root_entry_fix='R1_FOLLOWUP_RESOLVED_INDEPENDENTLY',
    e02_root_entry_manifest_sha256=sha(E/'manifest.json'),e02_root_entry_runtime_manifest_sha256=sha(E/'entry-manifest.json'),
    e02_root_entry_review_sha256=sha(review_path),e02_root_entry_current_review_sha256=sha(review_path),
    e02_root_entry_disposition=str(disposition),e02_execution_released=False,
    e02_preparation_reviewed_manifest_sha256=review['package_manifest_sha256'],
    next_work='Prepared original-corpus one-shot zero-inference profile and one readonly result review require explicit runtime allocation; E02 research acceptance remains open.')
data['next_action_scope']=dict(scope='original_corpus_zero_inference_profile_proposal_ready',approved=False,
    actual_case_allocation=0,actual_result_review_allocation=0,authority_issued=False,
    execution_proposal=str(REPO/'docs/plans/jarvis-work-e02-source13-root-entry-execution-proposal-20261106.md'),
    readiness=str(readiness),model=data['model'],audio_actions=0)
replace(state,data)
summary='E01固定3/3及E03三正一负PASS；E02 HELLO余量补修89项离线检查及独立准备复核PASS，当前只为准备通过。原资料零推理单例及结果复核提案就绪、实际分配0；E02真实研究/T2仍未通过。'
cards=[REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md']
for path in cards:
    raw=path.read_bytes();ending='\r\n' if b'\r\n' in raw else '\n'
    path.write_bytes(raw+('\n## 2026-11-06 E02交接补修独立准备通过\n\n'+summary+'\n').replace('\n',ending).encode())
registry=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md');lines=registry.read_bytes().decode().splitlines(keepends=True);matches=0
for i,line in enumerate(lines):
    if line.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |'):
        lines[i]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+summary+' |'+('\r\n' if line.endswith('\r\n') else '\n');matches+=1
assert matches==1;registry.write_bytes(''.join(lines).encode())
result=subprocess.run([str(REPO/'tools/venv-openjarvis/Scripts/python.exe'),'-B','-X','utf8',r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True)
for suffix,body in (('stdout',result.stdout),('stderr',result.stderr)):
    with (E/f'verification/handoff-pass-queue.{suffix}').open('xb') as stream:stream.write(body)
assert result.returncode==0
members.update(archive/name for name in names)
members.update({E/'manifest.json',E/'entry-manifest.json',publication,report,readiness,state,*cards,
    E/'verification/handoff-pass-document-readback.json',E/'verification/handoff-pass-queue.stdout',E/'verification/handoff-pass-queue.stderr'})
foreign={name:sha(REPO/name) for name in gt(REPO,'diff','--name-only').splitlines() if REPO/name not in members}
assert foreign==load(E/'verification/handoff-review-checkpoint.json')['unrelated_files_preserved']
main=checkpoint(REPO,members,BASE,'Record independent PASS for E02 handoff preparation without runtime release')
mirror=checkpoint(MIRROR,{Path(row['mirror']) for row in mirrors},'aaeeeafac08d5765882b462b921be69e97b91f84','Mirror E02 handoff preparation PASS and concrete next-run scope')
for name,digest in foreign.items():assert sha(REPO/name)==digest
for row in published['files']:assert sha(E/row['path'])==row['sha256'],row['path']
for path,digest in entry['files'].items():assert sha(Path(path))==digest,path
assert sha(E/'entry-manifest.json')==review['manifest_sha256'] and canonical.read_bytes()==review_path.read_bytes()
assert not (E/'release').exists() and not (E/'runs').exists()
final=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),main=main,mirror=mirror,tag=TAG,
    reviewed_manifest_sha256=review['package_manifest_sha256'],published_manifest_sha256=sha(E/'manifest.json'),
    entry_manifest_sha256=sha(E/'entry-manifest.json'),review_sha256=sha(review_path),tests=89,
    gate='PASS_PREPARATION_ONLY',E01_fixed_positive=3,E03_fixed_positive=3,E03_fixed_negative=1,E02='NOT_PASSED',T2='NOT_PASSED',
    actual_case_allocation=0,actual_result_review_allocation=0,actual_authority=False,
    unrelated_files_preserved=foreign,mirrors=mirrors,new_push_attempted=False,remote_synced=False)
save_new(E/'verification/handoff-pass-checkpoint.json',final)
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,tests=89,gate=final['gate'],
    published_manifest=sha(E/'manifest.json'),runtime_authority=False,remote_synced=False)))
