"""Replay accepted SDK evidence read-only; no new case or inference credit."""
from pathlib import Path
import hashlib
import importlib.util
import json

N=Path(__file__).resolve().parents[1]
Q=N.parent/'e02-source13-exact-probe-20261106'
CASE=Q/'runs/a47c74c4-58e7-4a63-ad7d-f63be9c17a51/worker/case'

def inventory():
    return {str(p.relative_to(CASE)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in CASE.rglob('*') if p.is_file()}

def test_accepted_sdk_packet_and_output_replay_without_mutation():
    before=inventory()
    spec=importlib.util.spec_from_file_location('source13_plumbing_replay',N/'harness/adapter.py')
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    adapter.check_inputs()
    first=adapter.load(CASE/'service-first-result.json')
    with adapter.candidate_import_path():
        result=adapter.verify_exports(CASE,first,adapter.load_p4(),readonly=True)
    assert result['native_POST_attempts']==6  # Historical MockTransport count only.
    assert len(result['inventory'])==1
    assert result['inventory'][0]['sha256']=='a7e7e5906654d1981efb48a3e8006de0d45270f27db0adfee5ee02513c549df2'
    assert inventory()==before
    with (Path.cwd()/'plumbing-replay.json').open('x',encoding='utf8') as stream:
        json.dump(dict(result=result,evidence_files_unchanged=before,real_research_credit=0,model_calls=0),stream,indent=2)
