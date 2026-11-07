"""Static-function tests: no product imports, service, process or network calls."""
from pathlib import Path
import ast,contextlib,datetime as dt,hashlib,json,sys,types,unittest
N=Path(__file__).resolve().parents[1];Q=N.parent/'e02-source13-exact-probe-20261106'
RAW=(N/'harness/adapter.py').read_text('utf-8');TREE=ast.parse(RAW)
def require(ok,message):
    if not ok:raise ValueError(message)
def functions(*names,**extra):
    nodes=[n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name in names]
    ns=dict(Path=Path,hashlib=hashlib,json=json,require=require,PROTECTED_BASELINE=Q/'inputs/protected-baseline.json',**extra)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'harness-functions-only','exec'),ns)
    return ns

class LiveBoundary(unittest.TestCase):
    def test_candidate_environment_rebinds_legacy_helper_path(self):
        current=Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-e02-native-rejection\UltimaAgent')
        legacy=dict(PYTHONPATH='old-product-root',NO_PROXY='localhost,127.0.0.1,::1',TEMP='owned-temp')
        helper=types.SimpleNamespace(environment=lambda folder:dict(legacy))
        ns=functions('candidate_environment',C=current)
        result=ns['candidate_environment'](helper,N/'synthetic')
        self.assertEqual(result,dict(legacy,PYTHONPATH=str(current)))
        self.assertEqual(legacy['PYTHONPATH'],'old-product-root')

    def protected(self,count=7):
        roles=['ollama','brain_primary','brain_runtime_child','voice_primary','voice_runtime_child','voice_listener_primary','voice_listener_runtime_child']
        entries=[dict(role=roles[i],pid=i+100,parent_pid=i+50,created_filetime=100000+i,exe=sys.executable,
            command_line_sha256=hashlib.sha256(('command'+str(i)).encode('utf-16le')).hexdigest()) for i in range(count)]
        identities=[{k:r[k] for k in ('pid','created_filetime','exe')} for r in entries]
        rows={r['pid']:dict(ParentProcessId=r['parent_pid'],CommandLine='command'+str(i)) for i,r in enumerate(entries)}
        baseline=dict(protected5=entries[:5],protected_listener_pair=entries[5:],protected_process_count=count)
        p4=types.SimpleNamespace(protected=lambda:identities,identity=lambda pid:next(v for v in identities if v['pid']==pid),
            process_snapshot=lambda *a,**k:rows,snapshot_identity_matches=lambda key,row:True)
        ns=functions('validate_protected_members','validate_protected_native_members',load=lambda p:baseline)
        return ns['validate_protected_members'],identities,rows,p4
    def test_accepts_all_seven_protected_identities(self):
        check,ids,rows,p4=self.protected();self.assertEqual(check(ids,p4),ids)
    def test_rejects_legacy_five(self):
        check,ids,rows,p4=self.protected(5)
        with self.assertRaises(ValueError):check(ids,p4)
    def test_rejects_missing_listener(self):
        check,ids,rows,p4=self.protected();ids.pop()
        with self.assertRaises(ValueError):check(ids,p4)
    def test_rejects_parent_drift(self):
        check,ids,rows,p4=self.protected();rows[ids[-1]['pid']]['ParentProcessId']+=1
        with self.assertRaises(ValueError):check(ids,p4)
    def test_rejects_command_drift(self):
        check,ids,rows,p4=self.protected();rows[ids[-1]['pid']]['CommandLine']='different command'
        with self.assertRaises(ValueError):check(ids,p4)
    def test_rejects_native_creation_drift(self):
        check,ids,rows,p4=self.protected();p4.identity=lambda pid:dict(ids[0],created_filetime=1)
        with self.assertRaises(ValueError):check(ids,p4)
    def test_binds_current_product_and_helper(self):
        ns=dict(Path=Path,HERE=N/'harness',V=N,T=N.parent)
        nodes=[n for n in TREE.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('C','CANDIDATE','P4','P1')]
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'constant-bindings','exec'),ns)
        self.assertEqual(ns['CANDIDATE'],'d860b2ab4e4d9974e33c96472e4ea15abb807280')
        self.assertEqual(ns['C'],Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-e02-native-rejection\UltimaAgent'))
        self.assertEqual(ns['P4'],N.parent/'e01-source13-round3-20261106/code/controller.py')
    def test_product_argv_retains_research_and_original_question(self):
        ns=functions('candidate_argv',HERE=N/'harness',corpus=lambda:dict(query='ORIGINAL QUESTION'))
        server,cli=ns['candidate_argv'](dict(folder=N/'future',port=12345,request_id='r',session_id='s'))
        self.assertIn('--work-research',server);self.assertIn('--isolated',server)
        self.assertIn('--work',cli);self.assertIn('--research',cli);self.assertEqual(cli[-1],'ORIGINAL QUESTION')
        self.assertNotIn('--model',server+cli)
    def test_actual_child_uses_product_dispatch_without_model_patch(self):
        events=[];ns=functions('actual_child_entry',sys=sys,consume_clearance=lambda *a:events.append('clearance'),
            candidate_import_path=contextlib.nullcontext,install_browser_fixture=lambda:events.append('browser'),
            install_trusted_exports=lambda folder:events.append('observer'),candidate_argv=lambda c:([1,2,3,4,5,6,'--isolated','--work-research'],[]))
        context=dict(mode='actual',folder=N/'future',budget=types.SimpleNamespace(pre=lambda v:events.append('admission')))
        old=list(sys.argv)
        ns['actual_child_entry'](context,None,[],None,dispatch=lambda mod,**kw:events.append((mod,kw['run_name'],sys.argv[1:])))
        self.assertEqual(sys.argv,old)
        self.assertEqual(events,['clearance','browser','observer','admission',('src.brain.agent_server','__main__',['--isolated','--work-research'])])
    def test_browser_fixture_does_not_replace_native_client_or_transport(self):
        import unittest.mock
        client=type('Client',(),{'send':lambda self:None});send=client.send;transport=object()
        fake_http=types.SimpleNamespace(Client=client,HTTPTransport=transport,request=lambda:None,
            Response=lambda *a,**k:(a,k),Request=lambda *a:tuple(a))
        fake_ddgs=types.SimpleNamespace(DDGS=object())
        socket=types.SimpleNamespace(getaddrinfo=lambda *a:[],AF_INET=2,SOCK_STREAM=1)
        source=dict(final_url='https://raw.githubusercontent.com/fixed',body='original source',content_type='text/plain')
        ns=functions('install_browser_fixture',socket=socket,corpus=lambda:dict(sources=[source]))
        with unittest.mock.patch.dict(sys.modules,{'httpx':fake_http,'ddgs':fake_ddgs}):ns['install_browser_fixture']()
        self.assertIs(fake_http.Client,client);self.assertIs(client.send,send);self.assertIs(fake_http.HTTPTransport,transport)
        self.assertEqual(fake_http.request('GET',source['final_url'],follow_redirects=False,timeout=5)[1]['content'],b'original source')
        with self.assertRaises(ValueError):fake_http.request('POST','http://127.0.0.1:11434/api/chat',follow_redirects=False,timeout=5)

if __name__=='__main__':unittest.main(verbosity=2)
