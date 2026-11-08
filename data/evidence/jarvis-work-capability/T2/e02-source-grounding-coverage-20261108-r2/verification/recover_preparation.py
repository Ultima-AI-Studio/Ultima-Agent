"""Preserve r1 and correct only live observation of one unrelated changing file."""
from pathlib import Path
import ast,datetime as dt,hashlib,importlib.util,json
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
O=T/'e02-source-grounding-coverage-20261108-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
review=load(O/'review/independent-preparation-review.json')
assert review['verdict']=='NEEDS_FIXES' and review['candidate']=='43da3f014a763b8ea3963872a8f1ce8ebea77531'
manifest=load(O/'manifest.json');assert sha(O/'manifest.json')=='1d4b39c7457eb146fae9ab33f59c945de0b6e9ea74236271d25a37e9f23cae4f'
for name,h in manifest['files'].items():assert sha(O/name)==h,name
for name in manifest['files']:
    target=N/name;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write((O/name).read_bytes())
for src,dst in [('manifest.json','inputs/previous-preparation-manifest.json'),('review/independent-preparation-review.json','review/previous-preparation-review.json'),('review/independent-preparation-review.md','review/previous-preparation-review.md'),('progress.md','progress.md')]:
    with (N/dst).open('xb') as f:f.write((O/src).read_bytes())
p=N/'verification/verify_offline.py';s=p.read_text('utf8')
a=s.index('def foreign_readback():');b=s.index('def verify():',a)
s=s[:a]+'''def foreign_readback():
    original=load(N/'inputs/unrelated-working-tree.json')['files']
    observation=load(N/'inputs/unrelated-change-observation.json')
    assert observation['baseline_manifest_sha256']==sha(N/'inputs/unrelated-working-tree.json')
    changes=observation['observed_changes'];assert set(changes)=={'docs/tracker/北极星上线任务清单.html'}
    for name,h in original.items():
        if name in changes:
            data=changes[name];assert h==data['baseline_sha256']
            assert sha(Path(data['snapshot']))==data['observed_sha256']
            # This is explicitly not a model/product/dependency input. Observe
            # concurrent changes without granting any authority to write it.
            assert str(R/name) not in load(P/'inputs/input-manifest.json')['files']
            assert str(R/name) not in load(N/'inputs/current-inputs.json')['files']
        else:assert sha(R/name)==h,name
    target=R/next(iter(changes))
    return dict(files=len(original),baseline_unchanged=14,out_of_scope_observed=1,
                original_and_observed_snapshots_preserved=True,current_unowned_sha256=sha(target),
                current_unowned_mtime_ns=target.stat().st_mtime_ns,live_unowned_equality_required=False)
''' +s[b:]
ast.parse(s);p.write_text(s,encoding='utf8',newline='\n')
# Publication must also preserve every original r1 member and its failed review.
p=N/'verification/publish.py';s=p.read_text('utf8')
needle="project={N/name for name in manifest['files']}"
assert needle in s
s=s.replace(needle,needle+"\nprior_root=N.parent/'e02-source-grounding-coverage-20261108-r1'\nprior_manifest=v.load(prior_root/'manifest.json')\nfor name,h in prior_manifest['files'].items():assert v.sha(prior_root/name)==h,name\nproject.update(prior_root/name for name in prior_manifest['files'])\nproject.update(prior_root/name for name in ('manifest.json','review/independent-preparation-review.json','review/independent-preparation-review.md','progress.md'))")
p.write_text(s,encoding='utf8',newline='\n')
# Entry adopts identical observation-only treatment; it must never mutate HTML.
p=N/'verification/prepare_entry_tools.py';s=p.read_text('utf8')
s=s.replace("assert sha(R/name)==data['observed_sha256'];foreign['files'][name]=data['observed_sha256']","foreign['files'][name]=data['observed_sha256']")
s=s.replace("B=T/'e02-source-grounding-coverage-20261108-r1'","B=T/'e02-source-grounding-coverage-20261108-r2'")
needle="write('verify_preservation.py',s)" # actual generic loop is handled below
old="write(name,common((O/'verification'/name).read_text('utf8')))"
new="""s=common((O/'verification'/name).read_text('utf8'))
    if name=='verify_preservation.py':
        s=s.replace(\"for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(N.parents[4]/name)==h,name\",\"for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():\\n        if name!='docs/tracker/北极星上线任务清单.html':assert sha(N.parents[4]/name)==h,name\")
    if name in ('publish.py','final_readback.py'):
        s=s.replace(\"for name,digest in json.loads((N/'inputs/unrelated-working-tree.json').read_bytes())['files'].items():assert sha(R/name)==digest,name\",\"for name,digest in json.loads((N/'inputs/unrelated-working-tree.json').read_bytes())['files'].items():\\n    if name!='docs/tracker/北极星上线任务清单.html':assert sha(R/name)==digest,name\")
        s=s.replace(\"for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==h,name\",\"for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():\\n    if name!='docs/tracker/北极星上线任务清单.html':assert sha(R/name)==h,name\")
        s=s.replace(\"foreign_files_unchanged=len(json.loads((N/'inputs/unrelated-working-tree.json').read_bytes())['files'])\",\"foreign_files_unchanged=14,unowned_dynamic_file_excluded_from_write=True\").replace('foreign_preserved=15','foreign_preserved=14,unowned_dynamic_file_not_written=True')
    write(name,s)"""
