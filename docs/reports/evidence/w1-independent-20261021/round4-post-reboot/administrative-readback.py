import hashlib,json,subprocess,re
from pathlib import Path
from datetime import datetime,timezone
R=Path('H:/UltimaAI/UltimaAgent');O=Path(__file__).parent
def text(p):return Path(p).read_text(encoding='utf-8-sig')
def read(p):return json.loads(text(p))
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
def tagmatch(rel):
 p=subprocess.run(['git','show',tag+':'+rel],cwd=R,capture_output=True)
 return None if p.returncode else p.stdout==(R/rel).read_bytes()
tag='wo-s1-host-shell-done'; commit=git('rev-parse',tag+'^{commit}').decode().strip()
prior=read(O/'result.json'); bad=[]; currentbad=[]
for p,h in prior['source_manifest'].items():
 rel=Path(p).relative_to(R).as_posix()
 if sha(git('show',tag+':'+rel))!=h:bad.append(p)
 if sha(Path(p).read_bytes())!=h:currentbad.append(p)
cards={}
for d in sorted((R/'tasks/cards').glob('s1-host-shell-*')):
 cards[d.name]={}
 for name in ['task.md','completion.md','acceptance-evidence.md','landed-files.md']:
  p=d/name;t=text(p);rel=p.relative_to(R).as_posix()
  cards[d.name][name]={'sha256':sha(p.read_bytes()),'tag_matches_current':tagmatch(rel),'post_reboot_added':'维护重启后独立收口' in t,'closeout_evidence_link':'w1-post-reboot-closeout-20261021/' in t,'owner_gate_preserved':'v0.1仍待Owner单独审批' in t}
queue=text(R/'tasks/queue/wo-s1-host-shell.md');unchecked=re.findall(r'^- \[ \].*',queue,re.M)
glob=Path('H:/UltimaAI/_shared/queue/global-queue-index.md'); gt=text(glob)
grow=next(x for x in gt.splitlines() if '| UltimaAgent | wo-s1-host-shell |' in x)
prod=read(R/'sync/product.json'); prow=next(x for x in prod['work_orders'] if x['id']=='wo-s1-host-shell')
projection={}
for rel in ['docs/README.md','docs/文档库索引.md','tasks/queue/EXECUTION.md']:
 t=text(R/rel); projection[rel]={'sha256':sha((R/rel).read_bytes()),'mentions_internal_tag':tag in t,'mentions_owner':'Owner' in t,'tag_matches_current':tagmatch(rel)}
before=read(O/'support/logs/maintenance/w1-restart-20261021/before.json');markers=[{'path':m['path'],'absent':not Path(m['path']).exists(),'previously_owned':m['created_by_this_maintenance']} for m in before['dispatch_markers']]
done=read(R/'tasks/queue/runs/wo-s1-host-shell-20261021T023427316731Z/done.json');tags=git('tag','--list').decode().splitlines()
w2=read(R/'docs/reports/evidence/w2-20261021/round2/source-manifest.json');core={p:h for p,h in w2.items() if '/tasks/queue_engine/' in p.replace('\\','/') or '/tasks/tests/' in p.replace('\\','/')};w2bad=[p for p,h in core.items() if sha(Path(p).read_bytes())!=h]
checks={'actual_tag_commit_correct':commit=='a416acf201a17eaabfa0aeae6a5144d0787a3a92','tag_source_matches_technical_audit':not bad,'current_source_matches':not currentbad,'all_twenty_card_files_appended':all(all(v['post_reboot_added'] and v['closeout_evidence_link'] and v['tag_matches_current'] and v['owner_gate_preserved'] for v in c.values()) for c in cards.values()),'queue_all_checked':not unchecked,'global_host_frozen':'| frozen |' in grow,'product_host_closed':prow['status']=='已完成' and prow['acceptance']=='已审计闭环','projections_updated':all(v['mentions_internal_tag'] and v['mentions_owner'] and v['tag_matches_current'] for v in projection.values()),'maintenance_markers_removed':all(m['absent'] and m['previously_owned'] for m in markers),'old_adapter_preserved':done['exit_code']==125 and done['receipt_valid'] is False and done['state']=='blocked','version_tag_absent':'v0.1-frozen' not in tags,'W2_core_unchanged':len(core)==20 and not w2bad}
result={'at':datetime.now(timezone.utc).isoformat(),'status':'INTERNAL_ORDER_CLOSED' if all(checks.values()) else 'ADMINISTRATIVE_READBACK_BLOCKED','owner_version_decision':'AWAITING_APPROVAL','owner_freeze_approved':False,'tag':tag,'actual_tag_commit':commit,'checks':checks,'tag_source_mismatch':bad,'current_source_mismatch':currentbad,'cards':cards,'queue_unchecked':unchecked,'global_host_row':grow,'product_host_row':prow,'projection':projection,'markers':markers,'old_adapter':done,'tags':tags,'W2_core_mismatch':w2bad}
with (O/'administrative-readback.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False,indent=2))
