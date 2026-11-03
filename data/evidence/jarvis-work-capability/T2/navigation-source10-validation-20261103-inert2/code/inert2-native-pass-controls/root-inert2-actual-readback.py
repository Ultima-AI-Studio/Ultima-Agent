"""Independent closed-file readback only; never probes a port, imports a caller or reruns a case."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess
import uuid

C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
W=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101';W2=W/'inert-revision2'
H=Path('H:/UltimaAI/UltimaAgent');T=H/'data/evidence/jarvis-work-capability/T2'
OLD=T/'navigation-source10-validation-20261102';V=T/'navigation-source10-validation-20261103-inert2'
def unique(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ValueError('Duplicate JSON key')
        d[k]=v
    return d
def bad_constant(value):raise ValueError('Nonfinite JSON')
def read(p):return json.loads(p.read_bytes(),object_pairs_hook=unique,parse_constant=bad_constant)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def encode(d):return (json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def new(p,d):
    raw=encode(d)
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    assert p.read_bytes()==raw
def git(*args):
    r=subprocess.run(['git','-C',str(C),*args],capture_output=True);assert r.returncode==0,r.stderr[:1000];return r.stdout.decode().strip()
assert git('rev-parse','HEAD')=='118ba152b007c30d358c8bc44c51aabe8ae820f0'
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
process=read(V/'inert-root-exec-outcome.json')
assert process['exec_session']==2635 and process['session_closed'] is True
assert process['shell_exit_code']==process['python_exit_code']==0 and process['go_submissions']==1
assert process['raw_tool_output_sha256']==sha(V/'root-inert2-exec2635-output.raw.txt')
assert process['raw_tool_output_utf8_bytes']==(V/'root-inert2-exec2635-output.raw.txt').stat().st_size
r=read(V/'inert-root-result.json');raw=(V/'inert-root-result.json').read_bytes()
assert raw==(V/'inert-root-result.pending.json').read_bytes()==encode(r)
assert r['kind']=='source10_inert_root_adjudication' and r['overall']=='ELIGIBLE_FOR_ROOT_REVIEW'
assert r['first_cause'] is None and r['later_veto'] is None and r['attempts']==1 and r['retry']==0
assert r['actual'] is False and type(r['model_calls']) is int and r['model_calls']==0
assert r['T2']=='NOT_PASSED' and all(r[k]=='CLOSED' for k in ['T3','Owner','production'])
hello=read(V/'inert-root-live-hello.json');assert r['entry']==hello['entry'] and hello['entry']['pid']==29844
assert r['dispatch_sha256']==sha(V/'inert-root-dispatch.json') and r['release_sha256']==sha(V/'inert-root-release.json')
allocation=read(V/'inert-root-launch-allocation.json');release=read(V/'inert-root-release.json')
assert allocation['release_id']==release['release_id']==process['release_id']=='c54776d8-44fe-428f-b6ac-20c2824329ef'
assert allocation['consumed']==allocation['max_attempts']==1 and allocation['retry']==0
outcome=r['outcome'];terminal=outcome['result'];witness=outcome['witness'];folder=Path(terminal['folder'])
assert folder.resolve().is_relative_to((V/'inert').resolve()) and folder.name==witness['run_id']==terminal['run_id']
assert str(uuid.UUID(folder.name))==folder.name and uuid.UUID(folder.name).version==4
assert read(folder/'terminal.json')==terminal and sha(folder/'terminal.json')==witness['terminal_sha256']
assert terminal['kind']=='inert' and terminal['overall']=='READY_FOR_ROOT_TIMING_WITNESS'
assert terminal['actual'] is False and terminal['model_calls']==terminal['product_cli']==0
assert terminal['errors']==[] and terminal['first_failure'] is None
assert witness['eligible'] is True and witness['permanent'] is True and witness['observation_error'] is None
assert witness['observer']=='trusted-root-enclosing-contract'
assert set(witness['proofs'])=={'closed','cleanup','pins','protected','readback'} and all(v is True for v in witness['proofs'].values())
origin=hello['entry']['origin_ns'];assert r['origin_ns']==witness['origin_ns']==origin
assert witness['work_cutoff_ns']==origin+275000000000 and witness['cleanup_cutoff_ns']==origin+310000000000 and witness['outer_cutoff_ns']==origin+315000000000
assert type(witness['observed_ns']) is int and origin<=witness['observed_ns']<=witness['outer_cutoff_ns']
index=read(folder/'seal-index.json');assert sha(folder/'seal-index.json')==witness['seal_index_sha256']
assert index['files']==witness['member_hashes'] and index['run_id']==folder.name and index['timing']==terminal['timing']
members={p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()}
assert set(members)==set(index['files'])|{'seal-index.json'} and {n:members[n] for n in index['files']}==index['files']
cleanup=terminal['cleanup'];assert cleanup['status']=='PASS' and cleanup['port_closed'] is True and cleanup['port_definitively_closed'] is True and cleanup['logs_closed'] is True and cleanup['errors']==[] and not cleanup.get('effects_unknown',False)
assert read(folder/'cleanup.json')['status']=='PASS'
assert cleanup['processes'] and all(p['absent'] is True for p in cleanup['processes'])
ports=[e for e in terminal['io_events'] if e['io']=='port'];assert len(ports)==1 and ports[0]['code']==10061 and ports[0]['definitive_refusal'] is True
before=read(folder/'protected-before.json');after=read(folder/'protected-after.json')
expected=read(OLD/'inert/1cd7559d-0af9-455a-8c2b-cdecd5970197/protected-before.json')
assert before==after==expected and len(before)==5 and {p['pid'] for p in before}=={12796,492,37880,32856,18068}
assert not {p['identity']['pid'] for p in cleanup['processes']} & {p['pid'] for p in before}
admission=read(folder/'admission.json');boundary_before=read(folder/'boundary-before.json');boundary_after=read(folder/'boundary-after.json')
assert boundary_before==boundary_after and boundary_before['protected']==before
for path,h in admission['pins'].items():assert sha(Path(path))==h,path
for path,h in boundary_after['pins'].items():assert sha(Path(path))==h,path
corpus=T/'source6-native-reference/controlled-corpus-inputs/corpus.json'
assert sha(corpus)=='9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002'
question=read(folder/'argv-roundtrip.json')['question'];assert question==read(corpus)['query'] and len(question.encode('utf8'))==774
exchange=read(folder/'inert-exchange.json');assert exchange['mode']=='inert' and exchange['method']=='GET' and exchange['response']=={'inert':True}
m=read(W2/'inert-root-caller-manifest.json');assert sha(W2/'inert-root-caller-manifest.json')=='0e91519c9bfcbaba32ada6068b909281ab68fcb4a4142d15abd257a4759ac6d9'
for p,h in m['dependencies'].items():assert sha(Path(p))==h,p
for n,h in m['files'].items():assert sha(W2/n)==h,n
for p,h in read(V/'code/root-preparation-inputs-before.json')['old_pins'].items():assert sha(Path(p))==h,p
assert sha(OLD/'inert-actual1-root-readback.json')=='f37eb5d7ea954a899105d1efc4a358f382614b56cfa03fc4a671e4f93cbd4d7a'
proof=V/'inert-actual2-root-readback.json'
new(proof,dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),kind='ACTUAL_INERT2_CLOSED_PACKET_READBACK',candidate='118ba152b007c30d358c8bc44c51aabe8ae820f0',overall='PASS_INERT_ONLY',folder=str(folder),run_id=folder.name,exec_session=2635,shell_exit_code=0,python_exit_code=0,python_exit_explicitly_propagated=True,source_record_overall=r['overall'],witness_eligible=True,elapsed_seconds=(witness['observed_ns']-origin)/1e9,witness=witness,cleanup=cleanup,recorded_cleanup_port_events=ports,case_files=members,index_inventory_and_raw_hashes_match=True,protected5_native_before_after_exact=True,admitted_pins_current_raw_equal=True,query_roundtrip_exact=True,original_query_utf8_bytes=774,corpus_sha256=sha(corpus),canonical_pending_and_expected_serialization_equal=True,root_result_sha256=sha(V/'inert-root-result.json'),exec_outcome_sha256=sha(V/'inert-root-exec-outcome.json'),raw_tool_capture_sha256=sha(V/'root-inert2-exec2635-output.raw.txt'),caller_manifest_sha256=sha(W2/'inert-root-caller-manifest.json'),harness_manifest_sha256=sha(V/'harness/manifest.json'),launch_submissions=1,retry=0,model_calls=0,product_cli=0,oldactual1_remains='PERMANENT_FAIL_1of1_CLOSED',unknown_prior_mock_END='UNEXPLAINED_NOT_CLAIMED_FIXED',profile=False,actual=False,T2='NOT_PASSED',T3='CLOSED',Owner='CLOSED',production='CLOSED',scope='Root independent post-case byte/data readback; no new port/native probe or late promotion. Only inert listener/closure qualification; no product/model research acceptance.'))
print(json.dumps(dict(proof=str(proof),sha256=sha(proof),overall='PASS_INERT_ONLY',case_files=len(members),elapsed_seconds=(witness['observed_ns']-origin)/1e9,model_calls=0,protected5_exact=True)))
