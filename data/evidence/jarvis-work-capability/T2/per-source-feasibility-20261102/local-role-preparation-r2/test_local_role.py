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
import run_local_role_prefix as h


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
    # Keep new manifest and all mutation fixtures under owned prep.
    fixture_prep=tmp_path/'prep'; fixture_prep.mkdir()
    manifest=h.read(h.PREP/'manifest.json')
    inventories={}
    for n,(oldroot,entries) in enumerate(h.read(h.PREP/'old-namespace-inventories.json').items()):
        newroot=tmp_path/('old-namespace-'+str(n)); newroot.mkdir()
        for rel,digest in entries.items():
            target=newroot/rel
            if digest=='directory': target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((Path(oldroot)/rel).read_bytes())
        inventories[str(newroot)]=entries
    save(fixture_prep/'old-namespace-inventories.json',inventories)
    for item in manifest['first_failures']:
        oldpath=Path(item['path'])
        index=0 if item['source_id']=='S2' else 1
        oldroot=next(iter(h.read(h.PREP/'old-namespace-inventories.json'))) if index==0 else list(h.read(h.PREP/'old-namespace-inventories.json'))[1]
        item['path']=str(tmp_path/('old-namespace-'+str(index))/oldpath.relative_to(Path(oldroot)))
    save(fixture_prep/'manifest.json',manifest)
    monkeypatch.setattr(h,'PREP',fixture_prep)
    monkeypatch.setattr(h,'ACTUAL',tmp_path/'actual-fixture')
    monkeypatch.setattr(h,'TRUSTED_ACTUAL',tmp_path/'actual-fixture',raising=False)
    snap=dict(captured_unix=time.time(),available_ram_bytes=12*2**30,
              commit_headroom_bytes=16*2**30,gpu_free_bytes=8*2**30,
              head=h.HEAD,selected_digest=h.frozen_core().DIGEST,
              protected5=baseline['protected_processes_after'],protected5_unchanged=True,source_id='S4',source21_hashes_match=True,
              controller_readonly_metadata_not_trial=dict(loaded=dict(models=[])))
    snapshot=tmp_path/'snapshot.json'; save(snapshot,snap)
    root=h.ACTUAL/'S4/controller-unique'
    auth=dict(mode='local_role_sdk_prefix',execute=True,head=h.HEAD,digest=snap['selected_digest'],
              max_native_posts=1,group_total_cap=4,core_sha256=h.CORE_HASH,frozen_manifest_sha256=h.OLD_HASH,
              original_outcome_sha256=h.ORIGINAL_HASH,launcher_manifest_sha256=h.sha(h.PREP/'manifest.json'),
              source_id='S4',next_source='S4',previous_attempts=[],cumulative_spent_before=2,
              snapshot_path=str(snapshot),snapshot_sha256=h.sha(snapshot),run_root=str(root))
    auth['first_failures']=manifest['first_failures']
    review=tmp_path/'preparation-review.json'
    save(review,dict(SPEC='PASS',QUALITY='PASS',manifest_sha256=auth['launcher_manifest_sha256']))
    auth.update(preparation_review_path=str(review),preparation_review_sha256=h.sha(review))
    snap['run_root']=str(root);save(snapshot,snap);auth['snapshot_sha256']=h.sha(snapshot)
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


