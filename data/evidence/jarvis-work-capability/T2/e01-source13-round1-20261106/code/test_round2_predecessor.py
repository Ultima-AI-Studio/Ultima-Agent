import json

import pytest

from test_acceptance_entry import Backend, NOW, package, put


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def reseal(root, entry, authority):
    manifest = read(root/'manifest.json')
    for row in manifest['files']:
        row.update(bytes=(root/row['path']).stat().st_size, sha256=entry.sha(root/row['path']))
    put(root/'manifest.json', manifest)
    review = read(root/'release/independent-review.json')
    review['manifest_sha256'] = entry.sha(root/'manifest.json')
    put(root/'release/independent-review.json', review)
    authority.update(manifest_sha256=entry.sha(root/'manifest.json'),
                     review_sha256=entry.sha(root/'release/independent-review.json'))
    put(root/'release/authority.json', authority)


def rebind_prior(root, entry, authority):
    folder = root/'inputs/prior-round1'
    review = read(folder/'review.json')
    review['terminal_sha256'] = entry.sha(folder/'terminal.json')
    put(folder/'review.json', review)
    registration = read(folder/'registration.json')
    registration.update(terminal_sha256=entry.sha(folder/'terminal.json'),
                        result_review_sha256=entry.sha(folder/'review.json'))
    put(folder/'registration.json', registration)
    authority['prior_reviews'][0] = dict(case='e03-round1',candidate=entry.HEAD,
        terminal_sha256=entry.sha(folder/'terminal.json'),review_sha256=entry.sha(folder/'review.json'),
        registration_sha256=entry.sha(folder/'registration.json'))
    reseal(root,entry,authority)


def test_e01_admits_completed_e03_and_keeps_new_facts_pending(tmp_path,monkeypatch):
    entry,authority,proof = package(tmp_path,monkeypatch)
    assert entry.CASE == 'e01-round1' and entry.SCOPE == 'e01-round1-acceptance'
    backend = Backend(tmp_path,proof)
    result = entry.run_once(tmp_path,backend_factory=lambda root:backend)
    assert result['case']=='e01-round1' and result['work_cli_count']==1
    assert result['facts']=='PENDING_ROOT_INDEPENDENT_REVIEW' and result['acceptance_credit'] is False
    assert not (tmp_path/'actual/e03-round1').exists()
    assert (tmp_path/'actual/e01-round1/terminal.json').is_file()
    assert [row['case'] for row in authority['prior_reviews']] == [
        'e03-round1','e03-round2','e03-round3','e03-negative']


@pytest.mark.parametrize('file,field,value', [
    ('terminal.json','candidate','old-candidate'),
    ('terminal.json','case','e03-round2'),
    ('terminal.json','overall','FAIL'),
    ('terminal.json','mechanical','FAIL'),
    ('terminal.json','errors',[{'stage':'cleanup','error':'failed'}]),
    ('review.json','reviewer','root-self'),
    ('review.json','scope','e03-round1-acceptance-package'),
    ('review.json','candidate','old-candidate'),
    ('review.json','facts_verdict','FAIL'),
    ('review.json','final_claim_verdict','FAIL'),
    ('review.json','candidate_runtime_manifest_sha256','old-runtime'),
    ('registration.json','case_verdict','FAIL'),
    ('registration.json','acceptance_credit',False),
    ('registration.json','positive_passed',2),
    ('registration.json','same_candidate_terminals',2),
])
def test_ineligible_predecessor_rejected_even_when_new_package_is_resealed(tmp_path,monkeypatch,file,field,value):
    entry,authority,proof=package(tmp_path,monkeypatch)
    path=tmp_path/'inputs/prior-round1'/file;data=read(path);data[field]=value;put(path,data)
    rebind_prior(tmp_path,entry,authority)
    with pytest.raises(ValueError,match='[Pp]redecessor'):
        entry.verify_package(tmp_path)
    made=[]
    with pytest.raises(ValueError):entry.run_once(tmp_path,backend_factory=lambda root:made.append(root))
    assert made==[] and not (tmp_path/'actual').exists()


@pytest.mark.parametrize('file',['terminal.json','review.json','registration.json'])
def test_predecessor_dependency_cannot_be_omitted_from_new_seal(tmp_path,monkeypatch,file):
    entry,authority,proof=package(tmp_path,monkeypatch)
    path='inputs/prior-round1/'+file
    manifest=read(tmp_path/'manifest.json');manifest['files']=[r for r in manifest['files'] if r['path']!=path]
    put(tmp_path/'manifest.json',manifest)
    with pytest.raises(ValueError,match='[Rr]untime dependency'):
        entry.verify_package(tmp_path)


@pytest.mark.parametrize('field',['terminal_sha256','review_sha256','registration_sha256'])
def test_authority_requires_exact_predecessor_receipts(tmp_path,monkeypatch,field):
    entry,authority,proof=package(tmp_path,monkeypatch)
    authority['prior_reviews'][0][field]='0'*64;put(tmp_path/'release/authority.json',authority)
    made=[]
    with pytest.raises(ValueError):entry.run_once(tmp_path,backend_factory=lambda root:made.append(root))
    assert not made and not (tmp_path/'actual').exists()


def test_prior_round1_authority_does_not_allocate_round2(tmp_path,monkeypatch):
    entry,authority,proof=package(tmp_path,monkeypatch)
    authority.update(case='e03-round1',scope='e03-round1-acceptance',prior_reviews=[])
    put(tmp_path/'release/authority.json',authority)
    made=[]
    with pytest.raises(ValueError):entry.run_once(tmp_path,backend_factory=lambda root:made.append(root))
    assert not made and not (tmp_path/'actual').exists()
