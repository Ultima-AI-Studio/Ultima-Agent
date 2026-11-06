import datetime as dt
import hashlib
import importlib
import json
import shutil
from pathlib import Path

import pytest


NOW = dt.datetime(2026, 11, 6, 12, tzinfo=dt.timezone.utc)


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


def prior_material(tmp_path, entry):
    # Real historical receipts remain immutable; mutations affect this test's copy.
    shutil.copytree(Path(__file__).parent.parent/'inputs', tmp_path/'inputs', dirs_exist_ok=True)
    paths={p.relative_to(tmp_path).as_posix() for p in (tmp_path/'inputs').rglob('*') if p.is_file()}
    bindings=[dict(case='e03-round'+str(n), candidate=entry.HEAD,
                   **{key:entry.sha(tmp_path/'inputs'/('prior-round'+str(n))/name)
                      for key,name in [('terminal_sha256','terminal.json'),('review_sha256','review.json'),
                                       ('registration_sha256','registration.json')]}) for n in (1,2,3)]
    bindings.append(dict(case='e03-negative', candidate=entry.HEAD,
        **{key:entry.sha(tmp_path/'inputs/prior-negative'/name)
           for key,name in [('terminal_sha256','terminal.json'),('review_sha256','review.json'),
                            ('registration_sha256','registration.json')]}))
    bindings.append(dict(case='e01-round1', candidate=entry.HEAD,
        **{key:entry.sha(tmp_path/'inputs/prior-e01-round1'/name)
           for key,name in [('terminal_sha256','terminal.json'),('review_sha256','review.json'),
                            ('registration_sha256','registration.json')]}))
    bindings.append(dict(case='e01-round2', candidate=entry.HEAD,
        **{key:entry.sha(tmp_path/'inputs/prior-e01-round2'/name)
           for key,name in [('terminal_sha256','terminal.json'),('review_sha256','review.json'),
                            ('registration_sha256','registration.json')]}))
    return paths, bindings


def package(tmp_path, monkeypatch):
    entry = importlib.import_module('acceptance_entry')
    monkeypatch.setattr(entry, 'utcnow', lambda: NOW)
    for name in entry.RUNTIME_FILES:
        path=tmp_path/name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# sealed test dependency\n', encoding='utf-8')
    prior_paths, prior_reviews = prior_material(tmp_path, entry)
    baseline=json.loads((tmp_path/'inputs/protected-baseline.json').read_text(encoding='utf-8'))
    rows=[{key:row[key] for key in entry.PROTECTED_FIELDS}
          for row in baseline['protected5']+baseline['protected_listener_pair']]
    manifest=dict(schema=1, scope=entry.SCOPE, case=entry.CASE, package_root=str(tmp_path),
                  candidate=entry.HEAD, candidate_manifest_sha256=entry.CANDIDATE_MANIFEST,
                  python_executable=str(entry.PYTHON), model=entry.MODEL, digest=entry.DIGEST,
                  case_cap=1, product_cli_cap=1, audio_actions=0, retry_authorized=False,
                  proof_max_age_seconds=60, admission_max_seconds=120, fixture_required=False,
                  product_timeouts={'CLI':300,'SDK':1800,'controller_wait':315},
                  files=[dict(path=name, bytes=(tmp_path/name).stat().st_size,
                              sha256=entry.sha(tmp_path/name)) for name in sorted(entry.RUNTIME_FILES | prior_paths)])
    put(tmp_path/'manifest.json', manifest)
    review=dict(reviewer='root-independent', verdict='PASS', scope=entry.SCOPE+'-package',
                manifest_sha256=entry.sha(tmp_path/'manifest.json'), candidate=entry.HEAD)
    put(tmp_path/'release/independent-review.json', review)
    proof=dict(schema=1, scope=entry.SCOPE, recorded_at=NOW.isoformat(),
               source=dict(candidate=entry.HEAD, candidate_manifest_sha256=entry.CANDIDATE_MANIFEST,
                           model_digest=entry.DIGEST, code_gate='PASS'),
               model=dict(model=entry.MODEL, digest=entry.DIGEST, version={'version':'0.32.15'},
                          tags_sha256='b'*64, manifest_sha256=entry.DIGEST),
               protected_processes=rows, listener_pid=rows[0]['pid'])
    put(tmp_path/'release/preflight/test.json', proof)
    authority=dict(schema=1, issuer='root', scope=entry.SCOPE, case=entry.CASE,
                   candidate=entry.HEAD, candidate_manifest_sha256=entry.CANDIDATE_MANIFEST,
                   model=entry.MODEL, digest=entry.DIGEST, manifest_sha256=entry.sha(tmp_path/'manifest.json'),
                   review_sha256=entry.sha(tmp_path/'release/independent-review.json'),
                   proof_path='release/preflight/test.json', proof_sha256=entry.sha(tmp_path/'release/preflight/test.json'),
                   case_cap=1, product_cli_cap=1, audio_actions=0, retry_authorized=False,
                   acceptance_credit=False, prior_reviews=prior_reviews, user_authorization='Explicit test-only authority',
                   issued_at=NOW.isoformat(), expires_at=(NOW+dt.timedelta(seconds=120)).isoformat())
    put(tmp_path/'release/authority.json', authority)
    return entry, authority, proof


