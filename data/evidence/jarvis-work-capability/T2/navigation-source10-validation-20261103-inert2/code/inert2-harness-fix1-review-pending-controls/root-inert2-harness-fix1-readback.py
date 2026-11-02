"""Independent raw/JUnit readback and review packet; never executes the harness."""
from pathlib import Path
import datetime as dt
import difflib
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
W=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101'
H=Path('H:/UltimaAI/UltimaAgent')
T=H/'data/evidence/jarvis-work-capability/T2'
OLD=T/'navigation-source10-validation-20261102'
V=T/'navigation-source10-validation-20261103-inert2'
SOURCE='118ba152b007c30d358c8bc44c51aabe8ae820f0'
NAMES={'adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md','manifest.json'}
FINAL,COUNT,MANIFEST_SHA,REPORT_SHA,RECEIPT_SHA,JUNIT_SHA=sys.argv[1:]
COUNT=int(COUNT)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def new(p,raw):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(raw)
def out(p,d): new(p,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def git(*args,data=None):
    p=subprocess.run(['git','-C',str(C),*args],input=data,capture_output=True)
    assert p.returncode==0,(args,p.stderr[:1000]);return p.stdout
def junit(p):
    cases=list(ET.parse(p).getroot().iter('testcase'))
    return dict(tests=len(cases),failures=sum(t.find('failure') is not None for t in cases),errors=sum(t.find('error') is not None for t in cases),skipped=sum(t.find('skipped') is not None for t in cases),ids=sorted(t.attrib.get('classname','')+'::'+t.attrib['name'] for t in cases))
assert git('rev-parse','HEAD').decode().strip()==SOURCE
assert not git('diff','--name-only').strip() and not git('diff','--cached','--name-only').strip()
assert {p.name for p in (V/'harness').iterdir() if p.is_file()}==NAMES
initial=read(V/'code/root-preparation-inputs-before.json')
for p,h in initial['old_pins'].items():assert sha(Path(p))==h,p
assert sha(V/'source10-candidate-manifest.json')=='cdfbfb059f889ef9e92221c503dffe2ca7fa08106ebf4968bcc26037f214be50'
assert sha(V/'harness-deadline-design/root-decision.json')=='144be9bc0a63294f5fd4e75c7cbe06f8e2ad2d51df36d0b11896d2455a0b4d47'
assert sha(V/'harness-preparation-authority.json')=='f3dcea80f720f903cc98ce77d1f8b9461ca4ad9b4e87e9d9d8c8b89262ae118a'
m=read(V/'harness/manifest.json');current={n:sha(V/'harness'/n) for n in sorted(NAMES)}
assert current['manifest.json']==MANIFEST_SHA
assert set(m['files'])==NAMES-{'manifest.json'}
assert all(current[n]==h for n,h in m['files'].items())
assert m['preparation_authority_sha256']=='f3dcea80f720f903cc98ce77d1f8b9461ca4ad9b4e87e9d9d8c8b89262ae118a'
report=W/'task-4-inert2-harness-report.md';assert sha(report)==REPORT_SHA
assert hashlib.sha256(report.read_bytes()[:16751]).hexdigest()=='6fe4229e31c6fe19cbf33e2e02092b52d437d82d87a976a830dbb4984c491603'
assert report.read_bytes()[:16751]==(V/'code/harness-author-r1/report.md').read_bytes()
candidate=read(V/'source10-candidate-manifest.json')
pins={}
for k in ['source_files','sdk22','dependencies']:pins.update(candidate[k])
for pk,hk in [('local_manifest_path','local_manifest_observed_sha256'),('policy_path','policy_sha256')]:pins[candidate['model'][pk]]=candidate['model'][hk]
for p,h in pins.items():assert sha(Path(p))==h,p
tracked=candidate['tracked_inputs'];assert len(tracked)==30
raw=git('cat-file','--batch',data=('\n'.join(SOURCE+':'+p for p in tracked)+'\n').encode());offset=0;git_blobs={}
for p in tracked:
    end=raw.index(b'\n',offset);head=raw[offset:end].split();assert len(head)==3 and head[1]==b'blob'
    size=int(head[2]);body=raw[end+1:end+1+size];assert len(body)==size and raw[end+1+size:end+2+size]==b'\n'
    digest=hashlib.sha256(body).hexdigest();assert digest==candidate['source_files'][str(C/p)]
    git_blobs[p]=digest;offset=end+2+size
assert offset==len(raw)
old=junit(V/'code/harness-preparation-20261102T233937902427Z/harness/adapter.xml');assert old['tests']==216 and not old['failures']
stages=[];final_seen=False
for p in sorted((V/'code').glob('harness-preparation-*')):
    if p.name<='harness-preparation-20261102T233937902427Z':continue
    assert (p/'receipt.json').is_file(),('Unclosed preparation stage',str(p))
    d=read(p/'receipt.json');before=read(p/'source-before.json');after=read(p/'source-after.json')
    assert before==after and d['inputs_unchanged'] and d['harness_unchanged']
    assert d['harness_before']==d['harness_after']==d['files'] and set(d['files'])==NAMES
    snaps={n:sha(p/'harness-source'/n) for n in sorted(NAMES)};assert snaps==d['files']
    assert d['argv'][:6]==[str(H/'tools/venv-openjarvis/Scripts/python.exe'),'-B','-X','utf8','-m','pytest']
    assert d['model_calls']==d['product_launches']==0 and d['actual'] is False and d['inert'] is False
    j=junit(p/'harness/adapter.xml');assert j['errors']==j['skipped']==0
    retained=set(old['ids'])<=set(j['ids'])
    stages.append(dict(stage=p.name,receipt_sha256=sha(p/'receipt.json'),stdout_sha256=sha(p/'stdout.log'),stderr_sha256=sha(p/'stderr.log'),junit_sha256=sha(p/'harness/adapter.xml'),counts={k:j[k] for k in ['tests','failures','errors','skipped']},prior216_retained=retained,baseline_ids_present=len(set(old['ids'])&set(j['ids'])),six_snapshots_match=True,pin_count=len(after),inputs_before_after_sha256=[sha(p/'source-before.json'),sha(p/'source-after.json')]))
    if p.name==FINAL:
        assert not final_seen and '-k' not in d['argv'];final_seen=True
        assert d['exit_code']==d['pytest_exit_code']==0 and j['tests']==COUNT and j['failures']==0 and retained and snaps==current
        assert sha(p/'receipt.json')==RECEIPT_SHA and sha(p/'harness/adapter.xml')==JUNIT_SHA
        assert not (p/'stderr.log').read_bytes()
        for path,h in after.items():assert sha(Path(path))==h,path
        final_pins=after
assert final_seen and stages[-1]['stage']==FINAL
fixture=OLD/'code/harness-preparation-20261102T215807022506Z/temp/test_fix1_genuine_synthetic_ex0'
export=read(fixture/'trusted-export.json')
for p in [fixture/'trusted-export.json',fixture/'runtime-inputs.json']+[fixture/x['name'] for x in export['members'].values()]:
    assert final_pins.get(str(p))==sha(p),('Frozen fixture missing/drift',str(p))
proof=V/'code/root-inert2-harness-fix1-before-review.json'
out(proof,dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),candidate=SOURCE,six_files={n:dict(sha256=current[n],bytes=(V/'harness'/n).stat().st_size) for n in sorted(NAMES)},manifest_sha256=MANIFEST_SHA,report_sha256=REPORT_SHA,report_bytes=report.stat().st_size,old52_raw_pins_unchanged=True,source31_raw_match=True,tracked30_git_blobs=git_blobs,sdk22_raw_match=True,final_pin_count=len(final_pins),final216_retained=True,tests=COUNT,stages=stages,actual=False,inert=False,model_calls=0,T2='NOT_PASSED',scope='independent closed-byte/JUnit readback only; no suite or runtime'))
package=W/'task-4-inert2-harness-fix1-review-package.txt'
text='Task4-PORT-REV2 scoped exact six-file changea5b→'+MANIFEST_SHA+'\nProduct Git C118 unchanged. Evidence-only package; original task and gates retained.\n'
for n in sorted(NAMES):
    src=V/'code/harness-author-r1'/n;dest=V/'harness'/n
    text+='\nFILE '+str(dest)+' SHA256 '+current[n]+' bytes '+str(dest.stat().st_size)+'\n'
    text+=''.join(difflib.unified_diff(src.read_text('utf8').splitlines(keepends=True),dest.read_text('utf8').splitlines(keepends=True),fromfile='base-a5b/'+n,tofile=str(dest),n=15))
