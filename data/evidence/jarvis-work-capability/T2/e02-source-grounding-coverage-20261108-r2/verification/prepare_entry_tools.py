"""Prepare exact entry binding tools after Task3 plan review, without executing an entry."""
from pathlib import Path
import ast,json
B=Path(__file__).resolve().parents[1];T=B.parent
O=T/'e02-claim-generation-controlled-preparation-20261108-r1'
N=T/'e02-source-grounding-controlled-preparation-20261108-r1'
HEAD=json.loads((B/'verification/candidate-freeze.json').read_bytes())['candidate']
assert json.loads((N/'review/independent-plan-review.json').read_bytes())['verdict']=='PASS_PLAN_ONLY'
def common(s):
    replacements={
      'jarvis-e02-claim-generation-r1':'jarvis-e02-source-grounding-r1',
      'jarvis-e02-output-structure-r2':'jarvis-e02-claim-generation-r1',
      'e02-claim-generation-contract-20261108-r1':B.name,
      'e02-output-structure-controlled-preparation-20261108-r1':O.name,
      'jarvis-work-e02-claim-generation-controlled-entry-plan':'jarvis-work-e02-source-grounding-controlled-entry-plan',
      'jarvis-work-t2-e02-claim-generation-controlled-preparation':'jarvis-work-t2-e02-source-grounding-controlled-preparation',
      'e02-claim-generation-controlled-20261108':'e02-source-grounding-controlled-20261108',
      'ultimaagent-e02-claim-generation-candidate':'ultimaagent-e02-source-grounding-candidate',
      'ultimaagent-e02-claim-generation-controlled-ready':'ultimaagent-e02-source-grounding-controlled-ready',
      'd8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b':HEAD,'d8f8d97':HEAD[:7],
      'call_5411de619a6c4de0bab414126a228c7d':'call_3d33440cc40c401ea7a2cf11c8bc2bcf',
      '授权离线补修、必要独审与入口准备（推荐）':'授权离线审查、最小补修、必要独审与入口准备（推荐）',
      'SOURCE35':'SOURCE37','source35':'source37','CLAIM_GENERATION':'SOURCE_GROUNDING',
      'FROZEN_N34':'FROZEN_N36','N34 frozen994 product plus4 compatibility plus6 official reference':'N36 frozen1008 product plus4 compatibility plus10 official reference',
      'N34 product994 plus compatibility4 and official reference6':'N36 product1008 plus compatibility4 and official reference10',
      '1004':'1022','len(sources)==78':'len(sources)==79',"len(current['source_files'])==78":"len(current['source_files'])==79",'78 sources bound':'79 sources bound',
      "goal_status='blocked',goal_registry_status='blocked'":"goal_status='none',goal_registry_status='cleared_by_user'",
      "state['goal_status']==state['goal_registry_status']=='blocked'":"state['goal_status']=='none' and state['goal_registry_status']=='cleared_by_user'",
      'operation-first code claim':'evidence-first and source-reserve',
      'Frozen operation-first claim':'Frozen evidence-first and source-reserve',
      'claim-generation controlled entry preparation':'source-grounding controlled entry preparation',
      'e02_claim_generation_controlled_preparation':'e02_source_grounding_controlled_preparation',
      'claim generation controlled preparation reviewed':'source grounding controlled preparation reviewed',
      'bind operation-first claim candidate':'bind evidence-first source-reserve candidate',
      'mirror claim generation controlled entry':'mirror source grounding controlled entry'
    }
    for a,b in replacements.items():s=s.replace(a,b)
    return s
def write(name,s):
    ast.parse(s)
    with (N/'verification'/name).open('x',encoding='utf8',newline='\n') as f:f.write(s)
