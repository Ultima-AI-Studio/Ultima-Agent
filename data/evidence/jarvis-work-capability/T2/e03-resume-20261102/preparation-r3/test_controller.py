import copy,hashlib,json,sys,datetime as dt,subprocess
from pathlib import Path
import pytest
import controller as c

@pytest.fixture
def release(tmp_path,monkeypatch):
    monkeypatch.setattr(c,'R',tmp_path)
    def write(relative,value):
        path=tmp_path/relative; path.parent.mkdir(parents=True,exist_ok=True); c.save(path,value); return path
    write('source21-before.json',{})
    # Root authority is simulated only inside pytest's isolated owned root.
    monkeypatch.setattr(c,'P',tmp_path/'package'); (c.P).mkdir(); (c.P/'controller.py').write_bytes(Path(c.__file__).read_bytes()); c.save(c.P/'manifest.json',{'files':{'controller.py':c.sha(c.P/'controller.py')}})
    review=tmp_path/'review-preparation-3/review.md';review.parent.mkdir();review.write_text('independent PASS')
    approval=write('controller-preparation-approval.json',{'schema':2,'reviewer':'root-independent','overall':'PASS','preparation_manifest_sha256':c.sha(c.P/'manifest.json'),'review_sha256':c.sha(review)})
    ledger=write('controller-ledger.json',{'schema':2,'consumed':['e03-round1'],'released_case':'e03-round1'})
    proof=write('controller-native-preflight/e03-round1.json',{'recorded_at':c.utc().isoformat(),'source21_sha256':c.sha(tmp_path/'source21-before.json'),'head':'244d2120abcd6b8d7744f74a05bd22de46a2d3a5','model':c.MODEL,'digest':c.DIGEST})
    folder=tmp_path/'actual/e03-round1'; now=c.utc()
    auth=write('controller-authority/e03-round1.json',{'schema':2,'issuer':'root','case':'e03-round1','folder':str(folder),'issued_at':now.isoformat(),'expires_at':(now+dt.timedelta(seconds=110)).isoformat(),'model':c.MODEL,'digest':c.DIGEST,'preparation_manifest_sha256':c.sha(c.P/'manifest.json'),'approval_sha256':c.sha(approval),'ledger_sha256':c.sha(ledger),'native_preflight_sha256':c.sha(proof),'prior_reviews':[]})
    return folder,auth,ledger

def test_single_release(release): c.validate_authority('e03-round1',*release)
@pytest.mark.parametrize('case',['e02','e03','e03-round4','e01-round4','../e03-round1'])
def test_other_cases(release,case):
    with pytest.raises(ValueError): c.validate_authority(case,*release)
@pytest.mark.parametrize('change',['root','old','ledger','model','runner','prior','authority_path','ledger_path','expired','future','proof_age','sibling','approval','review'])
def test_failclosed(release,change):
    folder,auth,ledger=release; value=c.load(auth)
    if change=='root': folder=folder.parent.parent/'outside'
    if change=='old': folder.mkdir(parents=True)
    if change=='ledger': c.save(ledger,dict(c.load(ledger),consumed=['e03-round1']*2))
    if change=='model': value['digest']='other'
    if change=='runner': value['preparation_manifest_sha256']='stale'
    if change=='prior': value['prior_reviews']=[{'case':'fake'}]
    if change=='expired': value['expires_at']=(c.utc()-dt.timedelta(seconds=1)).isoformat()
    if change=='future': value['issued_at']=(c.utc()+dt.timedelta(seconds=10)).isoformat()
    if change=='proof_age':
        p=folder.parents[1]/'controller-native-preflight/e03-round1.json'; c.save(p,dict(c.load(p),recorded_at=(c.utc()-dt.timedelta(seconds=61)).isoformat()));value['native_preflight_sha256']=c.sha(p)
    if change=='sibling': (folder.parent/'e02').mkdir(parents=True)
    if change=='approval': value['approval_sha256']='old'
    if change=='review': (folder.parents[1]/'review-preparation-3/review.md').write_text('changed')
    c.save(auth,value)
    if change=='authority_path': copied=auth.with_name('copy.json');copied.write_bytes(auth.read_bytes());auth=copied
    if change=='ledger_path': copied=ledger.with_name('copy.json');copied.write_bytes(ledger.read_bytes());ledger=copied
    with pytest.raises(ValueError): c.validate_authority('e03-round1',folder,auth,ledger)