new(package,text.encode('utf8'))
archive=V/'code/harness-author-r2';archive.mkdir(exist_ok=False)
for n in NAMES:new(archive/n,(V/'harness'/n).read_bytes())
new(archive/'report.md',report.read_bytes())
out(archive/'seal.json',dict(manifest_sha256=MANIFEST_SHA,report_sha256=REPORT_SHA,files=current))
review_inputs=W/'task-4-inert2-harness-fix1-review-inputs.json'
input_paths=[W/'task-4-inert2-harness-fix1-brief.md',V/'harness-review-1/verdict.json',V/'harness-review-1/review.md',W/'task-4-inert2-harness-brief.md',W/'task-4-inert2-port-proof-ruling.md',W/'task-4-inert-port-native-diagnosis-report.md',report,package,proof,V/'harness-preparation-authority.json',V/'source10-candidate-manifest.json',V/'harness-deadline-design/root-decision.json',OLD/'harness-review-5/verdict.json',OLD/'harness-review-5/review.md',V/'code'/FINAL/'receipt.json',V/'code'/FINAL/'harness/adapter.xml']
out(review_inputs,dict(scope='T4_PORT_REV2_HARNESS_PREPARATION_REVIEW',candidate=SOURCE,base_manifest_sha256='a5b16aed8d8386d2e2018262a6e75677f00b958cb3553154af987a6658fe376d',manifest_sha256=MANIFEST_SHA,files=current,inputs={str(p):sha(p) for p in input_paths},retained_original_ids=old['ids'],tests=COUNT,actual=False,model_calls=0))
review_brief=W/'task-4-inert2-harness-fix1-review-brief.md'
review_text=f'''# Task4-PORT-REV2 Task1 FIX1 scoped re-review

Read fix requirements {W}/task-4-inert2-harness-fix1-brief.md and original narrow brief there; findings verbatim {V}/harness-review-1/review.md; SAME appended author report {report} (entire16751/6fe original preserved), read NEW append fully. Exact contextual six-file FIX diff {package}, base a5b16aed8d8386d2e2018262a6e75677f00b958cb3553154af987a6658fe376d → {MANIFEST_SHA}; companion {review_inputs}; root raw/JUnit proof {proof}. Review ONLY PORT2-I01 and NEW regressions caused by fix diff. Original21 closures and other initial checks held; no broad product/harness re-review. Name outside-diff concrete coupling checks. No suite reruns; author full evidence sealed, focused pure/mock new check only for concrete unanswered doubt; no native/socket/HTTP/model/process operations. Read-only checkout/index/refs; no subagents.

Global constraints: only current8B digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330; no14B/larger/otherweights/default/download. C118/SDK/source31/P4/P1/query/bodies/KWS/protected5/oldV/W5/frozenfixture/actual1PERMANENTFAIL immutable. Same shared3s/singleconnect,275/310/315/260/300/315/0retry,10061onlytruth, no renewal or physicalallfailure guarantee. No actual2 allocation/profile/model/T3/Owner/prod.

Judge PORT2-I01 guard original hint against both phase and private expiry BEFORE raw setter, while mandatory close/restoration works because P4 hint precedes its own finally. Review meaningful RED/GREEN rawsetter0/connect0 at exhaustion, realcleanup/observer integration and unexpired normal hints. Retain216 IDs plus additive tests. Verify raw logs/JUnit/input hash/source snapshots and original report prefix; don't trust prose alone.

Write NEW {V}/harness-review-2/review.md+verdict.json and identical {W}/task-4-inert2-harness-fix1-review-report.md. Human SPEC PASS/FAIL,QUALITY APPROVED/NEEDS_FIXES, PORT2-I01 ADDRESSED/NOT_ADDRESSED, new findings exactfile:line,checks/limits. Machine schema_version1,scopeT4_PORT_REV2_HARNESS_FIX1_REVIEW,candidate,base_manifest_sha256=a5b16aed8d8386d2e2018262a6e75677f00b958cb3553154af987a6658fe376d,harness_manifest_sha256={MANIFEST_SHA},spec,quality,spec_verdict=spec,quality_verdict=quality,execution_released=false,T2=NOT_PASSED,finding_verdicts[{{id:PORT2-I01,verdict:ADDRESSED/NOT_ADDRESSED,evidence}}],findings[] for newly open issues,held_closed original21,reviewed_hashes. No operational control/selfhash. Return compact verdict,paths/hashes.
'''
new(review_brief,review_text.encode('utf8'))
print(json.dumps(dict(proof=str(proof),proof_sha256=sha(proof),package=str(package),package_sha256=sha(package),package_bytes=package.stat().st_size,review_brief=str(review_brief),review_brief_sha256=sha(review_brief),tests=COUNT,stages=len(stages))))
