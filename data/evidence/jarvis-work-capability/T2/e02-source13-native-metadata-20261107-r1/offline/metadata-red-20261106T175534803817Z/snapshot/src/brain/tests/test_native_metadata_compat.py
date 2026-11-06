"""Saved native metadata compatibility; no server or model is contacted."""
import copy
import json
from pathlib import Path

import pytest

from src.brain.agent_server import _RESEARCH_DIGEST
from src.brain.work_research import checked_native_identity


@pytest.fixture
def saved_metadata():
    return json.loads((Path(__file__).parent / 'fixtures/native_metadata_0_32_15.json').read_bytes())


def check(value, digest=_RESEARCH_DIGEST):
    return checked_native_identity(json.dumps(value['version']).encode(),
                                   json.dumps(value['tags']).encode(), digest)


def test_saved_native_tags_preserve_capabilities(saved_metadata):
    version, tags = check(saved_metadata)
    assert version == saved_metadata['version']
    assert tags == saved_metadata['tags']
    assert tags['models'][0]['capabilities'] == ['completion']


@pytest.mark.parametrize('capabilities', [[], ['completion'], ['completion', 'tools'], ['embedding']])
def test_optional_capabilities_are_string_arrays(saved_metadata, capabilities):
    saved_metadata['tags']['models'][0]['capabilities'] = capabilities
    assert check(saved_metadata)[1] == saved_metadata['tags']


def test_legacy_metadata_without_capabilities_is_accepted(saved_metadata):
    for model in saved_metadata['tags']['models']:
        model.pop('capabilities')
    assert check(saved_metadata)[1] == saved_metadata['tags']


@pytest.mark.parametrize('capabilities', [None, 'completion', {}, 1, True, [1], [None], [False], [{}], [['completion']], ['completion', 2]])
@pytest.mark.parametrize('model_index', [0, 2])
def test_bad_capability_types_fail_closed(saved_metadata, capabilities, model_index):
    saved_metadata['tags']['models'][model_index]['capabilities'] = capabilities
    with pytest.raises(ValueError, match='Invalid native model metadata'):
        check(saved_metadata)


@pytest.mark.parametrize('fault', ['unknown_model_field', 'unknown_tags_field', 'wrong_version',
    'extra_version_field', 'wrong_digest', 'wrong_name', 'duplicate_target', 'alias_mismatch',
    'boolean_size', 'negative_size', 'oversized_size', 'nonstring_digest', 'nonobject_model'])
def test_capabilities_do_not_relax_existing_identity_checks(saved_metadata, fault):
    model = saved_metadata['tags']['models'][0]
    if fault == 'unknown_model_field': model['extra'] = True
    elif fault == 'unknown_tags_field': saved_metadata['tags']['extra'] = True
    elif fault == 'wrong_version': saved_metadata['version']['version'] = '0.32.16'
    elif fault == 'extra_version_field': saved_metadata['version']['extra'] = True
    elif fault == 'wrong_digest': model['digest'] = '0' * 64
    elif fault == 'wrong_name': model['name'] = model['model'] = 'other:latest'
    elif fault == 'duplicate_target': saved_metadata['tags']['models'].append(copy.deepcopy(model))
    elif fault == 'alias_mismatch': model['model'] = 'other:latest'
    elif fault == 'boolean_size': model['size'] = True
    elif fault == 'negative_size': model['size'] = -1
    elif fault == 'oversized_size': model['size'] = 2**63
    elif fault == 'nonstring_digest': model['digest'] = 123
    elif fault == 'nonobject_model': saved_metadata['tags']['models'][0] = []
    with pytest.raises(ValueError):
        check(saved_metadata)


def test_local_manifest_digest_is_still_required(saved_metadata):
    with pytest.raises(ValueError, match='digest mismatch'):
        check(saved_metadata, '0' * 64)


def test_duplicate_capabilities_key_is_rejected(saved_metadata):
    raw = json.dumps(saved_metadata['tags'])
    raw = raw.replace('"capabilities": ["completion"]',
                      '"capabilities": ["completion"], "capabilities": []', 1)
    assert raw != json.dumps(saved_metadata['tags'])
    with pytest.raises(ValueError):
        checked_native_identity(json.dumps(saved_metadata['version']).encode(), raw.encode(), _RESEARCH_DIGEST)
