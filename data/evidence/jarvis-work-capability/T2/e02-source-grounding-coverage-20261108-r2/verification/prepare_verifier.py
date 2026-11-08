"""Adapt offline verification to this scope; does not execute product or model."""
from pathlib import Path
import ast,json
N=Path(__file__).resolve().parents[1];B=N.parent/'e02-claim-generation-contract-20261108-r1'
s=(B/'verification/verify_offline.py').read_text('utf8')
s=s.replace('jarvis-e02-claim-generation-r1','jarvis-e02-source-grounding-r1').replace('jarvis-e02-output-structure-r2','jarvis-e02-claim-generation-r1')
s=s.replace('e02-output-structure-controlled-preparation-20261108-r1','e02-claim-generation-controlled-preparation-20261108-r1').replace('e02-output-structure-diagnostics-20261108-r2','e02-claim-generation-contract-20261108-r1')
replacements={
 'bf7f7a9cf0e4ba559c29daa388c00379d12d345a':'d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b',
 'call_5411de619a6c4de0bab414126a228c7d':'call_3d33440cc40c401ea7a2cf11c8bc2bcf',
 '1e26155fc2bf9a256d9cd4ed694a3537ad9deca6f7915381f2412ad41d09c0ea':'223d97202583e7a7a5475c0822547339ed178cb7e3b2345d72db7e97ca5f8490',
 '7ea4b91b21285088f05e1219303d2d39a47cf8d402fc08306e3377ccc0d44a2c':'82b7d2213526760e097563a775bc23210f26124ca93d9186818dcefcebebb14f',
 'ea078190d78a340d3db06092bb050662a4a59e37e2f327c595199073b195eb1f':'c36908a9a99f290889cb420613a93d70611386ace39765e8b970f55f5ea1f16a',
 '2c12627ea8cb8a78a6359d57f30825d3cd4c5ab5be91957f7d3627815105a0c0':'ab388abe9d994ee56b985c14183d14e2af3530a499de4cfe116a8c1a2315dddf',
 '119133eb103755f972ef006d1f6381b95001e026a29daf4f973e14c5c840ab58':'065d3f6fa910976672f01c02850d0c52f1f34567ccaa295451e427efbe0bb9af',
 "'src/brain/tests/test_work_claim_generation_contract.py')":"'src/brain/tests/test_work_evidence_first_generation.py',\n         'src/brain/tests/test_work_source_coverage_budget.py','src/brain/tests/test_work_research.py',\n         'src/brain/tests/test_work_failure_diagnostics.py','src/brain/tests/test_work_source_reference_schema.py')",
 "[('src/brain/agent_server.py','_research_code_claim_sampler_pattern'),('src/brain/work_navigation.py','v3_research_phase')]":"[('src/brain/agent_server.py',{'_research_sampler_schema'}),('src/brain/work_navigation.py',{'v3_research_phase','v3_phase_inspect_schema'})]",
 "getattr(x,'name',None)!=changed_function":"getattr(x,'name',None) not in changed_function",
 '1004':'1022','product_tests=994':'product_tests=1008','reference_conversion_tests=6':'reference_conversion_tests=10',
 "len(batch['groups'])==22":"len(batch['groups'])==23",'groups=22':'groups=23',
 'final-regression-batch.json':'final-regression-batch-r3.json'
}
for a,b in replacements.items():
    assert a in s,a
    s=s.replace(a,b)
marker="    foreign=load(N/'inputs/unrelated-working-tree.json')['files']"
insert="""    parents=load(N/'inputs/plan-reviewed-parent-snapshots.json')['files']
    for name,data in parents.items():
        assert sha(Path(data['snapshot']))==data['sha256']
        assert git(C,'show',BASE+':'+Path(name).relative_to(C).as_posix())==Path(data['snapshot']).read_bytes()
    for name,h in load(N/'review/plan-inputs.json')['files'].items():
        p=Path(parents[name]['snapshot']) if name in parents else Path(name)
        assert sha(p)==h,name
"""
assert marker in s;s=s.replace(marker,insert+marker)
ast.parse(s)
with (N/'verification/verify_offline.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
f=(B/'verification/freeze_candidate.py').read_text('utf8').replace('four reviewed-plan','eight scoped').replace('emit bound operation before free claim prose','select evidence before claims and reserve unread sources').replace('claim-generation-candidate','source-grounding-candidate')
with (N/'verification/freeze_candidate.py').open('x',encoding='utf8',newline='\n') as out:out.write(f)
print('created exact offline verifier and candidate freezer; not executed')
