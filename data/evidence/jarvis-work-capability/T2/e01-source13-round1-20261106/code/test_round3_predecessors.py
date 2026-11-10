import json

import pytest

from test_acceptance_entry import Backend, package, put
from test_round2_predecessor import read, reseal


def rebind_second(root, entry, authority, *, bind_inventory=True):
    folder=root/'inputs/prior-round2'
    review=read(folder/'review.json')
    review['terminal_sha256']=entry.sha(folder/'terminal.json')
    put(folder/'review.json',review)
    registration=read(folder/'registration.json')
    registration.update(terminal_sha256=entry.sha(folder/'terminal.json'),
                        result_review_sha256=entry.sha(folder/'review.json'))
    if bind_inventory:
        row=registration['same_candidate_terminal_bindings'][1]
        row.update(sha256=entry.sha(folder/'terminal.json'),review_sha256=entry.sha(folder/'review.json'))
    put(folder/'registration.json',registration)
    authority['prior_reviews'][1]=dict(case='e03-round2',candidate=entry.HEAD,
        terminal_sha256=entry.sha(folder/'terminal.json'),review_sha256=entry.sha(folder/'review.json'),
        registration_sha256=entry.sha(folder/'registration.json'))
    reseal(root,entry,authority)


def test_completed_e03_admits_only_e01_and_does_not_pregrant_facts(tmp_path,monkeypatch):
    entry,authority,proof=package(tmp_path,monkeypatch)
    backend=Backend(tmp_path,proof)
    result=entry.run_once(tmp_path,backend_factory=lambda root:backend)
    assert result['case']=='e01-round1' and result['work_cli_count']==1
    assert result['facts']=='PENDING_ROOT_INDEPENDENT_REVIEW' and result['acceptance_credit'] is False
    assert (tmp_path/'actual/e01-round1/terminal.json').is_file()
    assert not (tmp_path/'actual/e03-round2').exists()


@pytest.mark.parametrize('file,field,value',[
    ('terminal.json','candidate','old-candidate'),
    ('terminal.json','case','e03-round1'),
    ('terminal.json','overall','FAIL'),
    ('terminal.json','mechanical','FAIL'),
    ('terminal.json','errors',[{'stage':'cleanup','error':'failed'}]),
    ('terminal.json','cleanup',{'status':'FAIL'}),
    ('review.json','reviewer','root-self'),
    ('review.json','scope','e03-round2-acceptance-package'),
    ('review.json','facts_verdict','FAIL'),
    ('review.json','final_claim_verdict','FAIL'),
    ('review.json','candidate_runtime_manifest_sha256','old-runtime'),
    ('review.json','execution',{'model':'other-model','model_digest':'wrong','work_cli_count':1}),
    ('registration.json','case_verdict','FAIL'),
    ('registration.json','acceptance_credit',False),
    ('registration.json','positive_passed',1),
    ('registration.json','same_candidate_terminals',1),
    ('registration.json','cumulative_work_cli_count',1),
])
def test_second_predecessor_ineligible_even_with_new_hashes(tmp_path,monkeypatch,file,field,value):
    entry,authority,proof=package(tmp_path,monkeypatch)
    path=tmp_path/'inputs/prior-round2'/file;data=read(path);data[field]=value;put(path,data)
    rebind_second(tmp_path,entry,authority)
    with pytest.raises(ValueError,match='[Pp]redecessor'):
        entry.verify_package(tmp_path)
    made=[]
    with pytest.raises(ValueError): entry.run_once(tmp_path,backend_factory=lambda root:made.append(root) or Backend(root,proof))
    assert not made and not (tmp_path/'actual').exists()


@pytest.mark.parametrize('file',['terminal.json','review.json','registration.json'])
def test_second_predecessor_must_be_sealed(tmp_path,monkeypatch,file):
    entry,authority,proof=package(tmp_path,monkeypatch)
    manifest=read(tmp_path/'manifest.json')
    manifest['files']=[row for row in manifest['files'] if row['path']!='inputs/prior-round2/'+file]
    put(tmp_path/'manifest.json',manifest)
    with pytest.raises(ValueError,match='[Rr]untime dependency'): entry.verify_package(tmp_path)


@pytest.mark.parametrize('fault',[
    'duplicate-case','reversed-order','first-terminal-hash','second-review-hash',
    'prior-registration-hash','same-task','backwards-time','wrong-sequence','old-binding-candidate','review-prior-hash',
])
def test_second_registration_cannot_claim_unbound_two_round_chain(tmp_path,monkeypatch,fault):
    entry,authority,proof=package(tmp_path,monkeypatch)
    folder=tmp_path/'inputs/prior-round2';reg=read(folder/'registration.json')
    rows=reg['same_candidate_terminal_bindings']
    if fault=='duplicate-case': rows[1]['case']='e03-round1'
    elif fault=='reversed-order': rows.reverse()
    elif fault=='first-terminal-hash': rows[0]['sha256']='0'*64
    elif fault=='second-review-hash': rows[1]['review_sha256']='0'*64
    elif fault=='prior-registration-hash': reg['predecessor_registration_sha256']='0'*64
    elif fault=='same-task': rows[1]['task_id']=rows[0]['task_id']
    elif fault=='backwards-time': rows[1]['finished_at']='2026-11-05T09:59:00+00:00'
    elif fault=='wrong-sequence': reg['consecutive_positive_cases']=['e03-round1','e03-round1']
    elif fault=='old-binding-candidate': rows[1]['candidate']='old-candidate'
    elif fault=='review-prior-hash':
        review=read(folder/'review.json');review['authority_and_admission']['prior_round1']['review_sha256']='0'*64
        put(folder/'review.json',review)
    put(folder/'registration.json',reg)
    rebind_second(tmp_path,entry,authority,bind_inventory=(fault=='review-prior-hash'))
    with pytest.raises(ValueError,match='[Pp]redecessor'): entry.verify_package(tmp_path)
    made=[]
    with pytest.raises(ValueError): entry.run_once(tmp_path,backend_factory=lambda root:made.append(root) or Backend(root,proof))
    assert not made and not (tmp_path/'actual').exists()


@pytest.mark.parametrize('fault',['terminal_sha256','review_sha256','registration_sha256','missing','reversed','duplicate','old-scope'])
def test_negative_authority_requires_exact_ordered_bindings(tmp_path,monkeypatch,fault):
    entry,authority,proof=package(tmp_path,monkeypatch)
    if fault=='missing': authority['prior_reviews'].pop()
    elif fault=='reversed': authority['prior_reviews'].reverse()
    elif fault=='duplicate': authority['prior_reviews'][1]=dict(authority['prior_reviews'][0])
    elif fault=='old-scope': authority.update(case='e03-round2',scope='e03-round2-acceptance')
    else: authority['prior_reviews'][1][fault]='0'*64
    put(tmp_path/'release/authority.json',authority)
    made=[]
    with pytest.raises(ValueError): entry.run_once(tmp_path,backend_factory=lambda root:made.append(root) or Backend(root,proof))
    assert not made and not (tmp_path/'actual').exists()