@pytest.mark.parametrize('age,allowed', [(0,True),(60,True),(60.000001,False),(-0.000001,False)])
def test_original_sixty_second_proof_freshness_boundary(tmp_path, monkeypatch, age, allowed):
    entry, authority, proof=package(tmp_path,monkeypatch)
    proof['recorded_at']=(NOW-dt.timedelta(seconds=age)).isoformat()
    put(tmp_path/'release/preflight/test.json', proof)
    authority['proof_sha256']=entry.sha(tmp_path/'release/preflight/test.json')
    put(tmp_path/'release/authority.json', authority)
    if allowed:
        assert entry.validate_release(tmp_path, NOW)['proof']==proof
    else:
        with pytest.raises(ValueError, match='proof'):
            entry.validate_release(tmp_path, NOW)


@pytest.mark.parametrize('field,value', [
    ('scope','fixture-only-diagnostic'),('case','e03-round1'),('candidate','old'),
    ('model','qwen2.5:14b'),('digest','wrong'),('case_cap',True),('case_cap',2),
    ('product_cli_cap',2),('audio_actions',1),('retry_authorized',True),
    ('acceptance_credit',True),('prior_reviews',[{'case':'old-round1','verdict':'PASS'}]),
    ('user_authorization',''),('proof_path','../old/proof.json'),
    ('expires_at',(NOW+dt.timedelta(seconds=121)).isoformat()),
])
def test_release_rejects_expanded_or_legacy_scope(tmp_path, monkeypatch, field, value):
    entry, authority, proof=package(tmp_path,monkeypatch)
    authority[field]=value;put(tmp_path/'release/authority.json', authority)
    made=[]
    with pytest.raises(ValueError): entry.run_once(tmp_path, backend_factory=lambda root:made.append(root))
    assert made==[] and not (tmp_path/'actual').exists()


@pytest.mark.parametrize('fault', ['no-review','wrong-review','file-drift','unsealed-python','proof-drift','proof-model','protected-drift'])
def test_release_denies_before_native_construction(tmp_path, monkeypatch, fault):
    entry, authority, proof=package(tmp_path,monkeypatch)
    if fault=='no-review': (tmp_path/'release/independent-review.json').unlink()
    elif fault=='wrong-review':
        review=json.loads((tmp_path/'release/independent-review.json').read_text());review['verdict']='NEEDS_FIXES'
        put(tmp_path/'release/independent-review.json', review)
        authority['review_sha256']=entry.sha(tmp_path/'release/independent-review.json');put(tmp_path/'release/authority.json',authority)
    elif fault=='file-drift': (tmp_path/'code/controller.py').write_text('changed')
    elif fault=='unsealed-python': (tmp_path/'code/unreviewed.py').write_text('pass')
    elif fault=='proof-drift': (tmp_path/'release/preflight/test.json').write_text('{}')
    else:
        if fault=='proof-model': proof['model']['digest']='wrong'
        else: proof['protected_processes'][0]['created_filetime']+=1
        put(tmp_path/'release/preflight/test.json',proof)
        authority['proof_sha256']=entry.sha(tmp_path/'release/preflight/test.json');put(tmp_path/'release/authority.json',authority)
    made=[]
    with pytest.raises((ValueError,FileNotFoundError)):
        entry.run_once(tmp_path,backend_factory=lambda root:made.append(root))
    assert made==[] and not (tmp_path/'actual').exists()


class Backend:
    def __init__(self, root, proof, fail=None):
        self.root=root;self.proof=proof;self.fail=fail;self.calls=[];self.cli_count=0
    def inspect(self):
        self.calls.append('inspect')
        if self.fail=='postflight' and 'close' in self.calls: raise RuntimeError('postflight failed')
        return self.proof
    def start(self,folder):
        self.calls.append('start');self.folder=folder
        assert (folder/'admission.json').exists()
        if self.fail=='start': raise RuntimeError('start failed')
    def product(self,revalidate,admit_cli):
        revalidate();admit_cli();self.calls.append('product')
        if self.fail=='product': raise RuntimeError('product failed')
        self.cli_count += 1
        put(self.folder/'product-result.json', {'test_only':True})
        return {'mechanical':'PASS','facts':'PENDING_ROOT_INDEPENDENT_REVIEW'}
    def effects(self):
        self.calls.append('effects')
        if self.fail=='effects': raise RuntimeError('effects failed')
        put(self.folder/'pre-cleanup-effects.json', {'cli_count':self.cli_count,'test_only':True})
        return {'cli_count':self.cli_count,'outputs':[],'windows':[]}
    def close(self):
        self.calls.append('close')
        if self.fail=='close': raise RuntimeError('close failed')
        return {'status':'PASS'}
    def audit(self):
        self.calls.append('audit')
        if self.fail=='audit': raise RuntimeError('audit failed')
        return {'status':'PASS'}


