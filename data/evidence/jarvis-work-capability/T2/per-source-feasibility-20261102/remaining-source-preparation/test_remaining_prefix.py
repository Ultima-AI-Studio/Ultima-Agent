"""Socket-denied preparation. All mutable fixtures live under owned prep."""
import copy
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import pytest
import run_remaining_prefix as h


@pytest.fixture(autouse=True)
def deny_sockets(monkeypatch):
    calls=[]
    def deny(*a,**kw):
        calls.append(1)
        raise AssertionError('Real sockets prohibited')
    for name in ('connect','connect_ex'):
        monkeypatch.setattr(socket.socket,name,deny)
    monkeypatch.setattr(socket,'getaddrinfo',deny)
    yield
    assert calls == []


def save(path,value):
    path.write_text(json.dumps(value),encoding='utf8')


@pytest.fixture
def admitted(tmp_path,monkeypatch):
    assert tmp_path.resolve().is_relative_to(h.PREP.resolve())
    baseline=h.read(h.E/'S2-first-root-reconciliation.json')
    save(tmp_path/'S2-first-root-reconciliation.json',baseline)
    monkeypatch.setattr(h,'E',tmp_path)
    monkeypatch.setattr(h,'ACTUAL',tmp_path/'actual-fixture')
    snap=dict(captured_unix=time.time(),available_ram_bytes=12*2**30,
              commit_headroom_bytes=16*2**30,gpu_free_bytes=8*2**30,
              head=h.HEAD,selected_digest=h.frozen_core().DIGEST,
              protected5=baseline['protected_processes_after'],protected5_unchanged=True)
    snapshot=tmp_path/'snapshot.json'; save(snapshot,snap)
    root=h.ACTUAL/'S3/controller-unique'
    auth=dict(mode='remaining_source_sdk_prefix',execute=True,head=h.HEAD,digest=snap['selected_digest'],
              max_native_posts=1,group_total_cap=4,core_sha256=h.CORE_HASH,frozen_manifest_sha256=h.OLD_HASH,
              original_outcome_sha256=h.ORIGINAL_HASH,launcher_manifest_sha256=h.sha(h.PREP/'manifest.json'),
              source_id='S3',next_source='S3',previous_attempts=[],cumulative_spent_before=1,
              snapshot_path=str(snapshot),snapshot_sha256=h.sha(snapshot),run_root=str(root))
    return auth,root,snap


def test_admission_does_not_create_namespace(admitted):
    auth,root,_=admitted
    h.validate(auth,root)
    assert not h.ACTUAL.exists()


def test_tampered_core_bytes(tmp_path,monkeypatch):
    tampered=tmp_path/'core.py'
    tampered.write_bytes(h.CORE.read_bytes()+b'\n# tamper\n')
    monkeypatch.setattr(h,'CORE',tampered)
    with pytest.raises(ValueError,match='Hash mismatch'):
        h.frozen_core()


@pytest.mark.parametrize('mode',['S2','skip','spent','duplicate','original_hash','core_hash','stale',
                                 'low_ram','wrong_digest','protected','future','existing','unlisted'])
def test_reject_authority_before_io(admitted,mode):
    auth,root,snap=admitted
    if mode=='S2': auth['source_id']=auth['next_source']='S2'
    if mode=='skip': auth['source_id']=auth['next_source']='S1'
    if mode=='spent': auth['cumulative_spent_before']=4
    if mode=='duplicate': auth['previous_attempts']=[{}, {}, {}]
    if mode=='original_hash': auth['original_outcome_sha256']='0'*64
    if mode=='core_hash': auth['core_sha256']='0'*64
    if mode=='stale': snap['captured_unix']-=31
    if mode=='future': snap['captured_unix']+=60
    if mode=='low_ram': snap['available_ram_bytes']-=1
    if mode=='wrong_digest': snap['selected_digest']='0'*64
    if mode=='protected': snap['protected5'][0]['pid']=1
    if mode in ('existing','unlisted'):
        (root if mode=='existing' else root.with_name('unlisted')).mkdir(parents=True)
    save(Path(auth['snapshot_path']),snap); auth['snapshot_sha256']=h.sha(auth['snapshot_path'])
    with pytest.raises((ValueError,KeyError)):
        h.validate(auth,root)


def add_prior(auth, source, name):
    root=h.ACTUAL/source/name; root.mkdir(parents=True)
    packet=root/'outcome.json'
    save(packet,dict(source_id=source,status='PENDING_INDEPENDENT_FACT_REVIEW',native_posts=1,
                     native_post_intents=1,confirmed=True,stage_payload=dict(facts=[{'claim':'offline fixture'}])))
    review=root/'review.json'
    save(review,dict(verdict='PASS',source_id=source,run_root=str(root),outcome_sha256=h.sha(packet)))
    auth['previous_attempts'].append(dict(source_id=source,run_root=str(root),outcome_sha256=h.sha(packet),
                                        review_path=str(review),review_sha256=h.sha(review)))
    auth['cumulative_spent_before']+=1
    return packet,review


