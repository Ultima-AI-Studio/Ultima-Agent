from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parents[1]
assert json.loads((N/'review/independent-plan-review.json').read_bytes())['verdict']=='PASS_PLAN_ONLY'
p=N/'harness/test_adapter.py';s=p.read_text('utf8')
assert 'def test_export_diagnostics_current_native_refusal(' not in s
s+='''

@pytest.mark.parametrize('case',['six_reads','ack_after_write'])
def test_export_diagnostics_current_native_refusal(tmp_path,monkeypatch,sdk_io,mock_jar,case):
    from src.brain.tests.test_work_native_response_diagnostics import native_refusal
    observe_failure_exports(tmp_path,monkeypatch)
    ack=case=='ack_after_write'
    result,ledger,sent,responses=native_refusal(tmp_path/'outputs',sdk_io,mock_jar,monkeypatch,reads=6,ack=ack)
    raw=(tmp_path/'trusted-failure-diagnostic.raw').read_bytes();packet=json.loads(raw)
    receipt=a.load(tmp_path/'trusted-failure-diagnostic.export.json')
    assert raw==ledger._failure_diagnostic and len(raw)<=16384
    assert packet['kind']=='research_failure_diagnostic_v4'
    assert result['research_diagnostic']['kind']==packet['kind']
    assert receipt['sha256']==result['research_diagnostic']['sha256']==a.hashlib.sha256(raw).hexdigest()
    assert receipt['status']=='SAVED' and receipt['bytes']==len(raw)
    assert receipt['complete'] is False and receipt['END'] is False and receipt['acceptance_credit']==0
    assert a.load(tmp_path/'service-first-result.json')==result
    assert result['error']=='Invalid native research response' and not result['artifacts']
    assert not (tmp_path/'trusted-runtime.raw').exists() and not getattr(ledger,'_runtime_final',None)
    exported=a.load(tmp_path/'trusted-export.json')
    assert exported['complete'] is False and exported['END'] is False
    native=packet['native_response'];last=packet['last_http'];generation=5 if ack else 7
    assert native['reason']=='done_reason' and native['done_reason']=='length'
    assert native['max_tokens']==(256 if ack else 2048)
    assert native['generation']==last['generation']==generation==len(sent)
    assert native['receipt_index']==last['receipt_index']==3*generation-1
    assert native['request_sha256']==last['request_sha256']==a.hashlib.sha256(sent[-1]).hexdigest()
    assert native['response_sha256']==a.hashlib.sha256(responses[-1]).hexdigest()
    assert native['response_bytes']==last['admitted']==len(responses[-1])
    assert last['status']==200 and last['send_reserved'] and not last['validated_response'] and not last['transport_failed']
    assert packet['eligible_source_ids']==['S1','S2','S3']
    assert packet['complete'] is False and packet['acceptance_credit']==0 and not packet['ack_confirmed']
    assert exported['native_POST_attempts']==packet['budget']['native_posts']==generation
    files=list((tmp_path/'outputs').rglob('research.md'))
    if ack:
        assert result['status']=='needs_attention' and packet['branch']=='write_without_ack' and packet['write_confirmed']
        assert packet['budget']['reads_used']==3 and len(files)==1 and files[0].read_bytes()
        assert len(result['research_effects'])==1 and result['research_effects'][0]['state']=='completed'
        assert Path(result['research_effects'][0]['path']).resolve()==files[0].resolve()
    else:
        assert result['status']=='failed' and result['content']=='本次研究未交付。'
        assert packet['branch']=='unvalidated_response' and not packet['write_confirmed']
        assert packet['budget']['reads_used']==6 and len(packet['pages'])==6
        assert sum(page['confirmed'] for page in packet['pages'])==6
        assert sum(page['visible'] for page in packet['pages'])==5
        assert not files and not result.get('research_effects')
'''
p.write_text(s,encoding='utf8',newline='\n')
manifest_path=N/'harness/manifest.json';old=json.loads(manifest_path.read_bytes())
inputs=json.loads((N/'inputs/input-manifest.json').read_bytes())
old.update(candidate=inputs['candidate'],candidate_manifest_sha256=hashlib.sha256((N/'inputs/input-manifest.json').read_bytes()).hexdigest(),
    files={name:hashlib.sha256((N/'harness'/name).read_bytes()).hexdigest() for name in old['files']})
manifest_path.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(dict(new_observer_cases=2,harness_files=len(old['files']),actual_allocation=0)))