def test_optimized(release,monkeypatch):
    monkeypatch.setattr(c.sys,'flags',type('Flags',(),{'optimize':1})())
    with pytest.raises(ValueError): c.validate_authority('e03-round1',*release)

def test_traversal():
    with pytest.raises(ValueError): c.no_reparse(Path.cwd()/'x/../escape')
def test_reparse(tmp_path):
    target=tmp_path/'target';target.mkdir();link=tmp_path/'link';link.symlink_to(target,target_is_directory=True)
    with pytest.raises(ValueError): c.no_reparse(link/'new')
@pytest.mark.parametrize('length',[0,2,7,8])
def test_cap(release,length):
    folder,auth,ledger=release; sequence=list(c.ORDER[:length]);sequence+=['e01-round4'] if length==8 else []
    c.save(ledger,{'schema':2,'released_case':'e03-round1','consumed':sequence});c.save(auth,dict(c.load(auth),ledger_sha256=c.sha(ledger)))
    with pytest.raises(ValueError): c.validate_authority('e03-round1',folder,auth,ledger)

def test_model_manifest_mismatch():
    with pytest.raises(ValueError): c.old.metadata_valid({'ok':True,'model':c.MODEL,'agent':'native_react'},{'version':'0.32.15'},{'models':[]},b'wrong')
def test_source_drift(tmp_path,monkeypatch):
    monkeypatch.setattr(c.old,'R',tmp_path);monkeypatch.setattr(c.old,'ROOT',tmp_path)
    (tmp_path/'source.py').write_text('changed');c.save(tmp_path/'source21-before.json',{'source.py':'old'})
    with pytest.raises(ValueError): c.source_check()
def test_timeout_preserves(tmp_path):
    (tmp_path/'cli.stdout').write_text('partial')
    class CLI:
        def wait(self,timeout): raise subprocess.TimeoutExpired('owned',timeout)
    with pytest.raises(subprocess.TimeoutExpired): c.old.wait_cli(CLI(),tmp_path)
    assert (tmp_path/'cli.stdout').read_text()=='partial' and c.load(tmp_path/'timeout.json')['retry'] is False

@pytest.mark.parametrize('task',['C:/outside','../outside','not-uuid','A'*36,'00000000-0000-0000-0000-000000000000'])
def test_task_escape_refused_without_read(tmp_path,task,monkeypatch):
    monkeypatch.setattr(Path,'read_bytes',lambda self:pytest.fail('No read permitted'))
    with pytest.raises(ValueError): c.artifact_path(tmp_path,task,'C:/outside/data')
def test_absolute_outside_no_read(tmp_path,monkeypatch):
    monkeypatch.setattr(Path,'read_bytes',lambda self:pytest.fail('No outside read'))
    monkeypatch.setattr(c,'no_reparse',lambda path:pytest.fail('Outside path must not be inspected'))
    with pytest.raises(ValueError): c.artifact_path(tmp_path,'a64039d2-cbd0-4f5a-a679-ae3eb7fa6817',str(tmp_path.parent/'outside'))