s=common((O/'verification/rebind.py').read_text('utf8'))
s=s.replace("decision_id='call_3d33440cc40c401ea7a2cf11c8bc2bcf'","decision_id='user-message:sha256:'+hashlib.sha256(answer.encode('utf8')).hexdigest()")
s=s.replace("dict(source='user_question_reply',question_id=decision_id", "dict(source='user_question_reply',source_question_id='call_3d33440cc40c401ea7a2cf11c8bc2bcf',question_id=decision_id")
s=s.replace('identifier_is_platform_message_id=True','identifier_is_platform_message_id=False')
s=s.replace('Actual preparation question id; grants no actual case or result review','Content-derived preparation binding, not a platform id; source_question_id preserves the actual offline answer; allocations remain zero')
needle="copy(B/'inputs/unrelated-working-tree.json',N/'inputs/unrelated-working-tree.json')"
replacement="""foreign=load(B/'inputs/unrelated-working-tree.json');observed=load(B/'inputs/unrelated-change-observation.json')
for name,data in observed['observed_changes'].items():
    foreign['files'][name]=data['observed_sha256']
save(N/'inputs/unrelated-working-tree.json',foreign)
save(N/'inputs/unrelated-baseline-provenance.json',dict(original=str(B/'inputs/unrelated-working-tree.json'),original_sha256=sha(B/'inputs/unrelated-working-tree.json'),observation=str(B/'inputs/unrelated-change-observation.json'),observation_sha256=sha(B/'inputs/unrelated-change-observation.json'),original_unchanged=14,out_of_scope_observed=1,files_written_by_task=0))"""
assert needle in s;s=s.replace(needle,replacement)
needle="hm=load(N/'harness/manifest.json');"
addition="""# Same negative export purpose; reserve now rejects third repeated read.
test=N/'harness/test_adapter.py';text=test.read_text('utf8')
assert text.count('reads,posts,validated=4,5,False')==1
assert text.count("len(packet['pages'])==4")==1
text=text.replace('reads,posts,validated=4,5,False','reads,posts,validated=2,3,False').replace("len(packet['pages'])==4","len(packet['pages'])==2")
test.write_text(text,encoding='utf8',newline='\\n')
"""
assert needle in s;s=s.replace(needle,addition+needle)
write('rebind.py',s)
s=common((O/'verification/verify_preparation.py').read_text('utf8'))
a=s.index("    recovery=load(");b=s.index("    review=load(",a);s=s[:a]+s[b:]
a=s.index("    historical=load(");b=s.index('    groups={}',a);s=s[:a]+s[b:]
s=s.replace("        if str(path) in historical['harness_receipts']+second['harness_receipts']:continue\n",'')
s=s.replace(",first_attempt_failures_preserved=3,second_attempt_failure_preserved=1,first_attempt_index_sha256=sha(N/'verification/first-attempt-index.json')",'')
s=s.replace('two sampler fixture expressions migrated','reserved-read export fixture counts migrated')
write('verify_preparation.py',s)
for name in ('verify_preservation.py','run_final_checks.py','closeout.py','publish.py','final_readback.py'):
    s=common((O/'verification'/name).read_text('utf8'))
    if name=='verify_preservation.py':
        s=s.replace("for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(N.parents[4]/name)==h,name","for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():\n        if name!='docs/tracker/北极星上线任务清单.html':assert sha(N.parents[4]/name)==h,name")
    if name in ('publish.py','final_readback.py'):
        s=s.replace("for name,digest in json.loads((N/'inputs/unrelated-working-tree.json').read_bytes())['files'].items():assert sha(R/name)==digest,name","for name,digest in json.loads((N/'inputs/unrelated-working-tree.json').read_bytes())['files'].items():\n    if name!='docs/tracker/北极星上线任务清单.html':assert sha(R/name)==digest,name")
        s=s.replace("for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==h,name","for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():\n    if name!='docs/tracker/北极星上线任务清单.html':assert sha(R/name)==h,name")
        s=s.replace("foreign_files_unchanged=len(json.loads((N/'inputs/unrelated-working-tree.json').read_bytes())['files'])","foreign_files_unchanged=14,unowned_dynamic_file_excluded_from_write=True").replace('foreign_preserved=15','foreign_preserved=14,unowned_dynamic_file_not_written=True')
    write(name,s)
runtime='''from pathlib import Path
import ast,datetime as dt,hashlib,json
N=Path(__file__).resolve().parents[1];T=N.parent
O=T/'e02-claim-generation-controlled-preparation-20261108-r1';B=T/'e02-source-grounding-coverage-20261108-r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def funcs(p):return {x.name:ast.dump(x,include_attributes=False) for x in ast.parse(p.read_bytes()).body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
for name in ('code/entry.py','code/bindings.py','harness/adapter.py'):assert funcs(N/name)==funcs(O/name)
base=json.loads((B/'inputs/current-inputs.json').read_bytes())
historical=[O/'verification/runtime-readiness-pending.json',Path(base['protected_baseline_path'])]
value=dict(status='PENDING_FRESH_ACTUAL_PREFLIGHT',candidate=HEAD,current_runtime_verified=False,actual_preflight_unchanged=True,historical_files={str(p):sha(p) for p in historical},historical_evidence_is_current_proof=False,reason='Offline authorization; only future allocated original preflight may establish current runtime readiness',actual_cases=0,model_calls=0,network_requests=0,service_operations=0,os_packets=None,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
with (N/'verification/runtime-readiness-pending.json').open('x',encoding='utf8') as f:json.dump(value,f,indent=2)
print(json.dumps(dict(status=value['status'],current_runtime_verified=False,actual=0)))
'''.replace('candidate=HEAD','candidate='+repr(HEAD))
write('record_pending_runtime.py',runtime)
print(json.dumps(dict(status='ENTRY_TOOLS_PREPARED_NOT_RUN',candidate=HEAD,actual=0)))
