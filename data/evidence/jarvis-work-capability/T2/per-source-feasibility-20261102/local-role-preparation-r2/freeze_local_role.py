"""Offline freeze. No SDK engine owner, inference or actual namespace."""
import os,sys,json,hashlib,difflib
from pathlib import Path
P=Path(__file__).parent
for key,folder in [('TEMP','temp'),('TMP','temp'),('TMPDIR','temp'),('OPENJARVIS_HOME','sdk-home'),('HF_HOME','cache'),('XDG_CACHE_HOME','cache')]:os.environ[key]=str(P/folder)
os.environ['HF_HUB_OFFLINE']=os.environ['TRANSFORMERS_OFFLINE']='1'
sys.dont_write_bytecode=True
import run_local_role_prefix as h
core=h.frozen_core();core.socket_guard(mock=True);sys.path.insert(0,str(core.CHECKOUT))
from types import SimpleNamespace
from openjarvis.security.guardrails import GuardrailsEngine
from openjarvis.security.types import RedactionMode
old=h.read(h.OLD_MANIFEST)
proof=[]
query,sources=core.load_material()
for source in (sources[3],sources[0]):
 view,omitted=core.project(source);table=core.cards(source,view)
 ledger=core.StageLedger(dict(request_id='template',session_id='template',task_id='template'),source,view,table,36,lambda:0)
 ledger.token=h.SENTINEL;ledger.schema=core.schema_for(ledger.token,table)
 prefix=core.PrefixView(SimpleNamespace(_inner=GuardrailsEngine(SimpleNamespace(),mode=RedactionMode.REDACT)),ledger,query)
 prefix.prepare()
 prior=h.read(h.E/'preparation-r2'/(source['source_id']+'-template.json'))
 current=dict(source=source,view=view,omitted_ranges=omitted,table=ledger.table,schema=ledger.schema,raw_messages=prefix.raw_messages,
              preflight_messages=prefix.preflight_messages,lineage=prefix.preflight_lineage,decoded_query_sha256=core.sha(query.encode('utf8')))
 for key in ('source','view','omitted_ranges','schema'):
  assert core.compact(prior[key])==core.compact(current[key]),key
 assert {str(k):v for k,v in ledger.table.items()}==prior['table']
 for field in ('raw_messages','preflight_messages'):
  pm=prior[field];nm=current[field]
  old_system=pm[0]['content']
  expected=old_system.replace('If this source is irrelevant or insufficient, submit a short unused_reason instead.','Your deliverable is the contribution of this source to any part of the background question. If its visible evidence cannot support even one relevant claim under the citation rules, submit a short unused_reason instead.')
  assert expected==nm[0]['content']
  user=core.strict(pm[1]['content']);newuser=core.strict(nm[1]['content'])
  assert user.pop('original_query')==newuser.pop('background_original_query')==query
  assert user==newuser
 core.save(P/(source['source_id']+'-template.json'),current)
 proof.append(dict(source_id=source['source_id'],decoded_body_sha256=source['decoded_body_sha256'],decoded_query_sha256=current['decoded_query_sha256'],
                   visible_lines=len(view['lines']),eligible_lines=len(ledger.visible),cards=len(ledger.table),schema_equal=True,
                   raw_and_secured_only_two_approved_differences=True,token_convention=h.SENTINEL))
(P/'prompt.txt').write_text(core.PROMPT,encoding='utf8');core.save(P/'projection-proof.json',proof)
first=[dict(source_id='S2',path=str(h.ORIGINAL),sha256=h.ORIGINAL_HASH),dict(source_id='S3',path=str(h.E/'remaining-source-actual/S3/first-f53a803-r2/outcome.json'),sha256='c8c64b4f9fdff1c3e28d326309d605d3d4ca3d0536e7a559f7fd4a082e6aaa72')]
for item in first:h.checked(item['path'],item['sha256'])
files={**old['frozen_files'],**old['input_files'],**h.read(P/'preservation-before.json')}
files[str(h.E/'remaining-source-preparation-r2/run_remaining_prefix.py')]='d72ae47f3e8fa74f1648413ad538e6b75e597a459a9c73ec73e8de88cb0c4aa2'
files[str(h.E/'local-role-design-proposal/design.md')]='0a95e725c98a9e255059a93bb96e7305fc516c3d1b033c93d3f8a28b7fc10abb'
files[str(h.E.parent/'local-role-design-review-1/verdict.json')]='e7abb30a822a1171d68d9acebb27c0f2b1507a38b34f557bba4c22aadc6c3400'
for name in ('run_local_role_core.py','run_local_role_prefix.py','test_local_role.py','test_core_boundaries.py','run_offline_tests.py','freeze_local_role.py','old-namespace-inventories.json','S4-template.json','S1-template.json','prompt.txt','projection-proof.json','core.diff'):
 files[str(P/name)]=h.sha(P/name)
files.update(h.read(P/'p1-preservation-before.json'))
for path,digest in files.items():h.checked(path,digest)
core.save(P/'manifest.json',dict(status='READY_FOR_INDEPENDENT_REVIEW',actual_execution_released=False,actual_network_requests=0,
 frozen_files=files,first_failures=first,cumulative_spent=2,cumulative_cap=4,order=['S4','S1'],namespace=str(h.ACTUAL),
 input_files=old['input_files'],source21_unchanged=True,full_old_packets_bound=True,templates_frozen_before_actual=True,
 resources='Fresh <=30 seconds, >=12GiB RAM/16GiB commit/8GiB GPU and explicit loaded.models=[], source21_hashes_match true; source_id and run_root bound',
 authority='Root supplies separate mode local_role_sdk_prefix, exact source/runroot, head/digest/core/frozen/new manifest/review hashes, first_failures, prior list, cumulative count, snapshot path/hash. Implementer issues none.',
 limits=['Mock fixtures prove mechanics only; no factual PASS','Two spent permanent failures; no old S2/S3 retry','Root serialization only; no cross-process lock or signed authority service','T2 and original E02 remain pending; no product/source10 change']))
oldlauncher=(h.E/'remaining-source-preparation-r2/run_remaining_prefix.py').read_text('utf8')
(P/'launcher.diff').write_text(''.join(difflib.unified_diff(oldlauncher.splitlines(True),(P/'run_local_role_prefix.py').read_text('utf8').splitlines(True),fromfile='frozen/run_remaining_prefix.py',tofile='new/run_local_role_prefix.py')),encoding='utf8')
assert all(h.sha(P/n)==h.sha(h.E/'local-role-preparation'/n) for n in ('S4-template.json','S1-template.json','prompt.txt','projection-proof.json'))
assert not h.ACTUAL.exists()
print(json.dumps(dict(manifest_sha256=h.sha(P/'manifest.json'),core_sha256=h.CORE_HASH,templates=proof),indent=2))
