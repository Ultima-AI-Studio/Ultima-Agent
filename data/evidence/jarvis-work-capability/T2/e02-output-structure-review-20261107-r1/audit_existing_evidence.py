"""Read sealed files and parse source AST only; no target import or inference."""
from pathlib import Path
import ast, datetime, hashlib, json

R=Path('H:/UltimaAI/UltimaAgent')
T=R/'data/evidence/jarvis-work-capability/T2'
N=T/'e02-output-structure-review-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-budget/UltimaAgent')
ROOTS=[T/'e02-native-rejection-controlled-preparation-20261107-r1',
       T/'e02-output-budget-controlled-preparation-20261107-r1']
EXPECTED=['9cc9e1c9c38a5f23b9e5a0d72b52bd2558a720c99abea8b11148abde483523d6',
          '3ebd6811702ed9eb09beb1c2d2efe418a491bd9f0078b9ea51db507c38b47f61']
INPUTS={}
def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):
    path=Path(path); raw=path.read_bytes(); INPUTS[str(path)]=sha(raw); return raw
def load(path):return json.loads(read(path))
def verify(mapping,root=None):
    for name,expected in mapping.items():
        p=root/name if root is not None else Path(name)
        assert sha(read(p))==expected, str(p)
    return len(mapping)
def save(name,value):
    assert not (N/'manifest.json').exists(), 'Frozen audit cannot be rewritten'
    with (N/name).open('w',encoding='utf8',newline='\n') as f:
        f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

cases=[]
for base,expected in zip(ROOTS,EXPECTED):
    mp=base/'review/result-inputs/result-manifest.json'
    assert sha(read(mp))==expected
    manifest=load(mp); review=load(base/'review/independent-result-review.json')
    assert review['result_manifest_sha256']==expected and review['verdict']=='FAIL_CONFIRMED'
    a=base/'actual/E02-controlled-1'
    verified=verify(manifest['files'],base)
    seal=load(a/'seal-index.json');sealed=verify(seal['files'],a)
    prep=load(base/'manifest.json');prepared=verify(prep['files'],base)
    d=load(a/'trusted-failure-diagnostic.raw'); ri=load(a/'runtime-inputs.json')
    assert sha(json.dumps(ri['binding_key'],ensure_ascii=False,separators=(',',':')).encode())==d['binding_sha256']
    for key in ('generation','receipt_index','request_sha256'):
        assert d['native_response'][key]==d['last_http'][key]
    assert d['native_response']['response_bytes']==d['last_http']['admitted']==d['last_http']['retained']
    assert d['native_response']['done_reason']=='length' and d['native_response']['eval_count']==2048
    assert not d['complete'] and not d['write_confirmed'] and not d['ack_confirmed']
    cases.append(dict(root=str(base),run_id=manifest['run_id'],candidate=manifest['candidate'],
        result_manifest_sha256=expected,result_members=verified,seal_members=sealed,preparation_members=prepared,
        independent_result='FAIL_CONFIRMED',native=d['native_response'],http=d['last_http'],
        private_budget=d['budget'],pages=[dict(source_id=p['source_id'],start=p['requested_start'],
            confirmed=p['confirmed'],visible=p['visible'],cards=len(p['cards'])) for p in d['pages']],
        eligible_sources=d['eligible_source_ids'],research_files=len(list((a/'outputs').rglob('research.md'))),
        full_native_response_saved=False,full_body_absence_basis='Existing independent result review and sealed result inventory; no reconstruction from hashes',
        binding_verified=True,acceptance_credit=0))

pins=load(ROOTS[-1]/'inputs/input-manifest.json')
runtime=load(ROOTS[-1]/'inputs/candidate-runtime-manifest.json')
source_count=verify(runtime['source_files'])
foreign=load(ROOTS[-1]/'inputs/unrelated-working-tree.json')
foreign_count=verify(foreign['files'],R)
anchors=[]
selected={
    C/'src/brain/agent_server.py':['_research_sampler_schema','_research_code_claim_sampler_pattern','_research_budget','_NativeResearchLeaf','_ResearchEngineView'],
    C/'src/brain/work_navigation.py':['v3_writer_schema','v3_phase_writer_schema','v3_research_phase','v3_research_envelope','resolve_v3','render_v3'],
    C/'src/brain/work_research.py':['checked_native_response','_verify_runtime_order'],
    C/'src/brain/work_research_diagnostics.py':['record_native_response_rejection','_validate_native','validate_failure_diagnostic','_project'],
    C/'src/brain/work_tools.py':['WorkResearchWriteTool'],
}
installed=R/'tools/venv-openjarvis/Lib/site-packages/openjarvis'
for relative,names in [('agents/native_react.py',['_parse_json_response','NativeReActAgent']),('engine/ollama.py',['OllamaEngine'])]:
    p=installed/relative
    assert sha(read(p))==pins['files'][str(p)],str(p)
    selected[p]=names