def data(tmp_path):
    case='e03-round1';task='a64039d2-cbd0-4f5a-a679-ae3eb7fa6817';writeid='b64039d2-cbd0-4f5a-a679-ae3eb7fa6817';editid='c64039d2-cbd0-4f5a-a679-ae3eb7fa6817'
    target={'hwnd':1,'control_hwnd':2,'pid':123,'process_created_filetime':456,'title':'fixture','class':'Edit'}
    before=dict(target,text='prefix材料suffix',start_utf16=6,end_utf16=8,editable=True,password=False);other=dict(before,hwnd=3,control_hwnd=4,text='other')
    after=dict(before,text='prefix要点suffix',start_utf16=8,end_utf16=8)
    ids={'request_id':case,'session_id':case,'task_id':task};path=str(tmp_path/'outputs'/task/'rewrite.md');content='要点';digest=hashlib.sha256(content.encode()).hexdigest()
    edit=dict(ids,call_id=editid,before=before,after=after,expected_text=after['text'],replacement_text=content,companion_paths=[path])
    write=dict(ids,call_id=writeid,tool_name='ultima_work_file_write',success=True,path=path,content=content)
    replacement=dict(ids,call_id=editid,tool_name='ultima_work_replace_selection',success=True,result=dict(edit))
    send=dict(ids,call_id=editid,tool_name='ultima_work_replace_selection',event='mutation.send',may_have_committed=True)
    artifact=dict(ids,call_id=writeid,path=path,verified=True,sha256=digest,external_sha256=digest,text=content)
    capture={'capture_id':'d64039d2-cbd0-4f5a-a679-ae3eb7fa6817','available':True,'source':'win32.standard_edit','captured_at':c.utc().isoformat(),'window':target,'text_sha256':hashlib.sha256(before['text'].encode()).hexdigest(),'selection':{'start_utf16':6,'end_utf16':8,'text':'材料'}}
    trace=[]
    for name,content,params in [('ultima_work_file_write',content,{'path':path}),('ultima_work_replace_selection',content,{})]:
        trace.extend([{'type':'tool_call_start','data':{'tool':name,'arguments':dict(params,content=content)}},{'type':'tool_call_end','data':{'tool':name,'success':True}}])
    c.save(tmp_path/'dispatch-baseline-timing.json',{'ended_at':(c.utc()-dt.timedelta(seconds=1)).isoformat()});c.save(tmp_path/'final-windows-timing.json',{'ended_at':(c.utc()+dt.timedelta(seconds=1)).isoformat()})
    result=dict(ids,status='succeeded',work_context=capture,context_results=[edit],tool_results=[write,replacement,send,{'tool_name':'ultima_work_file_write','success':True},{'tool_name':'ultima_work_replace_selection','success':True}],trace=trace)
    return result,[artifact],[before,other],[after,other],[{'path':path,'sha256':digest,'bytes_hex':content.encode().hex()}]
def test_external_validator(tmp_path):
    result,artifacts,baseline,windows,inventory=data(tmp_path)
    assert c.mechanical('e03-round1',tmp_path,result,artifacts,baseline,windows,inventory)['facts']=='PENDING_ROOT_INDEPENDENT_REVIEW'
@pytest.mark.parametrize('drift',['outside','other','companion','identity','hash','product','partial-selection','missing-write','wrong-call','wrong-run','caret','unrelated','capture','missing-send','service-after'])
def test_external_refusals(tmp_path,drift):
    result,artifacts,baseline,windows,inventory=copy.deepcopy(data(tmp_path))
    baseline=copy.deepcopy(baseline); windows=copy.deepcopy(windows)
    if drift=='outside': windows[0]['text']='changed prefix'
    if drift=='other': windows[1]['text']='changed'
    if drift=='companion': artifacts[0]['text']='different'
    if drift=='identity': windows[0]['pid']=999
    if drift=='hash': artifacts[0]['external_sha256']='changed'
    if drift=='product': result['status']='failed'
    if drift=='partial-selection': result['context_results'][0]['before']['start_utf16']=7
    if drift=='missing-write': result['tool_results'].pop(0)
    if drift=='wrong-call': artifacts[0]['call_id']='e64039d2-cbd0-4f5a-a679-ae3eb7fa6817'
    if drift=='wrong-run': result['tool_results'][0]['request_id']='old'
    if drift=='caret': windows[0]['end_utf16']=9
    if drift=='unrelated': inventory.append({'path':'unrelated'})
    if drift=='capture': result['work_context']['selection']['start_utf16']=7
    if drift=='missing-send': result['tool_results'].pop(2)
    if drift=='service-after': result['context_results'][0]['after']['text']='service-only'
    with pytest.raises(ValueError): c.mechanical('e03-round1',tmp_path,result,artifacts,baseline,windows,inventory)
