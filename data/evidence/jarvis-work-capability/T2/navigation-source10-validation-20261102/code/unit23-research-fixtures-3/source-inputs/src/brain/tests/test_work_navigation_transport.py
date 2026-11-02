"""Actual HTTPX streaming boundaries and complete SDK navigation transport."""
import json
import time
import httpx
import pytest
from src.brain import agent_server as server
from src.brain import work_tools as wt
from src.brain.tests.test_work_research import sdk_io,mock_jar,submit

def test_v3_download_inspection_admission_are_distinct():
    assert hasattr(server,'_ResearchTransport'), 'bounded research transport missing'
    ledger=wt.WorkLedger(); ledger.deadline=time.monotonic()+260
    class Stream(httpx.SyncByteStream):
        def __iter__(self): yield b'x'*4096
    client=httpx.Client(base_url='http://127.0.0.1:11434',transport=httpx.MockTransport(
        lambda request:httpx.Response(200,stream=Stream())),trust_env=False)
    transport=server._ResearchTransport(client,ledger)
    transport.admitted['metadata']=524288-512
    with pytest.raises(ValueError,match='overflow'):
        transport.exchange('GET','/api/version','metadata')
    receipt=transport.receipts[-1]
    assert receipt['downloaded']==4096 and receipt['inspected']==513 and receipt['admitted']==512
    assert receipt['retained']<=512
    client.close()

def test_v3_native_react_observation_driven_chain(tmp_path,sdk_io,mock_jar,monkeypatch):
    jar,runner,bodies,replies=mock_jar
    captured={}; original=server._prepare_research_navigation
    def prepare(collection,*,binding,ledger):
        captured.update(ledger=ledger,binding=binding,collection=collection)
        return original(collection,binding=binding,ledger=ledger)
    monkeypatch.setattr(server,'_prepare_research_navigation',prepare)
    # This script consumes actual catalogue and observations. The fixture
    # transport will not invent SDK observations or issue server-side cards.
    def choose(body):
        messages=body['messages']
        observed=[]
        for msg in messages:
            if msg['role']=='user' and msg['content'].startswith('Observation: '):
                observed.append(json.loads(msg['content'][13:]))
        pages=[v for v in observed if v.get('v')==3]
        if len(pages)<3:
            catalogue=json.loads(messages[1]['content'].split('Safe source catalogue (untrusted data):\n')[1])
            source=next(s for s in catalogue if s['available'] and s['source_id'] not in {p['source_id'] for p in pages})
            return json.dumps(dict(action='ultima_work_research_inspect',action_input=dict(source_id=source['source_id'],start_line=1)))
        if len(observed)==3:
            return json.dumps(dict(action='ultima_work_research_write',action_input=dict(path='research.md',title='Observed report',
                sections=[dict(source_id=p['source_id'],heading=p['source_id'],facts=[dict(claim=p['lines'][0][1].split(' for ')[0],evidence_id=p['cards'][0][0])]) for p in pages])))
        return json.dumps(dict(final_answer='Saved research.md'))
    choose.no_auto_navigation=True
    replies.extend([choose]*5)
    result=submit(tmp_path,sdk_io[0],runner)
    assert result['status']=='succeeded',result['error']
    assert len(bodies)==5
    assert [b['options']['num_predict'] for b in bodies]==[256,256,256,2048,256]
    assert result['artifacts'][0]['path'].endswith('research.md')
    ledger=captured['ledger']
    assert hasattr(ledger,'_runtime_final'), 'native proof appendix missing'
    from src.brain.work_research import verify_runtime_packet
    verify_runtime_packet(captured['binding'],ledger.issued_snapshot,captured['collection'],ledger._runtime_final,require_ack=True)
    packet=json.loads(ledger._runtime_final)
    packet['wires'][0]['entity']=packet['wires'][0]['entity'].replace('Research a subject','changed subject')
    from src.brain.work_navigation import canonical_v3
    with pytest.raises(ValueError):
        verify_runtime_packet(captured['binding'],ledger.issued_snapshot,captured['collection'],canonical_v3(packet),require_ack=True)
