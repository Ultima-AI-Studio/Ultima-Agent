from pathlib import Path
import ast,hashlib,json,subprocess,xml.etree.ElementTree as ET
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
N=T/'e02-fixed-target-schema-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-fixed-target-schema/UltimaAgent')
TAG='ultimaagent-e02-fixed-target-candidate-20261107'
names={'sha','load','save_new','git','gt','checkpoint'}
tree=ast.parse((T/'e02-source13-root-entry-20261106/verification/checkpoint-task1.py').read_bytes())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'retained-checkpoint-functions','exec'),globals())
total=0;runs={}
for group,count in [('target-green',19),('diagnostics-green',17),('metadata-green',43),('research-a',68),('research-b',110),('navigation',90),('transport',104),('delivery',86)]:
    paths=[p for p in sorted((N/'offline').glob(group+'-*/receipt.json')) if load(p)['exit_code']==0 and load(p)['sources_unchanged']]
    assert paths,group
    path=paths[-1];receipt=load(path);tests=list(ET.parse(path.parent/'junit.xml').iter('testcase'))
    assert len(tests)==count and not any(t.find(tag) is not None for t in tests for tag in ('error','failure','skipped'))
    audit=load(path.parent/'offline-audit.json');assert audit['python_operations_clean'] and not audit['denied']
    for name,digest in receipt['source_sha256'].items():
        if Path(name).is_relative_to(C):assert sha(Path(name))==digest,name
    runs[group]=dict(receipt=str(path),sha256=sha(path),tests=count);total+=count
assert total==537
changed=['src/brain/work_navigation.py','src/brain/tests/test_work_fixed_target_schema.py']
assert gt(C,'diff','--name-only')=='src/brain/work_navigation.py'
assert gt(C,'ls-files','--others','--exclude-standard')=='src/brain/tests/test_work_fixed_target_schema.py'
record=checkpoint(C,[C/name for name in changed],'6cb9284c9f2bf60f2538d7cb34a124cc0bbf3696','fix(research): align generation schema with fixed research target')
save_new(N/'verification/product-checkpoint.json',dict(**record,tests=total,runs=runs,actual_calls=0))
print(json.dumps(dict(candidate=record,tests=total),ensure_ascii=False))
