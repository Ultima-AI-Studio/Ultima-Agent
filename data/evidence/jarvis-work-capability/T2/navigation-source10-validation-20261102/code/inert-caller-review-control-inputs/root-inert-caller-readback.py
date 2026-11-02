from pathlib import Path
import datetime,difflib,hashlib,json,subprocess,xml.etree.ElementTree as ET
C=Path(r'C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent');W=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101'
H=Path(r'H:/UltimaAI/UltimaAgent');V=H/'data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102';PY=H/'tools/venv-openjarvis/Scripts/python.exe'
SOURCE='118ba152b007c30d358c8bc44c51aabe8ae820f0';FINAL='inert-root-caller-preparation-20261102T222847075613Z'
NAMES={'root-inert-invocation.py','test_root_inert_invocation.py','inert-root-release-template.json','inert-root-caller-manifest.json','run-inert-root-caller-checks.py'}
HASHES={'root-inert-invocation.py':'912e612575a9a6d17d00e2f29fc245629c8c7119653ce4a882f3941540513035','test_root_inert_invocation.py':'a4c987aaea01d3adffaac48d28b2445aead050452338275177a176d28deaacbe','inert-root-release-template.json':'ad8091c955e2c3a1d82ac1df721fd775b7d24b80c775e47d2e948b197b7b1ee3','run-inert-root-caller-checks.py':'ef2f6314d34c6cdc352040136e20ebdb2d53937b0e52736264a6b252bf2af472','inert-root-caller-manifest.json':'83a55d081afd4ca945b18284097885041737bdbf9ad40d0674f1b0394ec58dfd'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def new(p,raw):
 with p.open('xb') as f:f.write(raw)
def newjson(p,d):new(p,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def git(*a):
 p=subprocess.run(['git','-C',str(C),*a],capture_output=True);assert p.returncode==0,p.stderr[:1000];return p.stdout.decode().strip()
assert git('rev-parse','HEAD')==SOURCE and not git('diff','--name-only') and not git('diff','--cached','--name-only')
report=W/'task-4-inert-root-invocation-report.md';assert sha(report)=='06ba572d5ea287ba21a48b0fdddd186fbd05b3741f44428e1dd621df1d49d99e'
for n,h in HASHES.items():assert sha(W/n)==h,n
m=read(W/'inert-root-caller-manifest.json');assert set(m['files'])==NAMES-{'inert-root-caller-manifest.json'}
assert m['files']=={n:HASHES[n] for n in m['files']} and m['candidate']==SOURCE and m['released'] is False and m['actual'] is False and m['inert'] is False and m['model_calls']==0
expected=read(V/'code/harness-preparation-20261102T221401644962Z/source-after.json');assert len(expected)==64
for n in ['adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md','manifest.json']:expected[str(V/'harness'/n)]=sha(V/'harness'/n)
extra={V/'harness-code-gate.json':'9842547ee2532bd39c388187d33a95be7764e2b1f5a12ddfbc07874258a3bca2',V/'harness-review-5/verdict.json':'7d1d239f7b83148b90d266b29579ce937d02aeb0071838d666d5aaf94803030c',V/'harness-review-5/review.md':'7e4ada38af9219d3a9edf4b8e629198407c6e130b563a9c6b5cbc9c08b7c983c',V/'inert-root-caller-preparation-authority.json':'02a9428d05ee4bc2625803e997661571970968d690f7b3fc77a76eaff15799a3',V.parent/'e03-resume-20261102/actual/e03-round1/boundaries.json':'ac89211e78de8be0bed9e756419584611cd361cf66980c86b228da1fae9f91ed'}
for p,h in extra.items():assert sha(p)==h;expected[str(p)]=h
assert len(expected)==75 and m['dependencies']==expected
current=dict(expected,**{str(W/n):h for n,h in HASHES.items()});assert len(current)==80
for path,h in current.items():assert sha(Path(path))==h,path
stages=[]
for p in sorted((V/'code').glob('inert-root-caller-preparation-*')):
 if not (p/'receipt.json').is_file():continue
 d=read(p/'receipt.json');before=read(p/'source-before.json');after=read(p/'source-after.json');assert before==after and d['inputs_unchanged'] and len(before)==80
 for label in ['before','after']:
  inventory=read(p/f'copies-{label}.json');assert set(inventory)==set(before)
  for original,item in inventory.items():
   copy=Path(item['copy']);assert copy.resolve().is_relative_to((p/f'source-{label}').resolve()) and copy.stat().st_size==item['bytes'] and sha(copy)==item['sha256']==before[original]
 stage_manifest=next(Path(x['copy']) for key,x in read(p/'copies-before.json').items() if key==str(W/'inert-root-caller-manifest.json'))
 sm=read(stage_manifest);assert sm['dependencies']==expected
 for n,h in sm['files'].items():assert before[str(W/n)]==h,n
 assert d['argv'][:6]==[str(PY),'-B','-X','utf8','-m','pytest'] and d['argv'][6]==str(W/'test_root_inert_invocation.py')
 assert d['actual'] is False and d['inert'] is False and d['model_calls']==0 and not d['drift_before'] and not d['drift_after']
 if 'kind' in d:assert d['kind']=='pure-mocked-caller-preparation-only' and d['product_launches']==0
 else:
  classifications={'inert-root-caller-preparation-20261102T222645463888Z-red':'TARGETED_RED_REGRESSION','inert-root-caller-preparation-20261102T222726593492Z-targeted':'TARGETED_GREEN_AFTER_RED','inert-root-caller-preparation-20261102T222738271144Z-targeted':'TARGETED_AFTER_FIXTURE_PIN_CORRECTION'}
  assert classifications.get(p.name)==d.get('classification')
 rows=list(ET.parse(p/'junit.xml').getroot().iter('testcase'));counts=dict(tests=len(rows),failures=sum(x.find('failure') is not None for x in rows),errors=sum(x.find('error') is not None for x in rows),skipped=sum(x.find('skipped') is not None for x in rows));assert counts['errors']==counts['skipped']==0
 stages.append(dict(stage=p.name,receipt_sha256=sha(p/'receipt.json'),junit_sha256=sha(p/'junit.xml'),stdout_sha256=sha(p/'stdout.log'),stderr_sha256=sha(p/'stderr.log'),source_before_sha256=sha(p/'source-before.json'),source_after_sha256=sha(p/'source-after.json'),counts=counts,source_copies=80,exit_code=d['exit_code'],pytest_exit_code=d.get('pytest_exit_code'),product_launches=d.get('product_launches'),receipt_format=d.get('kind',d.get('classification'))))
 if p.name==FINAL:
  assert before==current and d['exit_code']==d['pytest_exit_code']==0 and '-k' not in d['argv'] and counts==dict(tests=50,failures=0,errors=0,skipped=0) and not (p/'stderr.log').read_bytes()
  assert sha(p/'receipt.json')=='c4b7afb9601801b04af0b11096f2fcd9cb45b7ecfe559def2c21ebe0772af682' and sha(p/'junit.xml')=='1ee7f282257a23dc66faf2e900f4e9ddb9985558b507be2d4b5987afdf80f561'
assert len(stages)==5 and stages[-1]['stage']==FINAL
canonical=['harness-approval.json','inert-root-release.json','inert-root-release.consumed.json','inert-native-baseline.json','inert-authority.json','inert-root-result.json','inert','actual']
absent={str(V/n):not (V/n).exists() for n in canonical};assert all(absent.values())
archive=V/'code/inert-caller-author-r1';archive.mkdir()
for n in sorted(NAMES):new(archive/n,(W/n).read_bytes())
new(archive/'report.md',report.read_bytes())
proof=V/'code/root-inert-caller-before-review.json'
newjson(proof,dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate=SOURCE,manifest_sha256=HASHES['inert-root-caller-manifest.json'],report_sha256=sha(report),report_bytes=report.stat().st_size,caller5={n:dict(sha256=HASHES[n],bytes=(W/n).stat().st_size) for n in sorted(NAMES)},dependencies75=expected,pins80_current_raw_match=True,source_before_after_copies_match=True,stages=stages,final_tests=50,canonical_absence=absent,scope='ROOT pure-data/hash/JUnit readback only, no suite rerun or runtime qualification',historical_targeted_receipt_limits='First3 targeted receipts lack separate pytest_exit_code, product_launches and kind; record absent fields as null, not upgraded to final driver schema. Root reader first assumed final schema and was corrected without changing author bytes.',execution_released=False,T2='NOT_PASSED'))
package=W/'task-4-inert-root-invocation-review-package.txt'
with package.open('x',encoding='utf-8',newline='\n') as f:
 f.write('Task4C NEW5 root caller files only; evidence preparation, NOT a product Git diff. Product C118 and accepted six-file harness935b unchanged. BASE=absent, HEAD=caller manifest83a55d08.\n')
 for n in sorted(NAMES):
  p=W/n;f.write('\nFILE '+str(p)+' SHA256 '+sha(p)+' bytes '+str(p.stat().st_size)+'\n');f.write(''.join(difflib.unified_diff([],p.read_text('utf-8').splitlines(keepends=True),fromfile='/dev/null',tofile=str(p),n=10)))
print(json.dumps(dict(proof=str(proof),proof_sha256=sha(proof),package=str(package),package_bytes=package.stat().st_size,package_sha256=sha(package),report_bytes=report.stat().st_size,stages=len(stages),tests=50)))
