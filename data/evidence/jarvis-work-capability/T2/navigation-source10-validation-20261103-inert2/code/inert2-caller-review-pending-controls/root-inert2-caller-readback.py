"""Independent caller snapshot/JUnit readback and scoped review package; no runtime."""
from pathlib import Path
import datetime as dt
import difflib
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
W=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101';W2=W/'inert-revision2'
H=Path('H:/UltimaAI/UltimaAgent');T=H/'data/evidence/jarvis-work-capability/T2'
OLD=T/'navigation-source10-validation-20261102';V=T/'navigation-source10-validation-20261103-inert2'
PY=H/'tools/venv-openjarvis/Scripts/python.exe';SOURCE='118ba152b007c30d358c8bc44c51aabe8ae820f0'
NAMES={'root-inert-invocation.py','test_root_inert_invocation.py','inert-root-release-template.json','inert-root-caller-manifest.json','run-inert-root-caller-checks.py'}
FINAL,COUNT,MANIFEST_SHA,REPORT_SHA,RECEIPT_SHA,JUNIT_SHA=sys.argv[1:];COUNT=int(COUNT)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def new(p,raw):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(raw)
def out(p,d):new(p,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def git(*args):
    p=subprocess.run(['git','-C',str(C),*args],capture_output=True);assert p.returncode==0,p.stderr[:1000];return p.stdout.decode().strip()
def junit(p):
    rows=list(ET.parse(p).getroot().iter('testcase'))
    return dict(tests=len(rows),failures=sum(t.find('failure') is not None for t in rows),errors=sum(t.find('error') is not None for t in rows),skipped=sum(t.find('skipped') is not None for t in rows),ids={t.attrib.get('classname','')+'::'+t.attrib['name'] for t in rows})
assert git('rev-parse','HEAD')==SOURCE and not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert {p.name for p in W2.iterdir() if p.is_file()}==NAMES
initial=read(V/'code/root-preparation-inputs-before.json')
for p,h in initial['old_pins'].items():assert sha(Path(p))==h,p
assert sha(W/'task-4-inert-root-invocation-report.md')=='aaa309ddaa9c73b0c7c4a22529fd61830b87dfeb24997f67bb2c5a0ad4efb263'
assert sha(W/'task-4-navigation-adapter-report.md')=='b8fb39ee75d9753a4189c50126cb514647c1a7768e1cb6390ef506fbf4bfadbc'
base=read(W/'inert-root-caller-manifest.json');assert sha(W/'inert-root-caller-manifest.json')=='d4b73f6cf7731e149323d016c590a27656eefdd54d2fcf426d9b037e592168af'
gate=read(V/'harness-code-gate.json');assert gate['spec']=='PASS' and gate['quality']=='APPROVED' and gate['execution_released'] is False
newreview=Path(gate['review'])
rebase={str(OLD/n):str(V/n) for n in ['harness-preparation-authority.json','source10-candidate-manifest.json','harness-code-gate.json','inert-root-caller-preparation-authority.json','harness-deadline-design/root-decision.json']}
rebase.update({str(OLD/'harness'/n):str(V/'harness'/n) for n in ['adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md','manifest.json']})
rebase[str(OLD/'harness-review-5/verdict.json')]=str(newreview)
rebase[str(OLD/'harness-review-5/review.md')]=str(newreview.with_name('review.md'))
expected={rebase.get(p,p):(sha(Path(rebase[p])) if p in rebase else h) for p,h in base['dependencies'].items()}
allowed_extra={str(W/'task-4-inert2-port-proof-ruling.md'):sha(W/'task-4-inert2-port-proof-ruling.md'),str(W/'task-4-inert2-caller-brief.md'):sha(W/'task-4-inert2-caller-brief.md')}
fixture=OLD/'code/harness-preparation-20261102T215807022506Z/temp/test_fix1_genuine_synthetic_ex0'
allowed_extra.update({p:h for p,h in initial['old_pins'].items() if Path(p).resolve().is_relative_to(fixture.resolve())})
def deps(values):
    assert set(expected)<=set(values) and {p:values[p] for p in expected}==expected
    extra=set(values)-set(expected);assert extra<=set(allowed_extra) and all(values[p]==allowed_extra[p] for p in extra)
    return extra
hashes={n:sha(W2/n) for n in NAMES};assert hashes['inert-root-caller-manifest.json']==MANIFEST_SHA
m=read(W2/'inert-root-caller-manifest.json');assert set(m['files'])==NAMES-{'inert-root-caller-manifest.json'}
assert m['files']=={n:hashes[n] for n in m['files']} and m['candidate']==SOURCE
assert m['released'] is False and m['actual'] is False and m['inert'] is False and m['model_calls']==0
extra=deps(m['dependencies']);current=dict(m['dependencies'],**{str(W2/n):h for n,h in hashes.items()})
for p,h in current.items():assert sha(Path(p))==h,p
report=W/'task-4-inert2-caller-report.md';assert sha(report)==REPORT_SHA
old=junit(OLD/'code/inert-root-caller-preparation-20261102T230116820186Z/junit.xml');assert old['tests']==84
stages=[];metadata_stages=[];seen=False;copies_checked=0
def stage_time(p):
    found=re.search(r'\d{8}T\d{12}Z$',p.name);assert found,p.name
    return found.group()
for p in sorted((V/'code').glob('inert-root-caller-preparation-*'),key=stage_time):
    assert (p/'receipt.json').is_file()
    d=read(p/'receipt.json')
    if d.get('kind')=='fresh-binding-preparation':
        assert p.name.startswith('inert-root-caller-preparation-bindings-') and not (p/'junit.xml').exists()
        before=read(p/'immutable-before.json');after=read(p/'immutable-after.json')
        assert before==after and d['old_and_harness_unchanged'] and d['actual'] is False and d['inert'] is False and d['model_calls']==0
        assert d['files']=={str(W2/n):h for n,h in hashes.items()}
        for path,h in after.items():assert sha(Path(path))==h,path
        metadata_stages.append(dict(stage=p.name,receipt_sha256=sha(p/'receipt.json'),kind=d['kind'],old_and_harness_unchanged=True,immutable_before_sha256=sha(p/'immutable-before.json'),immutable_after_sha256=sha(p/'immutable-after.json'),tests_executed=False))
        continue
    before=read(p/'source-before.json');after=read(p/'source-after.json')
    assert before==after and d['inputs_unchanged'] and not d['drift_before'] and not d['drift_after']
    stage_manifest=None
    for label in ['before','after']:
        inventory=read(p/('copies-'+label+'.json'));assert set(inventory)==set(before)
        for original,item in inventory.items():
            cp=Path(item['copy']);assert cp.resolve().is_relative_to((p/('source-'+label)).resolve())
            assert cp.stat().st_size==item['bytes'] and sha(cp)==item['sha256']==before[original]
            copies_checked+=1
            if original==str(W2/'inert-root-caller-manifest.json') and label=='before':stage_manifest=read(cp)
    assert stage_manifest is not None;deps(stage_manifest['dependencies'])
    assert len(before)==len(stage_manifest['dependencies'])+5
    for n,h in stage_manifest['files'].items():assert before[str(W2/n)]==h
    assert d['argv'][:7]==[str(PY),'-B','-X','utf8','-m','pytest',str(W2/'test_root_inert_invocation.py')]
    assert d['actual'] is False and d['inert'] is False and d['model_calls']==0
    if d.get('kind')=='pure-mocked-caller-preparation-only':
        assert d['product_launches']==0
    elif d.get('kind')=='pure-mocked-focused-fresh-bindings':
        assert p.name.startswith('inert-root-caller-preparation-focus-') and '-k' in d['argv']
    else:
        raise AssertionError(('Unknown preparation receipt classification',p.name,d.get('kind')))
    j=junit(p/'junit.xml');assert j['errors']==j['skipped']==0
    stages.append(dict(stage=p.name,receipt_sha256=sha(p/'receipt.json'),junit_sha256=sha(p/'junit.xml'),stdout_sha256=sha(p/'stdout.log'),stderr_sha256=sha(p/'stderr.log'),counts={k:j[k] for k in ['tests','failures','errors','skipped']},source_copy_count=2*len(before),pins=len(before),exit_code=d['exit_code'],kind=d.get('kind'),product_launches=d.get('product_launches'),receipt_limit='Missing optional historical/focused metadata is null, never upgraded'))
    if p.name==FINAL:
        assert not seen;seen=True
        assert before==current and d['exit_code']==d['pytest_exit_code']==0 and '-k' not in d['argv']
        assert j['tests']==COUNT and j['failures']==0 and old['ids']<=j['ids'] and not (p/'stderr.log').read_bytes()
        assert sha(p/'receipt.json')==RECEIPT_SHA and sha(p/'junit.xml')==JUNIT_SHA
assert seen and stages[-1]['stage']==FINAL
canonical=['inert-root-dispatch.json','harness-approval.json','inert-root-release.json','inert-root-release.consumed.json','inert-native-baseline.json','inert-authority.json','inert-root-result.json','inert-root-result.pending.json','inert-root-launch-allocation.json','inert-root-live-hello.json','inert','actual']
absent={str(V/n):not (V/n).exists() for n in canonical};assert all(absent.values())
proof=V/'code/root-inert2-caller-before-review.json'
out(proof,dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),candidate=SOURCE,manifest_sha256=MANIFEST_SHA,report_sha256=REPORT_SHA,report_bytes=report.stat().st_size,caller5={n:dict(sha256=hashes[n],bytes=(W2/n).stat().st_size) for n in sorted(NAMES)},dependencies=m['dependencies'],additional_pins=sorted(extra),pin_count=len(current),source_raw_copies_checked=copies_checked,metadata_stages=metadata_stages,stages=stages,final_tests=COUNT,all_prior84_ids_retained=True,canonical_absence=absent,old_inputs_unchanged=True,scope='ROOT pure-data/hash/JUnit readback; no suite/runtime',execution_released=False,T2='NOT_PASSED'))
archive=V/'code/inert2-caller-author-r1';archive.mkdir(exist_ok=False)
for n in NAMES:new(archive/n,(W2/n).read_bytes())
new(archive/'report.md',report.read_bytes());out(archive/'seal.json',dict(files=hashes,report_sha256=REPORT_SHA))
package=W/'task-4-inert2-caller-review-package.txt';text='Task4-PORT-REV2 Task2 exact5 diff d4b→'+MANIFEST_SHA+'; productC118 and accepted new harness unchanged.\n'
for n in sorted(NAMES):
    p=W2/n;text+='\nFILE '+str(p)+' SHA256 '+hashes[n]+' bytes '+str(p.stat().st_size)+'\n'
    text+=''.join(difflib.unified_diff((W/n).read_text('utf8').splitlines(keepends=True),p.read_text('utf8').splitlines(keepends=True),fromfile='base-d4b/'+n,tofile=str(p),n=15))
