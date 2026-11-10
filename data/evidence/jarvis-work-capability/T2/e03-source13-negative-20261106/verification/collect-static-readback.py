"""Read-only sources/receipts; writes only this package's preparation evidence."""
from pathlib import Path
import ast
from collections import Counter
import datetime as dt
import difflib
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[1]
parent=root.parent/'e03-source13-round3-20261106'
recovery=root.parent/'runtime-reconcile-20261106-after-round3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    assert not p.exists(),str(p)
    p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def verify(path,digest):assert path.is_file() and sha(path)==digest,str(path)

manifest=load(root/'inputs/candidate-runtime-manifest.json')
for section in ('source_files','dependencies'):
    for name,digest in manifest[section].items():verify(Path(name),digest)
sdk_count=0
for component in manifest['sdk_components'].values():
    for name,digest in component['files'].items():verify(Path(component['root'])/name,digest);sdk_count+=1
model=manifest['model'];verify(Path(model['local_manifest_path']),model['local_manifest_observed_sha256'])
verify(Path(model['policy_path']),model['policy_sha256'])
gate=manifest['code_gate'];verify(Path(gate['path']),gate['sha256']);verify(Path(gate['report_path']),gate['report_sha256'])
tests=manifest['final_code_tests']
verify(Path(tests['full_receipt']),tests['full_sha256']);verify(Path(tests['compat_receipt']),tests['compat_sha256'])
for name,key in [('original_corpus_readback','original_corpus_readback_sha256'),
                 ('last_protected_readback','last_protected_readback_sha256'),
                 ('historical_source21_path','historical_source21_sha256'),
                 ('code_review_manifest_path','code_review_manifest_sha256')]:verify(Path(manifest[name]),manifest[key])
candidate=Path(manifest['candidate_root'])
def git(*args):return subprocess.check_output(['git','-C',str(candidate),*args],text=True).strip()
assert git('rev-parse','HEAD')==manifest['candidate']
assert git('branch','--show-current')==manifest['branch']
assert not git('status','--porcelain','--untracked-files=no')
pm=load(parent/'manifest.json')
for row in pm['files']:
    p=parent/row['path'];verify(p,row['sha256']);assert p.stat().st_size==row['bytes']
verify(root/'history/parent-manifest.json',sha(parent/'manifest.json'))
pairs=[]
prior_roots=[root.parent/'e03-source13-runtime-fix-20261105-r1',root.parent/'e03-source13-round2-20261106',parent]
for n,pr in enumerate(prior_roots,1):
    for name,original in [('terminal.json',pr/'actual'/('e03-round'+str(n))/'terminal.json'),
                          ('review.json',pr/'independent-result-review.json'),
                          ('registration.json',pr/'verification/result-registration.json')]:
        copied=root/'inputs'/('prior-round'+str(n))/name;verify(copied,sha(original))
        pairs.append(dict(original=str(original),copy=str(copied),sha256=sha(copied)))
for name,original in [('runtime-reconciliation.json','restoration-result.json'),
                      ('runtime-manual-confirmation.json','manual-start-confirmation.json'),
                      ('runtime-user-approval.json','user-approval.json')]:
    verify(root/'inputs'/name,sha(recovery/original))
    pairs.append(dict(original=str(recovery/original),copy=str(root/'inputs'/name),sha256=sha(root/'inputs'/name)))
raw=recovery/'protected-baseline-restored.json';raw_value=load(raw);current=load(root/'inputs/protected-baseline.json')
verify(root/'history/restored-baseline-before-schema-completion.json',sha(raw))
assert current['created_utc_derivation']['original_snapshot_sha256']==sha(raw)
for old,new in zip(raw_value['protected5']+raw_value['protected_listener_pair'],current['protected5']+current['protected_listener_pair']):
    for key in ('pid','created_filetime','exe','parent_pid','command_line_sha256'):assert old[key]==new[key]
