import socket,sys,os,json
from pathlib import Path
def deny(*a,**k): raise AssertionError("sockets prohibited")
socket.socket.connect=socket.socket.connect_ex=socket.getaddrinfo=deny
import run_local_role_prefix as h, httpx
core=h.frozen_core()
sys.path.insert(0,str(core.CHECKOUT))
from src.brain.agent_server import _research_sampler_schema
template=h.read(h.PREP/'S4-template.json')
body=dict(model=core.MODEL,messages=template['preflight_messages'],format=_research_sampler_schema(template['schema']),options=dict(num_ctx=16384,temperature=0,num_predict=480),tools=[],think=False,stream=False,truncate=False,shift=False)
class Ledger:
    deadline=36.
    def clock(self): return now[0]
    def stamp(self,name):
        if now[0]>=self.deadline: raise TimeoutError(name)
orig=h.read
out=[]
for mode in ('expiry_during_template_read','rejected_entity'):
    now=[35.99]; transports=[]; attempts=[]; root=Path(os.environ['LOCAL_ROLE_REVIEW'])/mode;root.mkdir()
    def slow_read(p):
        result=orig(p)
        if mode=='expiry_during_template_read': now[0]=37.
        return result
    h.read=slow_read
    def transport(req):
        transports.append(now[0])
        return httpx.Response(200,json={})
    if mode=='rejected_entity':body['messages'][1]['content']+=' '
    with core.observe_http(attempts,lambda:'trial'), httpx.Client(base_url=core.ORIGIN,transport=httpx.MockTransport(transport),event_hooks={'request':[h.wire_gate(core,'S4')]}) as c:
        leaf=core.NativeLeaf(c,Ledger(),root,lambda:core.DIGEST)
        try: leaf.io('POST','/api/chat',json=body)
        except Exception as exc: reason=str(exc)
        else: raise AssertionError('expected rejection')
    out.append(dict(mode=mode,deadline=36,transport_times=transports,observed_post_rows=len(attempts),native_posts=leaf.posts,native_post_intents=leaf.post_intents,error=reason))
assert out[0]['transport_times']==[37.] and out[1]['transport_times']==[] and out[1]['native_posts']==1
print(json.dumps(out,indent=2))