assert old in s;s=s.replace(old,new);ast.parse(s);p.write_text(s,encoding='utf8',newline='\n')
p=N/'preparation-report.md';s=p.read_text('utf8')
s=s.replace('本报告封存时准备独审待办','本r2报告封存时准备独审待办，r1保全绑定失败审查保留')
s=s.replace('后续严格核对该观察值，不回写、不纳入提交','后续只记录当前变化，原与各次观察快照仍严格核对，不回写、不暂存原HTML')
s+='\n## r2保全登记修正\n\nr1候选与4293成员完全匹配，但独审时无关HTML再次变化，导致旧观察相等门失败；NEEDS_FIXES原样保留。r2只修改证据登记：此明确非产品/模型/依赖输入的HTML允许并发变化，动态摘要用于报告，不成为产品准入或写入权限；其余14文件和全部源码、依赖、历史证据仍逐字节相等。原HTML不在任何提交路径，仅快照落盘。新候选43da3f0和本轮1022检查均未改变，不重跑产品测试。新包必须再独审，本轮仍actual/model0。\n'
p.write_text(s,encoding='utf8',newline='\n')
spec=importlib.util.spec_from_file_location('r2_readback',N/'verification/verify_offline.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
checked=v.verify();save(N/'verification/recovery-offline-readback.json',checked)
save(N/'inputs/preparation-recovery.json',dict(previous_root=str(O),previous_manifest_sha256=sha(O/'manifest.json'),previous_review_sha256=sha(O/'review/independent-preparation-review.json'),previous_members=4293,candidate=manifest['candidate'],product_changed=False,product_tests_rerun=False,tests=1022,reason='One unrelated live HTML observation equality removed; immutable snapshots and all product/dependency pins remain strict',actual_cases=0))
members=[p for p in N.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='progress.md']
save(N/'manifest.json',dict(manifest,kind='OFFLINE_SOURCE_GROUNDING_COVERAGE_PREPARATION_R2',previous_preparation_sha256=sha(O/'manifest.json'),files={p.relative_to(N).as_posix():sha(p) for p in sorted(members)},created_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
state=load(T/'current-run.json');state.update(active_evidence=str(N),phase='SOURCE36_E02_SOURCE_GROUNDING_PREPARATION_R2_REVIEW',active_review_agent='/root/review_e02_source_grounding_preparation_r2')
state['source36_offline'].update(root=str(N),manifest_sha256=sha(N/'manifest.json'),status='PREPARATION_R2_REVIEW_UNOWNED_DYNAMIC_FILE_OBSERVATION_ONLY')
(T/'current-run.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(dict(candidate=manifest['candidate'],members=len(members),manifest_sha256=sha(N/'manifest.json'),tests=1022,product_changed=False)))
