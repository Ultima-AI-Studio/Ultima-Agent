from pathlib import Path
import copy, json, os, socket, sys
from dataclasses import replace
from unittest.mock import patch
e=Path(__file__).parent
os.environ['OPENJARVIS_HOME']=str(e/'sdk-probe-home')
sys.path.insert(0, str(Path.cwd()))
def denied(*a,**kw): raise AssertionError('real network prohibited')
socket.socket.connect=socket.socket.connect_ex=socket.getaddrinfo=denied
import httpx
from openjarvis import Jarvis
from openjarvis.core.config import JarvisConfig
from openjarvis.core.events import EventType
from openjarvis.engine.ollama import OllamaEngine
from src.brain.work_tools import bind_work,WorkBinding,WorkLedger,WorkCapabilities
requests=[]; events=[]
answers=iter([{'final_answer':'control'}, {'action':'calculator','action_input':{'expression':'2+2'}},{'final_answer':'four'},{'final_answer':'control again'}])
def mock(req):
    assert req.method=='POST' and req.url.path=='/api/chat'
    requests.append(json.loads(req.content))
    return httpx.Response(200,json={'message':{'role':'assistant','content':json.dumps(next(answers))},'done':True})
raw=OllamaEngine(host='http://mock.invalid')
raw._client.close()
raw._client=httpx.Client(base_url='http://mock.invalid',transport=httpx.MockTransport(mock))
cfg=JarvisConfig(); cfg.telemetry.enabled=False; cfg.analytics.enabled=False; cfg.security.audit_log_path=str(e/'sdk-probe-home/audit.db')
model='qwen3-8b-uncensored'
j=Jarvis(config=cfg,model=model,engine_key='ollama')
for kind in [EventType.INFERENCE_END,EventType.TOOL_CALL_START,EventType.TOOL_CALL_END]:
    j._bus.subscribe(kind,lambda ev:events.append([ev.event_type.value,ev.data]))
with patch('openjarvis.sdk.get_engine',return_value=('ollama',raw)):
    j._ensure_engine()
base=j._engine
class View:
    def __init__(self,inner): self.inner=inner
    def __getattr__(self,key): return getattr(self.inner,key)
    def generate(self,messages,**kw):
        outgoing=list(messages)
        assert outgoing[0].role.value=='system'
        outgoing[0]=replace(outgoing[0],content=outgoing[0].content+'\nFor this request the wire format overrides the text format above. Return one JSON object with action and object action_input, or final_answer.')
        return self.inner.generate(outgoing,response_format={'type':'json_object'},**kw)
view=copy.copy(j); view._engine=View(base)
def ask(jar,tools):
    return jar.ask_full('Synthetic transport proof only.',agent='native_react',tools=tools,context=False,max_tokens=2048)
control=ask(j,['calculator'])
binding=WorkBinding(e,'probe-request','probe-session','probe-task')
caps=WorkCapabilities(research_json=json.dumps([{'source_id':'S'+str(i)} for i in (1,2,3)]))
with bind_work(binding,WorkLedger(),caps):
    structured=ask(view,['calculator','think','ultima_work_research_write','ultima_work_file_read'])
last=ask(j,['calculator'])
assert j._engine is base and base._inner.__class__.__name__=='GuardrailsEngine'
assert [r.get('format') for r in requests]==[None,'json','json',None]
assert structured['tool_results'][0]['success'] and structured['turns']==2
assert sum(k=='inference_end' for k,_ in events)==4
out={'proof':'mock transport; literal scripted controls and calculator action/final; no real inference','engine_stack':[type(base).__name__,type(base._inner).__name__,type(raw).__name__],'result':structured,'http_requests':requests,'events':events}
(e/'sdk-mock-boundary.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
print('PASS',len(requests),len(events),structured['tool_results'])
j.close()