@pytest.mark.parametrize('boundary',['namespace','source','prior_attempt'])
def test_real_windows_junction_refused(admitted,tmp_path,boundary):
    auth,root,_=admitted
    outside=tmp_path/'outside-namespace'; outside.mkdir()
    if boundary=='namespace':
        link=h.ACTUAL; target=outside
    elif boundary=='source':
        h.ACTUAL.mkdir(); link=h.ACTUAL/'S4'; target=outside
    else:
        add_prior(auth,'S4','first')
        link=h.ACTUAL/'S4/first'; target=outside/'first'
        link.rename(target)
        auth['source_id']=auth['next_source']='S1'
        root=h.ACTUAL/'S1/second'; auth['run_root']=str(root)
    result=subprocess.run(['cmd','/c','mklink','/J',str(link),str(target)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    def contents():
        return {str(f.relative_to(outside)):('directory',None) if f.is_dir() else ('file',f.read_bytes())
                for f in outside.rglob('*')}
    baseline=contents()
    try:
        assert link.is_junction() and not link.is_symlink()
        with pytest.raises(ValueError,match='[Rr]eparse'):
            h.validate(auth,root)
        assert contents()==baseline and not root.exists()
        save(tmp_path/'junction-proof.json',dict(boundary=boundary,is_junction=True,is_symlink=False,
             target_outside_namespace=not target.is_relative_to(h.TRUSTED_ACTUAL),
             off_namespace_writes_during_validation=0,run_leaf_created=False))
    finally:
        os.rmdir(link)  # remove only this test-created junction, never target content


def test_actual_constant_cannot_redefine_trusted_root(admitted,tmp_path,monkeypatch):
    auth,_,_=admitted
    monkeypatch.setattr(h,'ACTUAL',tmp_path/'redirected')
    root=h.ACTUAL/'S4/first'; auth['run_root']=str(root)
    with pytest.raises(ValueError,match='[Tt]rusted'):
        h.validate(auth,root)
    assert not h.ACTUAL.exists()


def test_noncanonical_attempt_alias_refused(admitted):
    auth,root,_=admitted
    aliased=root.parent/'unused/..'/root.name
    auth['run_root']=str(aliased)
    with pytest.raises(ValueError):
        h.validate(auth,aliased)


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
    packet,review=add_prior(auth,'S4','first')
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
    snap=h.read(auth['snapshot_path']);snap.update(source_id='S1',run_root=str(root));save(Path(auth['snapshot_path']),snap);auth['snapshot_sha256']=h.sha(auth['snapshot_path'])
    if mode=='pass': h.validate(auth,root)
    else:
        with pytest.raises(ValueError): h.validate(auth,root)


@pytest.mark.parametrize('optimization',['-O','-OO','env'])
def test_optimization_before_cli_and_files(tmp_path,optimization):
    env=os.environ.copy()
    argv=[sys.executable,'-B']
    if optimization=='env': env['PYTHONOPTIMIZE']='1'
    else: argv.append(optimization)
    argv += [str(h.PREP/'run_local_role_prefix.py'),'--authority',str(tmp_path/'missing'),
             '--run-root',str(tmp_path/'must-not-exist')]
    result=subprocess.run(argv,env=env,capture_output=True,text=True)
    assert result.returncode != 0 and 'Optimized Python execution is prohibited' in result.stderr
    assert not (tmp_path/'must-not-exist').exists()
    assert 'FileNotFoundError' not in result.stderr


@pytest.mark.parametrize('source_id',['S4','S1'])
def test_local_role_actual_sdk_mock(tmp_path,monkeypatch,source_id):
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
        assert ledger.source['source_id']==source_id
        assert body['options']==dict(num_ctx=16384,temperature=0,num_predict=480)
        assert all(body[k] is False for k in ('think','stream','truncate','shift'))
        assert body['messages'][0]['content'].startswith(core.PROMPT)
        ref,card=next(iter(ledger.table.items()))
        # Derived mechanical witness, never a supplied source answer or oracle.
        payload=dict(stage_token=ledger.token,facts=[dict(claim=card['symbol'] or 'mechanical witness only',ref=ref,
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
            out=core.run_prefix(owner,client,tmp_path,source_id,lambda:core.DIGEST,clock=lambda:now[0],request_proof=h.canonical_proof(core,source_id))
        assert out['status']=='PENDING_INDEPENDENT_FACT_REVIEW',out.get('error')
        assert requests==[('GET','/api/version'),('GET','/api/tags'),('POST','/api/chat')]
        assert out['native_posts']==out['native_post_intents']==1 and out['metadata_gets']==2
        assert out['confirmed'] and out['sdk_result']['turns']==1
        assert not out['captured_capabilities']['writer_exposed'] and out['effects']==[]
        assert out['d']-out['b']<=36 and out['preflight_messages']==out['secured_messages']
        h.verify_messages(core,source_id,out['raw_messages'],out['schema'],'raw_messages')
        assert len([e for e in out['events'] if e['type']=='tool_call_end'])==1
        # Generated messages are from the unchanged core and original source bytes.
        _,sources=core.load_material()
        assert holder['ledger'].source==sources[3 if source_id=='S4' else 0]
        assert h.sha(h.CORE)==h.CORE_HASH
    finally:
        owner.close()
        ToolRegistry._entries().pop(core.TOOL,None)  # test-owned registration only

@pytest.mark.parametrize('mode',['warm','missing_residency','source21','unbound_root','S3','low_commit','low_gpu','old_s2_tamper','old_s3_tamper','old_omission','new_zero_post','review_fail'])
def test_new_question_boundaries(admitted,mode):
    auth,root,snap=admitted
    if mode=='warm':snap['controller_readonly_metadata_not_trial']['loaded']['models']=[{'name':'resident'}]
    if mode=='missing_residency':snap.pop('controller_readonly_metadata_not_trial')
    if mode=='source21':snap['source21_hashes_match']=False
    if mode=='unbound_root':snap['run_root']=str(root.with_name('foreign'))
    if mode=='S3':auth['source_id']=auth['next_source']='S3'
    if mode=='low_commit':snap['commit_headroom_bytes']-=1
    if mode=='low_gpu':snap['gpu_free_bytes']-=1
    if mode in ('old_s2_tamper','old_s3_tamper'):
        Path(auth['first_failures'][0 if mode=='old_s2_tamper' else 1]['path']).write_text('{}')
    if mode=='old_omission':
        inventory=h.read(h.PREP/'old-namespace-inventories.json');oldroot=Path(next(iter(inventory)))
        (oldroot/'unexpected-zero-post').mkdir()
    if mode=='new_zero_post':root.with_name('zero-post').mkdir(parents=True)
    if mode=='review_fail':
        review=Path(auth['preparation_review_path']);save(review,dict(SPEC='FAIL',QUALITY='PASS',manifest_sha256=auth['launcher_manifest_sha256']));auth['preparation_review_sha256']=h.sha(review)
    save(Path(auth['snapshot_path']),snap);auth['snapshot_sha256']=h.sha(auth['snapshot_path'])
    with pytest.raises((ValueError,KeyError)):h.validate(auth,root)
    assert not root.exists()


@pytest.mark.parametrize('source',['S4','S1'])
def test_canonical_query_and_wire_refuse_tamper(source):
    import httpx
    from src.brain.agent_server import _research_sampler_schema
    core=h.frozen_core();template=h.read(h.PREP/(source+'-template.json'))
    query,catalogue=core.load_material()
    for field in ('raw_messages','preflight_messages'):
        h.verify_messages(core,source,template[field],template['schema'],field)
        material=core.strict(template[field][1]['content'])
        assert material['background_original_query'].encode('utf8')==query.encode('utf8')
        assert 'original_query' not in material
    body=dict(model=core.MODEL,messages=template['preflight_messages'],format=_research_sampler_schema(template['schema']),
              options=dict(num_ctx=16384,temperature=0,num_predict=480),tools=[],think=False,stream=False,truncate=False,shift=False)
    gate=h.wire_gate(core,source)
    gate(httpx.Request('POST',core.ORIGIN+'/api/chat',json=body))
    body['messages'][1]['content']+=' '
    with pytest.raises(ValueError):gate(httpx.Request('POST',core.ORIGIN+'/api/chat',json=body))


def test_import_only_core_direct_cli(tmp_path):
    core=h.frozen_core()
    result=subprocess.run([sys.executable,'-B',str(h.CORE),'--authority',str(tmp_path/'missing'),'--run-root',str(tmp_path/'forbidden')],capture_output=True,text=True)
    assert result.returncode!=0 and 'Import-only' in result.stderr and 'FileNotFoundError' not in result.stderr
    assert not (tmp_path/'forbidden').exists()


def test_native_get_budget_no_third_send(tmp_path):
    import httpx
    core=h.frozen_core();_,sources=core.load_material();source=sources[3]
    view,_=core.project(source);ledger=core.StageLedger({},source,view,core.cards(source,view),36,lambda:0)
    requests=[]
    def handle(req):requests.append(req);return httpx.Response(200,json={})
    with httpx.Client(base_url=core.ORIGIN,transport=httpx.MockTransport(handle)) as client:
        leaf=core.NativeLeaf(client,ledger,tmp_path,lambda:core.DIGEST)
        leaf.io('GET','/api/version');leaf.io('GET','/api/tags')
        with pytest.raises(ValueError,match='GET cap'):leaf.io('GET','/api/tags')
    assert len(requests)==2 and leaf.posts==0

@pytest.mark.parametrize('mode',['delayed_proof','projection_mismatch','happy'])
def test_pre_admission_canonical_dispatch(tmp_path,monkeypatch,mode):
    import httpx
    from src.brain.agent_server import _research_sampler_schema
    core=h.frozen_core();template=h.read(h.PREP/'S4-template.json')
    now=[35.99];transport_times=[];observer=[]
    source=template['source'];view=template['view'];table={int(k):v for k,v in template['table'].items()}
    ledger=core.StageLedger({},source,view,table,36,lambda:now[0]);ledger.token=h.SENTINEL;ledger.schema=template['schema']
    body=dict(model=core.MODEL,messages=copy.deepcopy(template['preflight_messages']),format=_research_sampler_schema(template['schema']),
              options=dict(num_ctx=16384,temperature=0,num_predict=480),tools=[],think=False,stream=False,truncate=False,shift=False)
    if mode=='projection_mismatch':body['messages'][1]['content']+=' '
    original_read=h.read
    def slow_read(path):
        result=original_read(path)
        if mode=='delayed_proof' and Path(path).name=='S4-template.json':now[0]=37.
        return result
    monkeypatch.setattr(h,'read',slow_read)
    def transport(request):transport_times.append(now[0]);return httpx.Response(200,json={})
    with httpx.Client(base_url=core.ORIGIN,transport=httpx.MockTransport(transport)) as client:
        leaf=core.NativeLeaf(client,ledger,tmp_path,lambda:core.DIGEST,h.canonical_proof(core,'S4'))
        leaf.expected_raw_messages=template['raw_messages']
        with core.observe_http(observer,lambda:'trial'):
            if mode=='happy':leaf.io('POST','/api/chat',json=body)
            else:
                with pytest.raises((ValueError,TimeoutError)):leaf.io('POST','/api/chat',json=body)
    if mode=='happy':
        assert transport_times==[35.99] and leaf.posts==leaf.post_intents==leaf.post_admissions==1
        assert observer[0]['method']=='POST'
    else:
        assert transport_times==[] and leaf.posts==0 and observer==[]
        assert leaf.post_intents==leaf.post_admissions==0
    core.save(tmp_path/'pre-admission-proof.json',dict(mode=mode,deadline=36,transport_times=transport_times,
              native_posts=leaf.posts,native_post_intents=leaf.post_intents,observer=observer))


def test_post_audit_failure_preserves_full_saved_packet(tmp_path,monkeypatch):
    import httpx
    core=h.frozen_core();template=h.read(h.PREP/'S4-template.json')
    holder={};requests=[]
    original_register=core.register_stage
    def register(ledger):holder['ledger']=ledger;return original_register(ledger)
    monkeypatch.setattr(core,'register_stage',register)
    def transport(req):
        requests.append((req.method,req.url.path))
        if req.url.path=='/api/tags':return httpx.Response(200,json={'models':[{'name':core.MODEL,'digest':core.DIGEST}]})
        if req.url.path=='/api/version':return httpx.Response(200,json={'version':'0.32.15'})
        ref,card=next(iter(holder['ledger'].table.items()))
        payload=dict(stage_token=holder['ledger'].token,facts=[dict(claim=card['symbol'] or 'mechanical witness',ref=ref,
                       ranges=[dict(lo=card['first_line'],hi=card['last_line'])])])
        return httpx.Response(200,json=dict(model=core.MODEL,message=dict(role='assistant',content=core.compact(dict(action=core.TOOL,action_input=payload))),
                              done=True,done_reason='stop',prompt_eval_count=4000,eval_count=50))
    init=httpx.Client.__init__
    def mock_init(self,*args,**kw):kw['transport']=httpx.MockTransport(transport);init(self,*args,**kw)
    monkeypatch.setattr(httpx.Client,'__init__',mock_init)
    owner=core.make_owner(tmp_path/'sdk-home')
    from openjarvis.core.registry import ToolRegistry
    try:
        owner._ensure_engine()
        with httpx.Client(base_url=core.ORIGIN) as client:
            original=core.run_prefix(owner,client,tmp_path,'S4',lambda:core.DIGEST,clock=lambda:100.,request_proof=h.canonical_proof(core,'S4'))
        assert original['status']=='PENDING_INDEPENDENT_FACT_REVIEW'
        # A labelled synthetic observation proves nonempty effects are not erased.
        original['effects']=[dict(kind='offline_preservation_sentinel',synthetic=True)]
        core.save(tmp_path/'outcome.json',original)
        saved_before=h.read(tmp_path/'outcome.json')
        output=h.preserve_failure(original,ValueError('forced post-run raw proof rejection'),'S4','trial',[])
        output['owner_closed']=True
        core.save(tmp_path/'outcome.json',output)
        saved_after=h.read(tmp_path/'outcome.json')
        for key,value in saved_before.items():
            if key not in ('status','owner_closed'):assert saved_after[key]==value,key
        assert saved_after['status']=='FAILED' and saved_after['confirmed'] is True
        assert saved_after['mechanical_status_before_audit']=='PENDING_INDEPENDENT_FACT_REVIEW'
        assert saved_after['audit_failures'][0]['classification']=='post_run_audit_failure'
        assert saved_after['native_posts']==saved_after['native_post_intents']==1
        assert saved_after['stage_payload']['facts'] and saved_after['owner_closed'] is True
        assert saved_after['timeline'] and saved_after['events'] and saved_after['sdk_result'] and saved_after['wire']
    finally:
        owner.close();ToolRegistry._entries().pop(core.TOOL,None)
