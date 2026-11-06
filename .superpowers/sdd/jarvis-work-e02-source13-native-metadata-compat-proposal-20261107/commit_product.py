from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess,xml.etree.ElementTree as ET
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2';N=T/'e02-source13-native-metadata-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-native-metadata/UltimaAgent')
TAG='ultimaagent-e02-native-metadata-candidate-20261107'
names={'sha','load','save_new','git','gt','checkpoint'}
tree=ast.parse((T/'e02-source13-root-entry-20261106/verification/checkpoint-task1.py').read_bytes())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'retained-checkpoint-functions','exec'),globals())
total=0;runs={}
for group,count in [('metadata-green',43),('research-a',68),('research-b',110),('navigation',90),('transport',104),('delivery',86)]:
    path=[p for p in sorted((N/'offline').glob(group+'-*/receipt.json')) if load(p)['exit_code']==0 and load(p)['sources_unchanged']][-1]
    receipt=load(path);tests=list(ET.parse(path.parent/'junit.xml').iter('testcase'))
    assert len(tests)==count and not any(t.find(tag) is not None for t in tests for tag in ('error','failure','skipped'))
    audit=load(path.parent/'offline-audit.json');assert audit['python_operations_clean'] and not audit['denied']
    for name,digest in receipt['source_sha256'].items():
        if Path(name).is_relative_to(C):assert sha(Path(name))==digest,name
    runs[group]=dict(receipt=str(path),sha256=sha(path),tests=count);total+=count
assert total==501
changed=['src/brain/work_research.py','src/brain/tests/test_native_metadata_compat.py','src/brain/tests/fixtures/native_metadata_0_32_15.json']
deps=load(N/'inputs/copied-frozen-dependencies.json')
for row in deps:
    assert sha(Path(row['source']))==sha(Path(row['destination']))==row['sha256']
    changed.append(Path(row['destination']).relative_to(C).as_posix())
assert len(changed)==7
record=checkpoint(C,[C/name for name in changed],'269aca511d88412dbb9c15d23911138469a37aa2','fix(research): validate optional native model capabilities without weakening identity')
save_new(N/'verification/product-checkpoint.json',dict(**record,tests=total,runs=runs,dependency_files_copied_verbatim=4,actual_calls=0))
print(json.dumps(dict(candidate=record,tests=total),ensure_ascii=False))