@pytest.mark.parametrize('mode',['pass','tamper_packet','tamper_review','fail_review','wrong_review_binding','zero_post','gap'])
def test_prior_chain(admitted,mode):
    auth,_,_=admitted
    packet,review=add_prior(auth,'S3','first')
    auth['source_id']=auth['next_source']='S1'; root=h.ACTUAL/'S1/second'; auth['run_root']=str(root)
    if mode=='tamper_packet': packet.write_text('{}')
    if mode=='tamper_review': review.write_text('{}')
    if mode in ('fail_review','wrong_review_binding'):
        verdict=h.read(review)
        verdict['verdict' if mode=='fail_review' else 'outcome_sha256']='FAIL'
        save(review,verdict); auth['previous_attempts'][0]['review_sha256']=h.sha(review)
    if mode=='zero_post':
        outcome=h.read(packet); outcome['native_posts']=0; save(packet,outcome)
        auth['previous_attempts'][0]['outcome_sha256']=h.sha(packet)
    if mode=='gap': auth['previous_attempts'][0]['source_id']='S1'
    if mode=='pass': h.validate(auth,root)
    else:
        with pytest.raises(ValueError): h.validate(auth,root)


@pytest.mark.parametrize('optimization',['-O','-OO','env'])
def test_optimization_before_cli_and_files(tmp_path,optimization):
    env=os.environ.copy()
    argv=[sys.executable,'-B']
    if optimization=='env': env['PYTHONOPTIMIZE']='1'
    else: argv.append(optimization)
    argv += [str(h.PREP/'run_remaining_prefix.py'),'--authority',str(tmp_path/'missing'),
             '--run-root',str(tmp_path/'must-not-exist')]
    result=subprocess.run(argv,env=env,capture_output=True,text=True)
    assert result.returncode != 0 and 'Optimized Python execution is prohibited' in result.stderr
    assert not (tmp_path/'must-not-exist').exists()
    assert 'FileNotFoundError' not in result.stderr


def test_s3_frozen_core_actual_sdk_mock(tmp_path,monkeypatch):
    import httpx
    core=h.frozen_core(); sys.path.insert(0,str(core.CHECKOUT))
    from openjarvis.core.registry import ToolRegistry
    from src.brain import agent_server
    now=[100.]; requests=[]; holder={}
    original_register=core.register_stage
    def register(ledger):
        holder['ledger']=ledger
        return original_register(ledger)
    monkeypatch.setattr(core,'register_stage',register)
    def transport(req):
        requests.append((req.method,req.url.path))
        if req.url.path=='/api/tags':
            return httpx.Response(200,json={'models':[{'name':core.MODEL,'digest':core.DIGEST}]})
        if req.url.path=='/api/version': return httpx.Response(200,json={'version':'0.32.15'})
        assert req.method=='POST' and req.url.path=='/api/chat'
        body=json.loads(req.content); ledger=holder['ledger']
        assert ledger.source['source_id']=='S3'
        assert body['options']==dict(num_ctx=16384,temperature=0,num_predict=480)
        assert all(body[k] is False for k in ('think','stream','truncate','shift'))
        assert body['messages'][0]['content'].startswith(core.PROMPT)
        ref,card=next((r,c) for r,c in ledger.table.items() if c['kind']=='code')
        # Derived mechanical witness, never a supplied source answer or oracle.
        payload=dict(stage_token=ledger.token,facts=[dict(claim=card['symbol'],ref=ref,
                     ranges=[dict(lo=card['first_line'],hi=card['last_line'])])])
        return httpx.Response(200,json=dict(model=core.MODEL,message=dict(role='assistant',
            content=core.compact(dict(action=core.TOOL,action_input=payload))),
            done=True,done_reason='stop',prompt_eval_count=4000,eval_count=50))
    init=httpx.Client.__init__
    def mock_init(self,*args,**kw):
        kw['transport']=httpx.MockTransport(transport); init(self,*args,**kw)
    monkeypatch.setattr(httpx.Client,'__init__',mock_init)
    owner=core.make_owner(tmp_path/'sdk-home')
    try:
        owner._ensure_engine()
        assert requests==[('GET','/api/tags')]
        requests.clear()
        with httpx.Client(base_url=core.ORIGIN) as client:
            out=core.run_prefix(owner,client,tmp_path,'S3',lambda:core.DIGEST,clock=lambda:now[0])
        assert out['status']=='PENDING_INDEPENDENT_FACT_REVIEW',out.get('error')
        assert requests==[('GET','/api/version'),('GET','/api/tags'),('POST','/api/chat')]
        assert out['native_posts']==out['native_post_intents']==1 and out['metadata_gets']==2
        assert out['confirmed'] and out['sdk_result']['turns']==1
        assert not out['captured_capabilities']['writer_exposed'] and out['effects']==[]
        assert out['d']-out['b']<=36 and out['preflight_messages']==out['secured_messages']
        # Generated messages are from the unchanged core and original S3 bytes.
        _,sources=core.load_material()
        assert holder['ledger'].source==sources[2]
        assert h.sha(h.CORE)==h.CORE_HASH
    finally:
        owner.close()
        ToolRegistry._entries().pop(core.TOOL,None)  # test-owned registration only
