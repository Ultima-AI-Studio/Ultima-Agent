"""Bind existing one-case orchestration to the actual explicit user reply."""
from pathlib import Path
import ast,hashlib,json
N=Path(__file__).resolve().parents[1];O=N.parent/'e02-output-budget-controlled-preparation-20261107-r1'
QUESTION='call_5c06d21b59b8475b873814f857990cc3'
TEXT='候选 bf7f7a9 的证据采集入口已完成 350 项新鲜检查、独立准备审查和本地提交/tag/镜像读回（项目 dff378f，镜像 17b53ac）。是否按[执行提案](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-output-structure-controlled-preparation-20261108-r1/execution-proposal.md)，明确分配一例当前 8B 的原题四来源研究及一次只读独立结果复核？保持原预算和完整原题验收，失败不重试；无 UI、音频或生产服务操作。需要此次分配，因为你此前要求“明确分配单例后”才实跑，当前额度为 0。'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(N/'manifest.json')=='ea078190d78a340d3db06092bb050662a4a59e37e2f327c595199073b195eb1f'
assert sha(N/'review/independent-preparation-review.json')=='85dc915c2712f6af7132456904dfa4d429e97b7a85aff4de2bb762fa80c22fe4'
final=json.loads((N/'verification/final-readback.json').read_bytes())
assert final['verdict']=='PASS_FINAL_LOCAL_READBACK' and final['heads']['project']=='dff378fec3ce30f9c252a4713147bc389e22c125'
changes={
    'call_8b7f20b59b8d4855b50e36d5ccc115ba':QUESTION,
    '0421a54cab572be013c3f7ad562e86406bfe8e52':'bf7f7a9cf0e4ba559c29daa388c00379d12d345a',
    '0421a54':'bf7f7a9',
    '2d2458b356f1836bf62cc5d616dfba61ec202bea54a4f06184f80bd27bf8fa8e':sha(N/'manifest.json'),
    '6ce6c185394aedccd4d7863471dbc56f02c533693752e375a2f69304e981b0fe':sha(N/'review/independent-preparation-review.json'),
    '7ee6b08efdf0375278cce79e4a4a81736ad1cfc3':final['heads']['project'],
    'jarvis-e02-output-budget':'jarvis-e02-output-structure-r2',
    'e02-output-budget-controlled':'e02-output-structure-controlled',
    'SOURCE31_E02_OUTPUT_BUDGET':'SOURCE33_E02_OUTPUT_STRUCTURE',
    'source31_preparation':'source33_preparation',
    'output_budget_alignment_one_case':'output_structure_evidence_one_case',
    'output budget':'output structure',
    '/root/review_e02_output_budget_actual_result':'/root/review_e02_output_structure_actual_result',
    '## 2026-11-07 E02':'## 2026-11-08 E02',
}
bindings={}
for name in ('register_allocation.py','observe_before_case.py','run_allocated_case.py','seal_allocated_result.py','register_result_audit.py'):
    source=O/'verification'/name;target=N/'verification'/name;s=source.read_text('utf8')
    if name=='register_allocation.py':
        old=next(x for x in ast.parse(s).body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id=='question')
        lines=s.splitlines(keepends=True);lines[old.lineno-1:old.end_lineno]=['question='+repr(TEXT)+'\n'];s=''.join(lines)
    for before,after in changes.items():s=s.replace(before,after)
    if name=='seal_allocated_result.py':
        s=s.replace("N/'verification/verify_preservation.py'","N/'verification/verify_result_preservation.py'")
        s=s.replace("packet['kind']=='research_failure_diagnostic_v4'","packet['kind'] in ('research_failure_diagnostic_v3','research_failure_diagnostic_v4','research_failure_diagnostic_v5')")
        s=s.replace("native_response=packet['native_response']","native_response=packet.get('native_response')")
        point="    summary['completed_native_posts']=packet['budget']['completed_posts']"
        assert s.count(point)==1
        extra="""
    structure=packet.get('output_structure')
    if structure is not None:
        evidence=structure['evidence']
        summary['output_structure_metadata']=dict(native_binding=structure['native_binding'],request=structure['request'],
            message=structure['message'],json=structure['json'],evidence=dict(mode=evidence['mode'],
                omitted_chars=evidence['omitted_chars'],fragment_ranges=[dict(start=f['start'],end=f['end']) for f in evidence['fragments']]))
"""
        s=s.replace(point,point+extra)
    ast.parse(s)
    with target.open('x',encoding='utf8',newline='\n') as f:f.write(s)
    bindings[name]=dict(source=str(source),source_sha256=sha(source),target_sha256=sha(target))
for name,h in json.loads((N/'manifest.json').read_bytes())['files'].items():assert sha(N/name)==h,name
with (N/'verification/allocation-program-bindings.json').open('x',encoding='utf8',newline='\n') as f:json.dump(dict(kind='CONTROLLER_ADAPTATION_FOR_EXPLICIT_ONE_CASE',question_id=QUESTION,files=bindings,changes='Fixed root/candidate/manifest/review/publication/question/purpose/registration only in launch programs. Post-result sealer reads v3/v4/v5 and exports metadata without content fragments; post-result preservation uses immutable file pins rather than obsolete pre-allocation state assertions. Frozen entry/adapter/product/budgets unchanged.',actual_artifacts_copied=False,actual_invocations=0),f,indent=2)
print(json.dumps(dict(question_id=QUESTION,programs=len(bindings),actual_invocations=0)))