@pytest.mark.parametrize('mode',['timeout','nonzero','invalid-json','missing-inference','readback','cleanup','boundary','dispatch-expiry','final-files','final-window','final-unknown','unchanged'])
def test_failure_ordering_and_overall(tmp_path,monkeypatch,mode):
    sys.path.insert(0,str(c.ROOT))
    events=[]; folder=tmp_path/'case';counter={'auth':0,'boundary':0}
    def authorize(*args,**kwargs):
        counter['auth']+=1
        if mode=='dispatch-expiry' and counter['auth']>=4: raise ValueError('expired before CLI')
        return {},{},{}
    monkeypatch.setattr(c,'validate_authority',authorize)
    def boundary():
        counter['boundary']+=1
        if mode=='boundary' and counter['boundary']>1: raise ValueError('boundary failed')
        return {}
    monkeypatch.setattr(c,'source_check',boundary);monkeypatch.setattr(c,'protected',lambda:[])
    monkeypatch.setattr(c,'native_proof',lambda proof:events.append('native') or {})
    monkeypatch.setattr(c,'listener_owner',lambda port:[123])
    monkeypatch.setattr(c,'assert_listener',lambda *a:events.append('listener') or {})
    monkeypatch.setattr(c,'get_json',lambda url:{'ok':True,'model':c.MODEL,'agent':'native_react'})
    monkeypatch.setattr(c,'read_artifacts',lambda *a:[])
    monkeypatch.setattr(c,'output_inventory',lambda *a:[])
    def validate(*args):
        if mode=='readback': raise ValueError('failed external readback')
        return {'mechanical':'PASS'}
    monkeypatch.setattr(c,'mechanical',validate)
    class Proc:
        returncode=1 if mode=='nonzero' else 0
    class Owned:
        known={5:{'role':'fixture','identity':{'created_filetime':9}}}
        def launch(self,argv,role):
            events.append(role)
            if role=='fixture': c.save(folder/'fixture.json',{'pid':5,'targets':[{'pid':5,'process_created_filetime':9}]})
            if role=='cli':
                result={'status':'succeeded','trace':[] if mode=='missing-inference' else [{'type':'inference_end','data':{'model':c.MODEL}}]}
                (folder/'cli.stdout').write_text('INVALID' if mode=='invalid-json' else json.dumps(result))
            return Proc()
        def discover(self): pass
        def flush(self): pass
        def cleanup(self,port): events.append('cleanup');return {'status':'FAIL' if mode=='cleanup' else 'PASS'}
    class Context:
        def __init__(self,case,folder,env): self.owned=Owned();self.port=None;self.fixture_ready=False;self.cli_count=0;self.result=None
        def observe(self,label): return [{'text':'fixed'},{}]
        def command(self): pass
        def effects(self):
            events.append('effects');value={'windows':[{'text':'fixed'},{}],'outputs':[]}
            if mode=='final-files':value['outputs']=[{'path':'changed','bytes_hex':'61','sha256':hashlib.sha256(b'a').hexdigest()}]
            if mode=='final-window':value['windows'][0]['text']='later conflict'
            if mode=='final-unknown':value['windows_unknown']='readback failed'
            return value
    monkeypatch.setattr(c,'Case',Context)
    import src.brain.tests.work_context_acceptance as h
    monkeypatch.setitem(h.CASES['e03'],'text','fixed')
    def wait(cli,folder):
        if mode=='timeout': raise subprocess.TimeoutExpired('owned',315)
        return cli.returncode
    monkeypatch.setattr(c.old,'wait_cli',wait)
    result=c.execute('e03-round1',folder,tmp_path/'auth',tmp_path/'ledger')
    assert result['overall']==('PASS' if mode=='unchanged' else 'FAIL')
    assert events[0]=='native' and events.index('native')<events.index('fixture')
    assert events.index('effects')<events.index('cleanup')
    if mode=='dispatch-expiry': assert 'cli' not in events
    if mode in ('cleanup','boundary','readback'):
        assert c.load(folder/'product-result.json')['status']=='succeeded'