new(package,text.encode('utf8'))
ip=W/'task-4-inert2-caller-review-inputs.json'
paths=[W/'task-4-inert2-caller-brief.md',report,proof,package,V/'harness-code-gate.json',newreview,newreview.with_name('review.md'),V/'inert-root-caller-preparation-authority.json',W/'task-4c-admission-protocol-ruling-1.md',W/'task-4c-read-publication-ruling-2.md',OLD/'inert-root-caller-review-3/verdict.json',OLD/'inert-root-caller-review-3/review.md']
out(ip,dict(candidate=SOURCE,manifest_sha256=MANIFEST_SHA,caller5=hashes,inputs={str(p):sha(p) for p in paths},tests=COUNT,all84_retained=True,execution_released=False))
bp=W/'task-4-inert2-caller-review-brief.md'
text=f'''# Task4-PORT-REV2 Task2 independent scoped caller review

Requirements {W}/task-4-inert2-caller-brief.md. Author report {report}. Exact contextual five-file diff {package} d4b→{MANIFEST_SHA}. Companion {ip} and root raw/JUnit proof {proof}. Read diff once; task-scoped spec+quality, no broad product or previous task review. Outside-diff reads only for a concrete named coupling and state why. Prior9 RC01..09 held closed unless this changed diff causes concrete regression.

Global constraints: only current8B digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330, no14B/larger/otherweights/fallback/default/download. C118/installedSDK/source31/P4/P1/query/fourbodies/protected5/KWS/H0a31 unchanged. NewW2five only, exactnewV2/harness/gate/review/preparation bindings; oldactual1PERMANENTFAIL1/1 immutable. Same275/310/315/260/300/315/0retry; no origin renewal, cap relaxation, native/model/profile/actual/UI/audio/kill or operational controls. Code review cannot grant runtime.

Verify namespace/dependency/hash bindings consistent, fixed future caller-review-1 path, freshabsence and typed release template. Existing HELLO/ROOTpreconsumeddispatch/one-entry/read-issued-two-paths-before-nativequeries/postadmitstate/restoration/firstcause/oneUUID/pending-close→atomiclink→canonicalexactbytes contracts preserved. Existing9closures and84originalIDs retained; examine code/test/evidence independently. Do not trust claims alone. No new capability/controller/algorithm or test that merely mirrors implementation.

Read-only checkout/index/refs; no subagents or Git mutation. No full suite or unchanged216/479+8 rerun. Only new focused pure/mock check if concrete code doubt has no existing answer, state and preserve evidence; no real processes/sockets/HTTP/model/actions. Report actual OS/timing as unverified separate native gate.

Write NEW {V}/inert-root-caller-review-1/review.md + verdict.json and identical {W}/task-4-inert2-caller-review-report.md. Human spec PASS/FAIL, strengths, Critical/Important/Minor findings file:line, named coupling checks/limits. Machine schema_version1, scopeT4_PORT_REV2_CALLER_BINDING_REVIEW,candidate,base_manifest_sha256=d4b73f6cf7731e149323d016c590a27656eefdd54d2fcf426d9b037e592168af,caller_manifest_sha256={MANIFEST_SHA},spec='PASS'/'FAIL',quality='APPROVED'/'NEEDS_FIXES',spec_verdict equal spec,quality_verdict equal quality,execution_released=false,T2NOT_PASSED,findings[],held_closed9IDs,reviewed_hashes. No selfhash or approval. Return compact verdict/findings/paths/hashes.
'''
new(bp,text.encode('utf8'))
print(json.dumps(dict(proof=str(proof),proof_sha256=sha(proof),package=str(package),package_sha256=sha(package),review_brief_sha256=sha(bp),tests=COUNT,stages=len(stages),copies=copies_checked,pins=len(current))))