seconds,fraction=divmod(current['protected5'][0]['created_filetime'],10_000_000)
derived=(dt.datetime(1601,1,1,tzinfo=dt.timezone.utc)+dt.timedelta(seconds=seconds)).strftime('%Y-%m-%dT%H:%M:%S')+'.'+str(fraction).zfill(7)+'Z'
assert current['protected5'][0]['created_utc']==derived
modules=sorted([*root.glob('code/*.py'),*root.glob('preparation-support/*.py')])
same=[];changed=[];added=[];diff=[]
for p in modules:
    ast.parse(p.read_text(encoding='utf-8-sig'));rel=p.relative_to(root).as_posix();old=parent/rel
    if not old.exists():added.append(rel)
    elif p.read_bytes()==old.read_bytes():same.append(rel)
    else:changed.append(rel)
    if not old.exists() or p.read_bytes()!=old.read_bytes():
        diff.extend(difflib.unified_diff(old.read_text(encoding='utf-8-sig').splitlines(True) if old.exists() else [],
                    p.read_text(encoding='utf-8-sig').splitlines(True),fromfile='parent/'+rel,tofile='negative/'+rel))
diff_path=root/'verification/parent-to-negative.diff';assert not diff_path.exists();diff_path.write_bytes(''.join(diff).encode('utf-8'))
def counts(p):return Counter((n.attrib['classname'],n.attrib['name'].split('[',1)[0]) for n in ET.parse(p).iter('testcase'))
before=counts(parent/'verification/entry-final.xml');after=counts(root/'verification/negative-final-green.xml')
aliases={
 'test_original_fixture_server_cli_path_and_final_revalidation_order':'test_negative_uses_only_fixture_and_revalidates_each_changed_target',
 'test_round3_admits_two_matching_predecessors_and_keeps_new_facts_pending':'test_negative_admits_three_matching_predecessors_and_keeps_new_facts_pending',
 'test_two_distinct_passes_admit_only_round3_and_do_not_pregrant_facts':'test_three_distinct_passes_admit_only_negative_and_do_not_pregrant_facts',
 'test_round3_authority_requires_both_exact_ordered_bindings':'test_negative_authority_requires_exact_ordered_bindings'}
translated=Counter({(module,aliases.get(name,name)):n for (module,name),n in before.items()})
assert all(after[k]>=n for k,n in translated.items())
final=load(root/'verification/negative-final-green.json');guard=load(root/'verification/negative-final-green-io-guard.json')
assert final['counts']==dict(tests=255,failures=0,errors=0,skipped=0) and final['source_unchanged']
assert final['exit_code']==guard['final_exit']==0 and not any(guard[k] for k in ('denied','allowed','open_owned_listeners'))
assert not (root/'release').exists() and not (root/'actual').exists()
report=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),candidate=manifest['candidate'],candidate_tracked_clean=True,
            source_files=len(manifest['source_files']),dependencies=len(manifest['dependencies']),sdk_files=sdk_count,
            sdk_components=len(manifest['sdk_components']),parent_sealed_files=len(pm['files']),
            parent_manifest_sha256=sha(parent/'manifest.json'),original_copy_pairs=pairs,
            restored_snapshot_sha256=sha(raw),negative_baseline_sha256=sha(root/'inputs/protected-baseline.json'),
            baseline_identity_changes=0,baseline_schema_completion=derived,AST_modules=len(modules),
            unchanged_python_modules=same,changed_parent_python_modules=changed,new_python_modules=added,
            parent_tests=sum(before.values()),current_tests=sum(after.values()),additional_tests=sum(after.values())-sum(before.values()),
            test_name_aliases=aliases,test_retention='All prior function/parameter counts retained; positive CLI path expectations adapted to zero-CLI negative path. Parent 191 evidence immutable.',
            frozen_product_tests='485/8 historical gate hashes verified; not rerun',
            native_UI=False,actual_cases=0,model_calls=0,audio_actions=0,
            limitations=['Offline native substitutions do not prove actual UI behavior.',
                        'Focus case only proves readonly re-observation of the original target, not focus-only replacement.',
                        'Runtime recovery is a saved observation; fresh actual admission still required.'])
save(root/'verification/entry-static-readback.json',report)
print(json.dumps({k:report[k] for k in ('source_files','dependencies','sdk_files','parent_sealed_files','AST_modules','current_tests','additional_tests','baseline_identity_changes')}))