def test_effects_invalid_json_keeps_outputs_and_windows(tmp_path):
    context=object.__new__(c.Case);context.folder=tmp_path;context.cli_count=1;context.fixture_ready=True;context.result=None
    context.owned=type('Owned',(),{'flush':lambda self:None})()
    context.observe=lambda label:[{'text':'actual still-live target'}]
    (tmp_path/'cli.stdout').write_text('invalid JSON partial')
    out=tmp_path/'outputs';out.mkdir();(out/'delivered.md').write_text('actual committed bytes')
    effects=context.effects()
    assert effects['windows'][0]['text']=='actual still-live target'
    assert bytes.fromhex(effects['outputs'][0]['bytes_hex'])==b'actual committed bytes'
    assert 'product_unknown' in effects and effects['native_start_count'] is None

@pytest.mark.parametrize('bad',['later-than-exit','earlier-than-parent','exe','argv','parent'])
def test_stale_parent_not_termination_authority(monkeypatch,bad):
    monkeypatch.setattr(c,'argv_parse',lambda text:text.split())
    root={'pid':4,'created_filetime':100};key={'pid':5,'created_filetime':110,'exe':'python.exe'}
    row={'ParentProcessId':4,'CommandLine':'python.exe --case-root OWNED'}
    if bad=='later-than-exit': key['created_filetime']=130
    if bad=='earlier-than-parent': key['created_filetime']=90
    if bad=='exe': key['exe']='foreign.exe'
    if bad=='argv': row['CommandLine']='python.exe --case-root FOREIGN'
    if bad=='parent': row['ParentProcessId']=99
    assert not c.candidate_valid(key,row,root,['--case-root','OWNED'],{'python.exe'},120)

def test_collision_listener_refused(tmp_path,monkeypatch):
    owned=type('Owned',(),{'discover':lambda self:None,'known':{},'folder':tmp_path})()
    monkeypatch.setattr(c,'listener_owner',lambda port:[999])
    with pytest.raises(ValueError,match='owned server'): c.assert_listener(owned,12345,[])

def test_preflight_failure_no_fixture_or_case(tmp_path,monkeypatch):
    events=[]
    monkeypatch.setattr(c,'validate_authority',lambda *a,**k:({}, {}, {}));monkeypatch.setattr(c,'source_check',lambda:{});monkeypatch.setattr(c,'protected',lambda:[])
    def fail(proof): events.append('native');raise ValueError('native mismatch')
    monkeypatch.setattr(c,'native_proof',fail)
    with pytest.raises(ValueError): c.execute('e03-negative',tmp_path/'case',tmp_path/'auth',tmp_path/'ledger')
    assert events==['native'] and not (tmp_path/'case').exists()

