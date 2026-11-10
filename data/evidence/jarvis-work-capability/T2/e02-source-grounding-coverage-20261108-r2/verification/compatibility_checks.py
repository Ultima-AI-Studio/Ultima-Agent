"""Frozen diagnostic decoding and existing export; no observer hook installation."""
from pathlib import Path
import hashlib,importlib.util,json
import pytest
from src.brain import work_research_diagnostics as d
from src.brain.tests.test_work_research import sdk_io,mock_jar,stable_navigation_entropy
from src.brain.tests.test_work_native_response_diagnostics import native_refusal
N=Path(__file__).resolve().parents[1]
P=N.parent/'e02-output-budget-controlled-preparation-20261107-r1'

@pytest.mark.parametrize('name,kind,expected',[
    ('e02-json-string-controlled-preparation-20261107-r1','research_failure_diagnostic_v3','ba5a830752dc9e4663e800a5b24fe1aa13b09c2960ae807695d591c91dc46304'),
    ('e02-output-budget-controlled-preparation-20261107-r1','research_failure_diagnostic_v4','3e1a4747653e31545bf3995e03e3ebe286670a0f13c36c988a478247e4533aaa')])
def test_frozen_actual_diagnostics_remain_readable(name,kind,expected):
    a=N.parent/name/'actual/E02-controlled-1';raw=(a/'trusted-failure-diagnostic.raw').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==expected
    result=json.loads((a/'product-result.json').read_bytes())
    value=d.validate_failure_diagnostic(raw,tuple(result[k] for k in ('request_id','session_id','task_id')))
    assert value['kind']==kind and 'output_structure' not in value
    assert raw==(a/'trusted-failure-diagnostic.raw').read_bytes()

@pytest.mark.parametrize('ack',[False,True])
def test_existing_export_accepts_bounded_v5(tmp_path,sdk_io,mock_jar,monkeypatch,ack):
    original=P/'harness/adapter.py'
    pins=json.loads((P/'manifest.json').read_bytes())['files']
    assert hashlib.sha256(original.read_bytes()).hexdigest()==pins['harness/adapter.py']
    spec=importlib.util.spec_from_file_location('unchanged_adapter_v5_export',original)
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    result,ledger,_,_=native_refusal(tmp_path/'outputs',sdk_io,mock_jar,monkeypatch,ack=ack)
    folder=tmp_path/'export';folder.mkdir()
    adapter.export_failure_diagnostic(folder,ledger,result)
    raw=(folder/'trusted-failure-diagnostic.raw').read_bytes()
    assert raw==ledger._failure_diagnostic and len(raw)<=16384
    assert json.loads(raw)['kind']=='research_failure_diagnostic_v5'
    receipt=json.loads((folder/'trusted-failure-diagnostic.export.json').read_bytes())
    assert receipt['status']=='SAVED' and receipt['sha256']==hashlib.sha256(raw).hexdigest()
    assert receipt['complete'] is False and receipt['END'] is False and receipt['acceptance_credit']==0
