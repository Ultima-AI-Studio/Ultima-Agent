import json

import pytest

from test_acceptance_entry import Backend, package, put
from test_round2_predecessor import reseal


@pytest.mark.parametrize('value',[1,True,2])
def test_negative_authority_rejects_any_nonzero_or_boolean_cli_allocation(tmp_path,monkeypatch,value):
    entry,authority,proof=package(tmp_path,monkeypatch)
    authority['product_cli_cap']=value;put(tmp_path/'release/authority.json',authority)
    made=[]
    with pytest.raises(ValueError):entry.run_once(tmp_path,backend_factory=lambda root:made.append(root))
    assert not made and not (tmp_path/'actual').exists()


@pytest.mark.parametrize('field',['product_cli_cap','model_requests','audio_actions'])
def test_package_cannot_allocate_calls_for_negative(tmp_path,monkeypatch,field):
    entry,authority,proof=package(tmp_path,monkeypatch)
    path=tmp_path/'manifest.json';manifest=json.loads(path.read_text());manifest[field]=1;put(path,manifest)
    reseal(tmp_path,entry,authority)
    with pytest.raises(ValueError):entry.verify_package(tmp_path)


@pytest.mark.parametrize('name',[
    'prior-round3/terminal.json','prior-round3/review.json','prior-round3/registration.json',
    'runtime-reconciliation.json','runtime-user-approval.json','runtime-manual-confirmation.json',
    'protected-baseline-before-recovery.json',
])
def test_negative_dependencies_must_be_in_seal(tmp_path,monkeypatch,name):
    entry,authority,proof=package(tmp_path,monkeypatch)
    path=tmp_path/'manifest.json';manifest=json.loads(path.read_text())
    manifest['files']=[r for r in manifest['files'] if r['path']!='inputs/'+name];put(path,manifest)
    with pytest.raises(ValueError,match='Runtime dependency'):entry.verify_package(tmp_path)


def test_nonzero_cli_terminal_is_fail_even_with_mechanical_flag_and_receipts(tmp_path,monkeypatch):
    entry,authority,proof=package(tmp_path,monkeypatch);backend=Backend(tmp_path,proof)
    original=backend.product
    def unexpected_cli(revalidate,admit):
        result=original(revalidate,admit);backend.cli_count=1
        put(backend.folder/'product-result.json',{'test_only':True})
        return result
    backend.product=unexpected_cli
    result=entry.run_once(tmp_path,backend_factory=lambda root:backend)
    assert result['overall']=='FAIL' and any(x['stage']=='scope' for x in result['errors'])
    assert 'close' in backend.calls
