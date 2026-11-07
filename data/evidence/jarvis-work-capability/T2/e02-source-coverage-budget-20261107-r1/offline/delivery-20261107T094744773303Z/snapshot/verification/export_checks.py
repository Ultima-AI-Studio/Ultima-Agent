"""Offline compatibility of the unchanged restricted exporter with current v3."""
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import types
import pytest
from src.brain.work_navigation import canonical_v3
from src.brain.tests.test_work_research import sdk_io,mock_jar,stable_navigation_entropy
from src.brain.tests.test_work_http_failure_diagnostics import failing_exchange

N=Path(__file__).resolve().parents[1]
P=N.parent/'e02-unique-sections-20261107-r1'

@pytest.fixture
def adapter(monkeypatch):
    # Import no live observer: fixed hostname avoids an unrelated native query.
    predecessor=json.loads((N.parent/'e02-native-http-diagnostics-20261107-r1/inputs/predecessor.json').read_bytes())
    assert hashlib.sha256((P/'manifest.json').read_bytes()).hexdigest()==predecessor['manifest_sha256']
    pins=json.loads((P/'manifest.json').read_bytes())['files']
    path=P/'harness/adapter.py'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==pins['harness/adapter.py']
    monkeypatch.setattr(socket,'gethostname',lambda:'offline-export-fixture')
    spec=importlib.util.spec_from_file_location('frozen_export_helper',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    # Scope: payload/export compatibility only. OS reparse/authority checks are not rerun here.
    monkeypatch.setattr(value,'load_p4',lambda:types.SimpleNamespace(no_reparse=lambda p:p))
    return value


def test_original_restricted_export_preserves_http500_with_zero_credit(tmp_path,sdk_io,mock_jar,monkeypatch,adapter):
    result,ledger,*_=failing_exchange(tmp_path/'work',sdk_io,mock_jar,monkeypatch)
    adapter.export_failure_diagnostic(tmp_path,ledger,result)
    raw=(tmp_path/'trusted-failure-diagnostic.raw').read_bytes()
    receipt=json.loads((tmp_path/'trusted-failure-diagnostic.export.json').read_bytes())
    assert raw==ledger._failure_diagnostic and json.loads(raw)['last_http']['status']==500
    assert receipt['sha256']==hashlib.sha256(raw).hexdigest() and receipt['bytes']==len(raw)<=16384
    assert receipt['complete'] is False and receipt['END'] is False and receipt['acceptance_credit']==0
    assert not list(tmp_path.rglob('research.md'))


@pytest.mark.parametrize('fault',['request_binding','public_digest','extra_body','old_version','unsafe_final'])
def test_original_exporter_rejects_forged_or_unsafe_v3(tmp_path,sdk_io,mock_jar,monkeypatch,adapter,fault):
    result,ledger,*_=failing_exchange(tmp_path/'work',sdk_io,mock_jar,monkeypatch)
    packet=json.loads(ledger._failure_diagnostic)
    if fault=='request_binding':result['request_id']='different-request'
    elif fault=='public_digest':result['research_diagnostic']['sha256']='0'*64
    else:
        if fault=='extra_body':packet['last_http']['body']='private'
        elif fault=='old_version':packet['kind']='research_failure_diagnostic_v2'
        else:
            text='password = "syntheticsecret"'
            packet.update(branch='final_before_write',final_answer=dict(text=text,length=len(text),sha256=hashlib.sha256(text.encode()).hexdigest()))
        ledger._failure_diagnostic=canonical_v3(packet)
        result['research_diagnostic']['sha256']=hashlib.sha256(ledger._failure_diagnostic).hexdigest()
        ledger._failure_diagnostic_summary=dict(result['research_diagnostic'])
    with pytest.raises(ValueError):adapter.export_failure_diagnostic(tmp_path,ledger,result)
    assert not (tmp_path/'trusted-failure-diagnostic.raw').exists()