def test_unseen_child_discovered_after_launcher_exit(tmp_path,monkeypatch):
    key={'pid':5,'created_filetime':110,'exe':'python.exe'};root={'pid':4,'created_filetime':100,'exe':'python.exe'}
    row={'ProcessId':5,'ParentProcessId':4,'CommandLine':'python.exe --case-root OWNED'}
    monkeypatch.setattr(c,'process_snapshot',lambda:{5:row});monkeypatch.setattr(c,'process_times',lambda proc:(100,120));monkeypatch.setattr(c,'identity',lambda pid:key);monkeypatch.setattr(c,'argv_parse',lambda x:x.split())
    owned=object.__new__(c.Owned);owned.folder=tmp_path;owned.allowed_exes={'python.exe'};owned.forbidden=set();owned.known={};owned.errors=[];owned.auxiliary={};owned.stale=[]
    owned.launchers=[{'proc':type('Exited',(),{'pid':4})(),'identity':root,'argv':['--case-root','OWNED'],'role':'server'}]
    owned.discover()
    assert owned.known[5]['identity']==key and not owned.errors

@pytest.mark.parametrize('bad',['focus','range','mutation','refusal','files'])
def test_negative_requires_actual_change_refusal_and_no_mutation(tmp_path,monkeypatch,bad):
    sys.path.insert(0,str(c.ROOT));import src.brain.work_context as wc
    targets=[{'hwnd':1,'control_hwnd':2},{'hwnd':3,'control_hwnd':4}];c.save(tmp_path/'fixture.json',{'targets':targets});c.save(tmp_path/'policy.json',{})
    state={'index':0,'select':True};base=[{'text':'a','start_utf16':0,'end_utf16':1},{'text':'other','start_utf16':0,'end_utf16':1}]
    context=object.__new__(c.Case);context.folder=tmp_path
    context.command=lambda index=0,select=True:state.update(index=index,select=select)
    context.observe=lambda label:[dict(base[0],end_utf16=1 if state['select'] or bad=='range' else 0),base[1]]
    class Native:
        def focused(self):
            target=targets[0 if bad=='focus' else state['index']];return target['hwnd'],target['control_hwnd']
    class Provider:
        def __init__(self,policy): pass
        def capture_work_context(self): return {'available':True,'selection':{'start_utf16':0,'end_utf16':1}}
        def release(self,capture): pass
        def replace_selection(self,capture,text,before_send):
            if bad=='mutation': before_send()
            if bad!='refusal': raise ValueError('stale')
    monkeypatch.setattr(wc,'WorkContextProvider',Provider);monkeypatch.setattr(wc,'Win32Edit',Native)
    count={'n':0}
    def inventory(folder):
        count['n']+=1;return [] if bad!='files' or count['n']==1 else [{'path':'changed'}]
    monkeypatch.setattr(c,'output_inventory',inventory)
    with pytest.raises(ValueError): context.negative(base)

def test_stale_product_success_not_predecessor_acceptance(release):
    folder,auth,ledger=release;root=folder.parents[1]
    previous=folder;previous.mkdir(parents=True);c.save(previous/'terminal.json',{'case':'e03-round1','overall':'FAIL','mechanical':'PASS','cleanup':'FAIL','boundaries':'PASS','product_status':'succeeded'})
    newfolder=folder.with_name('e03-round2');newauth=auth.with_name('e03-round2.json');newproof=root/'controller-native-preflight/e03-round2.json';newproof.write_bytes((newproof.with_name('e03-round1.json')).read_bytes())
    c.save(ledger,{'schema':2,'released_case':'e03-round2','consumed':['e03-round1','e03-round2']})
    value=dict(c.load(auth),case='e03-round2',folder=str(newfolder),ledger_sha256=c.sha(ledger),native_preflight_sha256=c.sha(newproof),prior_reviews=[{'case':'e03-round1','terminal_sha256':c.sha(previous/'terminal.json')}]);c.save(newauth,value)
    with pytest.raises(ValueError,match='overall'):c.validate_authority('e03-round2',newfolder,newauth,ledger)
