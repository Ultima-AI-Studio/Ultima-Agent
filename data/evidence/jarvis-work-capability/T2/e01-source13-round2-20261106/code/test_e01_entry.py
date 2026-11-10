import pytest

from test_acceptance_entry import Backend, package, put
from test_round2_predecessor import read, reseal
from test_e01_prerequisites import rebind


@pytest.mark.parametrize('field,value', [('scope', 'e03-negative-acceptance'), ('case', 'e03-negative'),
    ('product_cli_cap', 0), ('product_cli_cap', True), ('case_cap', 2),
    ('case', 'e01-round1'), ('scope', 'e01-round1-acceptance')])
def test_only_one_e01_cli_scope_can_reach_native_factory(tmp_path, monkeypatch, field, value):
    entry, authority, proof = package(tmp_path, monkeypatch)
    authority[field] = value
    put(tmp_path / 'release/authority.json', authority)
    made = []
    with pytest.raises(ValueError):
        entry.run_once(tmp_path, backend_factory=lambda root: made.append(root))
    assert made == [] and not (tmp_path / 'actual').exists()


@pytest.mark.parametrize('field,value', [('proof_max_age_seconds', 61), ('admission_max_seconds', 121),
    ('fixture_required', True), ('product_timeouts', {'CLI':900,'SDK':1800,'controller_wait':915}),
    ('product_cli_cap', 0), ('product_cli_cap', True)])
def test_package_cannot_describe_expanded_or_wrong_execution(tmp_path, monkeypatch, field, value):
    entry, authority, proof = package(tmp_path, monkeypatch)
    manifest = read(tmp_path / 'manifest.json')
    manifest[field] = value
    put(tmp_path / 'manifest.json', manifest)
    reseal(tmp_path, entry, authority)
    made = []
    with pytest.raises(ValueError):
        entry.run_once(tmp_path, backend_factory=lambda root: made.append(root))
    assert made == []


@pytest.mark.parametrize('name', ['terminal','review','registration','result-manifest','negative-evidence'])
def test_negative_dependencies_must_be_sealed_before_native_construction(tmp_path, monkeypatch, name):
    entry, authority, proof = package(tmp_path, monkeypatch)
    manifest = read(tmp_path / 'manifest.json')
    omitted = 'inputs/prior-negative/' + name + '.json'
    manifest['files'] = [row for row in manifest['files'] if row['path'] != omitted]
    put(tmp_path / 'manifest.json', manifest)
    reseal(tmp_path, entry, authority)
    made = []
    with pytest.raises(ValueError, match='[Rr]untime dependency'):
        entry.run_once(tmp_path, backend_factory=lambda root: made.append(root))
    assert made == []


def test_ineligible_negative_after_rehash_denied_before_backend(tmp_path, monkeypatch):
    entry, authority, proof = package(tmp_path, monkeypatch)
    path = tmp_path / 'inputs/prior-negative/review.json'
    review = read(path)
    review['behavior_verdict'] = 'FAIL'
    put(path, review)
    rebind(tmp_path)
    reseal(tmp_path, entry, authority)
    made = []
    with pytest.raises(ValueError, match='Negative predecessor'):
        entry.run_once(tmp_path, backend_factory=lambda root: made.append(root))
    assert made == []


def test_fake_completed_mechanical_with_zero_cli_does_not_pass(tmp_path, monkeypatch):
    entry, authority, proof = package(tmp_path, monkeypatch)
    backend = Backend(tmp_path, proof)
    original = backend.product
    def no_cli(revalidate, admit_cli):
        result = original(revalidate, admit_cli)
        backend.cli_count = 0
        return result
    backend.product = no_cli
    result = entry.run_once(tmp_path, backend_factory=lambda root: backend)
    assert result['overall'] == 'FAIL' and result['acceptance_credit'] is False


@pytest.mark.parametrize('name', ['terminal','review','registration'])
def test_e01_round1_dependencies_are_required_before_native_construction(tmp_path, monkeypatch, name):
    entry, authority, proof = package(tmp_path, monkeypatch)
    manifest = read(tmp_path / 'manifest.json')
    omitted = 'inputs/prior-e01-round1/' + name + '.json'
    manifest['files'] = [row for row in manifest['files'] if row['path'] != omitted]
    put(tmp_path / 'manifest.json', manifest)
    reseal(tmp_path, entry, authority)
    made = []
    with pytest.raises(ValueError, match='[Rr]untime dependency'):
        entry.run_once(tmp_path, backend_factory=lambda root: made.append(root))
    assert made == [] and not (tmp_path / 'actual').exists()


def test_ineligible_e01_round1_after_rehash_denied_before_backend(tmp_path, monkeypatch):
    from test_e01_round2_prerequisite import rebind as rebind_e01
    entry, authority, proof = package(tmp_path, monkeypatch)
    path = tmp_path / 'inputs/prior-e01-round1/review.json'
    review = read(path)
    review['facts_verdict'] = 'FAIL'
    put(path, review)
    rebind_e01(tmp_path)
    reseal(tmp_path, entry, authority)
    made = []
    with pytest.raises(ValueError, match='E01 predecessor'):
        entry.run_once(tmp_path, backend_factory=lambda root: made.append(root))
    assert made == [] and not (tmp_path / 'actual').exists()
