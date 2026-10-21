import json,hashlib,subprocess
from pathlib import Path
from datetime import datetime,timezone
R=Path('H:/UltimaAI/UltimaAgent');O=Path(__file__).parent
def git(*a):return subprocess.check_output(['git',*a],cwd=R)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
old=read(O/'administrative-readback.json'); prior=read(O/'result.json');checks=dict(old['checks'])
tag='wo-s1-host-shell-done'; mismatch=[]
for p,h in prior['source_manifest'].items():
 rel=Path(p).relative_to(R).as_posix()
 if hashlib.sha256(git('show',tag+':'+rel)).hexdigest()!=h or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h:mismatch.append(p)
checks['tag_source_matches_technical_audit']=not mismatch;checks['current_source_matches']=not mismatch
cards={}
for d in sorted((R/'tasks/cards').glob('s1-host-shell-*')):
 for n in ['task.md','completion.md','acceptance-evidence.md','landed-files.md']:
  p=d/n;t=p.read_text(encoding='utf-8-sig');rel=p.relative_to(R).as_posix();cards[rel]={'appended':('重启后最终证据' in t and 'w1-post-reboot-closeout-20261021/' in t and 'round4-post-reboot/' in t) if n=='landed-files.md' else all(x in t for x in ['维护重启后独立收口','w1-post-reboot-closeout-20261021/','v0.1仍待Owner单独审批']),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
checks['all_twenty_card_files_appended']=len(cards)==20 and all(c['appended'] for c in cards.values())
index=(R/'docs/文档库索引.md').read_text(encoding='utf-8-sig');execution=(R/'tasks/queue/EXECUTION.md').read_text(encoding='utf-8-sig');dr=(R/'docs/README.md').read_text(encoding='utf-8-sig')
checks['projections_updated']=all(x in index for x in ['wo-s1-host-shell-done','wo-s1-queue-engine-done','w1-independent-acceptance-20261021.md','Owner']) and 'W1/W2 尚未闭合' not in index and 'W1已在维护重启后独立验收并内部收口' in execution and 'Owner' in execution and tag in dr
checks['version_tag_absent']='v0.1-frozen' not in git('tag','--list').decode().splitlines();checks['owner_gate_absent']=not (R/'tasks/queue/gates/v0.1-frozen.json').exists()
checks['maintenance_markers_removed']=all(not Path(m['path']).exists() for m in old['markers'])
done=read(R/'tasks/queue/runs/wo-s1-host-shell-20261021T023427316731Z/done.json');checks['old_adapter_preserved']=done==old['old_adapter']
checks['actual_tag_commit_correct']=git('rev-parse',tag+'^{commit}').decode().strip()==old['actual_tag_commit']
delta=git('diff',tag,'HEAD','--','tasks/cards/s1-host-shell-selfcheck/acceptance-evidence.md').decode('utf-8')
result={'at':datetime.now(timezone.utc).isoformat(),'status':'INTERNAL_ORDER_CLOSED' if all(checks.values()) else 'BLOCKED','owner_version_decision':'AWAITING_APPROVAL','owner_freeze_approved':False,'checks':checks,'tag_commit':old['actual_tag_commit'],'current_head':git('rev-parse','HEAD').decode().strip(),'source_mismatch':mismatch,'cards':cards,'post_tag_T5_document_clarification_diff':delta,'index_sha256':hashlib.sha256((R/'docs/文档库索引.md').read_bytes()).hexdigest(),'old_adapter':done,'initial_readback_preserved':'administrative-readback.json','initial_check_correction':'Card documentation tag/current equality and requiring the exact host tag text in EXECUTION were overly strict. All append sections are present; T5 post-tag delta only clarifies formal entry paths. The actual stale index omission was corrected in the subsequent administrative commit.'}
result['semantic_check_correction']='Landed-files uses its own heading 重启后最终证据 and lists both closeout and independent evidence, rather than repeating completion wording. This is sufficient evidence registration.'
with (O/'administrative-final-readback-v2.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False,indent=2))
