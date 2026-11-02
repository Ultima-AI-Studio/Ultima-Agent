"""Independent stdlib-only readback of actual prepared HTTPX captures."""
import datetime,hashlib,json,math,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
RUN=HERE.parent/'unit23-fix2-covering'
H=lambda raw:hashlib.sha256(raw).hexdigest()
J=lambda value:json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
results=[]
for proof_path in sorted((RUN/'temp').rglob('fractional-proof.json')):
    proof=json.loads(proof_path.read_bytes());folder=proof_path.parent
    files={name:(folder/('fractional-'+name+'.json')).read_bytes() for name in ('runtime','prewrite','issued','views','inputs')}
    packet=json.loads(files['runtime']);prewrite=json.loads(files['prewrite']);inputs=json.loads(files['inputs'])
    assert J(packet)==files['runtime'] and packet['prewrite_packet'].encode()==files['prewrite'] and packet['prewrite_sha256']==H(files['prewrite'])
    for key in ('events','wires','timeline'): assert packet[key][:len(prewrite[key])]==prewrite[key]
    assert packet['transport']['receipts'][:12]==prewrite['transport']['receipts']
    deadline=float(proof['deadline']);author=float(proof['author_at']);ack=float(proof['ack_at'])
    assert deadline==1060.2 and inputs['deadline']==proof['deadline'] and proof['replay_accepted'] is True
    expected_author=math.nextafter(1005.2,-math.inf) if proof['edge'] else 1000.1
    expected_ack=math.nextafter(1060.2,-math.inf) if proof['edge'] else 1040.1
    assert author==expected_author and ack==expected_ack
    author_cap=(deadline-author)-55;ack_cap=deadline-ack
    assert 0<author_cap<25 and 0<ack_cap<25
    if not proof['edge']: assert author_cap==5.100000000000023 and ack_cap==20.100000000000136
    timeline=packet['timeline'];sends=[n for n in timeline if n['kind']=='send']
    assert len(sends)==15 and len(proof['prepared_requests'])==15 and len(packet['wires'])==5
    assert all(n['deadline']==inputs['deadline'] and math.isfinite(float(n['at'])) for n in timeline)
    assert all(float(a['at'])<=float(b['at']) for a,b in zip(timeline,timeline[1:]))
    for index,(capture,node,receipt) in enumerate(zip(proof['prepared_requests'],sends,packet['transport']['receipts'])):
        at=ack if index>=12 else author;cap=ack_cap if index>=12 else author_cap
        assert float(capture['at'])==float(node['at'])==at and node['receipt_index']==index
        assert capture['method']==receipt['method'] and capture['path']==receipt['path'] and capture['entity_sha256']==receipt['entity_sha256']
        timeout=json.loads(receipt['timeout_json'])
        assert timeout==capture['timeout']==dict(connect=cap,read=cap,write=cap,pool=cap)
        assert all(type(v) in (int,float) and math.isfinite(v) and 0<v<=cap and math.nextafter(v,math.inf)>cap for v in timeout.values())
        assert receipt['send_reserved'] is True and receipt['admission_error'] is None and receipt['error'] is None
        wire=packet['wires'][index//3]
        entity=wire['entity'].encode() if index%3==2 else b''
        assert receipt['entity_sha256']==H(entity) and receipt['entity_bytes']==len(entity)
        response=(wire['identity']['version_response'] if index%3==0 else wire['identity']['tags_response'] if index%3==1 else wire['raw_response']).encode()
        assert receipt['response_sha256']==H(response) and receipt['admitted']==receipt['inspected']==receipt['retained']==len(response)
    artifact=Path(proof['artifact']);raw=artifact.read_bytes()
    assert artifact.parent==Path(inputs['root']) and H(raw)==proof['artifact_sha256']
    events=[json.loads(e) for e in packet['events']]
    submitted=packet['wires'][3]['secured_envelope']['action_input']
    assert events[-2]['data']==dict(tool='ultima_work_research_write',agent='native_react',arguments=submitted)
    end=events[-1]['data'];report=json.loads(end['result'])
    assert end['agent']=='native_react' and end['tool']=='ultima_work_research_write' and end['success'] is True
    assert report['sha256']==H(raw) and packet['execution']['files'][0]['content'].encode()==raw
    assert packet['wires'][4]['secured_envelope']['final_answer'].strip()
    results.append(dict(folder=str(folder),edge=proof['edge'],author_cap=repr(author_cap),ack_cap=repr(ack_cap),
        prepared_requests=15,artifact_sha256=H(raw),files={k:H(v) for k,v in files.items()},proof_sha256=H(proof_path.read_bytes())))
assert len(results)==6 and sum(r['edge'] for r in results)==1
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),product_modules_imported=False,
    scope='actual same-prepared HTTPX captures, lossless binary64 replay/order/caps, genuine SDK writer/file hashes',
    cases=results,script_sha256=H(Path(__file__).read_bytes()),interpreter=sys.executable)
(HERE/'fractional-verification.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps(dict(cases=len(results),prepared_requests=sum(r['prepared_requests'] for r in results),all_fractional_checks=True)))
