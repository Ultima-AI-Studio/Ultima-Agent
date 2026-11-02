import copy, hashlib, json, subprocess, sys
from pathlib import Path
import pytest
import acceptance_adapter as a

@pytest.fixture
def release(tmp_path,monkeypatch):
    monkeypatch.setattr(a,'R',tmp_path)
    snapshot=tmp_path/'source21-before.json'; snapshot.write_text('{}')
    ledger={'consumed':['e03-round1'],'released_case':'e03-round1'}
    folder=tmp_path/'actual/e03-round1'
    authority={'schema':1,'issuer':'root','case':'e03-round1','runner_sha256':a.sha(a.__file__),'source21_sha256':a.sha(snapshot),'model':a.MODEL,'digest':a.DIGEST,'folder':str(folder),'ledger_sha256':hashlib.sha256(json.dumps(ledger,sort_keys=True).encode()).hexdigest(),'prior_reviews':[]}
    return folder,authority,ledger

def test_single_release(release):
    folder,auth,ledger=release
    assert a.validate_release('e03-round1',folder,auth,ledger)==folder

@pytest.mark.parametrize('case',['e02','e03','e03-round4','e01-round4','../e03-round1'])
def test_other_cases_refused(release,case):
    folder,auth,ledger=release
    with pytest.raises(ValueError): a.validate_release(case,folder,auth,ledger)

@pytest.mark.parametrize('change',['root','old','ledger','model','runner','prior'])
def test_fail_closed_release(release,change):
    folder,auth,ledger=release
    if change=='root': folder=folder.parent.parent/'escaped'
    if change=='old': folder.mkdir(parents=True)
    if change=='ledger': ledger['consumed']=['e03-round1','e03-round1']
    if change=='model': auth['digest']='different'
    if change=='runner': auth['runner_sha256']='different'
    if change=='prior': auth['prior_reviews']=[{'case':'e03-round1'}]
    with pytest.raises(ValueError): a.validate_release('e03-round1',folder,auth,ledger)

def test_optimized_forbidden(release,monkeypatch):
    folder,auth,ledger=release
    monkeypatch.setattr(a.sys,'flags',type('Flags',(),{'optimize':1})())
    with pytest.raises(ValueError,match='Optimized'): a.validate_release('e03-round1',folder,auth,ledger)

def test_traversal():
    with pytest.raises(ValueError): a.no_reparse(Path.cwd()/'x/../escape')

def test_model_proof():
    manifest=b'actual manifest'
    digest=hashlib.sha256(manifest).hexdigest()
    health={'ok':True,'model':a.MODEL,'agent':'native_react'}
    tags={'models':[{'name':a.MODEL+':latest','digest':digest,'details':{'parameter_size':'8.2B'}}]}
    from unittest.mock import patch
    with patch.object(a,'DIGEST',digest):
        a.metadata_valid(health,{'version':'0.32.15'},tags,manifest)
        with pytest.raises(ValueError): a.metadata_valid(health,{'version':'0.32.15'},tags,b'changed')
        with pytest.raises(ValueError): a.metadata_valid(dict(health,model='other'),{'version':'0.32.15'},tags,manifest)

def test_source_drift_before_any_work(tmp_path,monkeypatch):
    monkeypatch.setattr(a,'R',tmp_path); monkeypatch.setattr(a,'ROOT',tmp_path)
    (tmp_path/'source.py').write_text('changed')
    (tmp_path/'source21-before.json').write_text(json.dumps({'source.py':'old'}))
    with pytest.raises(ValueError,match='source21'): a.source_check()

def test_timeout_preserves_receipt_and_log(tmp_path):
    (tmp_path/'cli.stdout').write_text('partial live output')
    class CLI:
        def wait(self,timeout): raise subprocess.TimeoutExpired('owned CLI',timeout)
    with pytest.raises(subprocess.TimeoutExpired): a.wait_cli(CLI(),tmp_path)
    assert (tmp_path/'cli.stdout').read_text()=='partial live output'
    assert a.load(tmp_path/'timeout.json')['retry'] is False
    assert a.load(tmp_path/'timeout.json')['sdk_inference_count'] is None

def data():
    identity={'hwnd':1,'control_hwnd':2,'pid':123,'process_created_filetime':456,'title':'fixture','class':'Edit'}
    before=dict(identity,text='prefix材料suffix',start_utf16=6,end_utf16=8)
    other=dict(identity,hwnd=3,control_hwnd=4,text='other')
    edit={'before':before,'replacement_text':'要点'}
    result={'status':'succeeded','context_results':[edit]}
    artifacts=[{'path':'rewrite.md','verified':True,'sha256':'hash','text':'要点'}]
    windows=[dict(before,text='prefix要点suffix'),other]
    return result,artifacts,windows,[before,other]

def test_external_replacement_validator():
    result,artifacts,windows,baseline=data()
    check=a.external_validate('e03-round1',result,artifacts,windows,baseline)
    assert check['facts']=='PENDING_ROOT_INDEPENDENT_REVIEW'

@pytest.mark.parametrize('drift',['outside','other','companion','identity','hash','product'])
def test_external_readback_refuses(drift):
    result,artifacts,windows,baseline=data()
    windows=copy.deepcopy(windows)
    if drift=='outside': windows[0]['text']='WRONGprefix要点suffix'
    if drift=='other': windows[1]['text']='changed'
    if drift=='companion': artifacts[0]['text']='semantically similar but different'
    if drift=='identity': windows[0]['pid']=999
    if drift=='hash': artifacts[0]['verified']=False
    if drift=='product': result['status']='failed'
    with pytest.raises(ValueError): a.external_validate('e03-round1',result,artifacts,windows,baseline)

def test_reparse_refusal(tmp_path):
    target=tmp_path/'target'; target.mkdir()
    link=tmp_path/'link'
    link.symlink_to(target,target_is_directory=True)
    with pytest.raises(ValueError,match='Reparse'): a.no_reparse(link/'new')

@pytest.mark.parametrize('length',[0,2,7,8])
def test_no_skipping_or_overconsumption(release,length):
    folder,auth,ledger=release
    ledger['consumed']=list(a.ORDER[:length])
    if length==8: ledger['consumed'].append('e01-round4')
    auth['ledger_sha256']=hashlib.sha256(json.dumps(ledger,sort_keys=True).encode()).hexdigest()
    with pytest.raises(ValueError,match='ledger'): a.validate_release('e03-round1',folder,auth,ledger)
