from pathlib import Path
import datetime, difflib, hashlib, json, subprocess, sys, xml.etree.ElementTree as ET

C=Path(r'C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
H=Path(r'H:/UltimaAI/UltimaAgent')
V=H/'data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102'
W=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101'
SOURCE='118ba152b007c30d358c8bc44c51aabe8ae820f0'
NAMES={'adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md','manifest.json'}
FINAL, MANIFEST_SHA, REPORT_SHA, REPORT_SIZE, FINAL_TESTS, RECEIPT_SHA, JUNIT_SHA = sys.argv[1:]
REPORT_SIZE=int(REPORT_SIZE); FINAL_TESTS=int(FINAL_TESTS)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def newjson(p,d):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
def git(*args,data=None):
 p=subprocess.run(['git','-C',str(C),*args],input=data,capture_output=True)
 assert p.returncode==0,(args,p.stderr[:1000])
 return p.stdout
def junit(p):
 r=ET.parse(p).getroot(); rows=list(r.iter('testcase'))
 return dict(tests=len(rows),failures=sum(t.find('failure') is not None for t in rows),errors=sum(t.find('error') is not None for t in rows),skipped=sum(t.find('skipped') is not None for t in rows),ids=sorted(t.attrib.get('classname','')+'::'+t.attrib['name'] for t in rows))

assert git('rev-parse','HEAD').decode().strip()==SOURCE
assert not git('diff','--name-only').strip() and not git('diff','--cached','--name-only').strip()
assert {p.name for p in (V/'harness').iterdir() if p.is_file()}==NAMES
report=W/'task-4-navigation-adapter-report.md';raw=report.read_bytes()
assert sha(report)==REPORT_SHA
assert len(raw)==REPORT_SIZE and hashlib.sha256(raw[:69552]).hexdigest()=='6f9926ac5819579c80367fa2c510fe0f9654839e3a6b185d9e66219bc1a56168'
assert raw[:69552]==(V/'harness-preparation-author-r4/report.md').read_bytes()
manifest=V/'harness/manifest.json'
assert sha(manifest)==MANIFEST_SHA
m=read(manifest);assert set(m['files'])==NAMES-{'manifest.json'}
current={n:sha(V/'harness'/n) for n in sorted(NAMES)}
assert all(current[n]==h for n,h in m['files'].items())
candidate=read(V/'source10-candidate-manifest.json')
assert sha(V/'source10-candidate-manifest.json')=='cdfbfb059f889ef9e92221c503dffe2ca7fa08106ebf4968bcc26037f214be50'
for key in ['source_files','sdk22','dependencies']:
 for path,h in candidate[key].items():assert sha(Path(path))==h,(key,path)
for pk,hk in [('local_manifest_path','local_manifest_observed_sha256'),('policy_path','policy_sha256')]:assert sha(Path(candidate['model'][pk]))==candidate['model'][hk]
assert sha(V/'harness-preparation-authority.json')=='0e8c2e273bc2a4c35d0fd01e4c0022955609cb4bcecc2ec1f47d3bf95cdd5418'
assert sha(V/'harness-deadline-design/root-decision.json')=='144be9bc0a63294f5fd4e75c7cbe06f8e2ad2d51df36d0b11896d2455a0b4d47'
tracked=candidate['tracked_inputs'];assert len(tracked)==30
body=git('cat-file','--batch',data=('\n'.join(SOURCE+':'+p for p in tracked)+'\n').encode())
offset=0;git_blobs={}
for path in tracked:
 end=body.index(b'\n',offset);head=body[offset:end].split();assert len(head)==3 and head[1]==b'blob'
 size=int(head[2]);b=body[end+1:end+1+size];assert len(b)==size and body[end+size+1:end+size+2]==b'\n'
 digest=hashlib.sha256(b).hexdigest();assert digest==candidate['source_files'][str(C/path)]
 git_blobs[path]=digest;offset=end+size+2
assert offset==len(body)
old=junit(V/'code/harness-preparation-20261102T213445388959Z/harness/adapter.xml');assert old['tests']==145
stages=[]
for p in sorted((V/'code').glob('harness-preparation-*')):
 if p.name<='harness-preparation-20261102T213445388959Z' or not (p/'receipt.json').is_file():continue
 d=read(p/'receipt.json');before=read(p/'source-before.json');after=read(p/'source-after.json')
 assert before==after and d['inputs_unchanged']
 explicit_harness_before_after='harness_before' in d
 if explicit_harness_before_after:
  assert d['harness_unchanged'] and set(d['harness_before'])==set(d['harness_after'])==NAMES and d['harness_before']==d['harness_after']==d['files']
 else:
  assert p.name=='harness-preparation-20261102T201732500514Z' and set(d['files'])==NAMES
 snaps={n:sha(p/'harness-source'/n) for n in sorted(NAMES)};assert snaps==d['files']
 assert d['argv'][:6]==[str(H/'tools/venv-openjarvis/Scripts/python.exe'),'-B','-X','utf8','-m','pytest']
 assert d['model_calls']==0 and d['product_launches']==0 and d['actual'] is False and d['inert'] is False
 j=junit(p/'harness/adapter.xml');base_retained=set(old['ids'])<=set(j['ids']);assert j['errors']==j['skipped']==0
 stages.append(dict(stage=p.name,receipt_sha256=sha(p/'receipt.json'),stdout_sha256=sha(p/'stdout.log'),stderr_sha256=sha(p/'stderr.log'),junit_sha256=sha(p/'harness/adapter.xml'),counts={k:j[k] for k in ['tests','failures','errors','skipped']},original145_retained=base_retained,baseline_ids_present=len(set(old['ids']) & set(j['ids'])),six_snapshots_match=True,explicit_harness_before_after=explicit_harness_before_after,inputs_before_after_sha256=[sha(p/'source-before.json'),sha(p/'source-after.json')]))
 if p.name==FINAL:
  assert '-k' not in d['argv'], 'Final selection is not a complete unfiltered suite'
  assert d['exit_code']==0 and j['tests']==FINAL_TESTS and j['failures']==0 and snaps==current and base_retained
  assert sha(p/'receipt.json')==RECEIPT_SHA
  assert sha(p/'harness/adapter.xml')==JUNIT_SHA
  assert not (p/'stderr.log').read_bytes()
  assert len(after)==64
  for path,h in after.items():assert sha(Path(path))==h,path
assert stages and stages[-1]['stage']==FINAL
proof=V/'code/root-harness-fix3-before-review.json'
newjson(proof,dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate=SOURCE,report_sha256=sha(report),report_bytes=len(raw),original_report_prefix_bytes=69552,original_report_prefix_sha256=hashlib.sha256(raw[:69552]).hexdigest(),six_files={n:dict(sha256=current[n],bytes=(V/'harness'/n).stat().st_size) for n in sorted(NAMES)},manifest_sha256=sha(manifest),source31_current_raw_match=True,tracked30_git_blobs=git_blobs,preexisting_untracked=candidate['preexisting_untracked_inputs'],sdk22_current_raw_match=True,dependencies7_current_raw_match=True,pins64_current_raw_match=True,stages=stages,tests=FINAL_TESTS,code_covering479_compat8_unchanged=True,actual_model_inert_profile_calls=0,T2='NOT_PASSED',scope='independent data/hash/JUnit readback only; no suite rerun, qualification or operational guarantee'))
package=W/'task-4-navigation-harness-fix3-review-package.txt'
with package.open('x',encoding='utf-8',newline='\n') as f:
 f.write('Task4 FIX3 scoped six-file diff against archived e166 manifest. Product source remains '+SOURCE+'.\nNot a product Git diff; only evidence/harness files, root owns private evidence publication.\n')
 f.write('All requirements/report/root independent readback are separate named inputs.\n\n')
 for n in sorted(NAMES):
  p=V/'harness'/n;lines=p.read_bytes().decode('utf-8').splitlines(keepends=True)
  f.write('\nFILE '+str(p)+' SHA256 '+current[n]+' bytes '+str(p.stat().st_size)+'\n')
  before=(V/'harness-preparation-author-r4'/n).read_bytes().decode('utf-8').splitlines(keepends=True)
  f.write(''.join(difflib.unified_diff(before,lines,fromfile='base-e166/'+n,tofile=str(p),n=10)))
print(json.dumps(dict(proof=str(proof),proof_sha256=sha(proof),final_tests=FINAL_TESTS,stages=len(stages),package=str(package),package_bytes=package.stat().st_size,package_sha256=sha(package))))
