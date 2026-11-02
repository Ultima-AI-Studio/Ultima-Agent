from pathlib import Path
import datetime,difflib,hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
C=Path(r'C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent');W=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101'
H=Path(r'H:/UltimaAI/UltimaAgent');V=H/'data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102';PY=H/'tools/venv-openjarvis/Scripts/python.exe'
SOURCE='118ba152b007c30d358c8bc44c51aabe8ae820f0'
FINAL,MANIFEST_SHA,REPORT_SHA,REPORT_SIZE,FINAL_TESTS,RECEIPT_SHA,JUNIT_SHA=sys.argv[1:]
REPORT_SIZE=int(REPORT_SIZE);FINAL_TESTS=int(FINAL_TESTS)
NAMES={'root-inert-invocation.py','test_root_inert_invocation.py','inert-root-release-template.json','inert-root-caller-manifest.json','run-inert-root-caller-checks.py'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def new(p,raw):
 with p.open('xb') as f:f.write(raw)
def newjson(p,d):new(p,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def git(*a):
 p=subprocess.run(['git','-C',str(C),*a],capture_output=True);assert p.returncode==0,p.stderr[:1000];return p.stdout.decode().strip()
HASHES={n:sha(W/n) for n in NAMES};assert HASHES['inert-root-caller-manifest.json']==MANIFEST_SHA
assert git('rev-parse','HEAD')==SOURCE and not git('diff','--name-only') and not git('diff','--cached','--name-only')
report=W/'task-4-inert-root-invocation-report.md';raw_report=report.read_bytes();assert sha(report)==REPORT_SHA and len(raw_report)==REPORT_SIZE
assert hashlib.sha256(raw_report[:34953]).hexdigest()=='a81819206387e64f34ccdb7bb05280e6f6826d26dd14f1800b098a2dd2a9a0df' and raw_report[:34953]==(V/'code/inert-caller-author-r2/report.md').read_bytes()
for n,h in HASHES.items():assert sha(W/n)==h,n
m=read(W/'inert-root-caller-manifest.json');assert set(m['files'])==NAMES-{'inert-root-caller-manifest.json'}
assert m['files']=={n:HASHES[n] for n in m['files']} and m['candidate']==SOURCE and m['released'] is False and m['actual'] is False and m['inert'] is False and m['model_calls']==0
expected=read(V/'code/harness-preparation-20261102T221401644962Z/source-after.json');assert len(expected)==64
for n in ['adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md','manifest.json']:expected[str(V/'harness'/n)]=sha(V/'harness'/n)
extra={V/'harness-code-gate.json':'9842547ee2532bd39c388187d33a95be7764e2b1f5a12ddfbc07874258a3bca2',V/'harness-review-5/verdict.json':'7d1d239f7b83148b90d266b29579ce937d02aeb0071838d666d5aaf94803030c',V/'harness-review-5/review.md':'7e4ada38af9219d3a9edf4b8e629198407c6e130b563a9c6b5cbc9c08b7c983c',V/'inert-root-caller-preparation-authority.json':'02a9428d05ee4bc2625803e997661571970968d690f7b3fc77a76eaff15799a3',V.parent/'e03-resume-20261102/actual/e03-round1/boundaries.json':'ac89211e78de8be0bed9e756419584611cd361cf66980c86b228da1fae9f91ed'}
for p,h in extra.items():assert sha(p)==h;expected[str(p)]=h
assert len(expected)==75
allowed_extra={str(W/'task-4c-read-publication-ruling-2.md'):'d45cc1a71477050655ce8faf625ea5441a035e445e720dd9f2390960be969ace',str(W/'task-4-inert-root-caller-fix2-brief.md'):'a4eb452227391e0938d3bd472c6b5b64f78d23de82fd10b93505e0b17a5c644c',str(W/'task-4-inert-root-caller-fix2-findings-verbatim.md'):'529715ab387594af689615ebd8b3c4512e771806016a64621442fc9058445da3',str(W/'task-4c-admission-protocol-ruling-1.md'):'8c6b2d82c12c04ea13c573b67473d344c6d680b0bdb8d7b5b0aa9fb3dd9bc7d5',str(W/'task-4-inert-root-review-schema-addendum.md'):'fd7b0e350a3bbde93d43bf44f67754bec484089739e6b6d37110988d1bf6fa1b',str(W/'task-4-inert-root-caller-fix1-brief.md'):'f6fbff026a5ee5aab43e468e9a168f133f52cb3f080ba795fb8b3afd081417e0',str(W/'task-4-inert-root-caller-fix1-findings-verbatim.md'):'690b0bf9ffb0d64a704494b96e77a5b17ceef3b5e69a7de1eff80def814ce3f7'}
def check_dependencies(values):
 assert set(expected)<=set(values) and {p:values[p] for p in expected}==expected
 extras=set(values)-set(expected);assert extras<=set(allowed_extra) and all(values[p]==allowed_extra[p] for p in extras)
 return extras
extra_keys=check_dependencies(m['dependencies'])
current=dict(m['dependencies'],**{str(W/n):h for n,h in HASHES.items()});assert len(current)==len(m['dependencies'])+5
for path,h in current.items():assert sha(Path(path))==h,path
stages=[]
old_rows=list(ET.parse(V/'code/inert-root-caller-preparation-20261102T224824112616Z/junit.xml').getroot().iter('testcase'));old_ids={x.attrib.get('classname','')+'::'+x.attrib['name'] for x in old_rows};assert len(old_ids)==77
for p in sorted((V/'code').glob('inert-root-caller-preparation-*')):
 if p.name<='inert-root-caller-preparation-20261102T224824112616Z' or not (p/'receipt.json').is_file():continue
 d=read(p/'receipt.json');before=read(p/'source-before.json');after=read(p/'source-after.json');assert before==after and d['inputs_unchanged'] and len(before)>=80
 for label in ['before','after']:
  inventory=read(p/f'copies-{label}.json');assert set(inventory)==set(before)
  for original,item in inventory.items():
   copy=Path(item['copy']);assert copy.resolve().is_relative_to((p/f'source-{label}').resolve()) and copy.stat().st_size==item['bytes'] and sha(copy)==item['sha256']==before[original]
 stage_manifest=next(Path(x['copy']) for key,x in read(p/'copies-before.json').items() if key==str(W/'inert-root-caller-manifest.json'))
 sm=read(stage_manifest);check_dependencies(sm['dependencies']);assert len(before)==len(sm['dependencies'])+5
 for n,h in sm['files'].items():assert before[str(W/n)]==h,n
 assert d['argv'][:6]==[str(PY),'-B','-X','utf8','-m','pytest'] and d['argv'][6]==str(W/'test_root_inert_invocation.py')
 assert d['actual'] is False and d['inert'] is False and d['model_calls']==0 and not d['drift_before'] and not d['drift_after']
 if 'kind' in d:assert d['kind']=='pure-mocked-caller-preparation-only' and d['product_launches']==0
 rows=list(ET.parse(p/'junit.xml').getroot().iter('testcase'));counts=dict(tests=len(rows),failures=sum(x.find('failure') is not None for x in rows),errors=sum(x.find('error') is not None for x in rows),skipped=sum(x.find('skipped') is not None for x in rows))
 stages.append(dict(stage=p.name,receipt_sha256=sha(p/'receipt.json'),junit_sha256=sha(p/'junit.xml'),stdout_sha256=sha(p/'stdout.log'),stderr_sha256=sha(p/'stderr.log'),source_before_sha256=sha(p/'source-before.json'),source_after_sha256=sha(p/'source-after.json'),counts=counts,source_copies=len(before),exit_code=d['exit_code'],pytest_exit_code=d.get('pytest_exit_code'),product_launches=d.get('product_launches'),receipt_format=d.get('kind',d.get('classification'))))
 if p.name==FINAL:
  assert before==current and d['exit_code']==d['pytest_exit_code']==0 and '-k' not in d['argv'] and counts==dict(tests=FINAL_TESTS,failures=0,errors=0,skipped=0) and old_ids<={x.attrib.get('classname','')+'::'+x.attrib['name'] for x in rows} and not (p/'stderr.log').read_bytes()
  assert sha(p/'receipt.json')==RECEIPT_SHA and sha(p/'junit.xml')==JUNIT_SHA
assert stages and stages[-1]['stage']==FINAL
canonical=['inert-root-dispatch.json','harness-approval.json','inert-root-release.json','inert-root-release.consumed.json','inert-native-baseline.json','inert-authority.json','inert-root-result.json','inert-root-result.pending.json','inert','actual']
absent={str(V/n):not (V/n).exists() for n in canonical};assert all(absent.values())
archive=V/'code/inert-caller-author-r3';archive.mkdir()
for n in sorted(NAMES):new(archive/n,(W/n).read_bytes())
new(archive/'report.md',report.read_bytes())
proof=V/'code/root-inert-caller-fix2-before-review.json'
newjson(proof,dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate=SOURCE,manifest_sha256=HASHES['inert-root-caller-manifest.json'],report_sha256=sha(report),report_bytes=report.stat().st_size,caller5={n:dict(sha256=HASHES[n],bytes=(W/n).stat().st_size) for n in sorted(NAMES)},dependencies=dict(m['dependencies']),additional_root_pins=sorted(extra_keys),pin_count=len(current),current_raw_match=True,original_report_prefix_bytes=34953,original_report_prefix_sha256='a81819206387e64f34ccdb7bb05280e6f6826d26dd14f1800b098a2dd2a9a0df',source_before_after_copies_match=True,stages=stages,final_tests=FINAL_TESTS,all_prior77_ids_retained=True,canonical_absence=absent,scope='ROOT pure-data/hash/JUnit readback only, no suite rerun or runtime qualification',receipt_limits='Missing historical metadata fields are null, never upgraded; each new stage retained with actual counts, final complete and unchanged pins required.',execution_released=False,T2='NOT_PASSED'))
package=W/'task-4-inert-root-caller-fix2-review-package.txt'
with package.open('x',encoding='utf-8',newline='\n') as f:
 f.write('Task4C FIX2 exact5 diff from archiveb05bbe5d. Product C118 and accepted harness935b unchanged; full requirements/report/ruling/root proof are separate inputs.\n')
 for n in sorted(NAMES):
  p=W/n;f.write('\nFILE '+str(p)+' SHA256 '+sha(p)+' bytes '+str(p.stat().st_size)+'\n');f.write(''.join(difflib.unified_diff((V/'code/inert-caller-author-r2'/n).read_text('utf-8').splitlines(keepends=True),p.read_text('utf-8').splitlines(keepends=True),fromfile='baseb05bbe5d/'+n,tofile=str(p),n=10)))
print(json.dumps(dict(proof=str(proof),proof_sha256=sha(proof),package=str(package),package_bytes=package.stat().st_size,package_sha256=sha(package),report_bytes=report.stat().st_size,stages=len(stages),tests=FINAL_TESTS,pin_count=len(current))))