@pytest.mark.parametrize('drift',['sdk-start','sdk-end','sdk-result','stale-time','send-intent'])
def test_completed_sdk_and_capture_proofs(tmp_path,drift):
    result,artifacts,baseline,windows,inventory=data(tmp_path)
    if drift=='sdk-start': result['trace'].pop(0)
    if drift=='sdk-end': result['trace'][1]['data']['success']=False
    if drift=='sdk-result': result['tool_results']=[x for x in result['tool_results'] if 'call_id' in x]
    if drift=='stale-time': result['work_context']['captured_at']=(c.utc()-dt.timedelta(days=1)).isoformat()
    if drift=='send-intent': result['tool_results'][2]['may_have_committed']=False
    with pytest.raises(ValueError):c.mechanical('e03-round1',tmp_path,result,artifacts,baseline,windows,inventory)

@pytest.mark.parametrize('change',['hash','bytes','missing','additional','windows','caret','identity','selection','unknown-output','unknown-window','negative-file'])
def test_all_final_effect_conflicts_fail(change):
    raw=b'actual';record={'path':'owned/summary.md','sha256':hashlib.sha256(raw).hexdigest(),'bytes_hex':raw.hex()}
    window={'text':'rewrite','hwnd':1,'pid':2,'start_utf16':7,'end_utf16':7}
    expected={'outputs':[record],'windows':[window],'cli_count':1};effects=copy.deepcopy(expected)
    if change=='hash': effects['outputs'][0]['sha256']=hashlib.sha256(b'changed').hexdigest()
    if change=='bytes':
        effects['outputs'][0]['bytes_hex']=b'changed'.hex();effects['outputs'][0]['sha256']=hashlib.sha256(b'changed').hexdigest()
    if change=='missing': effects['outputs']=[]
    if change=='additional': effects['outputs'].append(dict(record,path='owned/extra'))
    if change=='windows': effects['windows'][0]['text']='later changed'
    if change=='caret': effects['windows'][0]['end_utf16']=8
    if change=='identity': effects['windows'][0]['pid']=3
    if change=='selection': effects['windows'][0]['start_utf16']=1
    if change=='unknown-output': effects['outputs_unknown']='cannot read'
    if change=='unknown-window': effects['windows_unknown']='cannot observe'
    if change=='negative-file': expected={'outputs':[],'windows':[window],'cli_count':0}
    with pytest.raises(ValueError):c.reconcile_effects(expected,effects)

def test_unchanged_final_effects_pass():
    record={'path':'owned/file','sha256':hashlib.sha256(b'a').hexdigest(),'bytes_hex':'61'}
    expected={'outputs':[record],'windows':[{'text':'actual','start_utf16':6,'end_utf16':6}],'cli_count':1}
    assert c.reconcile_effects(expected,copy.deepcopy(expected))=='PASS'
    assert c.reconcile_effects({'outputs':[],'windows':[{'text':'unchanged'}],'cli_count':0},{'outputs':[],'windows':[{'text':'unchanged'}],'product_unknown':'No CLI expected'})=='PASS'

def test_mechanical_later_inventory_bytes_conflict(tmp_path):
    result,artifacts,baseline,windows,inventory=data(tmp_path)
    inventory[0]['bytes_hex']=b'later bytes'.hex();inventory[0]['sha256']=hashlib.sha256(b'later bytes').hexdigest()
    with pytest.raises(ValueError,match='bytes/hash'):c.mechanical('e03-round1',tmp_path,result,artifacts,baseline,windows,inventory)

