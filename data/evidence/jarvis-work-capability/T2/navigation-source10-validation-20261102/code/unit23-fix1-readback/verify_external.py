"""FIX1 independent packet/file oracle: stdlib only, no product/SDK imports."""
import ast
import collections
import copy
import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
RUN=ROOT/'unit23-fix1-covering'
H=lambda raw:hashlib.sha256(raw).hexdigest()
J=lambda obj:json.dumps(obj,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
MODEL='qwen3-8b-uncensored'
DIGEST='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330'

def obj(**props): return dict(type='object',additionalProperties=False,properties=props,required=list(props))
def text(n): return dict(type='string',minLength=1,maxLength=n)
def array(items,a,z): return dict(type='array',items=items,minItems=a,maxItems=z)
FACT=obj(claim=text(2000),evidence_id=dict(type='string',pattern=r'^N3\.[0-9a-f]{16}$',minLength=19,maxLength=19))
SECTION=obj(source_id=dict(type='string',pattern=r'^S[1-5]$',minLength=2,maxLength=2),heading=text(200),facts=array(FACT,1,6))
WRITER=obj(path=text(2048),title=text(200),sections=array(SECTION,3,5))
INSPECT=dict(type='object',additionalProperties=False,properties=dict(source_id=dict(type='string',enum=['S1','S2','S3','S4','S5']),
    start_line=dict(type='integer',minimum=1,maximum=1024)),required=['source_id','start_line'])
FINAL=dict(type='object',additionalProperties=False,required=['final_answer'],properties=dict(final_answer=text(1000)))
def action(name,params):
    return dict(type='object',additionalProperties=False,required=['action','action_input'],properties=dict(action=dict(enum=[name]),action_input=params))
def sampler(schema):
    out=copy.deepcopy(schema);out.pop('maxLength',None)
    if 'properties' in out: out['properties']={k:sampler(v) for k,v in out['properties'].items()}
    if 'items' in out: out['items']=sampler(out['items'])
    if 'anyOf' in out: out['anyOf']=[sampler(v) for v in out['anyOf']]
    return out

sdk=Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Lib/site-packages/openjarvis')
sdk_pin=json.loads((ROOT/'unit23-delivery-readback/sdk-sources.json').read_bytes())
assert len(sdk_pin['sha256'])==22
assert all(H(Path(p).read_bytes())==sha for p,sha in sdk_pin['sha256'].items())
tree=ast.parse((sdk/'agents/native_react.py').read_text(encoding='utf8'))
template=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REACT_SYSTEM_PROMPT' for t in n.targets))
assert H(template.encode())=='a062f71243cd4986a2f2034cf3946912196fd4f4499394815cb0d3a1c522579b'
persona=(C/'libs/base/openjarvis/configs/openjarvis/prompts/personas/jarvis.md').read_text(encoding='utf8').strip()
rules=(C/'docs/specs/mainbrain-rules-baseline.md').read_text(encoding='utf8')
mainbrain=persona+'\n\n'+re.search(r'```\s*\r?\n(.*?)\r?\n```',rules,re.S).group(1).strip()
descriptions=('### ultima_work_research_inspect\nInspect one safe source page. Use only issued page references when writing.\nCategory: work\nParameters:\n  - source_id (string, required)\n  - start_line (integer, required)\n\n'
    '### ultima_work_research_write\nDeliver the requested research file. Supply your own source-supported facts in sections using the given source_id values. The server renders each stored source URL; do not copy URLs into facts. At least three distinct source IDs are required.\nCategory: work\nParameters:\n  - path (string, required)\n  - title (string, required)\n  - sections (array, required)')
original=(template+'\n\n'+mainbrain).format(tool_descriptions=descriptions,skill_examples='')
prefix=template.split('# Using Skills',1)[0]
assert H(prefix.encode())=='f1ac2c27009f1759da22b3dfc6f301d0912ba8370f1dd3964433421910474621'
replacement=('Return exactly one JSON object matching the phase schema. Use action and object action_input for one permitted SDK tool, '
    'or final_answer for refusal or the authorized final acknowledgement. Write prose style applies inside user-facing text only.\n\n')
replaced=original.replace(prefix,replacement,1)
AUTHOR=('Inspect safe source pages; author only atomic claims supported by the exact returned witnesses. '
    'Use at least three distinct source URLs and bodies. Write only research.md once, or refuse with final_answer. '
    'The phase schema is the entire output contract. Full argument schema (JSON):\n'
    +json.dumps(WRITER,ensure_ascii=False,separators=(',',':'))+'\nEnd argument schema.')
ACK='Acknowledge the verified research.md file. No further action is authorized.'

results=[]
for oracle_path in sorted((RUN/'temp').rglob('external-readback.json')):
    folder=oracle_path.parent; oracle=json.loads(oracle_path.read_bytes()); manifest=json.loads((folder/'packet-manifest.json').read_bytes())
    data={name:(folder/name).read_bytes() for name in ('runtime-replay.json','issued-snapshot.json','issued-views.json','runtime-inputs.json','prewrite-packet.json')}
    assert H(data['runtime-replay.json'])==manifest['runtime_sha256']
    assert H(data['issued-snapshot.json'])==manifest['issued_sha256']
    assert H(data['issued-views.json'])==manifest['views_sha256']
    assert H(data['runtime-inputs.json'])==manifest['inputs_sha256']
    assert H(data['prewrite-packet.json'])==manifest['prewrite_sha256']
    packet=json.loads(data['runtime-replay.json']); issued=json.loads(data['issued-snapshot.json']); views=json.loads(data['issued-views.json'])
    inputs=json.loads(data['runtime-inputs.json']); prewrite=json.loads(data['prewrite-packet.json'])
    assert J(packet)==data['runtime-replay.json'] and packet['prewrite_packet'].encode()==data['prewrite-packet.json']
    assert packet['prewrite_sha256']==manifest['prewrite_sha256'] and prewrite['prewrite_packet'] is None and prewrite['prewrite_sha256'] is None
    assert prewrite['execution']==dict(intent=None,files=[],effects=[])
    for key in ('events','wires','timeline'): assert packet[key][:len(prewrite[key])]==prewrite[key]
    assert packet['transport']['receipts'][:len(prewrite['transport']['receipts'])]==prewrite['transport']['receipts']
    assert packet['issued_manifest']==manifest['issued_sha256'] and packet['views_sha256']==manifest['views_sha256']
    assert packet['nonce']==issued['nonce'] and packet['binding']==issued['binding_key']==inputs['binding_key']
    assert packet['prompt']==inputs['prompt'] and 'Research a subject '+oracle['variant'] in inputs['prompt']
    assert packet['system_original']==original and H(mainbrain.encode())==oracle['persona_sha256']
    collection=issued['collection']; sources=json.loads(collection['catalogue_json']); gets={r['call_id']:r for r in issued['get_records']}
    attempts=json.loads(collection['attempts_json']); trace=json.loads(collection['trace_json'])
    assert [r['wire'] for r in issued['reads']]==views and len(views)==3
    source_packets={s['source_id']:s for s in issued['sources']}; refs=[];expected=['# Observed report','']
    events=[json.loads(e) for e in packet['events']]
    assert [e['type'] for e in events]==['tool_call_start','tool_call_end']*4
    for i,(source,read,view) in enumerate(zip(sources,issued['reads'],views)):
        url=source['final_url']; line=oracle['sources'][url]; code=url.endswith('.py'); domain='extracted-text' if oracle['variant']=='html' else 'raw'
        assert source['text']==line and view['lines']==[[1,line]] and read['wire_sha256']==H(J(view))
        record=gets[source['read_call_id']]; assert record['result']['body']==source['body'] and H(source['body'].encode())==source['decoded_body_sha256']
        assert all(record[k]==v for k,v in zip(('request_id','session_id','task_id'),inputs['binding_key']))
        attempt,=[a for a in attempts if a.get('adapter_call_id')==source['read_call_id']]
        get_events=[e for e in trace if e['sdk_call_id']==attempt['sdk_call_id']]
        assert [e['type'] for e in get_events]==['tool_call_start','tool_call_end']
        assert get_events[0]['data']['arguments']==dict(url=source['requested_url']) and get_events[1]['data']['metadata']['result']==record['result']
        key=read['key']; identity=source_packets[source['source_id']]['identity_json']
        view_id=H(J(['view3',issued['nonce'],inputs['binding_key'],identity,1,1,key['seq'],key['dispatch_uuid'],key['adapter_uuid']]))
        assert view_id==view['view_id'] and key['seq']==i+1 and key['generation']==i+1
        card=view['cards'][0]; assert card[1]==('code' if code else 'documented') and card[3:]==[1,1,1,1]
        assert card[0]=='N3.'+H(J(['card3',view_id,card[1],card[2],1,1,1,1,H(J([[1,line]])),H(J([[1,line]]))]))[:16]
        refs.append(card[0]); start,end=events[i*2:i*2+2]
        args=dict(source_id=source['source_id'],start_line=1)
        assert start['data']==dict(tool='ultima_work_research_inspect',agent='native_react',arguments=args)
        assert end['data']['success'] is True and end['data']['result']==J(view).decode()
        assert end['data']['metadata']==dict(seq=i+1,generation=i+1,dispatch_uuid=key['dispatch_uuid'],adapter_uuid=key['adapter_uuid'],binding=inputs['binding_key'],arguments=args)
        claim='Observed queue.dispatch' if code else line;label='代码观察' if code else '文档说明'
        expected+=['## '+source['source_id'],url,'',f'- {label}（{domain} L1–L1，依据 L1–L1）'+claim,'']
    artifact,=list(folder.rglob('research.md')); actual=artifact.read_bytes()
    assert str(artifact.parent)==inputs['root'] and actual=='\n'.join(expected).encode()
    assert H(actual)==manifest['artifact_sha256']==oracle['sha256']==oracle['expected_sha256']
    intent=packet['execution']['intent'];file,=packet['execution']['files'];effect,=packet['execution']['effects'];receipt=json.loads(events[-1]['data']['result'])
    assert intent['path']==file['path']==effect['path']==receipt['path']==str(artifact)
    assert intent['sha256']==receipt['sha256']==H(actual) and file['content'].encode()==actual and intent['bytes']==len(actual)
    assert intent['file_call_id']==file['call_id']==effect['file_call_id']==receipt['file_call_id']
    assert intent['report_call_id']==file['report_call_id']==effect['report_call_id']==receipt['report_call_id']
    assert intent['dispatch_uuid']==file['dispatch_uuid']==effect['dispatch_id']==receipt['dispatch_uuid']
    assert effect['state']=='completed' and file['success'] is True and file['tool_name']=='ultima_work_file_write'
    assert all(file[k]==effect[k]==v for k,v in zip(('request_id','session_id','task_id'),inputs['binding_key']))
    assert receipt['binding']==intent['binding']==inputs['binding_key'] and receipt['seq']==receipt['generation']==4
    assert receipt['runtime_sha256']==manifest['prewrite_sha256'] and receipt['replay_sha256']==manifest['issued_sha256']
    transport=packet['transport'];receipts=transport['receipts'];assert (transport['generations'],transport['gets'],transport['posts'],transport['completed'])==(5,10,5,5)
    assert len(receipts)==15 and transport['post_bytes']==sum(len(w['entity'].encode()) for w in packet['wires'])<=393216
    timeline=packet['timeline']; cursor=0; prior=None
    def take(kind,**fields):
        global_unused=None
        nonlocal_unused=None
        # Cursor is held in a small list because this module-level loop has no enclosing function.
        node=timeline[position[0]];position[0]+=1
        assert node['kind']==kind and node['order']==position[0] and all(node[k]==v for k,v in fields.items())
        assert node['deadline']==inputs['deadline']
        return Decimal(node['deadline'])-Decimal(node['at'])
    position=[0]
    assert packet['clock_domain']=='work_tools.monotonic;ledger-sequence-v1'
    assert all(Decimal(a['at'])<=Decimal(b['at']) for a,b in zip(timeline,timeline[1:]))
    for i,wire in enumerate(packet['wires']):
        ack=i==4; request=json.loads(wire['entity']);entity=wire['entity'].encode(); raw=json.loads(wire['raw_response'])
        assert J(request)==entity and request['messages']==wire['secured_messages']
        strict=FINAL if ack else dict(anyOf=[action('ultima_work_research_inspect',INSPECT)]+([action('ultima_work_research_write',WRITER)] if i>=3 else [])+[FINAL])
        assert wire['strict_schema']==strict and wire['sampler_schema']==request['format']==sampler(strict)
        assert wire['hashes']==dict(messages=H(J(request['messages'])),strict=H(J(strict)),sampler=H(J(request['format'])),entity=H(entity))
        assert request['messages'][0]==dict(role='system',content=replaced+'\n\n'+(ACK if ack else AUTHOR))
        assert request['messages'][1]==dict(role='user',content=inputs['prompt'])
        assert len(J([request['messages'],strict]))<=32768 and len(J([request['messages'],strict]))+512+request['options']['num_predict']<=16384
        if i:
            assert request['messages'][1:]==packet['wires'][i-1]['secured_messages'][1:]+[
                dict(role='assistant',content=packet['wires'][i-1]['raw']['message']['content']),dict(role='user',content='Observation: '+events[(i-1)*2+1]['data']['result'])]
        assert request['model']==MODEL and request['tools']==[] and all(request[k] is False for k in ('think','stream','truncate','shift'))
        assert request['options']==dict(num_ctx=16384,temperature=0,num_predict=256 if ack or i<3 else 2048)
        assert raw==wire['raw'] and raw['model'] in (MODEL,MODEL+':latest') and raw['done'] is True and raw['done_reason']=='stop'
        assert set(raw)<=set(('model','created_at','done','done_reason','total_duration','load_duration','prompt_eval_count','prompt_eval_duration','eval_count','eval_duration','message'))
        assert raw['message']['role']=='assistant' and set(raw['message'])=={'role','content'}
        assert all(type(raw[k]) is int and raw[k]>0 for k in ('prompt_eval_count','eval_count')) and raw['prompt_eval_count']+raw['eval_count']<=16384
        assert raw['eval_count']<=request['options']['num_predict'] and all(type(raw[k]) is int and 0<=raw[k]<2**63 for k in ('total_duration','load_duration','prompt_eval_duration','eval_duration'))
        envelope=json.loads(raw['message']['content']);assert envelope==wire['raw_envelope']==wire['secured_envelope']
        group=receipts[i*3:i*3+3];assert [(r['method'],r['path'],r['kind']) for r in group]==[('GET','/api/version','metadata'),('GET','/api/tags','metadata'),('POST','/api/chat','chat')]
        identity=wire['identity'];version=json.loads(identity['version_response']);tags=json.loads(identity['tags_response'])
        assert version==dict(version='0.32.15') and identity['local_manifest_sha256']==DIGEST
        selected,=[m for m in tags['models'] if m['name'] in (MODEL,MODEL+':latest')];assert selected['digest']==DIGEST and type(selected['size']) is int and selected['size']==4987654321
        bodies=[identity['version_response'].encode(),identity['tags_response'].encode(),wire['raw_response'].encode()]
        take('generation',generation=i+1)
        for j,(r,body) in enumerate(zip(group,bodies)):
            assert r['send_reserved'] is True and r['admission_error'] is None and r['error'] is None and r['status']==200
            assert r['response_sha256']==H(body) and r['admitted']==r['inspected']==r['retained']==len(body)
            assert r['downloaded'] is None or r['downloaded']>=len(body)
            assert r['entity_sha256']==H(b'' if j<2 else entity) and r['entity_bytes']==(0 if j<2 else len(entity))
            remaining=take('send',generation=i+1,receipt_index=i*3+j); budget=remaining if ack else remaining-55
            assert budget>0; timeout=json.loads(r['timeout_json']);base=min(Decimal(25),budget);read=min(Decimal(25 if ack or j<2 else 180),budget)
            assert all(Decimal(str(timeout[k]))>0 and Decimal(str(timeout[k]))<=limit for k,limit in (('connect',base),('pool',base),('write',base),('read',read)))
            assert take('return',generation=i+1,receipt_index=i*3+j)>0
        assert take('secured',generation=i+1)>=(0 if ack else 55)
        if i: take('promote',seq=i,wire_hash=issued['reads'][i-1]['wire_sha256']) if not ack else None
        if ack: assert set(envelope)=={'final_answer'};continue
        args=envelope['action_input']; assert events[i*2]['data']['arguments']==args and events[i*2]['data']['tool']==envelope['action']
        take('expect',seq=i+1,name=envelope['action'],args_hash=H(J(args)));take('sdk_start',seq=i+1,event_index=i*2)
        key=issued['reads'][i]['key'] if i<3 else intent
        take('claim',seq=i+1,dispatch_uuid=key['dispatch_uuid'],adapter_uuid=key['adapter_uuid'])
        if i==3:
            assert args['title']=='Observed report' and args['path']=='research.md' and [s['facts'][0]['evidence_id'] for s in args['sections']]==refs
            assert intent['args_hash']==H(J(args)) and events[-1]['data']['metadata']==dict(receipt,arguments=args)
            take('freeze',seq=4); assert take('intent',seq=4,file_call_id=intent['file_call_id'])>=55;take('file_end',file_call_id=intent['file_call_id'])
        take('sdk_end',seq=i+1,event_index=i*2+1)
    assert position[0]==len(timeline)
    assert all(transport['admitted'][kind]==sum(r['admitted'] for r in receipts if r['kind']==kind)<=524288 for kind in ('metadata','chat'))
    results.append(dict(variant=oracle['variant'],folder=str(folder),artifact=str(artifact),artifact_sha256=H(actual),artifact_bytes=len(actual),runtime_sha256=H(data['runtime-replay.json']),prewrite_sha256=H(data['prewrite-packet.json']),inputs_sha256=H(data['runtime-inputs.json']),timeline_records=len(timeline),metadata_replayed=True,intent_file_effect_bound=True,exact_phase_and_prompt=True))
assert len(results)==4
receipt=json.loads((RUN/'receipt.json').read_bytes());assert receipt['exit_code']==0 and receipt['source_unchanged']
assert json.loads((RUN/'loaded-paths.json').read_bytes())['unexpected']=={}
previous=ET.parse(ROOT/'unit23-delivery-covering/junit.xml').getroot().findall('.//testcase')
current=ET.parse(RUN/'junit.xml').getroot().findall('.//testcase')
ids=lambda cases:{c.attrib['classname']+'::'+c.attrib['name'] for c in cases}
assert ids(previous)<=ids(current) and len(current)==449
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='stdlib-only independent FIX1 original-input/metadata/native/transcript/prewrite/intent/file/literal-render readback',product_modules_imported=False,sdk_sources_unchanged=22,original_418_identities_preserved=True,cases=results,argv=sys.argv,interpreter=sys.executable,script_sha256=H(Path(__file__).read_bytes()))
(HERE/'external-verification.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps(dict(cases=len(results),current_junit=len(current),sdk22_unchanged=True,all_external_hashes_and_orders_pass=True)))