def test_one_case_keeps_fact_review_pending_and_cannot_be_reentered(tmp_path, monkeypatch):
    entry,authority,proof=package(tmp_path,monkeypatch);backend=Backend(tmp_path,proof)
    result=entry.run_once(tmp_path,backend_factory=lambda root:backend)
    assert result['mechanical']=='PASS' and result['overall']=='PENDING_FACT_REVIEW'
    assert result['facts']=='PENDING_ROOT_INDEPENDENT_REVIEW' and result['acceptance_credit'] is False
    assert result['work_cli_count']==1 and result['actual_native_start_count'] is None
    assert backend.calls==['inspect','start','inspect','product','effects','close','audit','inspect']
    made=[]
    with pytest.raises(FileExistsError):entry.run_once(tmp_path,backend_factory=lambda root:made.append(root))
    assert made==[]


@pytest.mark.parametrize('fail',['start','product','effects','close','audit','postflight'])
def test_failure_retains_claim_and_always_attempts_all_finalization(tmp_path,monkeypatch,fail):
    entry,authority,proof=package(tmp_path,monkeypatch);backend=Backend(tmp_path,proof,fail)
    result=entry.run_once(tmp_path,backend_factory=lambda root:backend)
    assert result['overall']=='FAIL' and result['acceptance_credit'] is False
    assert all(name in backend.calls for name in ('effects','close','audit'))
    assert backend.calls[-1]=='inspect'
    assert (tmp_path/'actual'/entry.CASE/'terminal.json').exists()
    with pytest.raises(FileExistsError):entry.run_once(tmp_path,backend_factory=lambda root:backend)


def test_live_drift_refuses_before_claim_or_windows(tmp_path,monkeypatch):
    entry,authority,proof=package(tmp_path,monkeypatch)
    live=json.loads(json.dumps(proof));live['protected_processes'][0]['created_filetime']+=1
    backend=Backend(tmp_path,live)
    with pytest.raises(ValueError,match='drift'):entry.run_once(tmp_path,backend_factory=lambda root:backend)
    assert backend.calls==['inspect'] and not (tmp_path/'actual').exists()


def test_readonly_preflight_has_no_authority_or_actual_allocation(tmp_path,monkeypatch):
    entry,authority,proof=package(tmp_path,monkeypatch)
    (tmp_path/'release/authority.json').unlink()
    backend=Backend(tmp_path,proof)
    result=entry.write_preflight(tmp_path,backend_factory=lambda root:backend)
    assert result['proof_path'].startswith('release/preflight/')
    assert json.loads((tmp_path/result['proof_path']).read_text())==proof
    assert backend.calls==['inspect']
    assert not (tmp_path/'actual').exists() and not (tmp_path/'release/authority.json').exists()


@pytest.mark.parametrize('inspection', [1,2])
def test_proof_expiring_during_live_inspection_stops_before_next_effect(tmp_path,monkeypatch,inspection):
    entry,authority,proof=package(tmp_path,monkeypatch);backend=Backend(tmp_path,proof)
    original=backend.inspect
    def slow_inspection():
        result=original()
        if backend.calls.count('inspect')==inspection:
            monkeypatch.setattr(entry,'utcnow',lambda:NOW+dt.timedelta(seconds=61))
        return result
    backend.inspect=slow_inspection
    if inspection==1:
        with pytest.raises(ValueError,match='proof'):entry.run_once(tmp_path,backend_factory=lambda root:backend)
        assert not (tmp_path/'actual').exists() and 'start' not in backend.calls
    else:
        result=entry.run_once(tmp_path,backend_factory=lambda root:backend)
        assert result['overall']=='FAIL' and backend.cli_count==0


def test_mechanical_flag_without_product_receipt_cannot_be_pending_acceptance(tmp_path,monkeypatch):
    entry,authority,proof=package(tmp_path,monkeypatch);backend=Backend(tmp_path,proof)
    original=backend.product
    def missing_receipt(revalidate,admit_cli):
        result=original(revalidate,admit_cli);(backend.folder/'product-result.json').unlink();return result
    backend.product=missing_receipt
    result=entry.run_once(tmp_path,backend_factory=lambda root:backend)
    assert result['overall']=='FAIL' and any(x['stage']=='evidence' for x in result['errors'])


def test_sealed_wrapper_drift_during_case_invalidates_final_boundary(tmp_path,monkeypatch):
    entry,authority,proof=package(tmp_path,monkeypatch);backend=Backend(tmp_path,proof)
    original=backend.product
    def change_wrapper(revalidate,admit_cli):
        result=original(revalidate,admit_cli);(tmp_path/'code/package_io.py').write_text('# drift\n');return result
    backend.product=change_wrapper
    result=entry.run_once(tmp_path,backend_factory=lambda root:backend)
    assert result['overall']=='FAIL' and any(x['stage']=='boundaries' for x in result['errors'])
    assert 'close' in backend.calls
