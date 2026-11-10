"""Bind existing controller orchestration to the newly explicit single-case answer."""
from pathlib import Path
import ast,hashlib,json
N=Path(__file__).resolve().parents[1];O=N.parent/'e02-native-rejection-controlled-preparation-20261107-r1'
QUESTION='call_8b7f20b59b8d4855b50e36d5ccc115ba'
TEXT='候选 0421a54 的离线补修和受控入口准备已完成：927 项产品/兼容检查、346 项入口检查、独立准备审查及最终读回均通过，项目/镜像已本地提交并打 tag（7ee6b08 / 06b138c）。是否按[执行提案](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-output-budget-controlled-preparation-20261107-r1/execution-proposal.md)，明确分配一例当前 8B 的原题四来源研究及一次只读独立结果复核？保持原预算，失败不重试，无 UI、音频或生产服务操作。需要此次分配，因为你本轮明确只授权离线补修、独审和入口准备，并要求新候选实跑另行明确分配；当前额度为 0。'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(N/'manifest.json')=='2d2458b356f1836bf62cc5d616dfba61ec202bea54a4f06184f80bd27bf8fa8e'
assert sha(N/'review/independent-preparation-review.json')=='6ce6c185394aedccd4d7863471dbc56f02c533693752e375a2f69304e981b0fe'
final=json.loads((N/'verification/final-readback.json').read_bytes());assert final['verdict']=='PASS_FINAL_LOCAL_READBACK' and final['heads']['project']=='7ee6b08efdf0375278cce79e4a4a81736ad1cfc3'
changes={
    'call_92c748ab12e24ba7a135ebd26783263f':QUESTION,
    'd860b2ab4e4d9974e33c96472e4ea15abb807280':'0421a54cab572be013c3f7ad562e86406bfe8e52',
    'd860b2a':'0421a54',
    '6bdbff35be5d300ae82fc36c9f8a3098781872923882d3e855cd87e6cf1171d7':sha(N/'manifest.json'),
    '6f3af350fbda2f78291d24412e9a3e551c44cd3c17a6232e105443ef7fb9c2d2':sha(N/'review/independent-preparation-review.json'),
    'c37e81ecd9024e79b3cbcd31c44445d64823d104':final['heads']['project'],
    'jarvis-e02-native-rejection':'jarvis-e02-output-budget',
    'e02-native-rejection-controlled':'e02-output-budget-controlled',
    'SOURCE29_E02_NATIVE_REJECTION':'SOURCE31_E02_OUTPUT_BUDGET',
    'source29_preparation':'source31_preparation',
    'native_response_rejection_diagnostics_one_case':'output_budget_alignment_one_case',
    'native rejection':'output budget',
    '/root/review_e02_native_rejection_actual_result':'/root/review_e02_output_budget_actual_result',
}
bindings={}
for name in ('register_allocation.py','observe_before_case.py','run_allocated_case.py','seal_allocated_result.py','register_result_audit.py'):
    source=O/'verification'/name;target=N/'verification'/name;s=source.read_text('utf8')
    if name=='register_allocation.py':
        old=next(x for x in ast.parse(s).body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id=='question')
        lines=s.splitlines(keepends=True);lines[old.lineno-1:old.end_lineno]=['question='+repr(TEXT)+'\n'];s=''.join(lines)
    for a,b in changes.items():s=s.replace(a,b)
    ast.parse(s)
    with target.open('x',encoding='utf8',newline='\n') as f:f.write(s)
    bindings[name]=dict(source=str(source),source_sha256=sha(source),target_sha256=sha(target))
for name,h in json.loads((N/'manifest.json').read_bytes())['files'].items():assert sha(N/name)==h,name
with (N/'verification/allocation-program-bindings.json').open('x',encoding='utf8',newline='\n') as f:json.dump(dict(kind='CONTROLLER_ADAPTATION_FOR_EXPLICIT_ONE_CASE',question_id=QUESTION,files=bindings,changes='Fixed root/candidate/manifest/review/publication/question/purpose and registration bindings only. Frozen entry/adapter/product/budgets unchanged.',actual_artifacts_copied=False,actual_invocations=0),f,indent=2)
print(json.dumps(dict(question_id=QUESTION,programs=len(bindings),actual_invocations=0)))
