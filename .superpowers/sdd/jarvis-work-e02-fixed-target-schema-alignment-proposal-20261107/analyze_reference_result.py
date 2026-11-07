"""Read sealed diagnostics and fixed code only; allocate the granted result review."""
from pathlib import Path
import datetime as dt,hashlib,json
R=Path('H:/UltimaAI/UltimaAgent');N=R/'data/evidence/jarvis-work-capability/T2/e02-fixed-target-schema-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-fixed-target-schema/UltimaAgent')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
b=load(N/'review/result-inputs/byte-readback.json');d=b['research_failure']
assert d==load(N/'actual/E02-controlled-1/product-result.json')['research_failure']==load(N/'actual/E02-controlled-1/service-first-result.json')['research_failure']
assert d==dict(stage='research.write',reason_code='FOREIGN_REFERENCE',error_type='ValueError',error_text_length=17,error_text_sha256=hashlib.sha256(b'Foreign reference').hexdigest())
nav=(C/'src/brain/work_navigation.py').read_text('utf8');writer=(C/'src/brain/work_tools.py').read_text('utf8')
assert nav.count("raise ValueError('Foreign reference')")==1
assert "if ref not in issued: raise ValueError('Unknown or unissued reference')" in nav
assert "if view.source_id!=sid: raise ValueError('Foreign reference')" in nav
assert writer.index("if params.get('path')!='research.md'")<writer.index('resolved, bindings = resolve_v3(params,snapshot,self.ledger._collection)')
proof=dict(kind='STATIC_CURRENT_RESULT_ATTRIBUTION_ONLY',candidate=b['candidate'],run_id=b['run_id'],result_manifest_sha256=sha(N/'review/result-inputs/result-manifest.json'),diagnostic=d,
    fixed_message='Foreign reference',condition='issued reference exists, but its owning view.source_id differs from submitted section.source_id',
    path_guard_precedes_resolution=True,exact_reference_id='UNKNOWN_NOT_EXPORTED',exact_submitted_source_id='UNKNOWN_NOT_EXPORTED',exact_owning_source_id='UNKNOWN_NOT_EXPORTED',
    old_failures_re_attributed=False,fact_quality_inferred=False,
    source_files={str(C/name):sha(C/name) for name in ('src/brain/work_navigation.py','src/brain/work_tools.py','src/brain/agent_server.py','src/brain/work_research.py','src/brain/work_service.py')},
    tests=0,model_calls=0,product_calls=0)
save(N/'verification/reference-contract-readback.json',proof)
scope=load(N/'inputs/granted-scope.json')
save(N/'review/result-review-allocation.json',dict(kind='ONE_READONLY_FIXED_TARGET_RESULT_REVIEW',question_id=scope['question_id'],answer=scope['answer'],result_manifest_sha256=proof['result_manifest_sha256'],run_id=b['run_id'],reviewer='/root/review_e02_fixed_target_result',allocated=1,consumed=1,remaining=0,new_actual_case=0,tests=0,retry=0,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
print(json.dumps(dict(reason=d['reason_code'],run_id=b['run_id'],review_allocated=1,new_case=0)))
