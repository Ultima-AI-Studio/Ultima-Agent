"""Offline compatibility with a frozen raw v3 receipt and unchanged observer export."""
from pathlib import Path
import hashlib,importlib.util,json
import pytest
from src.brain import work_research_diagnostics as d
from src.brain.tests.test_work_research import sdk_io,mock_jar,stable_navigation_entropy
from src.brain.tests.test_work_native_response_diagnostics import native_refusal

N=Path(__file__).resolve().parents[1]
P=N.parent/'e02-json-string-controlled-preparation-20261107-r1'


def test_frozen_actual_v3_is_read_without_modification():
    folder=P/'actual/E02-controlled-1';raw=(folder/'trusted-failure-diagnostic.raw').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='ba5a830752dc9e4663e800a5b24fe1aa13b09c2960ae807695d591c91dc46304'
    result=json.loads((folder/'product-result.json').read_bytes())
    packet=d.validate_failure_diagnostic(raw,tuple(result[k] for k in ('request_id','session_id','task_id')))
    assert packet['kind']=='research_failure_diagnostic_v3' and 'native_response' not in packet
    assert packet['branch']=='unvalidated_response' and packet['last_http']['status']==200
    assert raw==(folder/'trusted-failure-diagnostic.raw').read_bytes()


@pytest.mark.parametrize('ack',[False,True])
def test_unchanged_observer_exports_current_candidate_v4(tmp_path,sdk_io,mock_jar,monkeypatch,ack):
    from src.brain.work_tools import WorkLedger
    from src.brain.work_service import WorkService
    original=P/'harness/adapter.py'
    spec=importlib.util.spec_from_file_location('frozen_v3_adapter_for_v4_export',original)
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    # Only the existing observer/export functions execute, never its release or actual entry.
    monkeypatch.setattr(a,'C',Path(d.__file__).resolve().parents[2])
    monkeypatch.setattr(WorkLedger,'__init__',WorkLedger.__init__)
    monkeypatch.setattr(WorkLedger,'_freeze_runtime_inputs',WorkLedger._freeze_runtime_inputs)
    monkeypatch.setattr(WorkService,'submit_work',WorkService.submit_work)
    a.install_trusted_exports(tmp_path)
    result,ledger,_,_=native_refusal(tmp_path/'outputs',sdk_io,mock_jar,monkeypatch,ack=ack)
    raw=(tmp_path/'trusted-failure-diagnostic.raw').read_bytes()
    assert raw==ledger._failure_diagnostic and json.loads(raw)['kind']=='research_failure_diagnostic_v4'
    receipt=json.loads((tmp_path/'trusted-failure-diagnostic.export.json').read_bytes())
    assert receipt['status']=='SAVED' and receipt['sha256']==hashlib.sha256(raw).hexdigest()
    assert receipt['complete'] is False and receipt['END'] is False and receipt['acceptance_credit']==0
    assert json.loads((tmp_path/'service-first-result.json').read_bytes())==result
    assert Path(d.__file__).resolve().is_relative_to(a.C)