def test_nested_unknown_detected_without_termination_authority(tmp_path,monkeypatch):
    keys={pid:{'pid':pid,'created_filetime':100+pid,'exe':'python.exe'} for pid in (4,5,6,7)}
    rows={5:{'ProcessId':5,'ParentProcessId':4,'CommandLine':'python.exe --case-root OWNED'},6:{'ProcessId':6,'ParentProcessId':5,'CommandLine':'python.exe FOREIGN'},7:{'ProcessId':7,'ParentProcessId':6,'CommandLine':'python.exe FOREIGN'}}
    monkeypatch.setattr(c,'process_snapshot',lambda:rows);monkeypatch.setattr(c,'process_times',lambda p:(104,0));monkeypatch.setattr(c,'identity',lambda pid:keys[pid]);monkeypatch.setattr(c,'argv_parse',lambda x:x.split())
    owned=object.__new__(c.Owned);owned.folder=tmp_path;owned.allowed_exes={'python.exe'};owned.forbidden=set();owned.known={4:{'identity':keys[4],'role':'server','argv':['--case-root','OWNED']}};owned.errors=[];owned.auxiliary={};owned.stale=[]
    proc=type('Proc',(),{'pid':4,'wait':lambda self,timeout:None})()
    owned.launchers=[{'proc':proc,'identity':keys[4],'argv':['--case-root','OWNED'],'role':'server'}];owned.logs=[]
    with pytest.raises(ValueError,match='ambiguity'):owned.discover()
    assert set(owned.known)=={4,5}
    assert {x['identity']['pid'] for x in owned.errors if x['discovery']=='unknown-nested-descendant'}=={6,7}
    stopped=[]
    def stop(key): stopped.append(key['pid']);rows.pop(key['pid'],None)
    monkeypatch.setattr(c,'terminate_owned',stop)
    cleanup=owned.cleanup()
    assert cleanup['status']=='FAIL' and not ({6,7}&set(stopped))

def test_lossless_transport_strict_decode(monkeypatch):
    query='中文精确参数\n第二行事实'
    encoded=c.base64.b64encode(query.encode('utf-16-le')).decode('ascii')
    raw=json.dumps({'ProcessId':5,'ParentProcessId':4,'CommandLineBase64':encoded}).encode('ascii')
    monkeypatch.setattr(c.subprocess,'check_output',lambda *a,**k:raw)
    assert c.process_snapshot()[5]['CommandLine']==query

def test_later_product_observation_never_overwrites_original(tmp_path):
    context=object.__new__(c.Case);context.folder=tmp_path;context.cli_count=1;context.fixture_ready=False;context.result=None
    context.owned=type('Owned',(),{'flush':lambda self:None})()
    original={'status':'succeeded','content':'original product bytes'};later={'status':'failed','content':'later observation'}
    c.save(tmp_path/'product-result.json',original);(tmp_path/'cli.stdout').write_text(json.dumps(later))
    effects=context.effects()
    assert c.load(tmp_path/'product-result.json')==original and c.load(tmp_path/'pre-cleanup-product-observed.json')==later
    assert effects['product_result_conflict'] is True
    with pytest.raises(ValueError):c.reconcile_effects({'outputs':[],'windows':None,'cli_count':1},effects)

def test_e01_has_no_required_window_but_requires_files():
    expected={'outputs':[],'windows':None,'cli_count':1}
    assert c.reconcile_effects(expected,{'outputs':[],'windows_unknown':'No approved fixture was created'})=='PASS'
    with pytest.raises(ValueError):c.reconcile_effects(expected,{'outputs_unknown':'Cannot read required outputs','windows_unknown':'No approved fixture'})

@pytest.mark.parametrize('failure',['missing-second','invalid-utf8'])
def test_first_external_observations_survive_readback_failure(tmp_path,failure):
    task='a64039d2-cbd0-4f5a-a679-ae3eb7fa6817';root=tmp_path/'outputs'/task;root.mkdir(parents=True)
    first=root/'rewrite.md';first.write_bytes(b'first actual bytes' if failure=='missing-second' else b'\xff')
    artifacts=[{'path':str(first)}]
    if failure=='missing-second':artifacts.append({'path':str(root/'missing.md')})
    with pytest.raises((UnicodeError,FileNotFoundError)):c.read_artifacts(tmp_path,{'task_id':task,'artifacts':artifacts})
    attempts=c.load(tmp_path/'external-readback-attempts.json')
    assert bytes.fromhex(attempts[0]['bytes_hex'])==first.read_bytes()
    assert 'error' in attempts[-1]
    assert first.read_bytes()==(b'first actual bytes' if failure=='missing-second' else b'\xff')