for path,names in selected.items():
    raw=read(path);tree=ast.parse(raw.decode('utf-8-sig'))
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in names:
            anchors.append(dict(path=str(path),symbol=node.name,start=node.lineno,end=node.end_lineno,sha256=sha(raw)))

model=Path(pins['model_manifest_path'])
assert sha(read(model))==pins['model_digest']
corpus=Path(pins['corpus_path']);assert sha(read(corpus))==pins['corpus_sha256']
for name in ['jarvis-work-native-schema-compatibility-addendum-20261102.md','jarvis-work-e02-json-string-sampler-plan-20261107.md']:
    read(R/'docs/plans'/name)
read(T/'e02-interface-reassessment-20261102/report.md')
read(T/'local-role-design-review-1/review.md')
read(R/'docs/specs/jarvis-work-capability-contract-20261101.md')
historical_grammar=T/'source7-audit-correction/grammar-failure-diagnosis'
grammar_receipt=load(historical_grammar/'readback.json')
assert sha(read(historical_grammar/'failed-native-schema.json'))==grammar_receipt['schema_sha256']
assert sha(read(historical_grammar/'rejected.gbnf'))=='8640469f3cc859a43e933ed0aad55b3a32f019b00ecbcfb4b036300d34ed3471'
read(ROOTS[-1]/'harness/adapter.py')
read(ROOTS[-1]/'harness/test_adapter.py')

# These are shape-only byte calculations, never product responses or token estimates.
shapes=[]
for count in (1,3,6):
    obj=dict(action='ultima_work_research_write',action_input=dict(path='research.md',title='x',
        sections=[dict(source_id=f'S{i}',heading='x',facts=[dict(claim='x',evidence_id='N3.'+'0'*16) for _ in range(count)]) for i in range(1,4)]))
    wire=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode()
    shapes.append(dict(sections=3,facts_per_section=count,total_facts=3*count,
        compact_ascii_bytes=len(wire),placeholder_text_bytes=4+3*count,
        structural_bytes_excluding_placeholder_text=len(wire)-(4+3*count),
        synthetic_only=True,semantic_validity=False,token_count=None))

analysis=dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    scope='ROOT_READONLY_AUDIT_NOT_INDEPENDENT_PREPARATION_PASS',cases=cases,
    current_source_hashes_verified=source_count,foreign_tracked_hashes_unchanged=foreign_count,
    model_manifest_matches_frozen_digest=True,corpus_matches_original=True,
    historical_string_bound_grammar_failure='Recorded HTTP400 and repeated-rule complexity; previous incident only, not current failure cause',
    source_anchors=anchors,shape_calculations=shapes,
    budget_arithmetic=dict(original=dict(inspect=6,write=1,ack=1,total=8),
        six_inspect_plus_three_drafts_plus_one_commit_plus_ack=11,
        six_inspect_plus_three_combined_draft_writes_plus_ack=10,
        two_inspect_plus_four_drafts_plus_commit_plus_ack=8,
        latter_violates_unchanged_phase_contract=True,
        note='Single-source draft numbers are hypothetical POST counts, not executions; aggregate output budget also cannot be expanded.'),
    generation_calls_by_this_audit=0,product_imports=0,product_changes=0,network_calls=0,independent_reviews=0,
    hypotheses_not_proven=['field growth or repeated facts caused exhaustion','thinking tokens consumed budget','invalid inner JSON','serialization key overhead is dominant'],
    future_change_decision='Bounded rejection diagnostics first; retain single atomic write and full original acceptance; no functional fix selected without actual content evidence')
save('analysis.json',analysis)
save('input-hashes.json',dict(recorded_utc=analysis['recorded_utc'],files=INPUTS))
print(json.dumps(dict(status='READONLY_ANALYSIS_COMPLETE',cases=2,result_members=[c['result_members'] for c in cases],
    seal_members=[c['seal_members'] for c in cases],source_files=source_count,foreign_files=foreign_count,
    shapes=shapes,read_inputs=len(INPUTS),product_changes=0,model_calls=0),ensure_ascii=False))
