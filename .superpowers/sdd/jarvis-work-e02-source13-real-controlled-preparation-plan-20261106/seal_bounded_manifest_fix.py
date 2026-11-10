from pathlib import Path
import ast,datetime as dt,hashlib,json,difflib
R=Path(r'H:\UltimaAI\UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
OLD=T/'e02-source13-real-controlled-preparation-20261106';N=T/'e02-source13-real-controlled-preparation-20261107-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
base=load(OLD/'manifest.json')
for name,digest in base['files'].items():assert sha(OLD/name)==digest,name
assert sha(OLD/'review/independent-preparation-review.json')=='5dbb5c54eb38b5c8e4b04cb7e280cf7d5c9dd2e057dedeea20eac1999da4220f'
for name in ['code/entry.py','code/bindings.py',*('harness/'+p for p in ('adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md','manifest.json'))]:assert sha(N/name)==sha(OLD/name),name
red=load(N/'offline/entry-review-red/receipt.json');green=load(N/'offline/entry-review-green/receipt.json')
assert red['exit_code']==1 and red['result']['errors']==1 and green['exit_code']==0 and green['result']['tests']==26
assert not red['result']['denied'] and not green['result']['denied']
for path,digest in green['sources'].items():assert sha(Path(path))==digest,path
proposal=N/'execution-proposal.md';text=proposal.read_text('utf8')
assert str(OLD/'code/entry.py') in text
text=text.replace(str(OLD/'code/entry.py'),str(N/'code/entry.py')).replace('269项','270项').replace('25入口','26入口')
text+='\n## PREP-I01补修\n\n旧包与NEEDS_FIXES报告保持原字节。本候选仅统一封存路径为正斜杠；实际入口、harness、产品和模型未改。新增回归直接提取实际manifest生产函数，已观察Windows旧表示失败、规范表示通过；新入口回归26项。新目录不重置任何历史次数或预算，仍没有实际分配。\n'
proposal.write_text(text,encoding='utf8')
members={N/name for name in base['files']}
members.update(p for p in (N/'revision').iterdir() if p.is_file())
members.add(N/'verification/readiness_smoke.py')
for stage in ('entry-review-red','entry-review-green'):
    members.update(p for p in (N/'offline'/stage).rglob('*') if p.is_file())
tree=ast.parse((N/'verification/prepare_review.py').read_bytes());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='member_name')
namespace={'N':N};exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-canonical-manifest-producer','exec'),namespace)
keys={namespace['member_name'](p):sha(p) for p in sorted(members)}
assert all('\\' not in key for key in keys) and 'code/entry.py' in keys
manifest=dict(base,prepared_utc=dt.datetime.now(dt.timezone.utc).isoformat(),test_count=270,files=keys,
    correction='PREP-I01',previous_manifest_sha256=sha(OLD/'manifest.json'),previous_review_sha256=sha(OLD/'review/independent-preparation-review.json'))
with (N/'manifest.json').open('x',encoding='utf8') as f:json.dump(manifest,f,ensure_ascii=False,indent=2)
(N/'review').mkdir(exist_ok=False)
changed=[name for name,digest in base['files'].items() if sha(N/name)!=digest]
with (N/'revision/changed-members.json').open('x',encoding='utf8') as f:json.dump(dict(changed=changed,new_manifest_sha256=sha(N/'manifest.json'),source_runtime_bytes_unchanged=True),f,indent=2)
print(json.dumps(dict(manifest_sha256=sha(N/'manifest.json'),members=len(keys),changed=changed,tests=270)))
